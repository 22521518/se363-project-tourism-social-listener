# Intention Extraction - Data Access Objects (DAO)
# Database access layer for intention entities

from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

from .models import Base, IntentionModel,IntentionType
from ....ingestion.youtube.models import YouTubeCommentModel
from ....ingestion.youtube.dto import CommentDTO
from .dto import (
    IntentionDTO, 
    IntentionStatsDTO,
)

from .config import DatabaseConfig


class IntentionDAO:
    """
    Data Access Object for Intention entities.
    Handles all database operations for intention extraction results.
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
            # ==================== CREATE OPERATIONS ====================
    
    def save(self, intention_dto: IntentionDTO) -> Optional[IntentionDTO]:
        """
        Save a new intention record.
        
        Args:
            intention_dto: IntentionDTO to persist
            
        Returns:
            Saved IntentionDTO with database-generated ID, or None if failed
        """
        try:
            with self.get_session() as session:
                intention_model = IntentionModel(
                    source_id=intention_dto.source_id,
                    source_type=intention_dto.source_type,
                    raw_text=intention_dto.raw_text,
                    intention_type=intention_dto.intention_type.value,
                )
                
                session.add(intention_model)
                session.flush()  # Get the generated ID
                
                return self._model_to_dto(intention_model)
                
        except IntegrityError as e:
            logger.warning(f"Intention already exists for source_id={intention_dto.source_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating intention: {e}", exc_info=True)
            return None
    
    def save_batch(
    self,
    intention_dtos: List[IntentionDTO]
    ) -> List[IntentionDTO]:
        """
        Save multiple intention records in a single transaction.

        Args:
            intention_dtos: List of IntentionDTO objects to persist

        Returns:
            List of successfully saved IntentionDTOs
        """
        if not intention_dtos:
            return []

        saved_dtos: List[IntentionDTO] = []

        try:
            with self.get_session() as session:
                models = []

                for dto in intention_dtos:
                    model = IntentionModel(
                        source_id=dto.source_id,
                        source_type=dto.source_type,
                        raw_text=dto.raw_text,
                        intention_type=dto.intention_type.value,
                    )
                    models.append(model)

                session.add_all(models)
                session.flush()  # populate IDs without committing yet

                for model in models:
                    saved_dtos.append(self._model_to_dto(model))

                return saved_dtos

        except IntegrityError as e:
            logger.warning(f"Duplicate intention(s) detected in batch: {e}")
            return saved_dtos  # partial success is OK

        except Exception as e:
            logger.error("Error creating intention batch", exc_info=True)
            return []
    
    def upsert_intention(self, intention_dto: IntentionDTO) -> Optional[IntentionDTO]:
        """
        Insert or update intention (upsert based on source_id + source_type).
        
        Args:
            intention_dto: IntentionDTO to upsert
            
        Returns:
            Upserted IntentionDTO or None if failed
        """
        try:
            with self.get_session() as session:
                existing = session.query(IntentionModel).filter(
                    and_(
                        IntentionModel.source_id == intention_dto.source_id,
                        IntentionModel.source_type == intention_dto.source_type
                    )
                ).first()
                
                if existing:
                    # Update existing
                    existing.raw_text = intention_dto.raw_text
                    existing.intention_type = intention_dto.intention_type.value
                    
                    logger.info(f"Updated intention for source_id={intention_dto.source_id}")
                    return self._model_to_dto(existing)
                else:
                    # Create new
                    return self.create_intention(intention_dto)
                    
        except Exception as e:
            logger.error(f"Error upserting intention: {e}", exc_info=True)
            return None
    
    # ==================== READ OPERATIONS ====================

    
    def get_all_intentions(
        self,
        limit: int = 1000,
        offset: int = 0
    ) -> List[IntentionDTO]:
        """
        Get all intentions with pagination.
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of IntentionDTOs
        """
        try:
            with self.get_session() as session:
                intentions = session.query(IntentionModel).order_by(
                    IntentionModel.created_at.desc()
                ).limit(limit).offset(offset).all()
                
                return [self._model_to_dto(i) for i in intentions]
                
        except Exception as e:
            logger.error(f"Error getting all intentions: {e}", exc_info=True)
            return []
    def get_all_unprocessed(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[CommentDTO]:
        """
        Get all unprocessed comments with pagination.
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of CommentDTO
        """
        try:
            with self.get_session() as session:
                # Subquery to get all source_ids from intentions table
                processed_ids = session.query(IntentionModel.source_id).subquery()
                
                unprocessed = session.query(YouTubeCommentModel).filter(
                    YouTubeCommentModel.id.notin_(processed_ids)
                ).order_by(
                    YouTubeCommentModel.created_at.desc(),
                    YouTubeCommentModel.id.desc(),
                ).limit(limit).offset(offset).all()
                
                return [
                    CommentDTO(
                        id=comment.id,
                        video_id=comment.video_id,
                        author_display_name=comment.author_display_name,  # Map 'author' to 'author_display_name'
                        author_channel_id=comment.author_channel_id if hasattr(comment, 'author_channel_id') else None,
                        text=comment.text,
                        like_count=comment.like_count if hasattr(comment, 'like_count') else 0,
                        published_at=comment.published_at if hasattr(comment, 'published_at') else comment.created_at,
                        updated_at=comment.updated_at,
                        parent_id=comment.parent_id if hasattr(comment, 'parent_id') else None,
                        reply_count=comment.reply_count if hasattr(comment, 'reply_count') else 0,
                    )
                    for comment in unprocessed
                ] 
                
        except Exception as e:
            logger.error(f"Error getting all unprocessed comments: {e}", exc_info=True)
            return []
        
    # ==================== UPDATE OPERATIONS ====================
    
    def update(self, intention_dto: IntentionDTO) -> Optional[IntentionDTO]:
        """
        Update an existing intention record.
        
        Args:
            intention_dto: IntentionDTO with updated values
            
        Returns:
            Updated IntentionDTO or None if not found
        """
        try:
            with self.get_session() as session:
                existing = session.query(IntentionModel).filter(
                    IntentionModel.id == intention_dto.id
                ).first()
                
                if not existing:
                    logger.warning(f"Intention not found for update: {intention_dto.id}")
                    return None
                
                # Update fields
                existing.raw_text = intention_dto.raw_text
                existing.intention_type = intention_dto.intention_type.value
                
                session.flush()
                return self._model_to_dto(existing)
                
        except Exception as e:
            logger.error(f"Error updating intention: {e}", exc_info=True)
            return None
    
    # ==================== STATISTICS ====================
    
    def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> IntentionStatsDTO:
        """
        Get intention statistics for a time period.
        
        Args:
            start_date: Start of period (defaults to 30 days ago)
            end_date: End of period (defaults to now)
            
        Returns:
            IntentionStatsDTO with aggregated statistics
        """
        if start_date is None:
            start_date = datetime.now(UTC) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(UTC)
        
        try:
            with self.get_session() as session:
                # Total processed
                total = session.query(func.count(IntentionModel.id)).filter(
                    and_(
                        IntentionModel.created_at >= start_date,
                        IntentionModel.created_at <= end_date
                    )
                ).scalar() or 0
                
                # By intention type
                by_type = session.query(
                    IntentionModel.intention_type,
                    func.count(IntentionModel.id)
                ).filter(
                    and_(
                        IntentionModel.created_at >= start_date,
                        IntentionModel.created_at <= end_date
                    )
                ).group_by(IntentionModel.intention_type).all()
                
                
                # By source type
                by_source = session.query(
                    IntentionModel.source_type,
                    func.count(IntentionModel.id)
                ).filter(
                    and_(
                        IntentionModel.created_at >= start_date,
                        IntentionModel.created_at <= end_date
                    )
                ).group_by(IntentionModel.source_type).all()
                
               
                
                return IntentionStatsDTO(
                    period_start=start_date,
                    period_end=end_date,
                    total_processed=total,
                    by_intention_type={k.value: v for k, v in by_type if k is not None},
                    by_source_type={str(k): v for k, v in by_source},
            
                )
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            # Return empty stats on error
            return IntentionStatsDTO(
                period_start=start_date,
                period_end=end_date,
                total_processed=0,
                by_intention_type={},
                by_source_type={},
            )
    
    # ==================== DELETE OPERATIONS ====================
    
    def delete(self, intention_id: str) -> bool:
        """
        Delete intention by ID.
        
        Args:
            intention_id: UUID of the intention
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            with self.get_session() as session:
                deleted = session.query(IntentionModel).filter(
                    IntentionModel.id == intention_id
                ).delete()
                
                return deleted > 0
                
        except Exception as e:
            logger.error(f"Error deleting intention: {e}", exc_info=True)
            return False
    
    
    # ==================== HELPER METHODS ====================
    
    def _model_to_dto(self, model: IntentionModel) -> IntentionDTO:
        """Convert IntentionModel to IntentionDTO."""
        return IntentionDTO(
            id=str(model.id),
            source_id=model.source_id,
            source_type=model.source_type,
            raw_text=model.raw_text,
            intention_type=IntentionType(model.intention_type) if model.intention_type else IntentionType.OTHER,
        )
