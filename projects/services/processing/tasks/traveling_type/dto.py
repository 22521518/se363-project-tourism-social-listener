# Traveling Type Extraction - Data Transfer Objects (DTO)
# Immutable data structures for transferring traveling type analysis data between layers

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from .models import TravelingType





@dataclass(frozen=True)
class TravelingTypeDTO:
    """
    Data Transfer Object for extracted traveling type from text.
    
    Contains structured analysis of user traveling type 
    """

    source_id: str  # ID of the source content (comment_id, message_id, etc.)
    source_type: str  # Type of source ("youtube_comment", "message", etc.)
    raw_text: str  # Original text that was analyzed
    
    # Analysis results
    traveling_type: TravelingType
    
    id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "raw_text": self.raw_text,

            "traveling_type": self.traveling_type.value,
          
          
        }


@dataclass(frozen=True)
class TravelingStatsDTO:
    """
    Data Transfer Object for traveling type extraction statistics.
    
    Aggregated statistics for monitoring and reporting.
    """
    period_start: datetime
    period_end: datetime
    total_processed: int
    by_traveling_type: Dict[str, int]
   
    by_source_type: Dict[str, int]
  
  
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_processed": self.total_processed,
            "by_traveling_type": self.by_traveling_type,
            "by_source_type": self.by_source_type,
          
        }
        
@dataclass(frozen=True)
class ModelTravelingTypeDTO: 
    """
    Data Transfer Object for Model   .
    
    Aggregated statistics for monitoring and reporting.
    """
    text: str
    source_id: str
    source_type: str
    
    video_title: str = "Unknown"
    
    def to_prompt_dict(self) -> dict:
        """Convert to dict format expected by the batch prompt."""
        return {
            "text": self.text,
            "video_title": self.video_title
        }
    
# Helper functions for creating DTOs from raw data

def create_traveling_type_dto_from_model_output(
    source_id: str,
    source_type: str,
    raw_text: str,
    model_output: Dict[str, Any],
) -> TravelingTypeDTO:
    """
    Helper function to create IntentionDTO from model output.
    
    Args:
        source_id: ID of source content
        source_type: Type of source
        raw_text: Original text
        model_output: Structured output from the model
        model_name: Name of the model used
    
    Returns:
        IntentionDTO instance
    """
    import uuid
    
    # Parse intention type
    traveling_type_str = model_output.get("traveling_type", "other").lower()
    try:
        traveling_type = TravelingType(traveling_type_str)
    except ValueError:
        traveling_type = TravelingType.OTHER

    
   
    return TravelingTypeDTO(
        source_id=source_id,
        source_type=source_type,
        raw_text=raw_text,

        traveling_type=traveling_type,
        id=str(uuid.uuid4()),
     
    )