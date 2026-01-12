
# Location Extraction - Data Access Objects (DAO)
# Database access layer for location extraction entities (Simplified)

from datetime import datetime, UTC
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import logging
import uuid as uuid_lib

from ..orm.models import Base, LocationExtractionModel
from ..dto.persistence import PersistenceLocationDTO
from ..dto.location_result import LocationExtractionResult, Location
from ..config.settings import DatabaseConfig

logger = logging.getLogger(__name__)

class LocationExtractionDAO:
    """
    Data Access Object for Location Extraction entities (Simplified).
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
        """
        try:
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
                # Convert locations to list of dicts
                locations_list = [loc.model_dump() for loc in dto.extraction_result.locations]
                
                model = LocationExtractionModel(
                    source_id=dto.source_id,
                    source_type=dto.source_type,
                    raw_text=dto.raw_text,
                    locations=locations_list
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
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[PersistenceLocationDTO]:
        """Get all records with pagination."""
        try:
            with self.get_session() as session:
                models = session.query(LocationExtractionModel).order_by(
                    LocationExtractionModel.created_at.desc()
                ).limit(limit).offset(offset).all()
                
                return [self._model_to_dto(m) for m in models]
        except Exception as e:
            logger.error(f"Error getting all records: {e}", exc_info=True)
            return []

    def get_by_id(self, record_id: str) -> Optional[PersistenceLocationDTO]:
        """Get a record by ID."""
        try:
            with self.get_session() as session:
                model = session.query(LocationExtractionModel).filter(
                    LocationExtractionModel.id == uuid_lib.UUID(record_id)
                ).first()
                
                if model:
                    return self._model_to_dto(model)
                return None
        except Exception as e:
            logger.error(f"Error getting record by id: {e}", exc_info=True)
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics."""
        try:
            with self.get_session() as session:
                total = session.query(func.count(LocationExtractionModel.id)).scalar() or 0
                
                return {
                    "total_processed": total
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            return {"total_processed": 0}

    # ==================== HELPER METHODS ====================
    
    def _model_to_dto(self, model: LocationExtractionModel) -> PersistenceLocationDTO:
        """Convert ORM model to DTO."""
        # Convert locations from JSONB to Location objects
        locations = []
        for loc_dict in (model.locations or []):
            locations.append(Location(
                word=loc_dict.get("word", ""),
                score=loc_dict.get("score", 0.0),
                entity_group=loc_dict.get("entity_group", "LOC"),
                start=loc_dict.get("start", 0),
                end=loc_dict.get("end", 0)
            ))
        
        extraction_result = LocationExtractionResult(locations=locations)
        
        return PersistenceLocationDTO(
            id=str(model.id),
            source_id=model.source_id,
            source_type=model.source_type,
            raw_text=model.raw_text,
            extraction_result=extraction_result
        )
