# intention_service.py
# LangChain service for intention extraction using Flan-T5

from typing import Dict, Any, Optional
import logging
from langchain_openai import ChatOpenAI

import json
from typing import List
from ..dto import ModelIntentionDTO

from .prompts import BATCH_PROMPT
from .schemas import BatchIntentionResult


logger = logging.getLogger(__name__)


class IntentionExtractionService:
    """Service for extracting intentions from text using LangChain."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        ).with_structured_output(BatchIntentionResult)

        self.chain = BATCH_PROMPT | self.llm

    def batch_extract_intentions(
        self,
        items: List[ModelIntentionDTO]
    ) -> List[Dict[str, Any]]:

        if not items:
            return []

        prompt_items = [item.to_prompt_dict() for item in items]

        try:
            response: BatchIntentionResult = self.chain.invoke(
                {"items": json.dumps(prompt_items, ensure_ascii=False)}
            )

            results = []
            for r in response.results:
                results.append({
                    "intention_type": r.intention_type,
                })

            logger.info(f"Batch processed {len(results)} items")
            return results

        except Exception:
            logger.exception("Batch intention extraction failed")

            return [
                {
                    "intention_type": "other",
                }
                for _ in items
            ]
    

