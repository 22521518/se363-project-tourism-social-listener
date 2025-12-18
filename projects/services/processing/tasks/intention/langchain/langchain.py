# intention_service.py
# LangChain service for intention extraction using Flan-T5

from typing import Dict, Any, Optional
import time
import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain.chains import LLMChain

import json
from typing import List
from ..dto import ModelIntentionDTO

from .prompts import (
    get_prompt,
    get_output_parser
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentionExtractionService:
    """Service for extracting intentions from text using Flan-T5 and LangChain."""
    
    def __init__(
        self, 
        model_name: str = "google/flan-t5-base", 
        device: int = -1,
        prompt_type: str = "batch"
    ):
        """
        Initialize the intention extraction service.
        
        Args:
            model_name: HuggingFace model identifier
            device: Device to run on (-1 for CPU, 0+ for GPU)
            prompt_type: Type of prompt to use ('default','batch', 'detailed', 'simple')
        """
        self.model_name = model_name
        self.device = device
        self.prompt_type = prompt_type
        
        logger.info(f"Loading model: {model_name}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Create pipeline
        self.pipe = pipeline(
            "text2text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_length=256,
            device=device
        )
        
        # Create LangChain LLM
        self.llm = HuggingFacePipeline(pipeline=self.pipe)
        
        # Get prompt template from prompts.py
        self.prompt_template = get_prompt(prompt_type)
        
        # Create chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        
        logger.info(f"Model loaded successfully with '{prompt_type}' prompt")
    
    
    def batch_extract_intentions(
    self,
    items: list[ModelIntentionDTO]
    ) -> list[Dict[str, Any]]:
        """
        Extract intentions from multiple texts in ONE model call.
        """
        if not items:
            return []

        # Convert DTOs → prompt input
        prompt_items = [
            item.to_prompt_dict()
            for item in items
        ]

        parser = get_output_parser()
        try:
            # ONE LLM CALL
            result = self.chain.run(
                 items=json.dumps(prompt_items, ensure_ascii=False),
            )

            parsed_results = json.loads(result)

           

            # Attach shared metadata
            for r in parsed_results:
                r["model_used"] = self.model_name
              

            logger.info(f"Batch processed {len(items)} items")
            return parsed_results

        except Exception as e:
            logger.error("Batch intention extraction failed", exc_info=True)

            # Fallback: return safe defaults (1-to-1)
            return [
                {
                    "intention_type": "other",
                    "sentiment": "neutral",
                    "model_used": self.model_name,
                }
                for _ in items
            ]
    

