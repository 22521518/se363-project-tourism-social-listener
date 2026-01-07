"""
Crawl History Model - Tracks crawl operations.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base


class CrawlStatus(enum.Enum):
    """Status of a crawl operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlHistory(Base):
    """Model for tracking crawl operations."""
    
    __tablename__ = "crawl_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(36), unique=True, nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    content_type = Column(String(50), nullable=False)
    crawl_time = Column(DateTime, default=datetime.utcnow)
    status = Column(
        Enum(CrawlStatus),
        default=CrawlStatus.PENDING,
        nullable=False
    )
    error_message = Column(String(1024), nullable=True)
    
    # Relationship to result
    result = relationship("CrawlResult", back_populates="history", uselist=False)
    
    def __repr__(self):
        return f"<CrawlHistory(id={self.id}, request_id={self.request_id}, status={self.status.value})>"
