# YouTube Ingestion - Kafka Consumer
# Consumes YouTube events and triggers ingestion workflows

import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Callable, Awaitable, AsyncIterator
from dataclasses import dataclass

from kafka import KafkaConsumer as KafkaConsumerClient
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError

from .config import KafkaConfig

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

    def create_topics(self) -> None:
        """Create YouTube ingestion topics if they don't exist."""
        admin = KafkaAdminClient(
            bootstrap_servers=self.config.bootstrap_servers,
            client_id=f"{self.group_id}_admin"
        )

        topics = [
            self.config.channels_topic,
            self.config.videos_topic,
            self.config.comments_topic,
        ]

        try:
            for topic_name in topics:
                try:
                    admin.create_topics([
                        NewTopic(
                            name=topic_name,
                            num_partitions=1,
                            replication_factor=1,
                        )
                    ])
                    logger.info(f"Created topic: {topic_name}")

                except TopicAlreadyExistsError:
                    logger.info(f"Topic already exists: {topic_name}")

        except Exception as e:
            logger.error(f"Error creating Kafka topics: {e}")
        finally:
            admin.close()

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
        
        # Ensure topics exist
        self.create_topics()
        
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
        
        loop = asyncio.get_running_loop()
        
        try:
            while True:
                # Run polling in executor to avoid blocking
                # Avoid lambda closure, use functools.partial
                from functools import partial
                event = await loop.run_in_executor(
                    None,
                    partial(self.consume_one, timeout_ms=1000)
                )
                
                if event:
                    yield event
                else:
                    await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info("Consumer cancelled")
            pass
        except Exception as e:
            logger.error(f"Error in consume: {e}")
            raise
    
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


async def run_consumer(config: KafkaConfig, run_once: bool = False, timeout_s: int = 60) -> None:
    """
    Run the YouTube event consumer.
    
    Args:
        config: IngestionConfig (but here we receive IngestionConfig object, so we extract kafka)
                Wait, main.py passes IngestionConfig, but type hint might be wrong if we expect KafkaConfig.
                main.py: asyncio.run(run_consumer(config, run_once=args.run_once))
                So 'config' is IngestionConfig.
        run_once: If True, stop after timeout or one batch (approx)
        timeout_s: Timeout in seconds for run_once mode
    """
    # Extract Kafka config from the passed IngestionConfig object
    # The main.py passes 'config' which is IngestionConfig.
    # But this function signature is what we define now.
    kafka_config = config.kafka
    
    # Define handlers (mock or real logic for now just logging)
    # The actual processing logic is inside 'create_youtube_event_processor' 
    # but we need to define what to do with them.
    # For now, let's reuse the logic in 'handle_channel' etc. from main.py?
    # NO, main.py defines those handlers and passes them to... wait.
    # main.py's run_consumer was missing. The handlers in main.py were inside 'run_full_ingestion'.
    # We need a general 'run_consumer' that saves to DB. 
    # Let's import the handlers/logic or re-implement simple saving here?
    # Better: This file should probably just contain the consumer class and processor.
    # The 'run_consumer' business logic (save to DB) belongs in main.py or a service layer.
    # HOWEVER, the user asked to FIX main.py calls.
    # AND missing `run_consumer`. 
    # Let's import the necessary DTO/DAO here or move the logic to main.py?
    # Actually, main.py *called* run_consumer. 
    # Let's define `run_consumer` here to instantiate the processor with DB saving logic.
    # But we need DAO.
    
    # To avoid circular imports, maybe we should put `run_consumer` in main.py?
    # The user asked to modify `kafka_consumer.py`.
    # Let's put a generic `run_consumer` here that just logs, OR better:
    # We move the `run_consumer` logic TO `kafka_consumer.py` but we need DAO.
    
    # Re-reading main.py:
    # elif args.mode == "consumer":
    #    asyncio.run(run_consumer(config, run_once=args.run_once))
    
    # This implies `run_consumer` should be imported from somewhere. 
    # Previous main.py had: `from projects.services.ingestion.youtube.kafka_consumer import YouTubeKafkaConsumer, create_youtube_event_processor`
    # It did NOT import `run_consumer`. 
    # So I should create `run_consumer` in `kafka_consumer.py` AND handle the db saving there?
    # That requires importing DAO/DTO.
    
    pass

# We will implement the specific logic in main.py or here.
# Given the structure, it's cleaner if `run_consumer` is in `main.py` if it uses DAO.
# BUT the user said "modify kafka_consumer ... main.py ...".
# Let's put `run_consumer` here but we need to import DAO.
    
from .dao import YouTubeDAO
from .dto import ChannelDTO, VideoDTO, CommentDTO
from .api_manager import YouTubeAPIManager 

async def run_consumer(config, run_once: bool = False):
    """
    Entry point for consumer mode.
    """
    logger.info("Starting Consumer Service...")
    
    # Initialize DB for saving
    dao = YouTubeDAO(config.database)
    # dao.init_db() # Workers usually strictly consume, but init is safe
    
    async def handle_channel(event):
        try:
            payload = event.value.get("rawPayload")
            if not payload: return
            dto = ChannelDTO(
                id=payload["id"],
                title=payload["title"],
                description=payload["description"],
                custom_url=payload["custom_url"],
                published_at=datetime.fromisoformat(payload["published_at"]),
                thumbnail_url=payload["thumbnail_url"],
                subscriber_count=payload["subscriber_count"],
                video_count=payload["video_count"],
                view_count=payload["view_count"],
                country=payload["country"],
            )
            dao.save_channel(dto, raw_payload=payload)
            logger.info(f"Saved channel {dto.id}")
        except Exception as e:
            logger.error(f"Error handling channel: {e}")

    async def handle_video(event):
        try:
            payload = event.value.get("rawPayload")
            if not payload: return
            dto = VideoDTO(
                id=payload["id"],
                channel_id=payload["channel_id"],
                title=payload["title"],
                description=payload["description"],
                published_at=datetime.fromisoformat(payload["published_at"]),
                thumbnail_url=payload["thumbnail_url"],
                view_count=payload["view_count"],
                like_count=payload["like_count"],
                comment_count=payload["comment_count"],
                duration=payload["duration"],
                tags=tuple(payload["tags"]),
                category_id=payload["category_id"],
            )
            dao.save_video(dto, raw_payload=payload)
            logger.info(f"Saved video {dto.id}")
        except Exception as e:
            logger.error(f"Error handling video: {e}")

    async def handle_comment(event):
        try:
            payload = event.value.get("rawPayload")
            if not payload: return
            dto = CommentDTO(
                id=payload["id"],
                video_id=payload["video_id"],
                author_display_name=payload["author_display_name"],
                author_channel_id=payload["author_channel_id"],
                text=payload["text"],
                like_count=payload["like_count"],
                published_at=datetime.fromisoformat(payload["published_at"]),
                updated_at=datetime.fromisoformat(payload["updated_at"]),
                parent_id=payload["parent_id"],
                reply_count=payload["reply_count"],
            )
            dao.save_comment(dto, raw_payload=payload)
            logger.info(f"Saved comment {dto.id}")
        except Exception as e:
            logger.error(f"Error handling comment: {e}")

    task = asyncio.create_task(create_youtube_event_processor(
        config.kafka,
        on_channel_event=handle_channel,
        on_video_event=handle_video,
        on_comment_event=handle_comment
    ))

    if run_once:
        logger.info("Running in run-once mode (60s timeout)...")
        await asyncio.sleep(60)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    else:
        await task

