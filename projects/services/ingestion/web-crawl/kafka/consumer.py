"""
Web Crawl Kafka Consumer - Consumes crawl requests from Kafka and processes them.

Listens on webcrawl.requests topic and triggers crawl operations.
"""
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Callable

from kafka import KafkaConsumer as KafkaConsumerClient
from kafka.errors import NoBrokersAvailable

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import KafkaConfig

logger = logging.getLogger(__name__)


class WebCrawlKafkaConsumer:
    """
    Consumes crawl request events from Kafka.
    
    Listens on webcrawl.requests topic and invokes callback for each request.
    """
    
    def __init__(
        self,
        config: Optional[KafkaConfig] = None,
        group_id: str = "webcrawl_consumer_group",
    ):
        """
        Initialize the Kafka consumer.
        
        Args:
            config: Kafka configuration
            group_id: Consumer group ID
        """
        self.config = config or KafkaConfig.from_env()
        self.group_id = group_id
        self._consumer: Optional[KafkaConsumerClient] = None
        self._connected = False
        self._running = False
    
    def connect(self) -> None:
        """Connect to Kafka broker."""
        if self._connected:
            return
        
        try:
            self._consumer = KafkaConsumerClient(
                self.config.requests_topic,
                bootstrap_servers=self.config.bootstrap_servers,
                client_id=f"{self.config.client_id}_consumer",
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            self._connected = True
            logger.info(f"Connected to Kafka: {self.config.bootstrap_servers}")
        except NoBrokersAvailable:
            logger.error(f"No Kafka brokers available at {self.config.bootstrap_servers}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from Kafka broker."""
        self._running = False
        if self._consumer:
            self._consumer.close()
            self._consumer = None
            self._connected = False
            logger.info("Disconnected from Kafka")
    
    def consume(
        self,
        callback: Callable[[dict], None],
        poll_timeout_ms: int = 1000,
        max_messages: Optional[int] = None,
    ) -> None:
        """
        Start consuming messages and invoke callback for each.
        
        Args:
            callback: Function to call for each message
            poll_timeout_ms: Poll timeout in milliseconds
            max_messages: Maximum messages to consume (None = infinite)
        """
        if not self._connected:
            self.connect()
        
        self._running = True
        message_count = 0
        
        logger.info(f"Starting to consume from {self.config.requests_topic}")
        
        try:
            while self._running:
                messages = self._consumer.poll(timeout_ms=poll_timeout_ms)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            logger.info(f"Received message: {record.key}")
                            callback(record.value)
                            message_count += 1
                            
                            if max_messages and message_count >= max_messages:
                                logger.info(f"Reached max messages: {max_messages}")
                                self._running = False
                                return
                                
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            
        except KeyboardInterrupt:
            logger.info("Consumer interrupted")
        finally:
            self.disconnect()
    
    async def consume_async(
        self,
        callback: Callable[[dict], None],
        poll_timeout_ms: int = 1000,
        max_messages: Optional[int] = None,
    ) -> None:
        """
        Async version of consume.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.consume,
            callback,
            poll_timeout_ms,
            max_messages,
        )
    
    def stop(self) -> None:
        """Stop consuming messages."""
        self._running = False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
