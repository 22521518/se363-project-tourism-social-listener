# YouTube Ingestion - ORM Models
# SQLAlchemy models for database persistence

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Integer, BigInteger, DateTime, 
    Boolean, ForeignKey, ARRAY, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class YouTubeChannelModel(Base):
    """ORM model for YouTube channels."""
    __tablename__ = "youtube_channels"
    
    id = Column(String(50), primary_key=True)  # YouTube channel ID
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    custom_url = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    subscriber_count = Column(BigInteger, default=0)
    video_count = Column(Integer, default=0)
    view_count = Column(BigInteger, default=0)
    country = Column(String(10), nullable=True)
    
    # Tracking fields
    is_tracked = Column(Boolean, default=False)
    last_checked = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_payload = Column(JSONB, nullable=True)
    
    # Relationships
    videos = relationship("YouTubeVideoModel", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<YouTubeChannel(id={self.id}, title={self.title})>"


class YouTubeVideoModel(Base):
    """ORM model for YouTube videos."""
    __tablename__ = "youtube_videos"
    
    id = Column(String(50), primary_key=True)  # YouTube video ID
    channel_id = Column(String(50), ForeignKey("youtube_channels.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    view_count = Column(BigInteger, default=0)
    like_count = Column(BigInteger, default=0)
    comment_count = Column(Integer, default=0)
    duration = Column(String(50), nullable=True)
    tags = Column(ARRAY(String), default=[])
    category_id = Column(String(10), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_payload = Column(JSONB, nullable=True)
    
    # Relationships
    channel = relationship("YouTubeChannelModel", back_populates="videos")
    comments = relationship("YouTubeCommentModel", back_populates="video", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<YouTubeVideo(id={self.id}, title={self.title})>"


class YouTubeCommentModel(Base):
    """ORM model for YouTube comments."""
    __tablename__ = "youtube_comments"
    
    id = Column(String(100), primary_key=True)  # YouTube comment ID
    video_id = Column(String(50), ForeignKey("youtube_videos.id"), nullable=False)
    author_display_name = Column(String(255), nullable=False)
    author_channel_id = Column(String(50), nullable=True)
    text = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    published_at = Column(DateTime, nullable=False)
    updated_at_youtube = Column(DateTime, nullable=False)  # YouTube's update timestamp
    parent_id = Column(String(100), nullable=True)  # For replies
    reply_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_payload = Column(JSONB, nullable=True)
    
    # Relationships
    video = relationship("YouTubeVideoModel", back_populates="comments")
    
    def __repr__(self) -> str:
        return f"<YouTubeComment(id={self.id}, author={self.author_display_name})>"


class TrackedChannelModel(Base):
    """ORM model for tracking channel ingestion state."""
    __tablename__ = "youtube_tracked_channels"
    
    channel_id = Column(String(50), ForeignKey("youtube_channels.id"), primary_key=True)
    last_checked = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_video_published = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<TrackedChannel(channel_id={self.channel_id}, active={self.is_active})>"


def create_tables(connection_string: str) -> None:
    """Create all tables in the database."""
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)


def drop_tables(connection_string: str) -> None:
    """Drop all tables from the database. USE WITH CAUTION."""
    engine = create_engine(connection_string)
    Base.metadata.drop_all(engine)
