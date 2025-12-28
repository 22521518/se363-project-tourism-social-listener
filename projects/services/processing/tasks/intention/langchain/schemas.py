# schemas.py
from typing import List
from langchain_core.pydantic_v1 import BaseModel, Field


class IntentionResult(BaseModel):
    intention_type: str = Field(
        description="question, feedback, complaint, suggestion, praise, request, discussion, spam, or other"
    )


class BatchIntentionResult(BaseModel):
    results: List[IntentionResult]
