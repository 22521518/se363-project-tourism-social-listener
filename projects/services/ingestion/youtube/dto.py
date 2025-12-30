# YouTube Ingestion - Data Transfer Objects (DTO)
# Immutable data structures for transferring data between layers

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class ChannelDTO:
    """Data Transfer Object for YouTube Channel."""
    id: str
    title: str
    description: str
    custom_url: Optional[str]
    published_at: datetime
    thumbnail_url: str
    subscriber_count: int
    video_count: int
    view_count: int
    country: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "custom_url": self.custom_url,
            "published_at": self.published_at.isoformat(),
            "thumbnail_url": self.thumbnail_url,
            "subscriber_count": self.subscriber_count,
            "video_count": self.video_count,
            "view_count": self.view_count,
            "country": self.country,
        }


@dataclass(frozen=True)
class VideoDTO:
    """Data Transfer Object for YouTube Video."""
    id: str
    channel_id: str
    title: str
    description: str
    published_at: datetime
    thumbnail_url: str
    view_count: int
    like_count: int
    comment_count: int
    duration: str
    tags: tuple = field(default_factory=tuple)
    category_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "title": self.title,
            "description": self.description,
            "published_at": self.published_at.isoformat(),
            "thumbnail_url": self.thumbnail_url,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "duration": self.duration,
            "tags": list(self.tags),
            "category_id": self.category_id,
        }


@dataclass(frozen=True)
class CommentDTO:
    """Data Transfer Object for YouTube Comment."""
    id: str
    video_id: str
    author_display_name: str
    author_channel_id: Optional[str]
    text: str
    like_count: int
    published_at: datetime
    updated_at: datetime
    parent_id: Optional[str] = None  # None for top-level comments
    reply_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "video_id": self.video_id,
            "author_display_name": self.author_display_name,
            "author_channel_id": self.author_channel_id,
            "text": self.text,
            "like_count": self.like_count,
            "published_at": self.published_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "parent_id": self.parent_id,
            "reply_count": self.reply_count,
        }


@dataclass(frozen=True)
class RawIngestionMessage:
    """
    Standard ingestion output format as defined in AGENTS.md.
    
    Fields:
    - source: platform name (e.g., "youtube")
    - externalId: platform-specific ID
    - rawText: original content
    - createdAt: ISO timestamp
    - rawPayload: full API response
    """
    source: str
    external_id: str
    raw_text: str
    created_at: datetime
    raw_payload: Dict[str, Any]
    entity_type: str  # "channel", "video", or "comment"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source": self.source,
            "externalId": self.external_id,
            "rawText": self.raw_text,
            "createdAt": self.created_at.isoformat(),
            "rawPayload": self.raw_payload,
            "entityType": self.entity_type,
        }


@dataclass(frozen=True)
class TrackedChannelDTO:
    """Data Transfer Object for a tracked channel state."""
    channel_id: str
    last_checked: datetime
    last_video_published: Optional[datetime]
    is_active: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "channel_id": self.channel_id,
            "last_checked": self.last_checked.isoformat(),
            "last_video_published": self.last_video_published.isoformat() if self.last_video_published else None,
            "is_active": self.is_active,
        }


@dataclass
class IngestionCheckpointDTO:
    """
    Data Transfer Object for ingestion checkpoint/progress tracking.
    
    Used to resume fetching after rate limits or failures.
    """
    id: Optional[int]
    channel_id: str
    operation_type: str  # "fetch_videos", "fetch_comments", "full_ingestion"
    
    # Pagination state
    next_page_token: Optional[str] = None
    last_video_id: Optional[str] = None  # For comment fetching
    
    # Progress
    fetched_count: int = 0
    target_count: Optional[int] = None
    
    # Status
    status: str = "in_progress"  # in_progress, completed, rate_limited, failed
    error_message: Optional[str] = None
    error_code: Optional[int] = None
    
    # Rate limit info
    rate_limit_reset_at: Optional[datetime] = None
    retry_count: int = 0
    
    # Timestamps
    started_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "operation_type": self.operation_type,
            "next_page_token": self.next_page_token,
            "last_video_id": self.last_video_id,
            "fetched_count": self.fetched_count,
            "target_count": self.target_count,
            "status": self.status,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "rate_limit_reset_at": self.rate_limit_reset_at.isoformat() if self.rate_limit_reset_at else None,
            "retry_count": self.retry_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class RateLimitError(Exception):
    """
    Custom exception for YouTube API rate limit errors.
    
    Contains checkpoint info so the caller can save progress and retry later.
    """
    def __init__(
        self, 
        message: str, 
        error_code: int = 429,
        checkpoint: Optional[IngestionCheckpointDTO] = None,
        retry_after: Optional[int] = None,  # Seconds until rate limit resets
    ):
        super().__init__(message)
        self.error_code = error_code
        self.checkpoint = checkpoint
        self.retry_after = retry_after
    
    def __str__(self):
        base = f"RateLimitError({self.error_code}): {super().__str__()}"
        if self.retry_after:
            base += f" (retry after {self.retry_after}s)"
        if self.checkpoint:
            base += f" [checkpoint: {self.checkpoint.fetched_count} items fetched]"
        return base
