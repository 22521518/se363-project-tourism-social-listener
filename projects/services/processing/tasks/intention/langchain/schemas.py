# schemas.py
from typing import List
from pydantic  import BaseModel, Field


class IntentionResult(BaseModel):
    intention_type: str = Field(
      description="The classified intention type",
        examples=["question", "feedback", "complaint", "suggestion", "praise", 
                  "request", "discussion", "spam", "other"]
    )


class BatchIntentionResult(BaseModel):
    results: List[IntentionResult]
