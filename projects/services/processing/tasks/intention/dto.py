# Intention Extraction - Data Transfer Objects (DTO)
# Immutable data structures for transferring intention analysis data between layers

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class IntentionType(Enum):
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


class SentimentType(Enum):
    """Enumeration of sentiment types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"




@dataclass(frozen=True)
class IntentionDTO:
    """
    Data Transfer Object for extracted intention from text.
    
    Contains structured analysis of user intention including
    sentiment, category, priority, and key points.
    """
    id: str  # Unique identifier for this analysis
    source_id: str  # ID of the source content (comment_id, message_id, etc.)
    source_type: str  # Type of source ("youtube_comment", "message", etc.)
    raw_text: str  # Original text that was analyzed
    
    # Analysis results
    intention_type: IntentionType
    sentiment: SentimentType

    
    # Metadata
    processed_at: datetime = field(default_factory=datetime.utcnow)
    model_used: str = "flan-t5-base"
    
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "raw_text": self.raw_text,

            "intention_type": self.intention_type.value,
            "sentiment": self.sentiment.value,
           
        
            "processed_at": self.processed_at.isoformat(),
            "model_used": self.model_used,
          
          
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
    by_sentiment: Dict[str, int]
   
    by_source_type: Dict[str, int]
  
  
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_processed": self.total_processed,
            "by_intention_type": self.by_intention_type,
            "by_sentiment": self.by_sentiment,
            "by_source_type": self.by_source_type,
          
        }
@dataclass(frozen=True)
class ModelIntentionDTO: 
    """
    Data Transfer Object for Model   .
    
    Aggregated statistics for monitoring and reporting.
    """
    text: str
    video_title: str = "Unknown"

    def to_prompt_dict(self) -> dict:
        """Convert to dict format expected by the batch prompt."""
        return {
            "text": self.text,
            "video_title": self.video_title
        }
    
# Helper functions for creating DTOs from raw data

def create_intention_dto_from_model_output(
    source_id: str,
    source_type: str,
    raw_text: str,
    model_output: Dict[str, Any],
    model_name: str = "flan-t5-base",
  
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
    
    # Parse sentiment
    sentiment_str = model_output.get("sentiment", "neutral").lower()
    try:
        sentiment = SentimentType(sentiment_str)
    except ValueError:
        sentiment = SentimentType.NEUTRAL
    
   
    return IntentionDTO(
        id=str(uuid.uuid4()),
        source_id=source_id,
        source_type=source_type,
        raw_text=raw_text,

        intention_type=intention_type,
        sentiment=sentiment,
       
      
        model_used=model_name,
     
    )