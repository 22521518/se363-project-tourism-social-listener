
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from .location_result import LocationExtractionResult

class PersistenceLocationDTO(BaseModel):
    """
    DTO for persisting location extraction results.
    Combines the extraction result with source metadata.
    """
    id: Optional[str] = Field(default=None, description="Database ID")
    source_id: str = Field(..., description="ID of the source content")
    source_type: str = Field(..., description="Type of source content")
    raw_text: str = Field(..., description="Original text content")
    
    extraction_result: LocationExtractionResult = Field(..., description="The extraction result")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
