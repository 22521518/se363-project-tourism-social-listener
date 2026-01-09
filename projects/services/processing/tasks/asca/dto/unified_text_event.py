"""
Unified Text Event DTO.

This is the canonical input format for the ASCA extraction pipeline.
All processing starts from this DTO.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class UnifiedTextEvent(BaseModel):
    """
    Canonical input DTO for ASCA extraction.
    
    This is the only accepted input format for the extraction pipeline.
    It abstracts away source-specific details from ingestion systems.
    """
    
    source: str = Field(
        ...,
        description="Source platform (e.g., 'youtube', 'facebook', 'twitter')"
    )
    
    source_type: str = Field(
        ...,
        description="Type of content (e.g., 'comment', 'post', 'review')"
    )
    
    external_id: str = Field(
        ...,
        description="Unique identifier from the source platform"
    )
    
    text: str = Field(
        ...,
        description="Raw text content to extract aspects from"
    )
    
    language: Optional[str] = Field(
        default=None,
        description="ISO language code (e.g., 'en', 'vi') if known"
    )
    
    created_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the content was created"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional source-specific metadata"
    )
    
    # Validation flag - if True, skip processing
    validated: bool = Field(
        default=False,
        description="Whether this record has been validated by a human"
    )
    
    validated_by: Optional[str] = Field(
        default=None,
        description="User ID of the validator, if validated"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "source": "youtube",
                "source_type": "comment",
                "external_id": "abc123",
                "text": "Phòng sạch sẽ, nhân viên thân thiện",
                "language": "vi",
                "created_at": "2024-01-15T10:30:00Z",
                "metadata": {"video_id": "v1"},
                "validated": False,
                "validated_by": None
            }
        }
