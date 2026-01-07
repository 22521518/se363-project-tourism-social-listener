import sys
import os
import json
import logging
from datetime import datetime
from typing import List
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Add the root directory to path
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from projects.services.processing.tasks.intention.config import ConsumerConfig
    from projects.services.processing.tasks.intention.dao import IntentionDAO
    from projects.services.ingestion.youtube.dto import CommentDTO
except ImportError as e:
    logger.error(f"Error importing project modules: {e}")
    logger.error("Make sure project modules are in PYTHONPATH")
    sys.exit(1)


class UnprocessedCommentProducer:
    """Producer that fetches unprocessed YouTube comments and sends them to Kafka."""
    
    def __init__(self, config: ConsumerConfig):
        self.config = config
        self.dao = IntentionDAO(config.database)
        
        # Initialize Kafka Producer
        self.producer = KafkaProducer(
            bootstrap_servers=config.kafka.bootstrap_servers,
            client_id=f"{config.kafka.client_id}_producer",
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',  # Wait for all replicas to acknowledge
            retries=3,
            max_in_flight_requests_per_connection=1  # Ensure ordering
        )
        
        logger.info(f"Kafka Producer initialized for topic: {config.kafka.topic}")
    
    def _comment_to_kafka_message(self, comment: CommentDTO) -> dict:
        """Convert CommentDTO to Kafka message format."""
        return {
            "source": "youtube",
            "externalId": comment.id,
            "rawText": comment.text,
            "createdAt": comment.updated_at.isoformat() if comment.updated_at else None,
            "entityType": "comment",
            "rawPayload": {
                "text": comment.text,
                "video_id": comment.video_id,
            }
        }
    
    def send_to_kafka(self, comment: CommentDTO) -> bool:
        """Send a single comment to Kafka."""
        try:
            message = self._comment_to_kafka_message(comment)
            key = comment.id  # Use comment ID as key for partitioning
            
            future = self.producer.send(
                self.config.kafka.unprocessed_topic,
                key=key,
                value=message
            )
            
            # Wait for send to complete (blocking)
            record_metadata = future.get(timeout=10)
            
            logger.debug(
                f"Sent comment {comment.id} to topic {record_metadata.topic} "
                f"partition {record_metadata.partition} offset {record_metadata.offset}"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send comment {comment.id} to Kafka: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending comment {comment.id}: {e}")
            return False
    
    def process_batch(self, batch_size: int = 100) -> int:
        """
        Fetch unprocessed comments and send them to Kafka.
        
        Args:
            batch_size: Number of comments to process in this batch
            
        Returns:
            Number of successfully sent messages
        """
        try:
            # Fetch unprocessed comments
            unprocessed = self.dao.get_all_unprocessed(
                limit=batch_size,
                offset=0
            )
            
            if not unprocessed:
                logger.info("No unprocessed comments found")
                return 0
            
            logger.info(f"Found {len(unprocessed)} unprocessed comments")
            
            # Send each comment to Kafka
            success_count = 0
            for comment in unprocessed:
                if self.send_to_kafka(comment):
                    success_count += 1
            
            # Ensure all messages are sent
            self.producer.flush()
            
            logger.info(
                f"Successfully sent {success_count}/{len(unprocessed)} "
                f"comments to Kafka"
            )
            
            return success_count
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}", exc_info=True)
            return 0
    
    def run_continuous(self, batch_size: int = 100, interval_seconds: int = 60):
        """
        Run producer continuously, fetching and sending comments at intervals.
        
        Args:
            batch_size: Number of comments to process per batch
            interval_seconds: Wait time between batches
        """
        import time
        
        logger.info(
            f"Starting continuous producer (batch_size={batch_size}, "
            f"interval={interval_seconds}s)"
        )
        
        try:
            while True:
                sent_count = self.process_batch(batch_size)
                
                if sent_count == 0:
                    logger.info(f"No messages sent, waiting {interval_seconds}s...")
                else:
                    logger.info(f"Sent {sent_count} messages")
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            self.close()
    
    def run_once(self, batch_size: int = 100):
        """
        Run producer once and exit.
        
        Args:
            batch_size: Number of comments to process
        """
        logger.info(f"Running producer once (batch_size={batch_size})")
        
        try:
            sent_count = self.process_batch(batch_size)
            logger.info(f"Completed. Sent {sent_count} messages")
        finally:
            self.close()
    
    def close(self):
        """Close Kafka producer connection."""
        if self.producer:
            logger.info("Closing Kafka producer...")
            self.producer.close()
            logger.info("Kafka producer closed")


def main():
    """Main entry point for the producer."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Produce unprocessed YouTube comments to Kafka'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of comments to process per batch (default: 100)'
    )
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run once and exit (default: continuous mode)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Interval in seconds between batches in continuous mode (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = ConsumerConfig.from_env()
        
          # Initialize DAO and tables
        dao = IntentionDAO(config.database)
        try:
            dao.init_db()
            print("Database tables initialized successfully.")
        except Exception as e:
            print(f"Warning: Could not initialize database tables: {e}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Create and run producer
    producer = UnprocessedCommentProducer(config)
    
    if args.run_once:
        producer.run_once(batch_size=args.batch_size)
    else:
        producer.run_continuous(
            batch_size=args.batch_size,
            interval_seconds=args.interval
        )


if __name__ == "__main__":
    main()