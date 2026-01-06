# YouTube Ingestion - API Manager
# Encapsulates all YouTube Data API v3 operations

import asyncio
import logging
from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict, Any, Tuple
from functools import wraps

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import YouTubeConfig, IngestionConfig
from .dto import ChannelDTO, VideoDTO, CommentDTO, RawIngestionMessage, IngestionCheckpointDTO, RateLimitError
from .dao import YouTubeDAO

# Configure structured logging
logger = logging.getLogger(__name__)


def parse_rate_limit_headers(error: HttpError) -> Tuple[Optional[int], Optional[str]]:
    """
    Parse rate limit info from YouTube API error response.
    
    Returns:
        Tuple of (retry_after_seconds, error_reason)
    """
    retry_after = None
    reason = None
    
    try:
        # Check for Retry-After header
        if hasattr(error, 'resp') and error.resp:
            retry_after_str = error.resp.get('retry-after')
            if retry_after_str:
                retry_after = int(retry_after_str)
        
        # Parse error reason from response body
        if hasattr(error, 'content'):
            import json
            content = json.loads(error.content.decode('utf-8'))
            errors = content.get('error', {}).get('errors', [])
            if errors:
                reason = errors[0].get('reason', 'unknown')
    except Exception:
        pass
    
    return retry_after, reason


def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for exponential backoff retry on API errors.
    Follows AGENTS.md convention for error handling.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except HttpError as e:
                    last_exception = e
                    retry_after, reason = parse_rate_limit_headers(e)
                    
                    if e.resp.status in (403, 429):  # Rate limit or quota exceeded
                        delay = retry_after if retry_after else base_delay * (2 ** attempt)
                        logger.warning(
                            f"Rate limited on attempt {attempt + 1}/{max_retries} "
                            f"[status={e.resp.status}, reason={reason}], "
                            f"retrying in {delay}s"
                        )
                        logger.debug(f"Rate limit error details: {e}")
                        await asyncio.sleep(delay)
                    elif e.resp.status >= 500:  # Server error
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Server error on attempt {attempt + 1}/{max_retries} "
                            f"[status={e.resp.status}], retrying in {delay}s: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise  # Don't retry client errors
                except Exception as e:
                    last_exception = e
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Error on attempt {attempt + 1}/{max_retries}, "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator


class YouTubeAPIManager:
    """
    Encapsulates all YouTube Data API v3 operations.
    
    Provides service-level methods for:
    - Channel management (populate, remove, retrieve)
    - Channel information (profile, metadata)
    - Video fetching
    - Comment fetching
    - Database persistence
    - Checkpoint-based resumable fetching
    """
    
    def __init__(self, config: IngestionConfig, dao: Optional[YouTubeDAO] = None):
        """
        Initialize the YouTube API Manager.
        
        Args:
            config: Ingestion configuration containing API key and settings
            dao: Optional DAO instance for database operations
        """
        self.config = config
        self.youtube = build(
            "youtube", "v3",
            developerKey=config.youtube.api_key,
            cache_discovery=False
        )
        self.dao = dao
    
    async def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous function in the event loop."""
        # return self._loop.run_in_executor(None, lambda: func(*args, **kwargs))
        return await asyncio.to_thread(func, *args, **kwargs)
    
    def _create_checkpoint(
        self,
        channel_id: str,
        operation_type: str,
        **kwargs
    ) -> IngestionCheckpointDTO:
        """Create a new checkpoint DTO."""
        return IngestionCheckpointDTO(
            id=None,
            channel_id=channel_id,
            operation_type=operation_type,
            started_at=datetime.now(UTC),
            **kwargs
        )
    
    def _save_checkpoint(self, checkpoint: IngestionCheckpointDTO) -> IngestionCheckpointDTO:
        """Save checkpoint to database and return updated DTO with ID."""
        if not self.dao:
            return checkpoint
        
        checkpoint_id = self.dao.save_checkpoint(checkpoint)
        checkpoint.id = checkpoint_id
        return checkpoint
    
    def _handle_rate_limit(
        self,
        error: HttpError,
        checkpoint: IngestionCheckpointDTO,
        context: str = ""
    ) -> RateLimitError:
        """
        Handle rate limit error: log details, update checkpoint, and return custom exception.
        """
        retry_after, reason = parse_rate_limit_headers(error)
        
        # Calculate reset time
        reset_at = None
        if retry_after:
            reset_at = datetime.now(UTC) + timedelta(seconds=retry_after)
        
        # Update checkpoint with rate limit info
        checkpoint.status = "rate_limited"
        checkpoint.error_message = f"{reason or 'quota_exceeded'}: {str(error)}"
        checkpoint.error_code = error.resp.status
        checkpoint.rate_limit_reset_at = reset_at
        checkpoint.retry_count += 1
        
        # Save updated checkpoint
        if self.dao:
            self.dao.save_checkpoint(checkpoint)
        
        # Log detailed info
        logger.error(
            f"RATE LIMIT HIT during {context} for channel {checkpoint.channel_id}\n"
            f"  Status: {error.resp.status}\n"
            f"  Reason: {reason}\n"
            f"  Retry After: {retry_after}s\n"
            f"  Progress: {checkpoint.fetched_count}/{checkpoint.target_count or '?'} items\n"
            f"  Page Token: {checkpoint.next_page_token}\n"
            f"  Checkpoint ID: {checkpoint.id}"
        )
        
        return RateLimitError(
            message=f"Rate limit hit during {context}",
            error_code=error.resp.status,
            checkpoint=checkpoint,
            retry_after=retry_after
        )
    
    # ===================
    # Channel Management Services
    # ===================
    
    async def resolve_handle_to_id(self, handle: str) -> Optional[str]:
        """
        Resolve a YouTube handle (e.g., @KhoaiLangThang) to a Channel ID.
        Tries efficient 'forHandle' parameter first (1 quota unit).
        Falls back to 'search' if not supported (100 quota units).
        
        Args:
            handle: The handle string (with or without @)
            
        Returns:
            Channel ID if found, None otherwise
        """
        if not handle:
            return None
            
        clean_handle = handle.strip()
        if clean_handle.startswith("@"):
            clean_handle = clean_handle[1:]
        
        logger.debug(f"Resolving handle: @{clean_handle}")
        
        try:
            # 1. Try efficient 'forHandle' method
            try:
                request = self.youtube.channels().list(
                    part="id",
                    forHandle=f"@{clean_handle}"
                )
                response = await self._run_sync(request.execute)
                
                if response.get("items"):
                    channel_id = response["items"][0]["id"]
                    logger.debug(f"Resolved @{clean_handle} to {channel_id} (via forHandle)")
                    return channel_id
            except Exception as e:
                # Catching generic Exception because google-api-client might raise
                # various errors for unexpected kwargs or API issues.
                logger.warning(f"'forHandle' optimization failed, falling back to search. Error: {e}")
            
            # 2. Fallback to search (expensive: 100 utils)
            logger.info(f"Searching for handle: {clean_handle}")
            request = self.youtube.search().list(
                part="snippet",
                q=f"@{clean_handle}",
                type="channel",
                maxResults=1
            )
            response = await self._run_sync(request.execute)
            
            if response.get("items"):
                channel_id = response["items"][0]["snippet"]["channelId"]
                logger.debug(f"Resolved @{clean_handle} to {channel_id} (via search)")
                return channel_id
            
            logger.warning(f"Could not resolve handle: @{clean_handle}")
            return None
            
        except HttpError as e:
            logger.warning(f"Error resolving handle @{clean_handle}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error resolving handle @{clean_handle}: {e}")
            return None

    @with_retry(max_retries=3)
    async def populate_channel(self, channel_id: str) -> ChannelDTO:
        """
        Populate channel data into database.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            ChannelDTO with channel data
        """
        # Resolve handle if provided
        if channel_id.startswith("@"):
            resolved_id = await self.resolve_handle_to_id(channel_id)
            if not resolved_id:
                raise ValueError(f"Could not resolve handle: {channel_id}")
            channel_id = resolved_id
            
        logger.info(f"Populating channel: {channel_id}")
        
        # Fetch channel info
        channel_dto, raw_payload = await self.fetch_channel_info(channel_id, return_raw=True)
        
        # Save to database
        if self.dao:
            self.dao.save_channel(channel_dto, raw_payload)
            logger.info(f"Channel {channel_id} saved to database")
        
        return channel_dto
    
    async def remove_channel(self, channel_id: str) -> bool:
        """
        Remove channel data from database.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            True if channel was removed, False if not found
        """
        # Resolve handle if provided
        if channel_id.startswith("@"):
            resolved_id = await self.resolve_handle_to_id(channel_id)
            if resolved_id: 
                channel_id = resolved_id
            # If resolution fails, we still try removing with original string just in case,
            # though it's unlikely to match if it's a handle.

        if not self.dao:
            logger.warning("DAO not configured, cannot remove channel")
            return False
        
        result = self.dao.delete_channel(channel_id)
        if result:
            logger.info(f"Channel {channel_id} removed from database")
        else:
            logger.warning(f"Channel {channel_id} not found in database")
        return result
    
    async def get_channel(self, channel_id: str) -> Optional[ChannelDTO]:
        """
        Retrieve channel data from database.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            ChannelDTO if found, None otherwise
        """
        if not self.dao:
            logger.warning("DAO not configured, fetching from API instead")
            return await self.fetch_channel_info(channel_id)
        
        return self.dao.get_channel(channel_id)
    
    # ===================
    # Channel Information Services
    # ===================
    
    @with_retry(max_retries=3)
    async def fetch_channel_info(
        self, 
        channel_id: str,
        return_raw: bool = False
    ) -> ChannelDTO | tuple[ChannelDTO, Dict[str, Any]]:
        """
        Fetch detailed channel profile and metadata from YouTube API.
        
        Args:
            channel_id: YouTube channel ID
            return_raw: If True, also return raw API response
            
        Returns:
            ChannelDTO, or tuple of (ChannelDTO, raw_payload) if return_raw=True
        """
        # Resolve handle if provided
        if channel_id.startswith("@"):
            resolved_id = await self.resolve_handle_to_id(channel_id)
            if not resolved_id:
                raise ValueError(f"Could not resolve handle: {channel_id}")
            channel_id = resolved_id
            
        logger.debug(f"Fetching channel info for: {channel_id}")
        
        request = self.youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=channel_id
        )
        response = await self._run_sync(request.execute)
        
        if not response.get("items"):
            raise ValueError(f"Channel not found: {channel_id}")
        
        item = response["items"][0]
        snippet = item["snippet"]
        statistics = item.get("statistics", {})
        
        channel_dto = ChannelDTO(
            id=item["id"],
            title=snippet["title"],
            description=snippet.get("description", ""),
            custom_url=snippet.get("customUrl"),
            published_at=datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            ),
            thumbnail_url=snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
            subscriber_count=int(statistics.get("subscriberCount", 0)),
            video_count=int(statistics.get("videoCount", 0)),
            view_count=int(statistics.get("viewCount", 0)),
            country=snippet.get("country"),
        )
        
        if return_raw:
            return channel_dto, item
        return channel_dto
    
    # ===================
    # Video Services
    # ===================
    
    @with_retry(max_retries=3)
    async def fetch_channel_videos(
        self, 
        channel_id: str, 
        max_results: int = None,
        existing_video_ids: set = None,
        stop_on_existing: bool = False
    ) -> List[VideoDTO]:
        """
        Fetch videos uploaded by a channel.
        
        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to fetch
            existing_video_ids: Set of video IDs already in database (for incremental fetch)
            stop_on_existing: If True, stop fetching when hitting existing video (incremental mode)
            
        Returns:
            List of VideoDTO objects
        """
        # Resolve handle if provided
        if channel_id.startswith("@"):
            resolved_id = await self.resolve_handle_to_id(channel_id)
            if not resolved_id:
                raise ValueError(f"Could not resolve handle: {channel_id}")
            channel_id = resolved_id
            
        max_results = max_results or self.config.max_videos_per_channel
        existing_video_ids = existing_video_ids or set()
        
        mode_str = "incremental" if stop_on_existing and existing_video_ids else "full"
        logger.info(f"Fetching videos for channel {channel_id} (mode={mode_str}, max={max_results})")
        
        # First, get the uploads playlist ID
        request = self.youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        response = await self._run_sync(request.execute)
        
        if not response.get("items"):
            raise ValueError(f"Channel not found: {channel_id}")
        
        uploads_playlist_id = (
            response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        )
        
        # Fetch video IDs from uploads playlist
        video_ids = []
        next_page_token = None
        hit_existing = False
        
        while len(video_ids) < max_results:
            request = self.youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - len(video_ids)),
                pageToken=next_page_token
            )
            response = await self._run_sync(request.execute)
            
            for item in response.get("items", []):
                vid_id = item["contentDetails"]["videoId"]
                
                # Incremental mode: stop when we hit an existing video
                if stop_on_existing and vid_id in existing_video_ids:
                    logger.info(f"Hit existing video {vid_id}, stopping incremental fetch")
                    hit_existing = True
                    break
                    
                video_ids.append(vid_id)
            
            if hit_existing:
                break
                
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        
        if stop_on_existing:
            logger.info(f"Incremental fetch found {len(video_ids)} new video IDs")
        
        # Fetch video details in batches
        videos = []
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i + 50]
            batch_videos = await self._fetch_video_details_batch(batch_ids, channel_id)
            videos.extend(batch_videos)
        
        return videos

    async def fetch_channel_videos_resumable(
        self, 
        channel_id: str, 
        max_results: int = None,
        existing_video_ids: set = None,
        stop_on_existing: bool = False,
        resume_checkpoint: IngestionCheckpointDTO = None
    ) -> Tuple[List[VideoDTO], Optional[IngestionCheckpointDTO]]:
        """
        Fetch videos with checkpoint support for resumable fetching.
        
        This method saves progress after each page, so if rate limited,
        we can resume from the last successful page.
        
        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to fetch
            existing_video_ids: Set of video IDs already in database
            stop_on_existing: If True, stop when hitting existing video
            resume_checkpoint: Optional checkpoint to resume from
            
        Returns:
            Tuple of (videos, checkpoint) - checkpoint is None if completed successfully
            
        Raises:
            RateLimitError: If rate limited, contains checkpoint info for resuming
        """
        # Resolve handle if provided
        if channel_id.startswith("@"):
            resolved_id = await self.resolve_handle_to_id(channel_id)
            if not resolved_id:
                raise ValueError(f"Could not resolve handle: {channel_id}")
            channel_id = resolved_id
            
        max_results = max_results or self.config.max_videos_per_channel
        existing_video_ids = existing_video_ids or set()
        
        # Create or resume checkpoint
        if resume_checkpoint:
            checkpoint = resume_checkpoint
            checkpoint.status = "in_progress"
            logger.info(
                f"Resuming video fetch for {channel_id} from checkpoint "
                f"(fetched={checkpoint.fetched_count}, token={checkpoint.next_page_token})"
            )
        else:
            checkpoint = self._create_checkpoint(
                channel_id=channel_id,
                operation_type="fetch_videos",
                target_count=max_results
            )
        
        # Save initial checkpoint
        checkpoint = self._save_checkpoint(checkpoint)
        
        mode_str = "incremental" if stop_on_existing and existing_video_ids else "full"
        logger.info(f"Fetching videos for channel {channel_id} (mode={mode_str}, max={max_results}, resumable=True)")
        
        try:
            # Get uploads playlist ID (only if we don't have a page token yet)
            request = self.youtube.channels().list(
                part="contentDetails",
                id=channel_id
            )
            response = await self._run_sync(request.execute)
            
            if not response.get("items"):
                raise ValueError(f"Channel not found: {channel_id}")
            
            uploads_playlist_id = (
                response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            )
        except HttpError as e:
            if e.resp.status in (403, 429):
                raise self._handle_rate_limit(e, checkpoint, "fetch_channel_videos (playlist)")
            raise
        
        # Fetch video IDs from uploads playlist with checkpoint support
        video_ids = []
        next_page_token = checkpoint.next_page_token  # Resume from checkpoint
        hit_existing = False
        
        while len(video_ids) + checkpoint.fetched_count < max_results:
            try:
                request = self.youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(video_ids) - checkpoint.fetched_count),
                    pageToken=next_page_token
                )
                response = await self._run_sync(request.execute)
                
            except HttpError as e:
                if e.resp.status in (403, 429):
                    # Save progress before raising
                    checkpoint.next_page_token = next_page_token
                    raise self._handle_rate_limit(e, checkpoint, "fetch_channel_videos (pagination)")
                raise
            
            for item in response.get("items", []):
                vid_id = item["contentDetails"]["videoId"]
                
                # Incremental mode: stop when we hit an existing video
                if stop_on_existing and vid_id in existing_video_ids:
                    logger.info(f"Hit existing video {vid_id}, stopping incremental fetch")
                    hit_existing = True
                    break
                    
                video_ids.append(vid_id)
            
            # Update checkpoint after each successful page
            next_page_token = response.get("nextPageToken")
            checkpoint.next_page_token = next_page_token
            checkpoint.fetched_count += len(response.get("items", []))
            self._save_checkpoint(checkpoint)
            
            if hit_existing or not next_page_token:
                break
        
        logger.info(f"Fetched {len(video_ids)} video IDs (checkpoint: {checkpoint.fetched_count} total processed)")
        
        # Fetch video details in batches
        videos = []
        for i in range(0, len(video_ids), 50):
            try:
                batch_ids = video_ids[i:i + 50]
                batch_videos = await self._fetch_video_details_batch(batch_ids, channel_id)
                videos.extend(batch_videos)
            except HttpError as e:
                if e.resp.status in (403, 429):
                    # Save videos fetched so far
                    if self.dao and videos:
                        self.dao.save_videos(videos)
                        logger.info(f"Saved {len(videos)} videos before rate limit")
                    raise self._handle_rate_limit(e, checkpoint, "fetch_channel_videos (details)")
                raise
        
        # Mark checkpoint as completed
        if self.dao and checkpoint.id:
            self.dao.complete_checkpoint(checkpoint.id)
        
        return videos, None  # None checkpoint means completed
    
    async def _fetch_video_details_batch(
        self, 
        video_ids: List[str],
        channel_id: str
    ) -> List[VideoDTO]:
        """Fetch details for a batch of videos."""
        request = self.youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(video_ids)
        )
        response = await self._run_sync(request.execute)
        
        videos = []
        for item in response.get("items", []):
            snippet = item["snippet"]
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            
            video_dto = VideoDTO(
                id=item["id"],
                channel_id=channel_id,
                title=snippet["title"],
                description=snippet.get("description", ""),
                published_at=datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                ),
                thumbnail_url=snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                view_count=int(statistics.get("viewCount", 0)),
                like_count=int(statistics.get("likeCount", 0)),
                comment_count=int(statistics.get("commentCount", 0)),
                duration=content_details.get("duration", ""),
                tags=tuple(snippet.get("tags", [])),
                category_id=snippet.get("categoryId"),
            )
            videos.append(video_dto)
        
        return videos
    
    @with_retry(max_retries=3)
    async def fetch_video_details(self, video_id: str) -> VideoDTO:
        """
        Fetch details for a single video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            VideoDTO with video details
        """
        videos = await self._fetch_video_details_batch([video_id], "")
        if not videos:
            raise ValueError(f"Video not found: {video_id}")
        return videos[0]
    
    # ===================
    # Comment Services
    # ===================
    
    @with_retry(max_retries=3)
    async def fetch_video_comments(
        self, 
        video_id: str, 
        max_results: int = None
    ) -> List[CommentDTO]:
        """
        Fetch comments for a video.
        
        Args:
            video_id: YouTube video ID
            max_results: Maximum number of comments to fetch
            
        Returns:
            List of CommentDTO objects
        """
        max_results = max_results or self.config.max_comments_per_video
        logger.info(f"Fetching up to {max_results} comments for video: {video_id}")
        
        comments = []
        next_page_token = None
        
        try:
            while len(comments) < max_results:
                request = self.youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=min(100, max_results - len(comments)),
                    pageToken=next_page_token,
                    textFormat="plainText"
                )
                response = await self._run_sync(request.execute)
                
                for item in response.get("items", []):
                    # Top-level comment
                    top_comment = item["snippet"]["topLevelComment"]
                    snippet = top_comment["snippet"]
                    
                    comment_dto = CommentDTO(
                        id=top_comment["id"],
                        video_id=video_id,
                        author_display_name=snippet["authorDisplayName"],
                        author_channel_id=snippet.get("authorChannelId", {}).get("value"),
                        text=snippet["textDisplay"],
                        like_count=snippet.get("likeCount", 0),
                        published_at=datetime.fromisoformat(
                            snippet["publishedAt"].replace("Z", "+00:00")
                        ),
                        updated_at=datetime.fromisoformat(
                            snippet["updatedAt"].replace("Z", "+00:00")
                        ),
                        reply_count=item["snippet"].get("totalReplyCount", 0),
                    )
                    comments.append(comment_dto)
                    
                    # Include replies if available
                    if "replies" in item:
                        for reply in item["replies"]["comments"]:
                            reply_snippet = reply["snippet"]
                            reply_dto = CommentDTO(
                                id=reply["id"],
                                video_id=video_id,
                                author_display_name=reply_snippet["authorDisplayName"],
                                author_channel_id=reply_snippet.get("authorChannelId", {}).get("value"),
                                text=reply_snippet["textDisplay"],
                                like_count=reply_snippet.get("likeCount", 0),
                                published_at=datetime.fromisoformat(
                                    reply_snippet["publishedAt"].replace("Z", "+00:00")
                                ),
                                updated_at=datetime.fromisoformat(
                                    reply_snippet["updatedAt"].replace("Z", "+00:00")
                                ),
                                parent_id=top_comment["id"],
                            )
                            comments.append(reply_dto)
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
                    
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"Comments disabled for video: {video_id}")
                return []
            raise
        
        return comments[:max_results]
    
    # ===================
    # Persistence Methods
    # ===================
    
    async def save_channel(self, channel: ChannelDTO) -> None:
        """Persist channel to database."""
        if not self.dao:
            raise RuntimeError("DAO not configured")
        self.dao.save_channel(channel)
    
    async def save_videos(self, videos: List[VideoDTO]) -> None:
        """Persist videos to database."""
        if not self.dao:
            raise RuntimeError("DAO not configured")
        self.dao.save_videos(videos)
    
    async def save_comments(self, comments: List[CommentDTO]) -> None:
        """Persist comments to database."""
        if not self.dao:
            raise RuntimeError("DAO not configured")
        self.dao.save_comments(comments)
    
    # ===================
    # Convenience Methods
    # ===================
    
    async def ingest_channel_smart(
        self, 
        channel_id: str,
        fetch_comments: bool = True
    ) -> Dict[str, Any]:
        """
        Smart channel ingestion: fetch all on first run, only new videos on subsequent runs.
        
        This method automatically detects if it's the first run (no existing videos)
        and performs a full fetch. On subsequent runs, it only fetches videos newer
        than those already in the database, stopping early once it hits existing content.
        
        Args:
            channel_id: YouTube channel ID or handle
            fetch_comments: Whether to also fetch comments for new videos
            
        Returns:
            Dict with counts of ingested items and mode used
        """
        # Resolve handle if provided
        if channel_id.startswith("@"):
            resolved_id = await self.resolve_handle_to_id(channel_id)
            if not resolved_id:
                raise ValueError(f"Could not resolve handle: {channel_id}")
            channel_id = resolved_id
        
        # Fetch and save channel info
        channel = await self.populate_channel(channel_id)
        
        # Check existing videos to determine mode
        existing_ids = set()
        if self.dao:
            existing_ids = set(self.dao.get_video_ids_for_channel(channel_id))
        
        is_first_run = len(existing_ids) == 0
        mode = "full" if is_first_run else "incremental"
        
        logger.info(f"Smart ingestion for {channel_id}: mode={mode}, existing_videos={len(existing_ids)}")
        
        # Fetch videos with appropriate mode
        videos = await self.fetch_channel_videos(
            channel_id,
            existing_video_ids=existing_ids,
            stop_on_existing=not is_first_run  # Only stop on existing if not first run
        )
        
        # Save new videos
        if self.dao and videos:
            self.dao.save_videos(videos)
            logger.info(f"Saved {len(videos)} {'new ' if not is_first_run else ''}videos")
        
        # Fetch comments for new videos only
        total_comments = 0
        if fetch_comments:
            for video in videos:
                try:
                    comments = await self.fetch_video_comments(video.id)
                    if self.dao:
                        self.dao.save_comments(comments)
                    total_comments += len(comments)
                except Exception as e:
                    logger.error(f"Error fetching comments for video {video.id}: {e}")
        
        result = {
            "channel_id": channel_id,
            "channel_title": channel.title,
            "mode": mode,
            "is_first_run": is_first_run,
            "existing_videos_count": len(existing_ids),
            "new_videos_count": len(videos),
            "comments_count": total_comments,
        }
        
        logger.info(f"Smart ingestion complete: {result}")
        return result

    async def ingest_channel_smart_resumable(
        self, 
        channel_id: str,
        fetch_comments: bool = True
    ) -> Dict[str, Any]:
        """
        Smart channel ingestion with checkpoint support for resumable fetching.
        
        Same as ingest_channel_smart but saves progress to database.
        If rate limited, progress is saved and can be resumed later.
        
        Args:
            channel_id: YouTube channel ID or handle
            fetch_comments: Whether to also fetch comments for new videos
            
        Returns:
            Dict with counts of ingested items and mode used
            
        Raises:
            RateLimitError: If rate limited, contains checkpoint for resuming
        """
        # Resolve handle if provided
        original_channel_id = channel_id
        if channel_id.startswith("@"):
            resolved_id = await self.resolve_handle_to_id(channel_id)
            if not resolved_id:
                raise ValueError(f"Could not resolve handle: {channel_id}")
            channel_id = resolved_id
        
        # Check for existing checkpoint to resume from
        resume_checkpoint = None
        if self.dao:
            resume_checkpoint = self.dao.get_active_checkpoint(channel_id, "fetch_videos")
            if resume_checkpoint:
                logger.info(
                    f"Found active checkpoint for {channel_id}: "
                    f"status={resume_checkpoint.status}, "
                    f"fetched={resume_checkpoint.fetched_count}, "
                    f"retry_count={resume_checkpoint.retry_count}"
                )
        
        # Fetch and save channel info
        channel = await self.populate_channel(channel_id)
        
        # Check existing videos to determine mode
        existing_ids = set()
        if self.dao:
            existing_ids = set(self.dao.get_video_ids_for_channel(channel_id))
        
        is_first_run = len(existing_ids) == 0 and not resume_checkpoint
        mode = "full" if is_first_run else "incremental"
        
        logger.info(
            f"Smart resumable ingestion for {channel_id}: "
            f"mode={mode}, existing_videos={len(existing_ids)}, "
            f"resuming={resume_checkpoint is not None}"
        )
        
        # Fetch videos with checkpoint support
        videos, remaining_checkpoint = await self.fetch_channel_videos_resumable(
            channel_id,
            existing_video_ids=existing_ids,
            stop_on_existing=not is_first_run,
            resume_checkpoint=resume_checkpoint
        )
        
        # Save new videos
        if self.dao and videos:
            self.dao.save_videos(videos)
            logger.info(f"Saved {len(videos)} {'new ' if not is_first_run else ''}videos")
        
        # Fetch comments for new videos only
        total_comments = 0
        if fetch_comments:
            for video in videos:
                try:
                    comments = await self.fetch_video_comments(video.id)
                    if self.dao:
                        self.dao.save_comments(comments)
                    total_comments += len(comments)
                except RateLimitError:
                    logger.warning(f"Rate limited while fetching comments for {video.id}")
                    # Continue with other videos, comments can be fetched later
                except Exception as e:
                    logger.error(f"Error fetching comments for video {video.id}: {e}")
        
        result = {
            "channel_id": channel_id,
            "channel_title": channel.title,
            "mode": mode,
            "is_first_run": is_first_run,
            "existing_videos_count": len(existing_ids),
            "new_videos_count": len(videos),
            "comments_count": total_comments,
            "was_resumed": resume_checkpoint is not None,
        }
        
        logger.info(f"Smart resumable ingestion complete: {result}")
        return result

    async def resume_rate_limited_checkpoints(self) -> List[Dict[str, Any]]:
        """
        Resume all rate-limited checkpoints that are ready to retry.
        
        This method finds all checkpoints marked as rate_limited where
        the rate_limit_reset_at time has passed, and resumes them.
        
        Returns:
            List of results from each resumed ingestion
        """
        if not self.dao:
            logger.warning("DAO not configured, cannot resume checkpoints")
            return []
        
        checkpoints = self.dao.get_rate_limited_checkpoints()
        logger.info(f"Found {len(checkpoints)} rate-limited checkpoints ready to resume")
        
        results = []
        for checkpoint in checkpoints:
            try:
                logger.info(f"Resuming checkpoint {checkpoint.id} for channel {checkpoint.channel_id}")
                
                if checkpoint.operation_type == "fetch_videos":
                    result = await self.ingest_channel_smart_resumable(checkpoint.channel_id)
                    results.append(result)
                else:
                    logger.warning(f"Unknown operation type: {checkpoint.operation_type}")
                    
            except RateLimitError as e:
                logger.warning(f"Still rate limited for checkpoint {checkpoint.id}: {e}")
            except Exception as e:
                logger.error(f"Error resuming checkpoint {checkpoint.id}: {e}")
        
        return results

    async def ingest_channel_full(self, channel_id: str) -> Dict[str, Any]:
        """
        Full channel ingestion: fetch channel, videos, and comments.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Dict with counts of ingested items
        """
        # Resolve handle if provided
        if channel_id.startswith("@"):
            resolved_id = await self.resolve_handle_to_id(channel_id)
            if not resolved_id:
                raise ValueError(f"Could not resolve handle: {channel_id}")
            channel_id = resolved_id
            
        logger.info(f"Starting full ingestion for channel: {channel_id}")
        
        # Fetch and save channel
        channel = await self.populate_channel(channel_id)
        
        # Fetch and save videos
        videos = await self.fetch_channel_videos(channel_id)
        if self.dao:
            self.dao.save_videos(videos)
        
        # Fetch and save comments for each video
        total_comments = 0
        for video in videos:
            try:
                comments = await self.fetch_video_comments(video.id)
                if self.dao:
                    self.dao.save_comments(comments)
                total_comments += len(comments)
            except Exception as e:
                logger.error(f"Error fetching comments for video {video.id}: {e}")
        
        result = {
            "channel_id": channel_id,
            "channel_title": channel.title,
            "videos_count": len(videos),
            "comments_count": total_comments,
        }
        
        logger.info(f"Full ingestion complete: {result}")
        return result
    
    def to_raw_message(
        self, 
        entity: ChannelDTO | VideoDTO | CommentDTO,
        raw_payload: Dict[str, Any] = None
    ) -> RawIngestionMessage:
        """
        Convert an entity to the standard ingestion output format.
        
        Args:
            entity: Channel, Video, or Comment DTO
            raw_payload: Original API response
            
        Returns:
            RawIngestionMessage following AGENTS.md format
        """
        if isinstance(entity, ChannelDTO):
            return RawIngestionMessage(
                source="youtube",
                external_id=entity.id,
                raw_text=entity.description,
                created_at=entity.published_at,
                raw_payload=raw_payload or entity.to_dict(),
                entity_type="channel",
            )
        elif isinstance(entity, VideoDTO):
            return RawIngestionMessage(
                source="youtube",
                external_id=entity.id,
                raw_text=f"{entity.title}\n\n{entity.description}",
                created_at=entity.published_at,
                raw_payload=raw_payload or entity.to_dict(),
                entity_type="video",
            )
        elif isinstance(entity, CommentDTO):
            return RawIngestionMessage(
                source="youtube",
                external_id=entity.id,
                raw_text=entity.text,
                created_at=entity.published_at,
                raw_payload=raw_payload or entity.to_dict(),
                entity_type="comment",
            )
        else:
            raise ValueError(f"Unknown entity type: {type(entity)}")
    
    # ===================
    # Database Query Methods (for Frontend)
    # ===================
    
    def list_all_channels(self, limit: int = 100, offset: int = 0) -> List[ChannelDTO]:
        """
        List all channels from database with pagination.
        
        Args:
            limit: Maximum number of channels to return
            offset: Number of channels to skip
            
        Returns:
            List of ChannelDTO objects
        """
        if not self.dao:
            logger.warning("DAO not configured, cannot list channels")
            return []
        return self.dao.list_channels(limit=limit, offset=offset)
    
    def get_channel_videos(self, channel_id: str, limit: int = 50) -> List[VideoDTO]:
        """
        Get videos for a specific channel from database.
        
        Args:
            channel_id: YouTube channel ID
            limit: Maximum number of videos to return
            
        Returns:
            List of VideoDTO objects ordered by published_at desc
        """
        if not self.dao:
            logger.warning("DAO not configured, cannot get videos")
            return []
        return self.dao.get_channel_videos(channel_id, limit=limit)
    
    def get_video_comments_from_db(self, video_id: str, limit: int = 100) -> List[CommentDTO]:
        """
        Get comments for a specific video from database.
        
        Args:
            video_id: YouTube video ID
            limit: Maximum number of comments to return
            
        Returns:
            List of CommentDTO objects ordered by published_at desc
        """
        if not self.dao:
            logger.warning("DAO not configured, cannot get comments")
            return []
        return self.dao.get_video_comments(video_id, limit=limit)
    
    def get_tracking_statistics(self) -> Dict[str, Any]:
        """
        Get overall tracking statistics for dashboard display.
        
        Returns:
            Dict with statistics:
            - total_channels: Total number of channels in database
            - tracked_channels: Number of actively tracked channels
            - total_videos: Total number of videos
            - total_comments: Total number of comments
        """
        if not self.dao:
            logger.warning("DAO not configured, cannot get statistics")
            return {
                "total_channels": 0,
                "tracked_channels": 0,
                "total_videos": 0,
                "total_comments": 0,
            }
        
        with self.dao.get_session() as session:
            from .models import (
                YouTubeChannelModel, 
                YouTubeVideoModel, 
                YouTubeCommentModel,
                TrackedChannelModel
            )
            
            total_channels = session.query(YouTubeChannelModel).count()
            tracked_channels = session.query(TrackedChannelModel).filter_by(is_active=True).count()
            total_videos = session.query(YouTubeVideoModel).count()
            total_comments = session.query(YouTubeCommentModel).count()
            
            return {
                "total_channels": total_channels,
                "tracked_channels": tracked_channels,
                "total_videos": total_videos,
                "total_comments": total_comments,
            }
    
    def get_tracked_channels_with_details(self) -> List[Dict[str, Any]]:
        """
        Get tracked channels with their full details for dashboard.
        
        Returns:
            List of dicts with channel info and tracking status
        """
        if not self.dao:
            logger.warning("DAO not configured, cannot get tracked channels")
            return []
        
        tracked = self.dao.get_tracked_channels(active_only=True)
        result = []
        
        for t in tracked:
            channel = self.dao.get_channel(t.channel_id)
            if channel:
                result.append({
                    "channel_id": t.channel_id,
                    "title": channel.title,
                    "thumbnail_url": channel.thumbnail_url,
                    "subscriber_count": channel.subscriber_count,
                    "video_count": channel.video_count,
                    "view_count": channel.view_count,
                    "last_checked": t.last_checked.isoformat() if t.last_checked else None,
                    "last_video_published": t.last_video_published.isoformat() if t.last_video_published else None,
                    "is_active": t.is_active,
                })
        
        return result
    
    def get_recent_videos(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent videos across all channels for dashboard.
        
        Args:
            limit: Maximum number of videos to return
            
        Returns:
            List of video dicts with channel info
        """
        if not self.dao:
            logger.warning("DAO not configured, cannot get recent videos")
            return []
        
        with self.dao.get_session() as session:
            from .models import YouTubeVideoModel, YouTubeChannelModel
            
            videos = (
                session.query(YouTubeVideoModel)
                .order_by(YouTubeVideoModel.published_at.desc())
                .limit(limit)
                .all()
            )
            
            result = []
            for v in videos:
                channel = session.query(YouTubeChannelModel).filter_by(id=v.channel_id).first()
                result.append({
                    "id": v.id,
                    "title": v.title,
                    "channel_id": v.channel_id,
                    "channel_title": channel.title if channel else "Unknown",
                    "thumbnail_url": v.thumbnail_url,
                    "published_at": v.published_at.isoformat() if v.published_at else None,
                    "view_count": v.view_count,
                    "like_count": v.like_count,
                    "comment_count": v.comment_count,
                })
            
            return result
    
    def get_recent_comments(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent comments across all videos for dashboard.
        
        Args:
            limit: Maximum number of comments to return
            
        Returns:
            List of comment dicts with video info
        """
        if not self.dao:
            logger.warning("DAO not configured, cannot get recent comments")
            return []
        
        with self.dao.get_session() as session:
            from .models import YouTubeCommentModel, YouTubeVideoModel
            
            comments = (
                session.query(YouTubeCommentModel)
                .order_by(YouTubeCommentModel.published_at.desc())
                .limit(limit)
                .all()
            )
            
            result = []
            for c in comments:
                video = session.query(YouTubeVideoModel).filter_by(id=c.video_id).first()
                result.append({
                    "id": c.id,
                    "video_id": c.video_id,
                    "video_title": video.title if video else "Unknown",
                    "author_display_name": c.author_display_name,
                    "text": c.text[:200] + "..." if len(c.text) > 200 else c.text,
                    "like_count": c.like_count,
                    "published_at": c.published_at.isoformat() if c.published_at else None,
                    "reply_count": c.reply_count,
                })
            
            return result

