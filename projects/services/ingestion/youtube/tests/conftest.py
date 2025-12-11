# YouTube Ingestion - Test Fixtures (conftest.py)
# Shared pytest fixtures for testing

import os
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

# Set test environment variables before importing modules
os.environ.setdefault("YOUTUBE_API_KEY", "test_api_key")
os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
os.environ.setdefault("DB_HOST", "localhost")

from ..config import IngestionConfig, YouTubeConfig, KafkaConfig, DatabaseConfig
from ..dto import ChannelDTO, VideoDTO, CommentDTO
from ..dao import YouTubeDAO


@pytest.fixture
def youtube_config():
    """Fixture for YouTube configuration."""
    return YouTubeConfig(api_key="test_api_key")


@pytest.fixture
def kafka_config():
    """Fixture for Kafka configuration."""
    return KafkaConfig(
        bootstrap_servers="localhost:9092",
        client_id="test_client",
    )


@pytest.fixture
def database_config():
    """Fixture for database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="test_db",
        user="test_user",
        password="test_password",
    )


@pytest.fixture
def ingestion_config(youtube_config, kafka_config, database_config):
    """Fixture for full ingestion configuration."""
    return IngestionConfig(
        youtube=youtube_config,
        kafka=kafka_config,
        database=database_config,
    )


@pytest.fixture
def sample_channel():
    """Fixture for a sample channel DTO."""
    return ChannelDTO(
        id="UC_test_channel",
        title="Test Channel",
        description="A test channel for unit testing",
        custom_url="@testchannel",
        published_at=datetime(2020, 1, 1, 0, 0, 0),
        thumbnail_url="https://example.com/thumb.jpg",
        subscriber_count=10000,
        video_count=100,
        view_count=1000000,
        country="US",
    )


@pytest.fixture
def sample_video():
    """Fixture for a sample video DTO."""
    return VideoDTO(
        id="video123",
        channel_id="UC_test_channel",
        title="Test Video Title",
        description="This is a test video description",
        published_at=datetime(2023, 6, 15, 12, 0, 0),
        thumbnail_url="https://example.com/video_thumb.jpg",
        view_count=50000,
        like_count=2500,
        comment_count=150,
        duration="PT10M30S",
        tags=("test", "video", "sample"),
        category_id="22",
    )


@pytest.fixture
def sample_comment():
    """Fixture for a sample comment DTO."""
    return CommentDTO(
        id="comment_abc123",
        video_id="video123",
        author_display_name="Test User",
        author_channel_id="UC_user_channel",
        text="This is a great video! Thanks for sharing.",
        like_count=10,
        published_at=datetime(2023, 6, 16, 8, 30, 0),
        updated_at=datetime(2023, 6, 16, 8, 30, 0),
        parent_id=None,
        reply_count=2,
    )


@pytest.fixture
def sample_reply(sample_comment):
    """Fixture for a sample reply comment DTO."""
    return CommentDTO(
        id="reply_xyz789",
        video_id="video123",
        author_display_name="Another User",
        author_channel_id="UC_another_user",
        text="I agree, very informative!",
        like_count=3,
        published_at=datetime(2023, 6, 16, 10, 0, 0),
        updated_at=datetime(2023, 6, 16, 10, 0, 0),
        parent_id=sample_comment.id,
        reply_count=0,
    )


@pytest.fixture
def mock_youtube_api():
    """Fixture for mocked YouTube API client."""
    with patch("googleapiclient.discovery.build") as mock_build:
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        yield mock_youtube


@pytest.fixture
def mock_youtube_channel_response():
    """Fixture for mocked YouTube channel API response."""
    return {
        "items": [{
            "id": "UC_test_channel",
            "snippet": {
                "title": "Test Channel",
                "description": "A test channel",
                "customUrl": "@testchannel",
                "publishedAt": "2020-01-01T00:00:00Z",
                "thumbnails": {"default": {"url": "https://example.com/thumb.jpg"}},
                "country": "US",
            },
            "statistics": {
                "subscriberCount": "10000",
                "videoCount": "100",
                "viewCount": "1000000",
            },
            "contentDetails": {
                "relatedPlaylists": {
                    "uploads": "UU_test_uploads"
                }
            }
        }]
    }


@pytest.fixture
def mock_youtube_video_response():
    """Fixture for mocked YouTube video API response."""
    return {
        "items": [{
            "id": "video123",
            "snippet": {
                "title": "Test Video",
                "description": "Test description",
                "publishedAt": "2023-06-15T12:00:00Z",
                "thumbnails": {"medium": {"url": "https://example.com/thumb.jpg"}},
                "tags": ["test", "video"],
                "categoryId": "22",
            },
            "statistics": {
                "viewCount": "50000",
                "likeCount": "2500",
                "commentCount": "150",
            },
            "contentDetails": {
                "duration": "PT10M30S",
            }
        }]
    }


@pytest.fixture
def mock_youtube_comments_response():
    """Fixture for mocked YouTube comments API response."""
    return {
        "items": [{
            "snippet": {
                "topLevelComment": {
                    "id": "comment123",
                    "snippet": {
                        "authorDisplayName": "Test User",
                        "authorChannelId": {"value": "UC_user"},
                        "textDisplay": "Great video!",
                        "likeCount": 5,
                        "publishedAt": "2023-06-16T08:00:00Z",
                        "updatedAt": "2023-06-16T08:00:00Z",
                    }
                },
                "totalReplyCount": 0,
            }
        }]
    }


@pytest.fixture
def mock_kafka_producer():
    """Fixture for mocked Kafka producer."""
    with patch("kafka.KafkaProducer") as mock_producer_class:
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer
        yield mock_producer


@pytest.fixture
def mock_kafka_admin():
    """Fixture for mocked Kafka admin client."""
    with patch("kafka.admin.KafkaAdminClient") as mock_admin_class:
        mock_admin = MagicMock()
        mock_admin_class.return_value = mock_admin
        yield mock_admin
