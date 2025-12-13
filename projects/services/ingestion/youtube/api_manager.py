# YouTube Ingestion - API Manager
# Encapsulates all YouTube Data API v3 operations

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from functools import wraps

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import YouTubeConfig, IngestionConfig
from .dto import ChannelDTO, VideoDTO, CommentDTO, RawIngestionMessage
from .dao import YouTubeDAO

# Configure structured logging
logger = logging.getLogger(__name__)


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
                    if e.resp.status in (403, 429):  # Rate limit or quota exceeded
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Rate limited on attempt {attempt + 1}, "
                            f"retrying in {delay}s: {e}"
                        )
                        await asyncio.sleep(delay)
                    elif e.resp.status >= 500:  # Server error
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Server error on attempt {attempt + 1}, "
                            f"retrying in {delay}s: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise  # Don't retry client errors
                except Exception as e:
                    last_exception = e
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Error on attempt {attempt + 1}, "
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
        max_results: int = None
    ) -> List[VideoDTO]:
        """
        Fetch videos uploaded by a channel.
        
        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to fetch
            
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
        logger.info(f"Fetching up to {max_results} videos for channel: {channel_id}")
        
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
        
        while len(video_ids) < max_results:
            request = self.youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - len(video_ids)),
                pageToken=next_page_token
            )
            response = await self._run_sync(request.execute)
            
            for item in response.get("items", []):
                video_ids.append(item["contentDetails"]["videoId"])
            
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        
        # Fetch video details in batches
        videos = []
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i + 50]
            batch_videos = await self._fetch_video_details_batch(batch_ids, channel_id)
            videos.extend(batch_videos)
        
        return videos
    
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

