# schemas.py
from typing import List
from langchain_core.pydantic_v1 import BaseModel, Field


class TravelingTypeResult(BaseModel):
    traveling_type: str = Field(
        description="business, leisure, adventure, backpacking, luxury, budget, solo, group, family, romantic, or other"
    )


class BatchTravelingTypeResult(BaseModel):
    results: List[TravelingTypeResult]
