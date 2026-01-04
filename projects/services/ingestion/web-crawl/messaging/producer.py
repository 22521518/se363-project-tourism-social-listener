"""
Web Crawl Kafka Producer - Publishes crawl results to Kafka.
"""
import json
import logging
from typing import Optional

from kafka import KafkaProducer as KafkaProducerClient
from kafka.errors import NoBrokersAvailable

from config import KafkaConfig

logger = logging.getLogger(__name__)


class WebCrawlKafkaProducer:
    """
    Publishes crawl results to Kafka topics.
    """
    
    def __init__(self, config: Optional[KafkaConfig] = None):
        """
        Initialize the Kafka producer.
        
        Args:
            config: Kafka configuration
        """
        self.config = config or KafkaConfig.from_env()
        self._producer: Optional[KafkaProducerClient] = None
        self._connected = False
    
    def connect(self) -> None:
        """Connect to Kafka broker."""
        if self._connected:
            return
            
        try:
            self._producer = KafkaProducerClient(
                bootstrap_servers=self.config.bootstrap_servers,
                client_id=f"{self.config.client_id}_producer",
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
            )
            self._connected = True
            logger.info(f"Connected to Kafka producer: {self.config.bootstrap_servers}")
        except NoBrokersAvailable:
            logger.error(f"No Kafka brokers available at {self.config.bootstrap_servers}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from Kafka broker."""
        if self._producer:
            self._producer.flush()
            self._producer.close()
            self._producer = None
            self._connected = False
            logger.info("Disconnected from Kafka producer")
    
    def produce_crawl_result(self, result: dict) -> None:
        """
        Publish a crawl result to the results topic.
        
        Args:
            result: The crawl result dictionary
        """
        if not self._connected:
            self.connect()
            
        try:
            url = result.get("url", "unknown")
            request_id = result.get("request_id", "unknown")
            
            self._producer.send(
                self.config.results_topic,
                key=request_id,
                value=result
            )
            logger.info(f"Produced crawl result for {url} to {self.config.results_topic}")
        except Exception as e:
            logger.error(f"Failed to produce crawl result: {e}")
            raise

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
