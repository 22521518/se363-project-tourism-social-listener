# intention_service.py
# LangChain service for intention extraction using Flan-T5

from typing import Dict, Any, Optional
import logging
from langchain_openai import ChatOpenAI

import json
from typing import List
from ..dto import ModelTravelingTypeDTO

from .prompts import BATCH_PROMPT
from .schemas import BatchTravelingTypeResult
from ..config import ModelConfig

logger = logging.getLogger(__name__)


class TravelingTypeExtractionService:
    """Service for extracting traveling type from text using LangChain."""
    
    def __init__(self, model_config: ModelConfig):
        self.llm = ChatOpenAI(
            model=model_config.model_name,
            temperature=0,
            max_tokens=model_config.max_tokens,
            api_key=model_config.openai_api_key  # Pass API key from config
        ).with_structured_output(BatchTravelingTypeResult)

        self.chain = BATCH_PROMPT | self.llm

    def batch_extract_traveling_types(
        self,
        items: List[ModelTravelingTypeDTO]
    ) -> List[Dict[str, Any]]:

        if not items:
            return []

        prompt_items = [item.to_prompt_dict() for item in items]

        try:
            response: BatchTravelingTypeResult = self.chain.invoke(
                {"items": json.dumps(prompt_items, ensure_ascii=False)}
            )

            results = []
            for r in response.results:
                results.append({
                    "traveling_type": r.traveling_type,
                })

            logger.info(f"Batch processed {len(results)} items")
            return results

        except Exception:
            logger.exception("Batch traveling type extraction failed")

            return [
                {
                    "traveling_type": "other",
                }
                for _ in items
            ]
    

