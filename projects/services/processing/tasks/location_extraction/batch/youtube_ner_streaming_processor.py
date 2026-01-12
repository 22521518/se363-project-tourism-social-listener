#!/usr/bin/env python3
"""
YouTube NER Streaming Processor for Location Extraction.

Combines batch processing (historical data) with Kafka streaming (new data):
1. Phase 1: Process ALL unprocessed YouTube comments from database
2. Phase 2: Once caught up, start Kafka consumer and run indefinitely

Usage:
    python -m projects.services.processing.tasks.location_extraction.batch.youtube_ner_streaming_processor
    
Environment Variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD - Database configuration
    KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_LOCATION_INPUT - Kafka configuration
    BATCH_SIZE - Number of records to process per batch (default: 100)
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from pathlib import Path

# Setup path for imports
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables - try multiple paths in order of priority
def load_env_files():
    """Load .env files from multiple possible locations."""
    current_file = Path(__file__).resolve()
    
    possible_paths = [
        # 1. Local .env (location_extraction/.env)
        current_file.parent.parent / ".env",
        # 2. projects/.env
        current_file.parents[4] / ".env",  # batch -> location_extraction -> tasks -> processing -> services -> projects
        # 3. airflow root .env
        current_file.parents[5] / ".env",  # projects -> airflow
        # 4. Docker paths
        Path("/opt/airflow/projects/services/processing/tasks/location_extraction/.env"),
        Path("/opt/airflow/projects/.env"),
        Path("/opt/airflow/.env"),
    ]
    
    loaded = False
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            print(f"✅ YouTube NER Streaming Processor: Loaded .env from: {env_path}")
            loaded = True
            break
    
    if not loaded:
        load_dotenv()
        print("⚠️ YouTube NER Streaming Processor: Using default dotenv search")

load_env_files()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after path setup
from kafka import KafkaConsumer, KafkaProducer

from projects.services.processing.tasks.location_extraction.config.settings import (
    DatabaseConfig, KafkaConfig
)
from projects.services.processing.tasks.location_extraction.dto import (
    UnifiedTextEvent, LocationExtractionResult
)
from projects.services.processing.tasks.location_extraction.dto.persistence import PersistenceLocationDTO
from projects.services.processing.tasks.location_extraction.dto.location_result import Location
from projects.services.processing.tasks.location_extraction.extractors.ner_extractor import NERLocationExtractor
from projects.services.processing.tasks.location_extraction.dao.dao import LocationExtractionDAO
from projects.services.processing.tasks.location_extraction.batch.youtube_ner_batch_processor import YouTubeNERBatchProcessor


class YouTubeNERStreamingProcessor:
    """
    Combined batch + streaming processor for YouTube location extraction.
    
    Uses NER model (Davlan/xlm-roberta-base-ner-hrl) for both batch and streaming modes.
    """
    
    SOURCE_TYPE = "youtube_comment"
    
    def __init__(self, batch_size: int = 100):
        """
        Initialize the streaming processor.
        
        Args:
            batch_size: Number of records to process per batch in catch-up phase
        """
        self.batch_size = batch_size
        
        # Initialize configurations
        self.db_config = DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "airflow"),
            password=os.getenv("DB_PASSWORD", "airflow"),
            database=os.getenv("DB_NAME", "airflow")
        )
        self.kafka_config = KafkaConfig.from_env()
        
        # Initialize NER extractor (shared between batch and streaming)
        logger.info("Initializing NER extractor (this may take a moment on first run)...")
        self.extractor = NERLocationExtractor()
        
        # Initialize DAO
        self.dao = LocationExtractionDAO(self.db_config)
        
        logger.info(f"YouTubeNERStreamingProcessor initialized - batch_size={batch_size}")
        logger.info(f"Kafka bootstrap: {self.kafka_config.bootstrap_servers}")
        logger.info(f"Kafka input topic: {self.kafka_config.input_topic}")
    
    def run_batch_catchup(self) -> Dict[str, Any]:
        """
        Phase 1: Process ALL unprocessed records from database.
        
        Loops until no more unprocessed records are found.
        """
        logger.info("=" * 60)
        logger.info("PHASE 1: Batch Catch-up - Processing all historical data")
        logger.info("=" * 60)
        
        total_processed = 0
        total_failed = 0
        iteration = 0
        
        # Create batch processor with unlimited max_records
        batch_processor = YouTubeNERBatchProcessor(
            batch_size=self.batch_size,
            max_records=self.batch_size * 10,  # Fetch 10 batches at a time
            db_config=self.db_config
        )
        # Share the NER extractor to avoid loading model twice
        batch_processor.extractor = self.extractor
        
        while True:
            iteration += 1
            logger.info(f"Catch-up iteration {iteration}...")
            
            # Fetch unprocessed comments
            comments = batch_processor.fetch_unprocessed_comments(limit=self.batch_size * 10)
            
            if not comments:
                logger.info("No more unprocessed records found. Catch-up complete!")
                break
            
            # Process in batches
            for i in range(0, len(comments), self.batch_size):
                batch = comments[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                
                logger.info(f"Processing batch {batch_num} ({len(batch)} comments)...")
                successful, failed = batch_processor.process_batch(batch)
                total_processed += successful
                total_failed += failed
                
                logger.info(f"Batch {batch_num} complete: {successful} successful, {failed} failed")
        
        stats = {
            "phase": "batch_catchup",
            "total_processed": total_processed,
            "total_failed": total_failed,
            "iterations": iteration
        }
        
        logger.info(f"Phase 1 complete: {stats}")
        return stats
    
    def run_streaming(self):
        """
        Phase 2: Start Kafka consumer and process messages continuously.
        
        Runs indefinitely until interrupted.
        """
        logger.info("=" * 60)
        logger.info("PHASE 2: Streaming - Consuming new data from Kafka")
        logger.info("=" * 60)
        
        def safe_json_deserializer(m):
            try:
                return json.loads(m.decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to deserialize message: {e}")
                return None
        
        # Initialize Kafka consumer
        consumer = KafkaConsumer(
            self.kafka_config.input_topic,
            bootstrap_servers=self.kafka_config.bootstrap_servers,
            group_id=self.kafka_config.consumer_group,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=safe_json_deserializer,
            key_deserializer=lambda k: k.decode('utf-8') if k else None
        )
        
        # Initialize Kafka producer for output
        producer = KafkaProducer(
            bootstrap_servers=self.kafka_config.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            request_timeout_ms=240000,
            linger_ms=10,
            batch_size=32768,
            acks=1,
            retries=5
        )
        
        logger.info(f"Streaming consumer started for topic: {self.kafka_config.input_topic}")
        message_count = 0
        
        try:
            while True:
                try:
                    message_pack = consumer.poll(timeout_ms=1000)
                    
                    for tp, messages in message_pack.items():
                        for message in messages:
                            try:
                                data = message.value
                                if data is None:
                                    continue
                                
                                source_id = data.get('source_id', 'unknown')
                                source_type = data.get('source_type', 'unknown')
                                text = data.get('text', '')
                                
                                logger.info(f"[Streaming] Processing: {source_id}")
                                
                                # Extract locations using NER
                                result = self.extractor.extract(text)
                                
                                # Convert to LocationExtractionResult
                                locations = [
                                    Location(
                                        word=loc["word"],
                                        score=loc["score"],
                                        entity_group=loc.get("entity_group", "LOC"),
                                        start=loc.get("start", 0),
                                        end=loc.get("end", 0)
                                    )
                                    for loc in result.get("locations", [])
                                ]
                                extraction_result = LocationExtractionResult(locations=locations)
                                
                                # Save to database
                                dto = PersistenceLocationDTO(
                                    source_id=source_id,
                                    source_type=source_type,
                                    raw_text=text,
                                    extraction_result=extraction_result
                                )
                                
                                saved = self.dao.save(dto)
                                
                                if saved:
                                    logger.info(f"[Streaming] Saved: {source_id}")
                                    message_count += 1
                                else:
                                    logger.warning(f"[Streaming] Failed to save (may already exist): {source_id}")
                                
                                # Send output message
                                output = {
                                    "source_id": source_id,
                                    "source_type": source_type,
                                    "extraction_result": extraction_result.model_dump(),
                                    "processed_at": datetime.now(UTC).isoformat(),
                                    "success": saved is not None
                                }
                                producer.send(
                                    self.kafka_config.output_topic,
                                    key=source_id,
                                    value=output
                                )
                                producer.flush()
                                
                            except Exception as e:
                                logger.error(f"Error processing message: {e}", exc_info=True)
                                
                except ValueError as ve:
                    if "Invalid file descriptor: -1" in str(ve):
                        logger.warning("Caught selector error -1, retrying...")
                        continue
                    raise ve
                    
        except KeyboardInterrupt:
            logger.info(f"Streaming interrupted. Processed {message_count} messages.")
        finally:
            try:
                consumer.close()
                producer.close()
            except Exception as e:
                logger.error(f"Error during close: {e}")
            logger.info("Streaming consumer closed")
    
    def run(self):
        """
        Run the complete pipeline:
        1. Batch catch-up of all historical data
        2. Start streaming for new data
        """
        logger.info("Starting YouTube NER Streaming Processor")
        logger.info(f"Database: {self.db_config.user}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}")
        
        # Phase 1: Batch catch-up
        batch_stats = self.run_batch_catchup()
        
        # Phase 2: Streaming
        self.run_streaming()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="YouTube NER Streaming Processor - Batch + Kafka streaming"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("BATCH_SIZE", "100")),
        help="Number of records per batch (default: 100)"
    )
    parser.add_argument(
        "--skip-batch",
        action="store_true",
        help="Skip batch catch-up and go straight to streaming"
    )
    parser.add_argument(
        "--batch-only",
        action="store_true",
        help="Only run batch catch-up, don't start streaming"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    processor = YouTubeNERStreamingProcessor(batch_size=args.batch_size)
    
    if args.skip_batch:
        logger.info("Skipping batch catch-up, starting streaming directly...")
        processor.run_streaming()
    elif args.batch_only:
        logger.info("Batch-only mode, will exit after catch-up...")
        processor.run_batch_catchup()
    else:
        processor.run()


if __name__ == "__main__":
    main()
