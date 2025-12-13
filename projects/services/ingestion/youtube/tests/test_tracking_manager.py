# YouTube Ingestion - Tracking Manager Tests

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from ..tracking_manager import ChannelTrackingManager, IngestionMode, IngestionJob


class TestChannelTrackingManager:
    """Tests for ChannelTrackingManager class."""
    
    @pytest.fixture
    def mock_dao(self):
        """Create a mocked DAO."""
        dao = MagicMock()
        dao.get_channel.return_value = None
        dao.get_tracked_channels.return_value = []
        dao.get_video_ids_for_channel.return_value = []
        return dao
    
    @pytest.fixture
    def mock_api_manager(self, sample_channel, sample_video):
        """Create a mocked API manager."""
        api = MagicMock()
        api.populate_channel = AsyncMock(return_value=sample_channel)
        api.fetch_channel_videos = AsyncMock(return_value=[sample_video])
        api.fetch_video_comments = AsyncMock(return_value=[])
        return api
    
    @pytest.fixture
    def tracking_manager(self, ingestion_config, mock_api_manager, mock_dao):
        """Create tracking manager with mocks."""
        return ChannelTrackingManager(
            config=ingestion_config,
            api_manager=mock_api_manager,
            dao=mock_dao,
        )
    
    @pytest.mark.asyncio
    async def test_register_channel_new(
        self, tracking_manager, mock_dao, mock_api_manager
    ):
        """Test registering a new channel."""
        await tracking_manager.register_channel("UC_test")
        
        mock_api_manager.populate_channel.assert_called_once_with("UC_test")
        mock_dao.register_tracked_channel.assert_called_once_with("UC_test")
    
    @pytest.mark.asyncio
    async def test_register_channel_existing(
        self, tracking_manager, mock_dao, mock_api_manager, sample_channel
    ):
        """Test registering an existing channel."""
        mock_dao.get_channel.return_value = sample_channel
        
        await tracking_manager.register_channel("UC_test")
        
        # Should not fetch from API if channel exists
        mock_api_manager.populate_channel.assert_not_called()
        mock_dao.register_tracked_channel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unregister_channel(self, tracking_manager, mock_dao):
        """Test unregistering a channel."""
        await tracking_manager.unregister_channel("UC_test")
        mock_dao.unregister_tracked_channel.assert_called_once_with("UC_test")
    
    @pytest.mark.asyncio
    async def test_check_new_videos_finds_new(
        self, tracking_manager, mock_dao, mock_api_manager, sample_video
    ):
        """Test detecting new videos."""
        mock_dao.get_video_ids_for_channel.return_value = []  # No existing videos
        
        new_videos = await tracking_manager.check_new_videos("UC_test")
        
        assert len(new_videos) == 1
        assert new_videos[0].id == sample_video.id
        mock_dao.save_videos.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_new_videos_no_new(
        self, tracking_manager, mock_dao, mock_api_manager, sample_video
    ):
        """Test no new videos detected."""
        mock_dao.get_video_ids_for_channel.return_value = [sample_video.id]
        
        new_videos = await tracking_manager.check_new_videos("UC_test")
        
        assert len(new_videos) == 0
        mock_dao.save_videos.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_new_videos_callback(
        self, ingestion_config, mock_api_manager, mock_dao, sample_video
    ):
        """Test new video callback is triggered."""
        callback = AsyncMock()
        manager = ChannelTrackingManager(
            config=ingestion_config,
            api_manager=mock_api_manager,
            dao=mock_dao,
            on_new_video=callback,
        )
        
        await manager.check_new_videos("UC_test")
        
        callback.assert_called_once_with(sample_video)
    
    def test_initial_mode_stopped(self, tracking_manager):
        """Test initial ingestion mode is stopped."""
        assert tracking_manager.mode == IngestionMode.STOPPED
    
    @pytest.mark.asyncio
    async def test_queue_job(self, tracking_manager):
        """Test queueing an ingestion job."""
        job_id = await tracking_manager.queue_ingestion_job("UC_test", "full")
        
        assert job_id is not None
        assert "UC_test" in job_id
        
        job = await tracking_manager.get_job_status(job_id)
        assert job is not None
        assert job.channel_id == "UC_test"
    
    def test_list_jobs(self, tracking_manager):
        """Test listing jobs."""
        jobs = tracking_manager.list_jobs()
        assert isinstance(jobs, list)


class TestIngestionJob:
    """Tests for IngestionJob dataclass."""
    
    def test_job_creation(self):
        """Test creating an ingestion job."""
        job = IngestionJob(
            id="job_1",
            channel_id="UC_test",
            job_type="full",
            status="pending",
        )
        
        assert job.id == "job_1"
        assert job.channel_id == "UC_test"
        assert job.status == "pending"
        assert job.created_at is not None
        assert job.completed_at is None
        assert job.error is None
    
    def test_job_defaults(self):
        """Test job default values."""
        job = IngestionJob(
            id="job_2",
            channel_id="UC_test",
            job_type="videos",
            status="running",
        )
        
        assert job.result is None
        assert isinstance(job.created_at, datetime)


class TestIngestionMode:
    """Tests for IngestionMode enum."""
    
    def test_mode_values(self):
        """Test ingestion mode values."""
        assert IngestionMode.REALTIME.value == "realtime"
        assert IngestionMode.SCHEDULED.value == "scheduled"
        assert IngestionMode.STOPPED.value == "stopped"
