# Intention Extraction - ORM Model
# SQLAlchemy model for intention analysis persistence

from datetime import UTC, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, Enum, 
    Index, create_engine
)
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum 

Base = declarative_base()

class IntentionType(str, enum.Enum):
    """Enumeration of possible intention types."""
    QUESTION = "question"
    FEEDBACK = "feedback"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    PRAISE = "praise"
    REQUEST = "request"
    DISCUSSION = "discussion"
    SPAM = "spam"
    OTHER = "other"
    
class IntentionModel(Base):
    """ORM model for intention extraction results."""
    __tablename__ = "intentions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source reference
    source_id = Column(String(255), nullable=False, index=True)  # Comment ID, message ID, etc.
    source_type = Column(String(50), nullable=False, default="youtube_comment")  # youtube_comment, message, tweet, etc.
    
    # Original content
    raw_text = Column(Text, nullable=False)
    
    # Analysis results
    intention_type = Column(
        Enum(IntentionType),
        nullable=True,
        index=True
    )  # question, feedback, complaint, suggestion, praise, request, discussion, spam, other
    
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
        Index('idx_intentions_source_unique', 'source_id', 'source_type', unique=True),
        Index('idx_intentions_type', 'intention_type',),

    )
    
    def __repr__(self) -> str:
        return f"<IntentionModel(id={self.id}, type={self.intention_type})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "source_id": self.source_id,
            "source_type": self.source_type,
            "raw_text": self.raw_text,
            "intention_type": self.intention_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
         
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntentionModel":
        """Create model instance from dictionary."""
        return cls(
            source_id=data.get("source_id"),
            source_type=data.get("source_type", "youtube_comment"),
            raw_text=data.get("raw_text"),
            intention_type=data.get("intention_type"),
          
        )


# ==================== DATABASE UTILITIES ====================

def create_intention_tables(engine):
    """Create intention tables in the database."""
    Base.metadata.create_all(engine)


def drop_intention_tables(engine):
    """Drop intention tables from the database. USE WITH CAUTION!"""
    Base.metadata.drop_all(engine)