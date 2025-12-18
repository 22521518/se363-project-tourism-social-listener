# Intention Extraction - ORM Model
# SQLAlchemy model for intention analysis persistence

from datetime import UTC, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, 
    Index, create_engine
)
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

Base = declarative_base()


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
    intention_type = Column(String(50), nullable=True, index=True)  # question, feedback, complaint, suggestion, praise, request, discussion, spam, other
    sentiment = Column(String(50), nullable=True, index=True)  # positive, negative, neutral, mixed
    
    
    # Processing metadata
    processed_at = Column(DateTime, default=datetime.now(UTC), nullable=False, index=True)
    model_used = Column(String(100), nullable=True)  # Model name/version used for analysis
  
    
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now(UTC), nullable=False)
  
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_intentions_source_unique', 'source_id', 'source_type', unique=True),
        Index('idx_intentions_type_sentiment', 'intention_type', 'sentiment'),
        Index('idx_intentions_processed_at_desc', 'processed_at'),
    )
    
    def __repr__(self) -> str:
        return f"<IntentionModel(id={self.id}, type={self.intention_type}, sentiment={self.sentiment})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "source_id": self.source_id,
            "source_type": self.source_type,
            "raw_text": self.raw_text,
            "intention_type": self.intention_type,
            "sentiment": self.sentiment,
            
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "model_used": self.model_used,
      
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
            sentiment=data.get("sentiment"),
         
            model_used=data.get("model_used"),
          
        )


# ==================== DATABASE UTILITIES ====================

def create_intention_tables(engine):
    """Create intention tables in the database."""
    Base.metadata.create_all(engine)


def drop_intention_tables(engine):
    """Drop intention tables from the database. USE WITH CAUTION!"""
    Base.metadata.drop_all(engine)