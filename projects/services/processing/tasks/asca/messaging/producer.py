"""
ASCA Extraction - Kafka Producer
================================
Utility producer for sending messages to Kafka.
Used by Streamlit UI and other components.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

# Try to import Kafka
KAFKA_AVAILABLE = False
try:
    from kafka import KafkaProducer as KafkaProducerLib
    KAFKA_AVAILABLE = True
except ImportError:
    logger.warning("kafka-python-ng not installed")


class ASCAKafkaProducer:
    """
    Kafka producer for sending ASCA processing requests.
    """
    
    def __init__(self, bootstrap_servers: str = "kafka:9092", topic: str = "asca-input"):
        """
        Initialize the producer.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Default topic to send messages to
        """
        self.bootstrap_servers = bootstrap_servers
        self.default_topic = topic
        self._producer = None
        
        if KAFKA_AVAILABLE:
            try:
                self._producer = KafkaProducerLib(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    request_timeout_ms=10000,
                    linger_ms=10,
                    batch_size=32768,
                    acks=1,
                    retries=3
                )
                logger.info(f"Kafka producer initialized: {bootstrap_servers}")
            except Exception as e:
                logger.error(f"Failed to initialize Kafka producer: {e}")
                self._producer = None
    
    @property
    def is_available(self) -> bool:
        """Check if producer is available."""
        return self._producer is not None
    
    def send_text(
        self,
        text: str,
        source_id: Optional[str] = None,
        source_type: str = "message",
        topic: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a text message for ASCA processing.
        
        Args:
            text: Text content to process
            source_id: Optional source ID (auto-generated if not provided)
            source_type: Type of source (default: "message")
            topic: Topic to send to (default: self.default_topic)
            metadata: Additional metadata
            
        Returns:
            Message that was sent, or None if failed
        """
        if not self.is_available:
            logger.error("Kafka producer not available")
            return None
        
        import uuid
        
        # Create message
        message = {
            "source_id": source_id or f"msg_{uuid.uuid4().hex[:12]}",
            "source_type": source_type,
            "text": text,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": metadata or {}
        }
        
        topic = topic or self.default_topic
        
        try:
            future = self._producer.send(
                topic,
                key=message["source_id"],
                value=message
            )
            # Wait for confirmation
            future.get(timeout=10)
            self._producer.flush()
            
            logger.info(f"📤 Sent message to {topic}: {message['source_id']}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return None
    
    def send_batch(
        self,
        texts: list,
        source_type: str = "batch",
        topic: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Send multiple texts for processing.
        
        Args:
            texts: List of text strings
            source_type: Type of source
            topic: Topic to send to
            
        Returns:
            Dictionary with success and failed counts
        """
        if not self.is_available:
            logger.error("Kafka producer not available")
            return {"success": 0, "failed": len(texts)}
        
        import uuid
        
        topic = topic or self.default_topic
        success = 0
        failed = 0
        
        for i, text in enumerate(texts):
            message = {
                "source_id": f"batch_{uuid.uuid4().hex[:8]}_{i}",
                "source_type": source_type,
                "text": text,
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            try:
                self._producer.send(
                    topic,
                    key=message["source_id"],
                    value=message
                )
                success += 1
            except Exception as e:
                logger.error(f"Failed to send message {i}: {e}")
                failed += 1
        
        self._producer.flush()
        logger.info(f"Batch sent: {success} success, {failed} failed")
        
        return {"success": success, "failed": failed}
    
    def close(self):
        """Close the producer."""
        if self._producer:
            self._producer.close()
            self._producer = None


def create_producer_from_config():
    """Create a producer from environment config."""
    from projects.services.processing.tasks.asca.config import KafkaConfig
    
    config = KafkaConfig.from_env()
    return ASCAKafkaProducer(
        bootstrap_servers=config.bootstrap_servers,
        topic=config.input_topic
    )
