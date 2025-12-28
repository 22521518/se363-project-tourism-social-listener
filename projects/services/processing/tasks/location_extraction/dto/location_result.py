"""
Location Extraction Result DTOs.

These DTOs define the output format for location extraction,
matching the schema defined in location_extraction.schema.json.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


LocationType = Literal["country", "city", "state", "province", "landmark", "unknown"]
ExtractorType = Literal["llm", "gazetteer", "regex"]


class Location(BaseModel):
    """A single extracted location."""
    
    name: str = Field(
        ...,
        description="Name of the location"
    )
    
    type: LocationType = Field(
        ...,
        description="Type of location"
    )
    
    confidence: float = Field(
        ...,
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


class PrimaryLocation(BaseModel):
    """The primary/main location identified in the text."""
    
    name: str = Field(
        ...,
        description="Name of the primary location"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the primary location"
    )


    class Config:
        extra = 'allow'


class ExtractionMeta(BaseModel):
    """Metadata about the extraction process."""
    
    extractor: ExtractorType = Field(
        ...,
        description="Which extractor was used"
    )
    
    fallback_used: bool = Field(
        default=False,
        description="Whether a fallback extractor was used"
    )


    class Config:
        extra = 'allow'


class LocationExtractionResult(BaseModel):
    """
    Complete result of location extraction.
    
    This matches the schema defined in location_extraction.schema.json.
    """
    
    locations: List[Location] = Field(
        default_factory=list,
        description="List of extracted locations"
    )
    
    primary_location: Optional[PrimaryLocation] = Field(
        default=None,
        description="The primary location, if identified"
    )
    
    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence score for the extraction"
    )
    
    meta: ExtractionMeta = Field(
        ...,
        description="Metadata about the extraction process"
    )
    
    class Config:
        extra = 'allow'

    def to_dict(self) -> dict:
        """Convert to dictionary matching the JSON schema."""
        return self.model_dump()
    
    @classmethod
    def empty(cls, extractor: ExtractorType = "llm", fallback_used: bool = False) -> "LocationExtractionResult":
        """Create an empty but valid result."""
        return cls(
            locations=[],
            primary_location=None,
            overall_score=0.0,
            meta=ExtractionMeta(extractor=extractor, fallback_used=fallback_used)
        )
    
    def validate_primary_location(self) -> bool:
        """
        Validate that primary_location exists in locations list.
        
        Returns True if valid (primary is None or exists in locations).
        """
        if self.primary_location is None:
            return True
        
        location_names = [loc.name.lower() for loc in self.locations]
        return self.primary_location.name.lower() in location_names
