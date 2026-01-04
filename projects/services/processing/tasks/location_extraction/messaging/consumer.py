#!/usr/bin/env python3
"""
Location Extraction - Raw Kafka Consumer
=========================================
A standalone consumer for testing that:
1. Consumes messages from KAFKA_TOPIC_LOCATION_INPUT
2. Processes text with the LLM pipeline
3. Writes results to the database
4. Optionally produces output to KAFKA_TOPIC_LOCATION_OUTPUT

Usage:
    python -m projects.services.processing.tasks.location_extraction.kafka_files.consumer

Environment variables (from .env):
    - KAFKA_BOOTSTRAP_SERVERS
    - KAFKA_TOPIC_LOCATION_INPUT
    - KAFKA_TOPIC_LOCATION_OUTPUT
    - KAFKA_CONSUMER_GROUP
    - DB_* for database connection
    - LLM_* for LLM configuration
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, UTC

# Setup path for imports
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables from root .env
# project_root is already defined above (5 levels up from this file)
root_env_path = project_root / ".env"
local_env_path = Path(__file__).resolve().parent.parent / ".env"

if root_env_path.exists():
    load_dotenv(root_env_path)
    print(f"Loaded .env from: {root_env_path}")
elif local_env_path.exists():
    load_dotenv(local_env_path)
    print(f"Loaded .env from: {local_env_path}")
else:
    load_dotenv()
    print("Using default dotenv search")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after path setup
from kafka import KafkaConsumer, KafkaProducer
from projects.services.processing.tasks.location_extraction.config.settings import (
    DatabaseConfig, KafkaConfig, settings
)
from projects.services.processing.tasks.location_extraction.dao.dao import LocationExtractionDAO
from projects.services.processing.tasks.location_extraction.dto.persistence import PersistenceLocationDTO
from projects.services.processing.tasks.location_extraction.dto.location_result import (
    LocationExtractionResult, Location, PrimaryLocation, ExtractionMeta
)

# Try to import the LLM pipeline
LLM_AVAILABLE = False
try:
    from projects.services.processing.tasks.location_extraction.pipelines.extraction_pipeline import (
        ExtractionPipeline
    )
    LLM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LLM pipeline not available: {e}")


class LocationExtractionConsumer:
    """
    Kafka consumer that processes location extraction requests.
    """
    
    def __init__(self, use_llm: bool = True):
        """Initialize consumer with database and optional LLM."""
        self.kafka_config = KafkaConfig.from_env()
        self.db_config = DatabaseConfig.from_env()
        
        # DEBUG: Print config being used
        logger.info(f"=== CONFIG DEBUG ===")
        logger.info(f"Kafka Bootstrap Servers: {self.kafka_config.bootstrap_servers}")
        logger.info(f"DB Host: {self.db_config.host}")
        logger.info(f"===================")
        
        # DAO auto-initializes tables (auto_init=True by default)
        self.dao = LocationExtractionDAO(self.db_config)
        
        self.use_llm = use_llm and LLM_AVAILABLE
        self.pipeline = None
        
        if self.use_llm:
            try:
                self.pipeline = ExtractionPipeline()
                logger.info("LLM pipeline initialized")
            except Exception as e:
                logger.error(f"Failed to initialize LLM pipeline: {e}")
                self.use_llm = False
        
        def safe_json_deserializer(m):
            try:
                return json.loads(m.decode('utf-8'))
            except Exception as e:
                logger.error(f"❌ Failed to deserialize message: {e}")
                return None

        # Initialize Kafka consumer
        self.consumer = KafkaConsumer(
            self.kafka_config.input_topic,
            bootstrap_servers=self.kafka_config.bootstrap_servers,
            group_id=self.kafka_config.consumer_group,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=safe_json_deserializer,
            key_deserializer=lambda k: k.decode('utf-8') if k else None
        )
        
        # Initialize Kafka producer for output
        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_config.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            request_timeout_ms=240000,
            linger_ms=10,
            batch_size=32768,
            acks=1,
            retries=5
        )
        
        logger.info(f"Consumer initialized for topic: {self.kafka_config.input_topic}")
        logger.info(f"LLM processing: {'enabled' if self.use_llm else 'disabled (mock mode)'}")
    
    def process_message(self, message) -> dict:
        """
        Process a single message and return the result.
        
        Expected message format:
        {
            "source_id": "...",
            "source_type": "youtube_comment",
            "text": "...",
            "timestamp": "..."
        }
        """
        data = message.value
        if data is None:
            logger.warning(f"Skipping empty or invalid message at offset {message.offset}")
            return None

        source_id = data.get('source_id', 'unknown')
        source_type = data.get('source_type', 'unknown')
        text = data.get('text', '')
        
        logger.info(f"⚙️ Processing message ID: {source_id} (Type: {source_type})")
        logger.debug(f"Raw text (first 50 chars): {text[:50]}...")
        
        if self.use_llm and self.pipeline:
            # Use LLM pipeline for extraction
            try:
                from projects.services.processing.tasks.location_extraction.dto import UnifiedTextEvent
                event = UnifiedTextEvent(
                    source=source_type,
                    source_type=source_type,
                    external_id=source_id,
                    text=text
                )
                extraction_result = self.pipeline.process(event)
            except Exception as e:
                logger.error(f"LLM extraction failed: {e}")
                extraction_result = self._create_mock_result(text)
        else:
            # Mock result for testing without LLM
            extraction_result = self._create_mock_result(text)
        
        # Save to database
        dto = PersistenceLocationDTO(
            source_id=source_id,
            source_type=source_type,
            raw_text=text,
            extraction_result=extraction_result
        )
        
        saved = self.dao.save(dto)
        
        if saved:
            logger.info(f"Saved extraction for {source_id}")
        else:
            logger.warning(f"Failed to save extraction for {source_id} (may already exist)")
        
        # Prepare output message
        output = {
            "source_id": source_id,
            "source_type": source_type,
            "extraction_result": extraction_result.model_dump(),
            "processed_at": datetime.now(UTC).isoformat(),
            "success": saved is not None
        }
        
        return output
    
    def _create_mock_result(self, text: str) -> LocationExtractionResult:
        """Create a mock extraction result for testing."""
        # Simple mock: just return empty result
        return LocationExtractionResult(
            locations=[],
            primary_location=None,
            overall_score=0.0,
            meta=ExtractionMeta(extractor="llm", fallback_used=False)
        )
    
    def run(self, max_messages: int = None):
        """
        Run the consumer loop.
        
        Args:
            max_messages: Stop after processing this many messages (None = run forever)
        """
        logger.info("Starting consumer loop...")
        message_count = 0
        
        try:
            while True:
                try:
                    # Manually poll for messages to have better control on Windows/Python 3.12
                    message_pack = self.consumer.poll(timeout_ms=1000)
                    
                    for tp, messages in message_pack.items():
                        for message in messages:
                            try:
                                logger.info(f"📥 Received message {message.value} from {tp.topic} [partition {tp.partition}, offset {message.offset}]")
                                output = self.process_message(message)
                                logger.info(f"📤 Sent message to {self.kafka_config.output_topic} [partition {tp.partition}, offset {message.offset}]: {output}")
                                
                                # Produce output message if processing was successful
                                if output:
                                    self.producer.send(
                                        self.kafka_config.output_topic,
                                        key=output['source_id'],
                                        value=output
                                    )
                                    self.producer.flush()
                                    logger.info(f"Output sent to {self.kafka_config.output_topic}")
                                
                                message_count += 1
                                if max_messages and message_count >= max_messages:
                                    logger.info(f"Reached max messages ({max_messages}), stopping")
                                    return
                                    
                            except Exception as e:
                                logger.error(f"Error processing message: {e}", exc_info=True)
                                
                except ValueError as ve:
                    # This is a specific workaround for kafka-python on Windows + Python 3.12
                    if "Invalid file descriptor: -1" in str(ve):
                        logger.warning("Caught selector error -1 (common on Windows). Retrying poll...")
                        continue
                    raise ve
                    
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            try:
                self.consumer.close()
                self.producer.close()
            except Exception as e:
                logger.error(f"Error during close: {e}")
            logger.info("Consumer closed")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Location Extraction Kafka Consumer")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM processing (mock mode)")
    parser.add_argument("--max-messages", type=int, default=None, help="Max messages to process")
    args = parser.parse_args()
    
    consumer = LocationExtractionConsumer(use_llm=not args.no_llm)
    consumer.run(max_messages=args.max_messages)


if __name__ == "__main__":
    main()
