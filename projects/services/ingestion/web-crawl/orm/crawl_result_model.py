"""
Crawl Result Model - Stores extracted content from crawls.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base


class CrawlResult(Base):
    """Model for storing crawl results."""
    
    __tablename__ = "crawl_result"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    crawl_history_id = Column(
        Integer,
        ForeignKey("crawl_history.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    
    # Content fields
    title = Column(String(512), nullable=True)
    information = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)
    
    # JSON fields for complex data
    reviews_json = Column(JSON, nullable=True, default=list)
    comments_json = Column(JSON, nullable=True, default=list)
    blog_sections_json = Column(JSON, nullable=True, default=list)
    agency_info_json = Column(JSON, nullable=True)
    
    # Metadata
    detected_sections = Column(JSON, nullable=True, default=list)
    crawl_strategy = Column(String(20), default="single")
    extraction_strategy = Column(String(20), default="llm")
    
    # Relationship back to history
    history = relationship("CrawlHistory", back_populates="result")
    
    def __repr__(self):
        return f"<CrawlResult(id={self.id}, title={self.title[:50] if self.title else 'N/A'})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DTO building."""
        return {
            "title": self.title,
            "information": self.information,
            "language": self.language,
            "reviews": self.reviews_json or [],
            "comments": self.comments_json or [],
            "blog_sections": self.blog_sections_json or [],
            "agency_info": self.agency_info_json,
            "detected_sections": self.detected_sections or [],
            "crawl_strategy": self.crawl_strategy,
            "extraction_strategy": self.extraction_strategy,
        }
