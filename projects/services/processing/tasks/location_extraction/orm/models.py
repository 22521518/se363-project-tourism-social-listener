
# Location Extraction - ORM Model
# SQLAlchemy model for location extraction persistence

from datetime import UTC, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, Enum, 
    Index, create_engine, Boolean
)
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

Base = declarative_base()

class LocationExtractionModel(Base):
    """ORM model for location extraction results."""
    __tablename__ = "location_extractions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source reference
    source_id = Column(String(255), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, default="youtube_comment")
    
    # Original content
    raw_text = Column(Text, nullable=False)
    
    # LLM Extraction results (JSONB for complex structures)
    locations = Column(JSONB, nullable=False, default=list)
    primary_location = Column(JSONB, nullable=True)
    overall_score = Column(Float, nullable=False, default=0.0)
    meta = Column(JSONB, nullable=False, default=dict)
    
    # Human Approval fields
    is_approved = Column(Boolean, nullable=False, default=False, index=True)
    approved_result = Column(JSONB, nullable=True)  # Human-corrected extraction
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(255), nullable=True)
    
    # Soft Delete fields
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )
  
    # Indexes and constraints
    __table_args__ = (
        Index('idx_location_source_unique', 'source_id', 'source_type', unique=True),
        Index('idx_location_pending', 'is_approved', 'is_deleted'),
    )
    
    def __repr__(self) -> str:
        return f"<LocationExtractionModel(id={self.id}, source_id={self.source_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "source_id": self.source_id,
            "source_type": self.source_type,
            "raw_text": self.raw_text,
            "locations": self.locations,
            "primary_location": self.primary_location,
            "overall_score": self.overall_score,
            "meta": self.meta,
            "is_approved": self.is_approved,
            "approved_result": self.approved_result,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# ==================== DATABASE UTILITIES ====================

def create_location_tables(engine):
    """Create location extraction tables in the database."""
    Base.metadata.create_all(engine)

def drop_location_tables(engine):
    """Drop location extraction tables from the database. USE WITH CAUTION!"""
    Base.metadata.drop_all(engine)
