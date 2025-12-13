# YouTube Ingestion - Data Access Objects (DAO)
# Database access layer for YouTube entities

from datetime import datetime, UTC
from typing import Optional, List
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from .models import (
    Base,
    YouTubeChannelModel,
    YouTubeVideoModel,
    YouTubeCommentModel,
    TrackedChannelModel,
)
from .dto import ChannelDTO, VideoDTO, CommentDTO, TrackedChannelDTO
from .config import DatabaseConfig


class YouTubeDAO:
    """
    Data Access Object for YouTube entities.
    Handles all database operations for channels, videos, and comments.
    """
    
    def __init__(self, config: DatabaseConfig):
        """Initialize DAO with database configuration."""
        self.engine = create_engine(config.connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def init_db(self) -> None:
        """Initialize database tables."""
        Base.metadata.create_all(self.engine)
    
    # ===================
    # Channel Operations
    # ===================
    
    def save_channel(self, channel: ChannelDTO, raw_payload: dict = None) -> None:
        """
        Save or update a channel in the database.
        Uses upsert pattern for idempotency.
        """
        with self.get_session() as session:
            existing = session.query(YouTubeChannelModel).filter_by(id=channel.id).first()
            
            if existing:
                # Update existing channel
                existing.title = channel.title
                existing.description = channel.description
                existing.custom_url = channel.custom_url
                existing.thumbnail_url = channel.thumbnail_url
                existing.subscriber_count = channel.subscriber_count
                existing.video_count = channel.video_count
                existing.view_count = channel.view_count
                existing.country = channel.country
                existing.raw_payload = raw_payload
                existing.updated_at = datetime.now(UTC)
            else:
                # Insert new channel
                model = YouTubeChannelModel(
                    id=channel.id,
                    title=channel.title,
                    description=channel.description,
                    custom_url=channel.custom_url,
                    published_at=channel.published_at,
                    thumbnail_url=channel.thumbnail_url,
                    subscriber_count=channel.subscriber_count,
                    video_count=channel.video_count,
                    view_count=channel.view_count,
                    country=channel.country,
                    raw_payload=raw_payload,
                )
                session.add(model)
    
    def get_channel(self, channel_id: str) -> Optional[ChannelDTO]:
        """Retrieve a channel by ID."""
        with self.get_session() as session:
            model = session.query(YouTubeChannelModel).filter_by(id=channel_id).first()
            if not model:
                return None
            return self._model_to_channel_dto(model)
    
    def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel and all related data."""
        with self.get_session() as session:
            model = session.query(YouTubeChannelModel).filter_by(id=channel_id).first()
            if not model:
                return False
            session.delete(model)
            return True
    
    def list_channels(self, limit: int = 100, offset: int = 0) -> List[ChannelDTO]:
        """List all channels with pagination."""
        with self.get_session() as session:
            models = session.query(YouTubeChannelModel).limit(limit).offset(offset).all()
            return [self._model_to_channel_dto(m) for m in models]
    
    # ===================
    # Video Operations
    # ===================
    
    def save_video(self, video: VideoDTO, raw_payload: dict = None) -> None:
        """Save or update a video in the database."""
        with self.get_session() as session:
            existing = session.query(YouTubeVideoModel).filter_by(id=video.id).first()
            
            if existing:
                existing.title = video.title
                existing.description = video.description
                existing.thumbnail_url = video.thumbnail_url
                existing.view_count = video.view_count
                existing.like_count = video.like_count
                existing.comment_count = video.comment_count
                existing.duration = video.duration
                existing.tags = list(video.tags)
                existing.category_id = video.category_id
                existing.raw_payload = raw_payload
                existing.updated_at = datetime.now(UTC)
            else:
                model = YouTubeVideoModel(
                    id=video.id,
                    channel_id=video.channel_id,
                    title=video.title,
                    description=video.description,
                    published_at=video.published_at,
                    thumbnail_url=video.thumbnail_url,
                    view_count=video.view_count,
                    like_count=video.like_count,
                    comment_count=video.comment_count,
                    duration=video.duration,
                    tags=list(video.tags),
                    category_id=video.category_id,
                    raw_payload=raw_payload,
                )
                session.add(model)
    
    def save_videos(self, videos: List[VideoDTO], raw_payloads: List[dict] = None) -> None:
        """Save multiple videos in a batch."""
        raw_payloads = raw_payloads or [None] * len(videos)
        for video, payload in zip(videos, raw_payloads):
            self.save_video(video, payload)
    
    def get_video(self, video_id: str) -> Optional[VideoDTO]:
        """Retrieve a video by ID."""
        with self.get_session() as session:
            model = session.query(YouTubeVideoModel).filter_by(id=video_id).first()
            if not model:
                return None
            return self._model_to_video_dto(model)
    
    def get_channel_videos(self, channel_id: str, limit: int = 50) -> List[VideoDTO]:
        """Get videos for a specific channel."""
        with self.get_session() as session:
            models = (
                session.query(YouTubeVideoModel)
                .filter_by(channel_id=channel_id)
                .order_by(YouTubeVideoModel.published_at.desc())
                .limit(limit)
                .all()
            )
            return [self._model_to_video_dto(m) for m in models]
    
    def get_video_ids_for_channel(self, channel_id: str) -> List[str]:
        """Get list of video IDs for a channel (for deduplication)."""
        with self.get_session() as session:
            results = (
                session.query(YouTubeVideoModel.id)
                .filter_by(channel_id=channel_id)
                .all()
            )
            return [r[0] for r in results]
    
    # ===================
    # Comment Operations
    # ===================
    
    def save_comment(self, comment: CommentDTO, raw_payload: dict = None) -> None:
        """Save or update a comment in the database."""
        with self.get_session() as session:
            existing = session.query(YouTubeCommentModel).filter_by(id=comment.id).first()
            
            if existing:
                existing.text = comment.text
                existing.like_count = comment.like_count
                existing.updated_at_youtube = comment.updated_at
                existing.reply_count = comment.reply_count
                existing.raw_payload = raw_payload
                existing.updated_at = datetime.now(UTC)
            else:
                model = YouTubeCommentModel(
                    id=comment.id,
                    video_id=comment.video_id,
                    author_display_name=comment.author_display_name,
                    author_channel_id=comment.author_channel_id,
                    text=comment.text,
                    like_count=comment.like_count,
                    published_at=comment.published_at,
                    updated_at_youtube=comment.updated_at,
                    parent_id=comment.parent_id,
                    reply_count=comment.reply_count,
                    raw_payload=raw_payload,
                )
                session.add(model)
    
    def save_comments(self, comments: List[CommentDTO], raw_payloads: List[dict] = None) -> None:
        """Save multiple comments in a batch."""
        raw_payloads = raw_payloads or [None] * len(comments)
        for comment, payload in zip(comments, raw_payloads):
            self.save_comment(comment, payload)
    
    def get_video_comments(self, video_id: str, limit: int = 100) -> List[CommentDTO]:
        """Get comments for a specific video."""
        with self.get_session() as session:
            models = (
                session.query(YouTubeCommentModel)
                .filter_by(video_id=video_id)
                .order_by(YouTubeCommentModel.published_at.desc())
                .limit(limit)
                .all()
            )
            return [self._model_to_comment_dto(m) for m in models]
    
    # ===================
    # Tracking Operations
    # ===================
    
    def register_tracked_channel(self, channel_id: str) -> None:
        """Register a channel for tracking."""
        with self.get_session() as session:
            # Ensure channel exists to satisfy foreign key
            channel = session.query(YouTubeChannelModel).filter_by(id=channel_id).first()
            if not channel:
                # Create stub channel
                channel = YouTubeChannelModel(
                    id=channel_id,
                    title=f"Pending Ingestion ({channel_id})",
                    description="Channel added via monitor, pending ingestion",
                    published_at=datetime.now(UTC),
                    is_tracked=True,
                )
                session.add(channel)
                session.flush() # Ensure ID is available
            else:
                channel.is_tracked = True

            existing = session.query(TrackedChannelModel).filter_by(channel_id=channel_id).first()
            
            if existing:
                existing.is_active = True
                existing.updated_at = datetime.now(UTC)
            else:
                model = TrackedChannelModel(
                    channel_id=channel_id,
                    is_active=True,
                )
                session.add(model)
    
    def unregister_tracked_channel(self, channel_id: str) -> None:
        """Unregister a channel from tracking."""
        with self.get_session() as session:
            tracked = session.query(TrackedChannelModel).filter_by(channel_id=channel_id).first()
            if tracked:
                tracked.is_active = False
            
            channel = session.query(YouTubeChannelModel).filter_by(id=channel_id).first()
            if channel:
                channel.is_tracked = False
    
    def get_tracked_channels(self, active_only: bool = True) -> List[TrackedChannelDTO]:
        """Get all tracked channels."""
        with self.get_session() as session:
            query = session.query(TrackedChannelModel)
            if active_only:
                query = query.filter_by(is_active=True)
            models = query.all()
            return [self._model_to_tracked_dto(m) for m in models]
    
    def update_tracking_state(
        self, 
        channel_id: str, 
        last_checked: datetime,
        last_video_published: Optional[datetime] = None
    ) -> None:
        """Update tracking state after checking a channel."""
        with self.get_session() as session:
            tracked = session.query(TrackedChannelModel).filter_by(channel_id=channel_id).first()
            if tracked:
                tracked.last_checked = last_checked
                if last_video_published:
                    tracked.last_video_published = last_video_published
            
            channel = session.query(YouTubeChannelModel).filter_by(id=channel_id).first()
            if channel:
                channel.last_checked = last_checked
    
    # ===================
    # Helper Methods
    # ===================
    
    @staticmethod
    def _model_to_channel_dto(model: YouTubeChannelModel) -> ChannelDTO:
        """Convert ORM model to DTO."""
        return ChannelDTO(
            id=model.id,
            title=model.title,
            description=model.description or "",
            custom_url=model.custom_url,
            published_at=model.published_at,
            thumbnail_url=model.thumbnail_url or "",
            subscriber_count=model.subscriber_count,
            video_count=model.video_count,
            view_count=model.view_count,
            country=model.country,
        )
    
    @staticmethod
    def _model_to_video_dto(model: YouTubeVideoModel) -> VideoDTO:
        """Convert ORM model to DTO."""
        return VideoDTO(
            id=model.id,
            channel_id=model.channel_id,
            title=model.title,
            description=model.description or "",
            published_at=model.published_at,
            thumbnail_url=model.thumbnail_url or "",
            view_count=model.view_count,
            like_count=model.like_count,
            comment_count=model.comment_count,
            duration=model.duration or "",
            tags=tuple(model.tags or []),
            category_id=model.category_id,
        )
    
    @staticmethod
    def _model_to_comment_dto(model: YouTubeCommentModel) -> CommentDTO:
        """Convert ORM model to DTO."""
        return CommentDTO(
            id=model.id,
            video_id=model.video_id,
            author_display_name=model.author_display_name,
            author_channel_id=model.author_channel_id,
            text=model.text,
            like_count=model.like_count,
            published_at=model.published_at,
            updated_at=model.updated_at_youtube,
            parent_id=model.parent_id,
            reply_count=model.reply_count,
        )
    
    @staticmethod
    def _model_to_tracked_dto(model: TrackedChannelModel) -> TrackedChannelDTO:
        """Convert ORM model to DTO."""
        return TrackedChannelDTO(
            channel_id=model.channel_id,
            last_checked=model.last_checked,
            last_video_published=model.last_video_published,
            is_active=model.is_active,
        )
