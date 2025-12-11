# YouTube Ingestion - API Manager Tests

import pytest
from unittest.mock import MagicMock, patch

from ..api_manager import YouTubeAPIManager
from ..dto import ChannelDTO, VideoDTO, CommentDTO


class TestYouTubeAPIManager:
    """Tests for YouTubeAPIManager class."""
    
    @pytest.fixture
    def api_manager(self, ingestion_config, mock_youtube_api):
        """Create API manager with mocked YouTube API."""
        # The mock_youtube_api fixture already patches build and returns the mock
        # We need to ensure the manager uses this same mock instance
        manager = YouTubeAPIManager(ingestion_config)
        # Replace the youtube client with our mock
        manager.youtube = mock_youtube_api
        yield manager
    
    @pytest.mark.asyncio
    async def test_fetch_channel_info_success(
        self, api_manager, mock_youtube_api, mock_youtube_channel_response
    ):
        """Test fetching channel info successfully."""
        # Setup mock
        mock_request = MagicMock()
        mock_request.execute.return_value = mock_youtube_channel_response
        mock_youtube_api.channels.return_value.list.return_value = mock_request
        
        # Execute
        channel = await api_manager.fetch_channel_info("UC_test_channel")
        
        # Verify
        assert isinstance(channel, ChannelDTO)
        assert channel.id == "UC_test_channel"
        assert channel.title == "Test Channel"
        assert channel.subscriber_count == 10000
    
    @pytest.mark.asyncio
    async def test_fetch_channel_info_not_found(self, api_manager, mock_youtube_api):
        """Test fetching non-existent channel."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"items": []}
        mock_youtube_api.channels.return_value.list.return_value = mock_request
        
        with pytest.raises(ValueError, match="Channel not found"):
            await api_manager.fetch_channel_info("nonexistent")
    
    @pytest.mark.asyncio
    async def test_fetch_channel_videos(
        self, api_manager, mock_youtube_api, 
        mock_youtube_channel_response, mock_youtube_video_response
    ):
        """Test fetching channel videos."""
        # Setup mocks for channel and playlist
        mock_channel_request = MagicMock()
        mock_channel_request.execute.return_value = mock_youtube_channel_response
        mock_youtube_api.channels.return_value.list.return_value = mock_channel_request
        
        mock_playlist_request = MagicMock()
        mock_playlist_request.execute.return_value = {
            "items": [{"contentDetails": {"videoId": "video123"}}]
        }
        mock_youtube_api.playlistItems.return_value.list.return_value = mock_playlist_request
        
        mock_video_request = MagicMock()
        mock_video_request.execute.return_value = mock_youtube_video_response
        mock_youtube_api.videos.return_value.list.return_value = mock_video_request
        
        # Execute
        videos = await api_manager.fetch_channel_videos("UC_test_channel", max_results=1)
        
        # Verify
        assert len(videos) == 1
        assert isinstance(videos[0], VideoDTO)
        assert videos[0].id == "video123"
    
    @pytest.mark.asyncio
    async def test_fetch_video_comments(
        self, api_manager, mock_youtube_api, mock_youtube_comments_response
    ):
        """Test fetching video comments."""
        mock_request = MagicMock()
        mock_request.execute.return_value = mock_youtube_comments_response
        mock_youtube_api.commentThreads.return_value.list.return_value = mock_request
        
        comments = await api_manager.fetch_video_comments("video123", max_results=10)
        
        assert len(comments) >= 1
        assert isinstance(comments[0], CommentDTO)
        assert comments[0].author_display_name == "Test User"
    
    def test_to_raw_message_channel(self, api_manager, sample_channel):
        """Test converting channel to raw ingestion message."""
        message = api_manager.to_raw_message(sample_channel)
        
        assert message.source == "youtube"
        assert message.external_id == sample_channel.id
        assert message.entity_type == "channel"
        assert message.raw_text == sample_channel.description
    
    def test_to_raw_message_video(self, api_manager, sample_video):
        """Test converting video to raw ingestion message."""
        message = api_manager.to_raw_message(sample_video)
        
        assert message.source == "youtube"
        assert message.external_id == sample_video.id
        assert message.entity_type == "video"
        assert sample_video.title in message.raw_text
    
    def test_to_raw_message_comment(self, api_manager, sample_comment):
        """Test converting comment to raw ingestion message."""
        message = api_manager.to_raw_message(sample_comment)
        
        assert message.source == "youtube"
        assert message.external_id == sample_comment.id
        assert message.entity_type == "comment"
        assert message.raw_text == sample_comment.text


class TestChannelDTO:
    """Tests for ChannelDTO."""
    
    def test_to_dict(self, sample_channel):
        """Test channel DTO serialization."""
        data = sample_channel.to_dict()
        
        assert data["id"] == sample_channel.id
        assert data["title"] == sample_channel.title
        assert data["subscriber_count"] == sample_channel.subscriber_count
        assert "published_at" in data
    
    def test_immutability(self, sample_channel):
        """Test that DTO is immutable."""
        with pytest.raises(AttributeError):
            sample_channel.title = "New Title"


class TestVideoDTO:
    """Tests for VideoDTO."""
    
    def test_to_dict(self, sample_video):
        """Test video DTO serialization."""
        data = sample_video.to_dict()
        
        assert data["id"] == sample_video.id
        assert data["channel_id"] == sample_video.channel_id
        assert data["tags"] == list(sample_video.tags)


class TestCommentDTO:
    """Tests for CommentDTO."""
    
    def test_to_dict(self, sample_comment):
        """Test comment DTO serialization."""
        data = sample_comment.to_dict()
        
        assert data["id"] == sample_comment.id
        assert data["video_id"] == sample_comment.video_id
        assert data["text"] == sample_comment.text
        assert data["parent_id"] is None
    
    def test_reply_has_parent(self, sample_reply, sample_comment):
        """Test reply comment has parent ID."""
        data = sample_reply.to_dict()
        assert data["parent_id"] == sample_comment.id
