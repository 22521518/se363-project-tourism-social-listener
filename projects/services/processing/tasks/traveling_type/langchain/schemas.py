# schemas.py
from typing import List
from pydantic import BaseModel, Field

class TravelingTypeResult(BaseModel):
    """Result for a single traveling type extraction."""
    traveling_type: str = Field(
        description="The classified traveling type",
        examples=["business", "leisure", "adventure", "backpacking", "luxury", 
                  "budget", "solo", "group", "family", "romantic", "other"]
    )

class BatchTravelingTypeResult(BaseModel):
    """Batch results for multiple traveling type extractions."""
    results: List[TravelingTypeResult] = Field(
        description="List of traveling type results, one per input item in the same order"
    )