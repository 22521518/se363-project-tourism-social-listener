"""
NER-based Location Extractor using HuggingFace Transformers.

Uses the Davlan/xlm-roberta-base-ner-hrl model for multilingual Named Entity Recognition.
Supports automatic GPU/CPU fallback.
"""

import logging
from typing import Any, Dict, List, Optional

from .base import LocationExtractor

logger = logging.getLogger(__name__)


def _get_device() -> int:
    """
    Determine the best available device for inference.
    
    Returns:
        0 for GPU (CUDA), -1 for CPU
    """
    try:
        import torch
        if torch.cuda.is_available():
            logger.info(f"CUDA available. Using GPU: {torch.cuda.get_device_name(0)}")
            return 0  # Use GPU
        else:
            logger.info("CUDA not available. Using CPU.")
            return -1  # Use CPU
    except Exception as e:
        logger.warning(f"Error detecting device: {e}. Falling back to CPU.")
        return -1


class NERLocationExtractor(LocationExtractor):
    """
    NER-based location extractor using HuggingFace Transformers.
    
    Uses Davlan/xlm-roberta-base-ner-hrl for multilingual NER.
    Automatically uses GPU if available, otherwise falls back to CPU.
    
    Output format:
    {
        "locations": [
            {"word": "Hà Nội", "score": 0.999, "entity_group": "LOC", "start": 6, "end": 13},
            ...
        ]
    }
    """
    
    MODEL_NAME = "Davlan/xlm-roberta-base-ner-hrl"
    
    def __init__(self, model_name: str = None, device: Optional[int] = None):
        """
        Initialize the NER extractor.
        
        Args:
            model_name: HuggingFace model name (defaults to Davlan/xlm-roberta-base-ner-hrl)
            device: Device to use (-1 for CPU, 0+ for GPU). If None, auto-detect.
        """
        self._model_name = model_name or self.MODEL_NAME
        self._device = device  # Will be set during initialization if None
        self._pipeline = None
    
    @property
    def name(self) -> str:
        return "ner"
    
    def _initialize_pipeline(self):
        """Initialize the NER pipeline lazily with automatic device detection."""
        if self._pipeline is not None:
            return
        
        try:
            # Determine device if not specified
            if self._device is None:
                self._device = _get_device()
            
            from transformers import pipeline
            self._pipeline = pipeline(
                "ner",
                model=self._model_name,
                grouped_entities=True,
                device=self._device
            )
            device_name = "GPU" if self._device >= 0 else "CPU"
            logger.info(f"NER pipeline initialized with model: {self._model_name} on {device_name}")
        except Exception as e:
            logger.error(f"Failed to initialize NER pipeline: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if the NER extractor is available."""
        try:
            import transformers
            import torch
            return True
        except ImportError:
            return False
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract locations from text using NER.
        
        Args:
            text: Input text to extract locations from.
            
        Returns:
            Dictionary with locations list containing word, score, entity_group, start, end.
        """
        if not text or not text.strip():
            return self._empty_result()
        
        try:
            self._initialize_pipeline()
            
            # Run NER
            entities = self._pipeline(text)
            
            # Filter only LOC entities
            locations = []
            for entity in entities:
                if entity.get("entity_group") == "LOC":
                    locations.append({
                        "word": entity.get("word", ""),
                        "score": float(entity.get("score", 0.0)),
                        "entity_group": entity.get("entity_group", "LOC"),
                        "start": entity.get("start", 0),
                        "end": entity.get("end", 0)
                    })
            
            return {
                "locations": locations
            }
            
        except Exception as e:
            logger.error(f"NER extraction failed: {e}")
            raise
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return an empty but valid result."""
        return {
            "locations": []
        }
