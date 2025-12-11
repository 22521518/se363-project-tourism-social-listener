# YouTube Ingestion - Kafka Tests

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from ..kafka_producer import YouTubeKafkaProducer
from ..kafka_consumer import YouTubeKafkaConsumer, ConsumedEvent


class TestYouTubeKafkaProducer:
    """Tests for YouTubeKafkaProducer class."""
    
    @pytest.fixture
    def producer(self, kafka_config):
        """Create producer with mocked Kafka client."""
        with patch("youtube.kafka_producer.KafkaProducerClient") as mock_class:
            mock_producer = MagicMock()
            mock_class.return_value = mock_producer
            
            p = YouTubeKafkaProducer(kafka_config)
            p.connect()
            yield p, mock_producer
    
    def test_connect(self, kafka_config):
        """Test connecting to Kafka."""
        with patch("youtube.kafka_producer.KafkaProducerClient") as mock_class:
            producer = YouTubeKafkaProducer(kafka_config)
            producer.connect()
            
            mock_class.assert_called_once()
            assert producer._connected is True
    
    def test_disconnect(self, producer):
        """Test disconnecting from Kafka."""
        p, mock_kafka = producer
        p.disconnect()
        
        mock_kafka.close.assert_called_once()
        assert p._connected is False
    
    def test_produce_channel_event(self, producer, sample_channel, kafka_config):
        """Test producing a channel event."""
        p, mock_kafka = producer
        p.produce_channel_event(sample_channel)
        
        mock_kafka.send.assert_called_once()
        call_args = mock_kafka.send.call_args
        assert call_args.kwargs["topic"] == kafka_config.channels_topic
        assert call_args.kwargs["key"] == sample_channel.id
    
    def test_produce_video_event(self, producer, sample_video, kafka_config):
        """Test producing a video event."""
        p, mock_kafka = producer
        p.produce_video_event(sample_video)
        
        mock_kafka.send.assert_called_once()
        call_args = mock_kafka.send.call_args
        assert call_args.kwargs["topic"] == kafka_config.videos_topic
        assert call_args.kwargs["key"] == sample_video.id
    
    def test_produce_comment_event(self, producer, sample_comment, kafka_config):
        """Test producing a comment event."""
        p, mock_kafka = producer
        p.produce_comment_event(sample_comment)
        
        mock_kafka.send.assert_called_once()
        call_args = mock_kafka.send.call_args
        assert call_args.kwargs["topic"] == kafka_config.comments_topic
        assert call_args.kwargs["key"] == sample_comment.id
    
    def test_produce_batch(
        self, producer, sample_channel, sample_video, sample_comment
    ):
        """Test batch producing events."""
        p, mock_kafka = producer
        p.produce_batch(
            channels=[sample_channel],
            videos=[sample_video],
            comments=[sample_comment],
        )
        
        # Should have 3 calls: 1 channel + 1 video + 1 comment
        assert mock_kafka.send.call_count == 3
        mock_kafka.flush.assert_called_once()
    
    def test_flush(self, producer):
        """Test flushing the producer."""
        p, mock_kafka = producer
        p.flush()
        mock_kafka.flush.assert_called_once()
    
    def test_create_topics(self, kafka_config):
        """Test creating Kafka topics."""
        with patch("youtube.kafka_producer.KafkaAdminClient") as mock_admin_class:
            mock_admin = MagicMock()
            mock_admin_class.return_value = mock_admin
            
            producer = YouTubeKafkaProducer(kafka_config)
            producer.create_topics()
            
            mock_admin.create_topics.assert_called_once()
            mock_admin.close.assert_called_once()
    
    def test_context_manager(self, kafka_config):
        """Test context manager usage."""
        with patch("youtube.kafka_producer.KafkaProducerClient") as mock_class:
            mock_producer = MagicMock()
            mock_class.return_value = mock_producer
            
            with YouTubeKafkaProducer(kafka_config) as p:
                assert p._connected is True
            
            mock_producer.flush.assert_called()
            mock_producer.close.assert_called()


class TestYouTubeKafkaConsumer:
    """Tests for YouTubeKafkaConsumer class."""
    
    @pytest.fixture
    def consumer(self, kafka_config):
        """Create consumer with mocked Kafka client."""
        with patch("youtube.kafka_consumer.KafkaConsumerClient") as mock_class:
            mock_consumer = MagicMock()
            mock_class.return_value = mock_consumer
            
            c = YouTubeKafkaConsumer(kafka_config)
            c.connect()
            yield c, mock_consumer
    
    def test_connect(self, kafka_config):
        """Test connecting and subscribing."""
        with patch("youtube.kafka_consumer.KafkaConsumerClient") as mock_class:
            consumer = YouTubeKafkaConsumer(kafka_config)
            consumer.connect()
            
            mock_class.assert_called_once()
            assert consumer._connected is True
    
    def test_disconnect(self, consumer):
        """Test disconnecting."""
        c, mock_kafka = consumer
        c.disconnect()
        
        mock_kafka.close.assert_called_once()
        assert c._connected is False
    
    def test_consume_one_no_message(self, consumer):
        """Test consuming when no message available."""
        c, mock_kafka = consumer
        mock_kafka.poll.return_value = {}
        
        event = c.consume_one(timeout_ms=100)
        assert event is None
    
    def test_consume_one_with_message(self, consumer):
        """Test consuming a single message."""
        c, mock_kafka = consumer
        
        mock_message = MagicMock()
        mock_message.topic = "youtube.videos"
        mock_message.partition = 0
        mock_message.offset = 42
        mock_message.key = "video123"
        mock_message.value = {"externalId": "video123", "entityType": "video"}
        mock_message.timestamp = 1700000000000
        
        mock_kafka.poll.return_value = {
            ("youtube.videos", 0): [mock_message]
        }
        
        event = c.consume_one(timeout_ms=100)
        
        assert event is not None
        assert isinstance(event, ConsumedEvent)
        assert event.topic == "youtube.videos"
        assert event.external_id == "video123"
        assert event.entity_type == "video"
    
    def test_consume_batch(self, consumer):
        """Test consuming a batch of messages."""
        c, mock_kafka = consumer
        
        messages = []
        for i in range(3):
            msg = MagicMock()
            msg.topic = "youtube.comments"
            msg.partition = 0
            msg.offset = i
            msg.key = f"comment{i}"
            msg.value = {"externalId": f"comment{i}", "entityType": "comment"}
            msg.timestamp = 1700000000000
            messages.append(msg)
        
        mock_kafka.poll.return_value = {
            ("youtube.comments", 0): messages
        }
        
        events = c.consume_batch(max_records=10)
        
        assert len(events) == 3
        assert all(isinstance(e, ConsumedEvent) for e in events)
    
    def test_commit(self, consumer):
        """Test committing offsets."""
        c, mock_kafka = consumer
        c.commit()
        mock_kafka.commit.assert_called_once()
    
    def test_context_manager(self, kafka_config):
        """Test context manager usage."""
        with patch("youtube.kafka_consumer.KafkaConsumerClient") as mock_class:
            mock_consumer = MagicMock()
            mock_class.return_value = mock_consumer
            
            with YouTubeKafkaConsumer(kafka_config) as c:
                assert c._connected is True
            
            mock_consumer.close.assert_called()


class TestConsumedEvent:
    """Tests for ConsumedEvent dataclass."""
    
    def test_entity_type(self):
        """Test entity type extraction."""
        event = ConsumedEvent(
            topic="youtube.videos",
            partition=0,
            offset=0,
            key="video123",
            value={"entityType": "video", "externalId": "video123"},
            timestamp=datetime.now(),
        )
        
        assert event.entity_type == "video"
        assert event.external_id == "video123"
    
    def test_raw_text(self):
        """Test raw text extraction."""
        event = ConsumedEvent(
            topic="youtube.comments",
            partition=0,
            offset=0,
            key="comment123",
            value={
                "entityType": "comment",
                "externalId": "comment123",
                "rawText": "This is a comment"
            },
            timestamp=datetime.now(),
        )
        
        assert event.raw_text == "This is a comment"
    
    def test_missing_fields(self):
        """Test handling of missing fields."""
        event = ConsumedEvent(
            topic="youtube.channels",
            partition=0,
            offset=0,
            key=None,
            value={},
            timestamp=datetime.now(),
        )
        
        assert event.entity_type == "unknown"
        assert event.external_id == ""
        assert event.raw_text == ""
