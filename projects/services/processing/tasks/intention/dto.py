# Intention Extraction - Data Transfer Objects (DTO)
# Immutable data structures for transferring intention analysis data between layers

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from .models import IntentionType





@dataclass(frozen=True)
class IntentionDTO:
    """
    Data Transfer Object for extracted intention from text.
    
    Contains structured analysis of user intention including
    sentiment, category, priority, and key points.
    """

    source_id: str  # ID of the source content (comment_id, message_id, etc.)
    source_type: str  # Type of source ("youtube_comment", "message", etc.)
    raw_text: str  # Original text that was analyzed
    
    # Analysis results
    intention_type: IntentionType
    
    id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "raw_text": self.raw_text,

            "intention_type": self.intention_type.value,
          
          
        }


@dataclass(frozen=True)
class IntentionStatsDTO:
    """
    Data Transfer Object for intention extraction statistics.
    
    Aggregated statistics for monitoring and reporting.
    """
    period_start: datetime
    period_end: datetime
    total_processed: int
    by_intention_type: Dict[str, int]
   
    by_source_type: Dict[str, int]
  
  
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_processed": self.total_processed,
            "by_intention_type": self.by_intention_type,
            "by_source_type": self.by_source_type,
          
        }
        
@dataclass(frozen=True)
class ModelIntentionDTO: 
    """
    Data Transfer Object for Model   .
    
    Aggregated statistics for monitoring and reporting.
    """
    text: str
    source_id: str
    source_type: str
    
    
    def to_prompt_dict(self) -> dict:
        """Convert to dict format expected by the batch prompt."""
        return {
            "text": self.text,
        }
    
# Helper functions for creating DTOs from raw data

def create_intention_dto_from_model_output(
    source_id: str,
    source_type: str,
    raw_text: str,
    model_output: Dict[str, Any],
) -> IntentionDTO:
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
    intention_str = model_output.get("intention_type", "other").lower()
    try:
        intention_type = IntentionType(intention_str)
    except ValueError:
        intention_type = IntentionType.OTHER

    
   
    return IntentionDTO(
        source_id=source_id,
        source_type=source_type,
        raw_text=raw_text,

        intention_type=intention_type,
        id=str(uuid.uuid4()),
     
    )