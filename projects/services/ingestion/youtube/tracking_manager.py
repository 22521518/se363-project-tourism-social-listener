# YouTube Ingestion - Channel Tracking Manager
# Handles channel monitoring, new video detection, and ingestion modes

from datetime import UTC
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import IngestionConfig
from .dto import VideoDTO, TrackedChannelDTO
from .dao import YouTubeDAO
from .api_manager import YouTubeAPIManager

logger = logging.getLogger(__name__)


class IngestionMode(Enum):
    """Ingestion operation modes."""
    REALTIME = "realtime"
    SCHEDULED = "scheduled"
    STOPPED = "stopped"


@dataclass
class IngestionJob:
    """Represents an ingestion job."""
    id: str
    channel_id: str
    job_type: str  # "full", "videos", "comments"
    status: str  # "pending", "running", "completed", "failed"
    created_at: datetime = field(default_factory=datetime.now(UTC))
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[dict] = None


class ChannelTrackingManager:
    """
    Manages tracked channels and detects new videos.
    
    Supports two ingestion modes:
    - Real-time: Continuous polling with short intervals
    - Scheduled: Interval-based polling using APScheduler
    """
    
    def __init__(
        self,
        config: IngestionConfig,
        api_manager: YouTubeAPIManager,
        dao: YouTubeDAO,
        on_new_video: Optional[Callable[[VideoDTO], Awaitable[None]]] = None,
    ):
        """
        Initialize the Channel Tracking Manager.
        
        Args:
            config: Ingestion configuration
            api_manager: YouTube API manager instance
            dao: Database access object
            on_new_video: Callback function when new video is detected
        """
        self.config = config
        self.api_manager = api_manager
        self.dao = dao
        self.on_new_video = on_new_video
        
        self._mode = IngestionMode.STOPPED
        self._scheduler = AsyncIOScheduler()
        self._realtime_task: Optional[asyncio.Task] = None
        self._jobs: dict[str, IngestionJob] = {}
        self._job_counter = 0
    
    @property
    def mode(self) -> IngestionMode:
        """Current ingestion mode."""
        return self._mode
    
    # ===================
    # Channel Registration
    # ===================
    
    async def register_channel(self, channel_id: str) -> None:
        """
        Register a channel for tracking.
        
        Args:
            channel_id: YouTube channel ID
        """
        logger.info(f"Registering channel for tracking: {channel_id}")
        
        # Ensure channel exists in database
        existing = self.dao.get_channel(channel_id)
        if not existing:
            await self.api_manager.populate_channel(channel_id)
        
        # Register for tracking
        self.dao.register_tracked_channel(channel_id)
        logger.info(f"Channel {channel_id} registered for tracking")
    
    async def unregister_channel(self, channel_id: str) -> None:
        """
        Unregister a channel from tracking.
        
        Args:
            channel_id: YouTube channel ID
        """
        logger.info(f"Unregistering channel from tracking: {channel_id}")
        self.dao.unregister_tracked_channel(channel_id)
    
    async def list_tracked_channels(self) -> List[str]:
        """
        List all tracked channel IDs.
        
        Returns:
            List of channel IDs
        """
        tracked = self.dao.get_tracked_channels(active_only=True)
        return [t.channel_id for t in tracked]
    
    def get_tracked_channel_status(self, channel_id: str) -> Optional[TrackedChannelDTO]:
        """Get tracking status for a channel."""
        channels = self.dao.get_tracked_channels(active_only=False)
        for channel in channels:
            if channel.channel_id == channel_id:
                return channel
        return None
    
    # ===================
    # Video Detection
    # ===================
    
    async def check_new_videos(self, channel_id: str) -> List[VideoDTO]:
        """
        Check for new videos on a channel using incremental fetching.
        
        Uses smart fetching: stops early when hitting already-seen videos,
        rather than fetching all videos and filtering afterwards.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            List of new videos detected
        """
        logger.info(f"Checking for new videos on channel: {channel_id}")
        
        # Get existing video IDs for incremental fetch
        existing_ids = set(self.dao.get_video_ids_for_channel(channel_id))
        is_first_check = len(existing_ids) == 0
        
        # Fetch videos with incremental mode (stops when hitting existing video)
        # On first check, fetch all; on subsequent checks, use early termination
        new_videos = await self.api_manager.fetch_channel_videos(
            channel_id, 
            max_results=self.config.max_videos_per_channel,
            existing_video_ids=existing_ids,
            stop_on_existing=not is_first_check  # Only use incremental on subsequent checks
        )
        
        if new_videos:
            logger.info(f"Found {len(new_videos)} new videos for channel {channel_id}")
            
            # Save new videos to database
            self.dao.save_videos(new_videos)
            
            # Update tracking state
            latest_published = max(v.published_at for v in new_videos)
            self.dao.update_tracking_state(
                channel_id,
                last_checked=datetime.now(UTC),
                last_video_published=latest_published
            )
            
            # Trigger callback for each new video
            if self.on_new_video:
                for video in new_videos:
                    try:
                        await self.on_new_video(video)
                    except Exception as e:
                        logger.error(f"Error in new video callback: {e}")
        else:
            logger.debug(f"No new videos for channel {channel_id}")
            self.dao.update_tracking_state(
                channel_id,
                last_checked=datetime.now(UTC)
            )
        
        return new_videos
    
    async def get_last_checked(self, channel_id: str) -> Optional[datetime]:
        """Get when a channel was last checked."""
        status = self.get_tracked_channel_status(channel_id)
        return status.last_checked if status else None
    
    # ===================
    # Ingestion Modes
    # ===================
    
    async def start_realtime_ingestion(self, interval_seconds: int = 60) -> None:
        """
        Start real-time ingestion mode with continuous polling.
        
        Args:
            interval_seconds: Polling interval in seconds
        """
        if self._mode != IngestionMode.STOPPED:
            logger.warning("Ingestion already running, stopping first")
            await self.stop_ingestion()
        
        logger.info(f"Starting real-time ingestion with {interval_seconds}s interval")
        self._mode = IngestionMode.REALTIME
        
        async def polling_loop():
            while self._mode == IngestionMode.REALTIME:
                try:
                    await self._check_all_channels()
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(interval_seconds)
        
        self._realtime_task = asyncio.create_task(polling_loop())
    
    async def start_scheduled_ingestion(self, interval_minutes: int = None) -> None:
        """
        Start scheduler-based ingestion mode.
        
        Args:
            interval_minutes: Polling interval in minutes
        """
        if self._mode != IngestionMode.STOPPED:
            logger.warning("Ingestion already running, stopping first")
            await self.stop_ingestion()
        
        interval = interval_minutes or (self.config.polling_interval_seconds // 60)
        logger.info(f"Starting scheduled ingestion with {interval} minute interval")
        
        self._mode = IngestionMode.SCHEDULED
        
        self._scheduler.add_job(
            self._check_all_channels,
            IntervalTrigger(minutes=interval),
            id="channel_check",
            replace_existing=True,
        )
        self._scheduler.start()
    
    async def stop_ingestion(self) -> None:
        """Stop current ingestion mode."""
        logger.info("Stopping ingestion")
        
        if self._realtime_task:
            self._realtime_task.cancel()
            try:
                await self._realtime_task
            except asyncio.CancelledError:
                pass
            self._realtime_task = None
        
        if self._scheduler.running:
            self._scheduler.shutdown()
        
        self._mode = IngestionMode.STOPPED
    
    async def _check_all_channels(self) -> None:
        """Check all tracked channels for new videos."""
        channel_ids = await self.list_tracked_channels()
        logger.info(f"Checking {len(channel_ids)} tracked channels")
        
        for channel_id in channel_ids:
            try:
                await self.check_new_videos(channel_id)
            except Exception as e:
                logger.error(f"Error checking channel {channel_id}: {e}")
    
    # ===================
    # Job Management
    # ===================
    
    async def queue_ingestion_job(
        self, 
        channel_id: str, 
        job_type: str = "full"
    ) -> str:
        """
        Queue an ingestion job for a channel.
        
        Args:
            channel_id: YouTube channel ID
            job_type: Type of job ("full", "videos", "comments")
            
        Returns:
            Job ID
        """
        self._job_counter += 1
        job_id = f"job_{self._job_counter}_{channel_id}"
        
        job = IngestionJob(
            id=job_id,
            channel_id=channel_id,
            job_type=job_type,
            status="pending",
        )
        self._jobs[job_id] = job
        
        logger.info(f"Queued ingestion job: {job_id}")
        
        # Execute job asynchronously
        asyncio.create_task(self._execute_job(job))
        
        return job_id
    
    async def _execute_job(self, job: IngestionJob) -> None:
        """Execute an ingestion job."""
        job.status = "running"
        logger.info(f"Executing job: {job.id}")
        
        try:
            if job.job_type == "full":
                result = await self.api_manager.ingest_channel_full(job.channel_id)
            elif job.job_type == "videos":
                videos = await self.check_new_videos(job.channel_id)
                result = {"videos_count": len(videos)}
            elif job.job_type == "comments":
                # Fetch comments for all videos
                video_ids = self.dao.get_video_ids_for_channel(job.channel_id)
                total_comments = 0
                for video_id in video_ids:
                    comments = await self.api_manager.fetch_video_comments(video_id)
                    self.dao.save_comments(comments)
                    total_comments += len(comments)
                result = {"comments_count": total_comments}
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
            
            job.status = "completed"
            job.result = result
            job.completed_at = datetime.now(UTC)
            logger.info(f"Job completed: {job.id}")
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now(UTC)
            logger.error(f"Job failed: {job.id}: {e}")
    
    async def get_job_status(self, job_id: str) -> Optional[IngestionJob]:
        """Get status of a job by ID."""
        return self._jobs.get(job_id)
    
    def list_jobs(self, status: str = None) -> List[IngestionJob]:
        """List all jobs, optionally filtered by status."""
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return jobs
