"""
Persistence DTO for ASCA extractions.

Used for database operations and data transfer.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from .asca_result import ASCAExtractionResult


class PersistenceASCADTO(BaseModel):
    """
    DTO for persisting ASCA extraction results to database.
    
    Includes approval workflow fields.
    """
    
    id: Optional[str] = Field(
        default=None,
        description="Database record ID (UUID string)"
    )
    
    source_id: str = Field(
        ...,
        description="External source ID (e.g., YouTube comment ID)"
    )
    
    source_type: str = Field(
        ...,
        description="Type of source (e.g., 'youtube_comment')"
    )
    
    raw_text: str = Field(
        ...,
        description="Original text that was processed"
    )
    
    extraction_result: ASCAExtractionResult = Field(
        ...,
        description="ASCA extraction result"
    )
    
    # Approval workflow
    is_approved: bool = Field(
        default=False,
        description="Whether the extraction has been approved by human"
    )
    
    approved_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Human-corrected extraction result"
    )
    
    # Soft delete
    is_deleted: bool = Field(
        default=False,
        description="Whether this record has been soft-deleted"
    )

    class Config:
        extra = 'allow'
