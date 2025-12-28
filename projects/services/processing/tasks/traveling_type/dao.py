# Intention Extraction - Data Access Objects (DAO)
# Database access layer for intention entities

from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import logging

from .models import Base, TravelingTypeModel,TravelingType
from .dto import (
    TravelingTypeDTO, 
    TravelingStatsDTO,
)

from .config import DatabaseConfig


class TravelingTypeDAO:
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
    
    def save(self, traveling_type_dto: TravelingTypeDTO) -> Optional[TravelingTypeDTO]:
        """
        Save a new intention record.
        
        Args:
            traveling_type_dto: TravelingTypeDTO to persist
            
        Returns:
            Saved TravelingTypeDTO with database-generated ID, or None if failed
        """
        try:
            with self.get_session() as session:
                intention_model = TravelingTypeModel(
                    source_id=traveling_type_dto.source_id,
                    source_type=traveling_type_dto.source_type,
                    raw_text=traveling_type_dto.raw_text,
                    traveling_type=traveling_type_dto.traveling_type.value,
                )
                
                session.add(intention_model)
                session.flush()  # Get the generated ID
                
                return self._model_to_dto(intention_model)
                
        except IntegrityError as e:
            logger.warning(f"Intention already exists for source_id={traveling_type_dto.source_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating intention: {e}", exc_info=True)
            return None
    
    def save_batch(
    self,
    traveling_type_dtos: List[TravelingTypeDTO]
    ) -> List[TravelingTypeDTO]:
        """
        Save multiple intention records in a single transaction.

        Args:
            traveling_type_dtos: List of TravelingTypeDTO objects to persist

        Returns:
            List of successfully saved TravelingTypeDTOs
        """
        if not traveling_type_dtos:
            return []

        saved_dtos: List[TravelingTypeDTO] = []

        try:
            with self.get_session() as session:
                models = []

                for dto in traveling_type_dtos:
                    model = TravelingTypeModel(
                        source_id=dto.source_id,
                        source_type=dto.source_type,
                        raw_text=dto.raw_text,
                        traveling_type=dto.traveling_type.value,
                    )
                    models.append(model)

                session.add_all(models)
                session.flush()  # populate IDs without committing yet

                for model in models:
                    saved_dtos.append(self._model_to_dto(model))

                return saved_dtos

        except IntegrityError as e:
            logger.warning(f"Duplicate traveling type(s) detected in batch: {e}")
            return saved_dtos  # partial success is OK

        except Exception as e:
            logger.error("Error creating traveling type batch", exc_info=True)
            return []
    
    def upsert_traveling_type(self, traveling_type_dto: TravelingTypeDTO) -> Optional[TravelingTypeDTO]:
        """
        Insert or update intention (upsert based on source_id + source_type).
        
        Args:
            traveling_type_dto: TravelingTypeDTO to upsert
            
        Returns:
            Upserted TravelingTypeDTO or None if failed
        """
        try:
            with self.get_session() as session:
                existing = session.query(TravelingTypeModel).filter(
                    and_(
                        TravelingTypeModel.source_id == traveling_type_dto.source_id,
                        TravelingTypeModel.source_type == traveling_type_dto.source_type
                    )
                ).first()
                
                if existing:
                    # Update existing
                    existing.raw_text = traveling_type_dto.raw_text
                    existing.traveling_type = traveling_type_dto.traveling_type.value
                    
                    logger.info(f"Updated traveling type for source_id={traveling_type_dto.source_id}")
                    return self._model_to_dto(existing)
                else:
                    # Create new
                    return self.create_intention(traveling_type_dto)
                    
        except Exception as e:
            logger.error(f"Error upserting intention: {e}", exc_info=True)
            return None
    
    # ==================== READ OPERATIONS ====================

    
    def get_all_traveling_types(
        self,
        limit: int = 1000,
        offset: int = 0
    ) -> List[TravelingTypeDTO]:
        """
        Get all traveling type with pagination.
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of TravelingTypeDTOs
        """
        try:
            with self.get_session() as session:
                traveling_types = session.query(TravelingTypeModel).order_by(
                    TravelingTypeModel.created_at.desc()
                ).limit(limit).offset(offset).all()
                
                return [self._model_to_dto(i) for i in traveling_types]
                
        except Exception as e:
            logger.error(f"Error getting all traveling types: {e}", exc_info=True)
            return []
    
    # ==================== UPDATE OPERATIONS ====================
    
    def update(self, traveling_type_dto: TravelingTypeDTO) -> Optional[TravelingTypeDTO]:
        """
        Update an existing intention record.
        
        Args:
            traveling_type_dto: TravelingTypeDTO with updated values
            
        Returns:
            Updated TravelingTypeDTO or None if not found
        """
        try:
            with self.get_session() as session:
                existing = session.query(TravelingTypeModel).filter(
                    TravelingTypeModel.id == traveling_type_dto.id
                ).first()
                
                if not existing:
                    logger.warning(f"Traveling type not found for update: {traveling_type_dto.id}")
                    return None
                
                # Update fields
                existing.raw_text = traveling_type_dto.raw_text
                existing.traveling_type = traveling_type_dto.traveling_type.value
                
                session.flush()
                return self._model_to_dto(existing)
                
        except Exception as e:
            logger.error(f"Error updating traveling type: {e}", exc_info=True)
            return None
    
    # ==================== STATISTICS ====================
    
    def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TravelingStatsDTO:
        """
        Get traveling type statistics for a time period.
        
        Args:
            start_date: Start of period (defaults to 30 days ago)
            end_date: End of period (defaults to now)
            
        Returns:
            TravelingStatsDTO with aggregated statistics
        """
        if start_date is None:
            start_date = datetime.now(UTC) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(UTC)
        
        try:
            with self.get_session() as session:
                # Total processed
                total = session.query(func.count(TravelingTypeModel.id)).filter(
                    and_(
                        TravelingTypeModel.created_at >= start_date,
                        TravelingTypeModel.created_at <= end_date
                    )
                ).scalar() or 0
                
                # By traveling type
                by_type = session.query(
                    TravelingTypeModel.traveling_type,
                    func.count(TravelingTypeModel.id)
                ).filter(
                    and_(
                        TravelingTypeModel.created_at >= start_date,
                        TravelingTypeModel.created_at <= end_date
                    )
                ).group_by(TravelingTypeModel.traveling_type).all()
                
                
                # By source type
                by_source = session.query(
                    TravelingTypeModel.source_type,
                    func.count(TravelingTypeModel.id)
                ).filter(
                    and_(
                        TravelingTypeModel.created_at >= start_date,
                        TravelingTypeModel.created_at <= end_date
                    )
                ).group_by(TravelingTypeModel.source_type).all()
                
               
                
                return TravelingStatsDTO(
                    period_start=start_date,
                    period_end=end_date,
                    total_processed=total,
                    by_traveling_type={k.value: v for k, v in by_type if k is not None},
                    by_source_type={str(k): v for k, v in by_source},
            
                )
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            # Return empty stats on error
            return TravelingStatsDTO(
                period_start=start_date,
                period_end=end_date,
                total_processed=0,
                by_traveling_type={},
                by_source_type={},
            )
    
    # ==================== DELETE OPERATIONS ====================
    
    def delete(self, traveling_type_id: str) -> bool:
        """
        Delete traveling type by ID.
        
        Args:
            traveling_type_id: UUID of the traveling type
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            with self.get_session() as session:
                deleted = session.query(TravelingTypeModel).filter(
                    TravelingTypeModel.id == traveling_type_id
                ).delete()
                
                return deleted > 0
                
        except Exception as e:
            logger.error(f"Error deleting traveling type: {e}", exc_info=True)
            return False
    
    
    # ==================== HELPER METHODS ====================
    
    def _model_to_dto(self, model: TravelingTypeModel) -> TravelingTypeDTO:
        """Convert TravelingTypeModel to TravelingTypeDTO."""
        return TravelingTypeDTO(
            id=str(model.id),
            source_id=model.source_id,
            source_type=model.source_type,
            raw_text=model.raw_text,
            traveling_type=TravelingType(model.traveling_type) if model.traveling_type else TravelingType.OTHER,
        )
