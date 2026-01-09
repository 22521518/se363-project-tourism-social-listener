"""
Location Extraction Result DTOs.

Simplified DTOs for NER-based location extraction using Davlan/xlm-roberta-base-ner-hrl.
"""

from typing import List
from pydantic import BaseModel, Field, field_validator


class Location(BaseModel):
    """A single extracted location from NER."""
    
    word: str = Field(
        ...,
        description="The extracted location text"
    )
    
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1"
    )
    
    entity_group: str = Field(
        default="LOC",
        description="Entity group type (always LOC for locations)"
    )
    
    start: int = Field(
        default=0,
        description="Start character position in original text"
    )
    
    end: int = Field(
        default=0,
        description="End character position in original text"
    )

    class Config:
        extra = 'allow'
    
    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Ensure score is within valid range."""
        return max(0.0, min(1.0, v))


class LocationExtractionResult(BaseModel):
    """
    Complete result of location extraction.
    
    Simple structure containing only a list of extracted locations.
    """
    
    locations: List[Location] = Field(
        default_factory=list,
        description="List of extracted locations"
    )
    
    class Config:
        extra = 'allow'

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump()
    
    @classmethod
    def empty(cls) -> "LocationExtractionResult":
        """Create an empty but valid result."""
        return cls(locations=[])
    
    @classmethod
    def from_ner_output(cls, ner_output: List[dict]) -> "LocationExtractionResult":
        """
        Create from NER pipeline output.
        
        Args:
            ner_output: List of entity dictionaries from transformers pipeline
            
        Returns:
            LocationExtractionResult with filtered LOC entities
        """
        locations = []
        for entity in ner_output:
            if entity.get("entity_group") == "LOC":
                locations.append(Location(
                    word=entity.get("word", ""),
                    score=float(entity.get("score", 0.0)),
                    entity_group=entity.get("entity_group", "LOC"),
                    start=entity.get("start", 0),
                    end=entity.get("end", 0)
                ))
        return cls(locations=locations)
