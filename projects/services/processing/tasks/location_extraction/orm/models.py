
# Location Extraction - ORM Model
# SQLAlchemy model for location extraction persistence (Simplified schema)

from datetime import UTC, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Float, DateTime, 
    Index, create_engine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

Base = declarative_base()

class LocationExtractionModel(Base):
    """ORM model for location extraction results (simplified)."""
    __tablename__ = "location_extractions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source reference
    source_id = Column(String(255), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, default="youtube_comment")
    
    # Original content
    raw_text = Column(Text, nullable=False)
    
    # NER Extraction results (JSONB for list of locations)
    # Each location: {word, score, entity_group, start, end}
    locations = Column(JSONB, nullable=False, default=list)
    
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# ==================== DATABASE UTILITIES ====================

def create_location_tables(engine):
    """Create location extraction tables in the database."""
    Base.metadata.create_all(engine)

def drop_location_tables(engine):
    """Drop location extraction tables from the database. USE WITH CAUTION!"""
    Base.metadata.drop_all(engine)
