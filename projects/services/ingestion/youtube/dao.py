# YouTube Ingestion - Data Access Objects (DAO)
# Database access layer for YouTube entities

from datetime import datetime, UTC
from typing import Optional, List
from contextlib import contextmanager

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, ProgrammingError

from .models import (
    Base,
    YouTubeChannelModel,
    YouTubeVideoModel,
    YouTubeCommentModel,
    TrackedChannelModel,
    IngestionCheckpointModel,
)
from .dto import ChannelDTO, VideoDTO, CommentDTO, TrackedChannelDTO, IngestionCheckpointDTO
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
        # Ensure schema integrity before creating new tables
        self._ensure_schema_integrity()
        Base.metadata.create_all(self.engine)

    def _ensure_schema_integrity(self) -> None:
        """
        Check for and fix known schema issues.
        Specifically ensures tables have primary keys.
        """
        inspector = inspect(self.engine)
        
        # List of tables to check for missing PKs
        tables_to_check = ["youtube_channels", "youtube_videos", "youtube_comments"]
        
        with self.engine.connect() as conn:
            for table_name in tables_to_check:
                if inspector.has_table(table_name):
                    pk_constraint = inspector.get_pk_constraint(table_name)
                    if not pk_constraint or not pk_constraint.get("constrained_columns"):
                        print(f"Fixing missing PRIMARY KEY on {table_name} table...")
                        try:
                            # We assume 'id' column exists and should be the PK
                            conn.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY (id)"))
                            conn.commit()
                            print(f"Successfully added PRIMARY KEY to {table_name}")
                        except Exception as e:
                            print(f"Warning: Could not add PRIMARY KEY to {table_name}: {e}")

    
    # ===================
    # Channel Operations
    # ===================
    
    # ===================
    # Channel Operations
    # ===================
    
    def save_channel(self, channel: ChannelDTO, raw_payload: dict = None) -> None:
        """
        Save or update a channel in the database.
        Uses upsert pattern for idempotency.
        """
        self.save_channels([channel], [raw_payload] if raw_payload else None)

    def save_channels(self, channels: List[ChannelDTO], raw_payloads: List[dict] = None) -> None:
        """Save multiple channels in a batch using optimal Postgres upsert."""
        if not channels:
            return

        from sqlalchemy.dialects.postgresql import insert
        
        raw_payloads = raw_payloads or [None] * len(channels)
        values_dict = {}  # Use dict to deduplicate by id, keeping last occurrence
        now = datetime.now(UTC)

        for channel, payload in zip(channels, raw_payloads):
            values_dict[channel.id] = {
                "id": channel.id,
                "title": channel.title,
                "description": channel.description,
                "custom_url": channel.custom_url,
                "published_at": channel.published_at,
                "thumbnail_url": channel.thumbnail_url,
                "subscriber_count": channel.subscriber_count,
                "video_count": channel.video_count,
                "view_count": channel.view_count,
                "country": channel.country,
                "raw_payload": payload,
                "updated_at": now
            }

        values = list(values_dict.values())  # Deduplicated list
        stmt = insert(YouTubeChannelModel).values(values)
        
        # Define update columns (exclude primary key and created_at)
        update_dict = {
            col.name: col for col in stmt.excluded 
            if col.name not in ['id', 'created_at']
        }
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_=update_dict
        )
        
        with self.get_session() as session:
            try:
                session.execute(stmt)
            except Exception as e:
                print(f"Error bulk saving channels: {e}")
                raise
    
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
        self.save_videos([video], [raw_payload] if raw_payload else None)
    
    def save_videos(self, videos: List[VideoDTO], raw_payloads: List[dict] = None) -> None:
        """Save multiple videos in a batch using optimal Postgres upsert."""
        if not videos:
            return

        from sqlalchemy.dialects.postgresql import insert
        
        raw_payloads = raw_payloads or [None] * len(videos)
        values_dict = {}  # Use dict to deduplicate by id, keeping last occurrence
        now = datetime.now(UTC)

        for video, payload in zip(videos, raw_payloads):
            values_dict[video.id] = {
                "id": video.id,
                "channel_id": video.channel_id,
                "title": video.title,
                "description": video.description,
                "published_at": video.published_at,
                "thumbnail_url": video.thumbnail_url,
                "view_count": video.view_count,
                "like_count": video.like_count,
                "comment_count": video.comment_count,
                "duration": video.duration,
                "tags": list(video.tags),
                "category_id": video.category_id,
                "raw_payload": payload,
                "updated_at": now
            }

        values = list(values_dict.values())  # Deduplicated list

        stmt = insert(YouTubeVideoModel).values(values)
        
        update_dict = {
            col.name: col for col in stmt.excluded 
            if col.name not in ['id', 'created_at']
        }
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_=update_dict
        )
        
        with self.get_session() as session:
            try:
                session.execute(stmt)
            except Exception as e:
                print(f"Error bulk saving videos: {e}")
                # Fallback or re-raise? Re-raising to let Spark retry logic handle it
                raise
    
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
        self.save_comments([comment], [raw_payload] if raw_payload else None)
    
    def save_comments(self, comments: List[CommentDTO], raw_payloads: List[dict] = None) -> None:
        """Save multiple comments in a batch using optimal Postgres upsert."""
        if not comments:
            return

        from sqlalchemy.dialects.postgresql import insert
        
        raw_payloads = raw_payloads or [None] * len(comments)
        values_dict = {}  # Use dict to deduplicate by id, keeping last occurrence
        now = datetime.now(UTC)

        for comment, payload in zip(comments, raw_payloads):
            values_dict[comment.id] = {
                "id": comment.id,
                "video_id": comment.video_id,
                "author_display_name": comment.author_display_name,
                "author_channel_id": comment.author_channel_id,
                "text": comment.text,
                "like_count": comment.like_count,
                "published_at": comment.published_at,
                "updated_at_youtube": comment.updated_at,
                "parent_id": comment.parent_id,
                "reply_count": comment.reply_count,
                "raw_payload": payload,
                "updated_at": now
            }

        values = list(values_dict.values())  # Deduplicated list
        stmt = insert(YouTubeCommentModel).values(values)
        
        update_dict = {
            col.name: col for col in stmt.excluded 
            if col.name not in ['id', 'created_at']
        }
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_=update_dict
        )
        
        with self.get_session() as session:
            try:
                session.execute(stmt)
            except Exception as e:
                print(f"Error bulk saving comments: {e}")
                raise
    
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

    # ===================
    # Checkpoint Operations
    # ===================
    
    def save_checkpoint(self, checkpoint: 'IngestionCheckpointDTO') -> int:
        """
        Save or update an ingestion checkpoint.
        
        Returns:
            The checkpoint ID
        """
        from .models import IngestionCheckpointModel
        
        with self.get_session() as session:
            if checkpoint.id:
                # Update existing
                model = session.query(IngestionCheckpointModel).filter_by(id=checkpoint.id).first()
                if model:
                    model.next_page_token = checkpoint.next_page_token
                    model.last_video_id = checkpoint.last_video_id
                    model.fetched_count = checkpoint.fetched_count
                    model.target_count = checkpoint.target_count
                    model.status = checkpoint.status
                    model.error_message = checkpoint.error_message
                    model.error_code = checkpoint.error_code
                    model.rate_limit_reset_at = checkpoint.rate_limit_reset_at
                    model.retry_count = checkpoint.retry_count
                    model.completed_at = checkpoint.completed_at
                    session.flush()
                    return model.id
            
            # Create new
            model = IngestionCheckpointModel(
                channel_id=checkpoint.channel_id,
                operation_type=checkpoint.operation_type,
                next_page_token=checkpoint.next_page_token,
                last_video_id=checkpoint.last_video_id,
                fetched_count=checkpoint.fetched_count,
                target_count=checkpoint.target_count,
                status=checkpoint.status,
                error_message=checkpoint.error_message,
                error_code=checkpoint.error_code,
                rate_limit_reset_at=checkpoint.rate_limit_reset_at,
                retry_count=checkpoint.retry_count,
            )
            session.add(model)
            session.flush()
            return model.id
    
    def get_active_checkpoint(
        self, 
        channel_id: str, 
        operation_type: str
    ) -> Optional['IngestionCheckpointDTO']:
        """
        Get an active (non-completed) checkpoint for a channel and operation.
        
        Used to resume interrupted fetches.
        """
        from .models import IngestionCheckpointModel
        from .dto import IngestionCheckpointDTO
        
        with self.get_session() as session:
            model = (
                session.query(IngestionCheckpointModel)
                .filter_by(
                    channel_id=channel_id,
                    operation_type=operation_type,
                )
                .filter(IngestionCheckpointModel.status.in_(["in_progress", "rate_limited"]))
                .order_by(IngestionCheckpointModel.started_at.desc())
                .first()
            )
            
            if not model:
                return None
            
            return self._model_to_checkpoint_dto(model)
    
    def get_checkpoint_by_id(self, checkpoint_id: int) -> Optional['IngestionCheckpointDTO']:
        """Get a checkpoint by ID."""
        from .models import IngestionCheckpointModel
        
        with self.get_session() as session:
            model = session.query(IngestionCheckpointModel).filter_by(id=checkpoint_id).first()
            if not model:
                return None
            return self._model_to_checkpoint_dto(model)
    
    def complete_checkpoint(self, checkpoint_id: int) -> None:
        """Mark a checkpoint as completed."""
        from .models import IngestionCheckpointModel
        
        with self.get_session() as session:
            model = session.query(IngestionCheckpointModel).filter_by(id=checkpoint_id).first()
            if model:
                model.status = "completed"
                model.completed_at = datetime.now(UTC)
    
    def get_rate_limited_checkpoints(self) -> List['IngestionCheckpointDTO']:
        """Get all checkpoints that are rate-limited and ready to retry."""
        from .models import IngestionCheckpointModel
        from .dto import IngestionCheckpointDTO
        
        with self.get_session() as session:
            now = datetime.now(UTC)
            models = (
                session.query(IngestionCheckpointModel)
                .filter_by(status="rate_limited")
                .filter(
                    (IngestionCheckpointModel.rate_limit_reset_at == None) |  # noqa: E711
                    (IngestionCheckpointModel.rate_limit_reset_at <= now)
                )
                .all()
            )
            return [self._model_to_checkpoint_dto(m) for m in models]
    
    def delete_old_checkpoints(self, days: int = 7) -> int:
        """Delete completed checkpoints older than specified days."""
        from .models import IngestionCheckpointModel
        from datetime import timedelta
        
        with self.get_session() as session:
            cutoff = datetime.now(UTC) - timedelta(days=days)
            deleted = (
                session.query(IngestionCheckpointModel)
                .filter_by(status="completed")
                .filter(IngestionCheckpointModel.completed_at < cutoff)
                .delete()
            )
            return deleted
    
    @staticmethod
    def _model_to_checkpoint_dto(model: 'IngestionCheckpointModel') -> 'IngestionCheckpointDTO':
        """Convert ORM model to DTO."""
        from .dto import IngestionCheckpointDTO
        
        return IngestionCheckpointDTO(
            id=model.id,
            channel_id=model.channel_id,
            operation_type=model.operation_type,
            next_page_token=model.next_page_token,
            last_video_id=model.last_video_id,
            fetched_count=model.fetched_count,
            target_count=model.target_count,
            status=model.status,
            error_message=model.error_message,
            error_code=model.error_code,
            rate_limit_reset_at=model.rate_limit_reset_at,
            retry_count=model.retry_count,
            started_at=model.started_at,
            last_updated=model.last_updated,
            completed_at=model.completed_at,
        )
