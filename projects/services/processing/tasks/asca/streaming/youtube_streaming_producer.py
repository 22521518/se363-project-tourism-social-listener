#!/usr/bin/env python3
"""
YouTube Streaming Producer for ASCA
====================================
Real-time streaming producer that reads YouTube comments from the database
and sends them to Kafka for ASCA processing.

Features:
- Continuous streaming mode with configurable interval
- Reads unprocessed comments (not yet in asca_extractions)
- Joins with video info for context
- Sends to ASCA Kafka topic for processing

Usage:
    python -m projects.services.processing.tasks.asca.streaming.youtube_streaming_producer
    
    # With options
    python -m ... --batch-size 100 --interval 10 --max-messages 1000
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup path for imports
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load .env
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try Kafka import
KAFKA_AVAILABLE = False
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    logger.warning("kafka-python-ng not installed")


class YouTubeStreamingProducer:
    """
    Streaming producer that reads YouTube comments from database
    and sends them to Kafka for ASCA processing.
    
    Runs continuously in streaming mode, checking for new unprocessed
    comments at configurable intervals.
    """
    
    def __init__(
        self,
        batch_size: int = 100,
        check_interval: int = 10,  # seconds between checks
        max_messages: Optional[int] = None,  # None = unlimited
        kafka_bootstrap_servers: str = None,
        kafka_topic: str = None,
        db_config: dict = None
    ):
        """
        Initialize the streaming producer.
        
        Args:
            batch_size: Number of records to fetch and send per batch
            check_interval: Seconds to wait between database checks
            max_messages: Maximum messages to send (None = unlimited streaming)
            kafka_bootstrap_servers: Kafka servers
            kafka_topic: Kafka topic for ASCA input
            db_config: Database configuration dict
        """
        self.batch_size = batch_size
        self.check_interval = check_interval
        self.max_messages = max_messages
        self.messages_sent = 0
        
        # Database config
        self.db_config = db_config or {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER", "airflow"),
            "password": os.getenv("DB_PASSWORD", "airflow"),
            "database": os.getenv("DB_NAME", "airflow"),
        }
        
        # Kafka config
        self.kafka_bootstrap_servers = kafka_bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"
        )
        self.kafka_topic = kafka_topic or os.getenv(
            "KAFKA_TOPIC_ASCA_INPUT", "asca-input"
        )
        
        # Initialize database
        connection_string = (
            f"postgresql+psycopg2://{self.db_config['user']}:{self.db_config['password']}"
            f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize Kafka producer
        self.producer = None
        if KAFKA_AVAILABLE:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.kafka_bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    request_timeout_ms=30000,
                    linger_ms=10,
                    batch_size=32768,
                    acks=1,
                    retries=3
                )
                logger.info(f"Kafka producer initialized: {self.kafka_bootstrap_servers}")
            except Exception as e:
                logger.error(f"Failed to initialize Kafka producer: {e}")
        
        logger.info(
            f"YouTubeStreamingProducer initialized - "
            f"batch_size={batch_size}, interval={check_interval}s, "
            f"topic={self.kafka_topic}"
        )
    
    @property
    def is_kafka_available(self) -> bool:
        """Check if Kafka producer is available."""
        return self.producer is not None
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def fetch_unprocessed_comments(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Fetch YouTube comments not yet processed by ASCA.
        
        Joins youtube_comments with youtube_videos for context.
        Excludes comments already in asca_extractions table.
        
        Returns:
            List of comment dictionaries
        """
        limit = limit or self.batch_size
        
        query = text("""
            SELECT 
                c.id AS comment_id,
                c.video_id,
                c.text AS comment_text,
                c.author_display_name,
                c.published_at AS comment_published_at,
                v.title AS video_title,
                v.channel_id
            FROM youtube_comments c
            INNER JOIN youtube_videos v ON c.video_id = v.id
            LEFT JOIN asca_extractions ae 
                ON c.id = ae.source_id 
                AND ae.source_type = 'youtube_comment'
            WHERE ae.id IS NULL
                AND c.text IS NOT NULL
                AND LENGTH(TRIM(c.text)) > 0
            ORDER BY c.published_at DESC
            LIMIT :limit
        """)
        
        try:
            with self.get_session() as session:
                result = session.execute(query, {"limit": limit})
                rows = result.fetchall()
                columns = result.keys()
                
                comments = [dict(zip(columns, row)) for row in rows]
                
                if comments:
                    logger.info(f"Fetched {len(comments)} unprocessed comments")
                
                return comments
                
        except Exception as e:
            logger.error(f"Error fetching comments: {e}", exc_info=True)
            return []
    
    def prepare_message(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a Kafka message from a comment.
        
        Args:
            comment: Comment dictionary from database
            
        Returns:
            Message dictionary for Kafka
        """
        comment_text = (comment.get("comment_text") or "").strip()
        video_title = (comment.get("video_title") or "").strip()
        
        # Combine text for better context
        if video_title:
            combined_text = f"[Video: {video_title}] {comment_text}"
        else:
            combined_text = comment_text
        
        return {
            "source_id": comment.get("comment_id"),
            "source_type": "youtube_comment",
            "text": combined_text,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": {
                "video_id": comment.get("video_id"),
                "video_title": video_title,
                "channel_id": comment.get("channel_id"),
                "author": comment.get("author_display_name"),
                "original_text": comment_text,
                "published_at": str(comment.get("comment_published_at"))
            }
        }
    
    def send_batch(self, comments: List[Dict[str, Any]]) -> int:
        """
        Send a batch of comments to Kafka.
        
        Args:
            comments: List of comment dictionaries
            
        Returns:
            Number of successfully sent messages
        """
        if not self.is_kafka_available:
            logger.warning("Kafka not available, skipping send")
            return 0
        
        sent = 0
        for comment in comments:
            try:
                message = self.prepare_message(comment)
                
                self.producer.send(
                    self.kafka_topic,
                    key=message["source_id"],
                    value=message
                )
                sent += 1
                
            except Exception as e:
                logger.error(f"Error sending message: {e}")
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        
        if sent > 0:
            logger.info(f"📤 Sent {sent} messages to {self.kafka_topic}")
        
        return sent
    
    def run_once(self) -> int:
        """
        Run one iteration: fetch and send batch.
        
        Returns:
            Number of messages sent
        """
        comments = self.fetch_unprocessed_comments()
        
        if not comments:
            return 0
        
        sent = self.send_batch(comments)
        self.messages_sent += sent
        
        return sent
    
    def run_streaming(self):
        """
        Run in continuous streaming mode.
        
        Continuously checks for new unprocessed comments and sends them
        to Kafka. Stops when max_messages is reached (if set) or on interrupt.
        """
        logger.info("Starting streaming mode...")
        logger.info(f"Max messages: {self.max_messages or 'unlimited'}")
        
        try:
            while True:
                # Check if max reached
                if self.max_messages and self.messages_sent >= self.max_messages:
                    logger.info(f"Reached max messages ({self.max_messages}), stopping")
                    break
                
                # Fetch and send
                remaining = None
                if self.max_messages:
                    remaining = self.max_messages - self.messages_sent
                
                limit = min(self.batch_size, remaining) if remaining else self.batch_size
                
                comments = self.fetch_unprocessed_comments(limit)
                
                if comments:
                    sent = self.send_batch(comments)
                    self.messages_sent += sent
                    
                    logger.info(f"Total sent: {self.messages_sent}")
                else:
                    logger.debug("No new comments, waiting...")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.close()
        
        logger.info(f"Streaming complete. Total messages sent: {self.messages_sent}")
        return self.messages_sent
    
    def close(self):
        """Close resources."""
        if self.producer:
            self.producer.close()
            self.producer = None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="YouTube Streaming Producer for ASCA"
    )
    parser.add_argument(
        "--batch-size", type=int,
        default=int(os.getenv("BATCH_SIZE", "100")),
        help="Number of records per batch (default: 100)"
    )
    parser.add_argument(
        "--interval", type=int,
        default=int(os.getenv("CHECK_INTERVAL", "10")),
        help="Seconds between database checks (default: 10)"
    )
    parser.add_argument(
        "--max-messages", type=int, default=None,
        help="Maximum messages to send (default: unlimited)"
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Run once and exit (don't stream)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    producer = YouTubeStreamingProducer(
        batch_size=args.batch_size,
        check_interval=args.interval,
        max_messages=args.max_messages
    )
    
    if args.once:
        sent = producer.run_once()
        logger.info(f"Sent {sent} messages")
        producer.close()
    else:
        producer.run_streaming()


if __name__ == "__main__":
    main()
