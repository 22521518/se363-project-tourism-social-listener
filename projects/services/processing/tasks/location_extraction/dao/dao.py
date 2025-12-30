
# Location Extraction - Data Access Objects (DAO)
# Database access layer for location extraction entities

from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import logging
import uuid as uuid_lib

from ..orm.models import Base, LocationExtractionModel
from ..dto.persistence import PersistenceLocationDTO
from ..dto.location_result import LocationExtractionResult
from ..config.settings import DatabaseConfig

logger = logging.getLogger(__name__)

class LocationExtractionDAO:
    """
    Data Access Object for Location Extraction entities.
    """
   
    def __init__(self, config: DatabaseConfig, auto_init: bool = True):
        """
        Initialize DAO with database configuration.
        
        Args:
            config: Database configuration
            auto_init: If True, automatically create tables if they don't exist
        """
        self.engine = create_engine(config.connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        if auto_init:
            self._ensure_tables_exist()
    
    def _ensure_tables_exist(self) -> None:
        """
        Check if required tables exist and create them if they don't.
        Uses SQLAlchemy's create_all which is idempotent (safe to call multiple times).
        """
        try:
            # create_all only creates tables that don't exist
            Base.metadata.create_all(self.engine, checkfirst=True)
            logger.info("Database tables ensured (created if not exist)")
        except Exception as e:
            logger.warning(f"Could not auto-init database tables: {e}")
    
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
        """Initialize database tables (explicit call)."""
        Base.metadata.create_all(self.engine)

    # ==================== CREATE OPERATIONS ====================

    def save(self, dto: PersistenceLocationDTO) -> Optional[PersistenceLocationDTO]:
        """Save a new location extraction record."""
        try:
            with self.get_session() as session:
                extraction_dict = dto.extraction_result.model_dump()
                
                model = LocationExtractionModel(
                    source_id=dto.source_id,
                    source_type=dto.source_type,
                    raw_text=dto.raw_text,
                    locations=extraction_dict.get('locations', []),
                    primary_location=extraction_dict.get('primary_location'),
                    overall_score=extraction_dict.get('overall_score', 0.0),
                    meta=extraction_dict.get('meta', {})
                )
                
                session.add(model)
                session.flush()
                return self._model_to_dto(model)
                
        except IntegrityError as e:
            logger.warning(f"Location extraction already exists for source_id={dto.source_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating location extraction: {e}", exc_info=True)
            return None

    # ==================== READ OPERATIONS ====================
    
    def get_all(self, limit: int = 100, offset: int = 0, include_deleted: bool = False) -> List[PersistenceLocationDTO]:
        """Get all records with pagination, excluding soft-deleted by default."""
        try:
            with self.get_session() as session:
                query = session.query(LocationExtractionModel)
                
                if not include_deleted:
                    query = query.filter(LocationExtractionModel.is_deleted == False)
                
                models = query.order_by(
                    LocationExtractionModel.created_at.desc()
                ).limit(limit).offset(offset).all()
                
                return [self._model_to_dto(m) for m in models]
        except Exception as e:
            logger.error(f"Error getting all records: {e}", exc_info=True)
            return []

    def get_pending(self, limit: int = 100) -> List[PersistenceLocationDTO]:
        """Get records not yet approved and not deleted."""
        try:
            with self.get_session() as session:
                models = session.query(LocationExtractionModel).filter(
                    and_(
                        LocationExtractionModel.is_approved == False,
                        LocationExtractionModel.is_deleted == False
                    )
                ).order_by(
                    LocationExtractionModel.created_at.desc()
                ).limit(limit).all()
                
                return [self._model_to_dto(m) for m in models]
        except Exception as e:
            logger.error(f"Error getting pending records: {e}", exc_info=True)
            return []

    def get_approved(self, limit: int = 100) -> List[PersistenceLocationDTO]:
        """Get approved records."""
        try:
            with self.get_session() as session:
                models = session.query(LocationExtractionModel).filter(
                    and_(
                        LocationExtractionModel.is_approved == True,
                        LocationExtractionModel.is_deleted == False
                    )
                ).order_by(
                    LocationExtractionModel.approved_at.desc()
                ).limit(limit).all()
                
                return [self._model_to_dto(m) for m in models]
        except Exception as e:
            logger.error(f"Error getting approved records: {e}", exc_info=True)
            return []

    def get_stats(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get statistics including approval counts."""
        if start_date is None:
            start_date = datetime.now(UTC) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(UTC)
            
        try:
            with self.get_session() as session:
                base_filter = and_(
                    LocationExtractionModel.created_at >= start_date,
                    LocationExtractionModel.created_at <= end_date,
                    LocationExtractionModel.is_deleted == False
                )
                
                # Total count
                total = session.query(func.count(LocationExtractionModel.id)).filter(
                    base_filter
                ).scalar() or 0
                
                # Approved count
                approved = session.query(func.count(LocationExtractionModel.id)).filter(
                    and_(base_filter, LocationExtractionModel.is_approved == True)
                ).scalar() or 0
                
                # Pending count
                pending = session.query(func.count(LocationExtractionModel.id)).filter(
                    and_(base_filter, LocationExtractionModel.is_approved == False)
                ).scalar() or 0
                
                return {
                    "total_processed": total,
                    "approved_count": approved,
                    "pending_count": pending,
                    "period_start": start_date,
                    "period_end": end_date
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            return {"total_processed": 0, "approved_count": 0, "pending_count": 0}

    # ==================== UPDATE OPERATIONS ====================

    def approve(self, record_id: str, approved_result: Dict[str, Any], approved_by: str = "human") -> bool:
        """Mark a record as approved with optional human-corrected result."""
        try:
            with self.get_session() as session:
                model = session.query(LocationExtractionModel).filter(
                    LocationExtractionModel.id == uuid_lib.UUID(record_id)
                ).first()
                
                if not model:
                    logger.warning(f"Record not found for approval: {record_id}")
                    return False
                
                model.is_approved = True
                model.approved_result = approved_result
                model.approved_at = datetime.now(UTC)
                model.approved_by = approved_by
                
                return True
        except Exception as e:
            logger.error(f"Error approving record: {e}", exc_info=True)
            return False

    def soft_delete(self, record_id: str) -> bool:
        """Mark a record as deleted (soft delete)."""
        try:
            with self.get_session() as session:
                model = session.query(LocationExtractionModel).filter(
                    LocationExtractionModel.id == uuid_lib.UUID(record_id)
                ).first()
                
                if not model:
                    logger.warning(f"Record not found for deletion: {record_id}")
                    return False
                
                model.is_deleted = True
                model.deleted_at = datetime.now(UTC)
                
                return True
        except Exception as e:
            logger.error(f"Error soft deleting record: {e}", exc_info=True)
            return False

    # ==================== HELPER METHODS ====================
    
    def _model_to_dto(self, model: LocationExtractionModel) -> PersistenceLocationDTO:
        """Convert ORM model to DTO."""
        extraction_result = LocationExtractionResult(
            locations=model.locations,
            primary_location=model.primary_location,
            overall_score=model.overall_score,
            meta=model.meta
        )
        
        return PersistenceLocationDTO(
            id=str(model.id),
            source_id=model.source_id,
            source_type=model.source_type,
            raw_text=model.raw_text,
            extraction_result=extraction_result,
            is_approved=model.is_approved,
            approved_result=model.approved_result,
            is_deleted=model.is_deleted
        )

