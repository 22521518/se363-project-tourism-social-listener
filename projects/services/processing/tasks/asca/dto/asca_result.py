"""
ASCA Extraction Result DTOs.

These DTOs define the output format for ASCA extraction.
Categories: LOCATION, PRICE, ACCOMMODATION, FOOD, SERVICE, AMBIENCE
Sentiments: positive, negative, neutral
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# Type definitions matching ASCA labels
CategoryType = Literal["LOCATION", "PRICE", "ACCOMMODATION", "FOOD", "SERVICE", "AMBIENCE"]
SentimentType = Literal["positive", "negative", "neutral"]
ExtractorType = Literal["asca", "manual"]


class AspectSentiment(BaseModel):
    """A single aspect-sentiment pair."""
    
    category: CategoryType = Field(
        ...,
        description="Aspect category"
    )
    
    sentiment: SentimentType = Field(
        ...,
        description="Sentiment for this aspect"
    )
    
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1"
    )

    class Config:
        extra = 'allow'
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is within valid range."""
        return max(0.0, min(1.0, v))
    
    @classmethod
    def from_tuple(cls, pair: tuple) -> "AspectSentiment":
        """Create from ASCA predictor output tuple (category, sentiment)."""
        return cls(category=pair[0], sentiment=pair[1], confidence=1.0)


class ExtractionMeta(BaseModel):
    """Metadata about the extraction process."""
    
    extractor: ExtractorType = Field(
        default="asca",
        description="Which extractor was used"
    )
    
    language: str = Field(
        default="vi",
        description="Language used for preprocessing"
    )
    
    model_version: Optional[str] = Field(
        default=None,
        description="Model version used for extraction"
    )

    class Config:
        extra = 'allow'


class ASCAExtractionResult(BaseModel):
    """
    Complete result of ASCA extraction.
    
    Maps to ASCA predictor output format:
    [('ACCOMMODATION', 'positive'), ('SERVICE', 'positive')]
    """
    
    aspects: List[AspectSentiment] = Field(
        default_factory=list,
        description="List of extracted aspect-sentiment pairs"
    )
    
    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence score for the extraction"
    )
    
    meta: ExtractionMeta = Field(
        default_factory=ExtractionMeta,
        description="Metadata about the extraction process"
    )
    
    class Config:
        extra = 'allow'

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump()
    
    @classmethod
    def empty(cls, extractor: ExtractorType = "asca", language: str = "vi") -> "ASCAExtractionResult":
        """Create an empty but valid result."""
        return cls(
            aspects=[],
            overall_score=0.0,
            meta=ExtractionMeta(extractor=extractor, language=language)
        )
    
    @classmethod
    def from_predictor_output(cls, predictions: List[tuple], language: str = "vi") -> "ASCAExtractionResult":
        """
        Create from ASCA predictor output.
        
        Args:
            predictions: List of (category, sentiment) tuples
            language: Language used for preprocessing
            
        Returns:
            ASCAExtractionResult
        """
        aspects = [AspectSentiment.from_tuple(p) for p in predictions]
        
        return cls(
            aspects=aspects,
            overall_score=1.0 if aspects else 0.0,
            meta=ExtractionMeta(extractor="asca", language=language)
        )
    
    @property
    def categories(self) -> List[str]:
        """Get list of categories found."""
        return [a.category for a in self.aspects]
    
    @property
    def sentiments(self) -> List[str]:
        """Get list of sentiments found."""
        return [a.sentiment for a in self.aspects]
    
    def get_sentiment_for_category(self, category: str) -> Optional[str]:
        """Get sentiment for a specific category."""
        for aspect in self.aspects:
            if aspect.category == category:
                return aspect.sentiment
        return None
