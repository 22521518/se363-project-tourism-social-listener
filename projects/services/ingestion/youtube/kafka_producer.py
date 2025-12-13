# YouTube Ingestion - Kafka Producer
# Publishes YouTube ingestion events to Kafka

import json
import logging
from datetime import datetime
from typing import Optional, List

from kafka import KafkaProducer as KafkaProducerClient
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable

from .config import KafkaConfig
from .dto import ChannelDTO, VideoDTO, CommentDTO, RawIngestionMessage

logger = logging.getLogger(__name__)


def json_serializer(obj):
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class YouTubeKafkaProducer:
    """
    Publishes YouTube ingestion events to Kafka.
    
    Topics:
    - youtube.channels: Channel metadata events
    - youtube.videos: Video metadata events
    - youtube.comments: Comment events
    """
    
    def __init__(self, config: KafkaConfig):
        """
        Initialize the Kafka producer.
        
        Args:
            config: Kafka configuration
        """
        self.config = config
        self._producer: Optional[KafkaProducerClient] = None
        self._connected = False
    
    def connect(self) -> None:
        """Connect to Kafka broker."""
        if self._connected:
            return
        
        try:
            self._producer = KafkaProducerClient(
                bootstrap_servers=self.config.bootstrap_servers,
                client_id=self.config.client_id,
                value_serializer=lambda v: json.dumps(
                    v, default=json_serializer
                ).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
            )
            self._connected = True
            logger.info(f"Connected to Kafka: {self.config.bootstrap_servers}")
        except NoBrokersAvailable:
            logger.error(f"No Kafka brokers available at {self.config.bootstrap_servers}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from Kafka broker."""
        if self._producer:
            self._producer.close()
            self._producer = None
            self._connected = False
            logger.info("Disconnected from Kafka")
    
    def create_topics(self) -> None:
        """Create YouTube ingestion topics if they don't exist."""
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=self.config.bootstrap_servers,
                client_id=f"{self.config.client_id}_admin"
            )
            
            topics = [
                NewTopic(
                    name=self.config.channels_topic,
                    num_partitions=1,
                    replication_factor=1
                ),
                NewTopic(
                    name=self.config.videos_topic,
                    num_partitions=1,
                    replication_factor=1
                ),
                NewTopic(
                    name=self.config.comments_topic,
                    num_partitions=1,
                    replication_factor=1
                ),
            ]
            
            admin.create_topics(topics)
            logger.info("Created Kafka topics for YouTube ingestion")
            
        except TopicAlreadyExistsError:
            logger.info("Kafka topics already exist")
        except Exception as e:
            logger.error(f"Error creating topics: {e}")
            raise
        finally:
            admin.close()
    
    def _ensure_connected(self) -> None:
        """Ensure producer is connected."""
        if not self._connected:
            self.connect()
    
    def produce_channel_event(self, channel: ChannelDTO) -> None:
        """
        Produce a channel event to Kafka.
        
        Args:
            channel: Channel DTO to publish
        """
        self._ensure_connected()
        
        message = RawIngestionMessage(
            source="youtube",
            external_id=channel.id,
            raw_text=channel.description,
            created_at=channel.published_at,
            raw_payload=channel.to_dict(),
            entity_type="channel",
        )
        
        self._producer.send(
            topic=self.config.channels_topic,
            key=channel.id,
            value=message.to_dict(),
        )
        logger.debug(f"Produced channel event: {channel.id}")
    
    def produce_video_event(self, video: VideoDTO) -> None:
        """
        Produce a video event to Kafka.
        
        Args:
            video: Video DTO to publish
        """
        self._ensure_connected()
        
        message = RawIngestionMessage(
            source="youtube",
            external_id=video.id,
            raw_text=f"{video.title}\n\n{video.description}",
            created_at=video.published_at,
            raw_payload=video.to_dict(),
            entity_type="video",
        )
        
        self._producer.send(
            topic=self.config.videos_topic,
            key=video.id,
            value=message.to_dict(),
        )
        logger.debug(f"Produced video event: {video.id}")
    
    def produce_comment_event(self, comment: CommentDTO) -> None:
        """
        Produce a comment event to Kafka.
        
        Args:
            comment: Comment DTO to publish
        """
        self._ensure_connected()
        
        message = RawIngestionMessage(
            source="youtube",
            external_id=comment.id,
            raw_text=comment.text,
            created_at=comment.published_at,
            raw_payload=comment.to_dict(),
            entity_type="comment",
        )
        
        self._producer.send(
            topic=self.config.comments_topic,
            key=comment.id,
            value=message.to_dict(),
        )
        logger.debug(f"Produced comment event: {comment.id}")
    
    def produce_batch(
        self, 
        channels: List[ChannelDTO] = None,
        videos: List[VideoDTO] = None,
        comments: List[CommentDTO] = None
    ) -> None:
        """
        Produce multiple events in a batch.
        
        Args:
            channels: List of channels to publish
            videos: List of videos to publish
            comments: List of comments to publish
        """
        for channel in (channels or []):
            self.produce_channel_event(channel)
        
        for video in (videos or []):
            self.produce_video_event(video)
        
        for comment in (comments or []):
            self.produce_comment_event(comment)
        
        self.flush()
    
    def flush(self) -> None:
        """Flush all pending messages."""
        if self._producer:
            self._producer.flush()
            logger.debug("Flushed Kafka producer")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.flush()
        self.disconnect()
