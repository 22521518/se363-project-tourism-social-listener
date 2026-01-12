#!/usr/bin/env python3
"""
ASCA Extraction - Raw Kafka Consumer
=====================================
A standalone consumer that:
1. Consumes messages from KAFKA_TOPIC_ASCA_INPUT
2. Processes text with the ASCA pipeline
3. Writes results to the database
4. Produces output to KAFKA_TOPIC_ASCA_OUTPUT

Usage:
    python -m projects.services.processing.tasks.asca.messaging.consumer

Environment variables (from .env):
    - KAFKA_BOOTSTRAP_SERVERS
    - KAFKA_TOPIC_ASCA_INPUT
    - KAFKA_TOPIC_ASCA_OUTPUT
    - KAFKA_CONSUMER_GROUP
    - DB_* for database connection
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
import os

# Load environment variables - try multiple paths
# Priority: 1. projects/.env (shared), 2. asca/.env (local), 3. Default search
env_paths = [
    Path("/opt/airflow/projects/.env"),  # Docker path
    project_root / "projects" / ".env",  # Local dev path
    Path(__file__).resolve().parent.parent / ".env",  # ASCA local .env
]

loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"✅ Loaded .env from: {env_path}")
        loaded = True

if not loaded:
    load_dotenv()
    print("⚠️ Using default dotenv search")

# DEBUG: Print raw env vars
print(f"DEBUG ENV - DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}")
print(f"DEBUG ENV - DB_PORT: {os.getenv('DB_PORT', 'NOT SET')}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after path setup
from kafka import KafkaConsumer, KafkaProducer
from projects.services.processing.tasks.asca.config.settings import (
    DatabaseConfig, KafkaConfig, settings
)
from projects.services.processing.tasks.asca.dao.dao import ASCAExtractionDAO
from projects.services.processing.tasks.asca.dto.persistence import PersistenceASCADTO
from projects.services.processing.tasks.asca.dto.asca_result import (
    ASCAExtractionResult, AspectSentiment, ExtractionMeta
)

# Try to import the ASCA pipeline
PIPELINE_AVAILABLE = False
try:
    from projects.services.processing.tasks.asca.pipelines.asca_pipeline import (
        ASCAExtractionPipeline
    )
    PIPELINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ASCA pipeline not available: {e}")


class ASCAExtractionConsumer:
    """
    Kafka consumer that processes ASCA extraction requests.
    """
    
    def __init__(self, use_pipeline: bool = True):
        """Initialize consumer with database and optional pipeline."""
        self.kafka_config = KafkaConfig.from_env()
        self.db_config = DatabaseConfig.from_env()
        
        # DEBUG: Print config being used
        logger.info(f"{'='*50}")
        logger.info(f"=== DATABASE CONFIG ===")
        logger.info(f"DB Host: {self.db_config.host}")
        logger.info(f"DB Port: {self.db_config.port}")
        logger.info(f"DB Name: {self.db_config.database}")
        logger.info(f"DB User: {self.db_config.user}")
        logger.info(f"Connection String: {self.db_config.connection_string}")
        logger.info(f"=== KAFKA CONFIG ===")
        logger.info(f"Kafka Bootstrap Servers: {self.kafka_config.bootstrap_servers}")
        logger.info(f"Input Topic: {self.kafka_config.input_topic}")
        logger.info(f"Output Topic: {self.kafka_config.output_topic}")
        logger.info(f"{'='*50}")
        
        # DAO auto-initializes tables
        self.dao = ASCAExtractionDAO(self.db_config)
        logger.info(f"✅ DAO initialized, table auto-created if not exists")
        
        self.use_pipeline = use_pipeline and PIPELINE_AVAILABLE
        self.pipeline = None
        
        if self.use_pipeline:
            try:
                self.pipeline = ASCAExtractionPipeline()
                logger.info("ASCA pipeline initialized")
            except Exception as e:
                logger.error(f"Failed to initialize ASCA pipeline: {e}")
                self.use_pipeline = False
        
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
        logger.info(f"Pipeline processing: {'enabled' if self.use_pipeline else 'disabled (mock mode)'}")
    
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
        
        extraction_result = None
        pipeline_success = False
        
        if self.use_pipeline and self.pipeline:
            # Use ASCA pipeline for extraction
            try:
                from projects.services.processing.tasks.asca.dto import UnifiedTextEvent
                event = UnifiedTextEvent(
                    source=source_type,
                    source_type=source_type,
                    external_id=source_id,
                    text=text
                )
                extraction_result = self.pipeline.process(event)
                
                # Check if extraction actually produced results
                if extraction_result and len(extraction_result.aspects) > 0:
                    pipeline_success = True
                    logger.info(f"✅ ASCA extracted {len(extraction_result.aspects)} aspects for {source_id}")
                else:
                    logger.warning(f"⚠️ ASCA extracted 0 aspects for {source_id}")
                    pipeline_success = True  # Still save if pipeline ran but found nothing
                    
            except Exception as e:
                logger.error(f"{'='*50}")
                logger.error(f"❌ ASCA EXTRACTION FAILED for {source_id}")
                logger.error(f"❌ Error: {e}")
                logger.error(f"{'='*50}")
                extraction_result = None
                pipeline_success = False
        else:
            logger.error(f"{'='*50}")
            logger.error(f"❌ PIPELINE NOT AVAILABLE - Cannot process {source_id}")
            logger.error(f"❌ use_pipeline={self.use_pipeline}, pipeline={self.pipeline}")
            logger.error(f"{'='*50}")
            pipeline_success = False
        
        # Only save if pipeline succeeded
        if not pipeline_success or extraction_result is None:
            logger.error(f"❌ SKIPPING SAVE for {source_id} - Pipeline failed or not available")
            return None
        
        # Save to database
        dto = PersistenceASCADTO(
            source_id=source_id,
            source_type=source_type,
            raw_text=text,
            extraction_result=extraction_result
        )
        
        saved = self.dao.save(dto)
        
        if saved:
            logger.info(f"✅ Saved extraction for {source_id}")
        else:
            logger.warning(f"⚠️ Failed to save extraction for {source_id} (may already exist)")
        
        # Prepare output message
        output = {
            "source_id": source_id,
            "source_type": source_type,
            "extraction_result": extraction_result.model_dump(),
            "processed_at": datetime.now(UTC).isoformat(),
            "success": saved is not None
        }
        
        return output
    
    def _create_mock_result(self, text: str) -> ASCAExtractionResult:
        """Create a mock extraction result for testing."""
        return ASCAExtractionResult(
            aspects=[],
            overall_score=0.0,
            meta=ExtractionMeta(extractor="asca", language="vi")
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
                    # Manually poll for messages
                    message_pack = self.consumer.poll(timeout_ms=1000)
                    
                    for tp, messages in message_pack.items():
                        for message in messages:
                            try:
                                logger.info(f"📥 Received message from {tp.topic} [partition {tp.partition}, offset {message.offset}]")
                                output = self.process_message(message)
                                
                                # Produce output message if processing was successful
                                if output:
                                    self.producer.send(
                                        self.kafka_config.output_topic,
                                        key=output['source_id'],
                                        value=output
                                    )
                                    self.producer.flush()
                                    logger.info(f"📤 Output sent to {self.kafka_config.output_topic}")
                                
                                message_count += 1
                                if max_messages and message_count >= max_messages:
                                    logger.info(f"Reached max messages ({max_messages}), stopping")
                                    return
                                    
                            except Exception as e:
                                logger.error(f"Error processing message: {e}", exc_info=True)
                                
                except ValueError as ve:
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
    
    parser = argparse.ArgumentParser(description="ASCA Extraction Kafka Consumer")
    parser.add_argument("--no-pipeline", action="store_true", help="Disable ASCA pipeline (mock mode)")
    parser.add_argument("--max-messages", type=int, default=None, help="Max messages to process")
    args = parser.parse_args()
    
    consumer = ASCAExtractionConsumer(use_pipeline=not args.no_pipeline)
    consumer.run(max_messages=args.max_messages)


if __name__ == "__main__":
    main()
