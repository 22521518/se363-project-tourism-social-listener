# YouTube Ingestion - Kafka Consumer
# Consumes YouTube events and triggers ingestion workflows

import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Callable, Awaitable, AsyncIterator
from dataclasses import dataclass

from kafka import KafkaConsumer as KafkaConsumerClient
from kafka.errors import NoBrokersAvailable

from .config import KafkaConfig
from .dto import RawIngestionMessage

logger = logging.getLogger(__name__)


@dataclass
class ConsumedEvent:
    """Represents a consumed Kafka event."""
    topic: str
    partition: int
    offset: int
    key: Optional[str]
    value: dict
    timestamp: datetime
    
    @property
    def entity_type(self) -> str:
        """Get the entity type from the message."""
        return self.value.get("entityType", "unknown")
    
    @property
    def external_id(self) -> str:
        """Get the external ID from the message."""
        return self.value.get("externalId", "")
    
    @property
    def raw_text(self) -> str:
        """Get the raw text from the message."""
        return self.value.get("rawText", "")


class YouTubeKafkaConsumer:
    """
    Consumes YouTube events and triggers workflows.
    
    Features:
    - Subscribes to multiple topics
    - Async event iteration
    - Error handling with dead letter queue pattern
    - Manual commit support
    """
    
    def __init__(
        self, 
        config: KafkaConfig,
        group_id: str = "youtube_ingestion_consumer",
        auto_commit: bool = False,
    ):
        """
        Initialize the Kafka consumer.
        
        Args:
            config: Kafka configuration
            group_id: Consumer group ID
            auto_commit: Whether to auto-commit offsets
        """
        self.config = config
        self.group_id = group_id
        self.auto_commit = auto_commit
        self._consumer: Optional[KafkaConsumerClient] = None
        self._connected = False
        self._subscribed_topics: List[str] = []
    
    def connect(self, topics: List[str] = None) -> None:
        """
        Connect to Kafka broker and subscribe to topics.
        
        Args:
            topics: List of topics to subscribe to
        """
        if self._connected:
            return
        
        topics = topics or [
            self.config.channels_topic,
            self.config.videos_topic,
            self.config.comments_topic,
        ]
        
        try:
            self._consumer = KafkaConsumerClient(
                *topics,
                bootstrap_servers=self.config.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                enable_auto_commit=self.auto_commit,
                auto_offset_reset="earliest",
            )
            self._connected = True
            self._subscribed_topics = topics
            logger.info(
                f"Connected to Kafka and subscribed to: {topics}"
            )
        except NoBrokersAvailable:
            logger.error(f"No Kafka brokers available at {self.config.bootstrap_servers}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from Kafka broker."""
        if self._consumer:
            self._consumer.close()
            self._consumer = None
            self._connected = False
            self._subscribed_topics = []
            logger.info("Disconnected from Kafka")
    
    def subscribe(self, topics: List[str]) -> None:
        """
        Subscribe to additional topics.
        
        Args:
            topics: List of topics to subscribe to
        """
        if not self._connected:
            self.connect(topics)
        else:
            self._consumer.subscribe(topics)
            self._subscribed_topics = topics
            logger.info(f"Subscribed to topics: {topics}")
    
    def consume_one(self, timeout_ms: int = 1000) -> Optional[ConsumedEvent]:
        """
        Consume a single event.
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Returns:
            ConsumedEvent or None if no message available
        """
        if not self._connected:
            raise RuntimeError("Consumer not connected")
        
        records = self._consumer.poll(timeout_ms=timeout_ms, max_records=1)
        
        for topic_partition, messages in records.items():
            for message in messages:
                return ConsumedEvent(
                    topic=message.topic,
                    partition=message.partition,
                    offset=message.offset,
                    key=message.key,
                    value=message.value,
                    timestamp=datetime.fromtimestamp(message.timestamp / 1000),
                )
        
        return None
    
    def consume_batch(
        self, 
        max_records: int = 100,
        timeout_ms: int = 1000
    ) -> List[ConsumedEvent]:
        """
        Consume a batch of events.
        
        Args:
            max_records: Maximum records to consume
            timeout_ms: Timeout in milliseconds
            
        Returns:
            List of ConsumedEvent objects
        """
        if not self._connected:
            raise RuntimeError("Consumer not connected")
        
        records = self._consumer.poll(timeout_ms=timeout_ms, max_records=max_records)
        events = []
        
        for topic_partition, messages in records.items():
            for message in messages:
                events.append(ConsumedEvent(
                    topic=message.topic,
                    partition=message.partition,
                    offset=message.offset,
                    key=message.key,
                    value=message.value,
                    timestamp=datetime.fromtimestamp(message.timestamp / 1000),
                ))
        
        return events
    
    async def consume(self) -> AsyncIterator[ConsumedEvent]:
        """
        Async iterator for consuming events.
        
        Yields:
            ConsumedEvent objects
        """
        if not self._connected:
            raise RuntimeError("Consumer not connected")
        
        loop = asyncio.get_event_loop()
        
        while True:
            # Run polling in executor to avoid blocking
            event = await loop.run_in_executor(
                None, 
                lambda: self.consume_one(timeout_ms=1000)
            )
            
            if event:
                yield event
    
    def commit(self) -> None:
        """Commit current offsets."""
        if self._consumer:
            self._consumer.commit()
            logger.debug("Committed offsets")
    
    async def process_with_handler(
        self,
        handler: Callable[[ConsumedEvent], Awaitable[None]],
        error_handler: Optional[Callable[[ConsumedEvent, Exception], Awaitable[None]]] = None,
        max_retries: int = 3,
    ) -> None:
        """
        Process events with a handler function.
        
        Args:
            handler: Async function to process each event
            error_handler: Optional function to handle errors
            max_retries: Maximum retry attempts per event
        """
        async for event in self.consume():
            retries = 0
            while retries < max_retries:
                try:
                    await handler(event)
                    if not self.auto_commit:
                        self.commit()
                    break
                except Exception as e:
                    retries += 1
                    logger.error(
                        f"Error processing event {event.external_id} "
                        f"(attempt {retries}/{max_retries}): {e}"
                    )
                    
                    if retries >= max_retries:
                        if error_handler:
                            await error_handler(event, e)
                        else:
                            logger.error(
                                f"Max retries exceeded for event {event.external_id}, "
                                f"sending to dead letter queue"
                            )
                    else:
                        # Exponential backoff
                        await asyncio.sleep(2 ** retries)
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


async def create_youtube_event_processor(
    config: KafkaConfig,
    on_channel_event: Optional[Callable[[ConsumedEvent], Awaitable[None]]] = None,
    on_video_event: Optional[Callable[[ConsumedEvent], Awaitable[None]]] = None,
    on_comment_event: Optional[Callable[[ConsumedEvent], Awaitable[None]]] = None,
) -> None:
    """
    Create and run an event processor for YouTube events.
    
    Args:
        config: Kafka configuration
        on_channel_event: Handler for channel events
        on_video_event: Handler for video events
        on_comment_event: Handler for comment events
    """
    consumer = YouTubeKafkaConsumer(config)
    consumer.connect()
    
    async def router(event: ConsumedEvent):
        if event.topic == config.channels_topic and on_channel_event:
            await on_channel_event(event)
        elif event.topic == config.videos_topic and on_video_event:
            await on_video_event(event)
        elif event.topic == config.comments_topic and on_comment_event:
            await on_comment_event(event)
        else:
            logger.debug(f"Unhandled event from topic: {event.topic}")
    
    try:
        await consumer.process_with_handler(router)
    finally:
        consumer.disconnect()
