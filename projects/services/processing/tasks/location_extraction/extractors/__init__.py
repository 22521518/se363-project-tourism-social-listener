"""
Extractors module for Location Extraction.

Provides factory function and exports for all extractor implementations.
"""

from typing import Optional

from .base import LocationExtractor
from .llm_extractor import LLMLocationExtractor
from .gazetteer_extractor import GazetteerLocationExtractor
from .regex_extractor import RegexLocationExtractor
from .ner_extractor import NERLocationExtractor

try:
    from ..config import settings, LLMProvider
except ImportError:
    # Fallback for standalone execution
    from config import settings, LLMProvider


def get_extractor(
    extractor_type: str = "llm",
    provider: Optional[LLMProvider] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> LocationExtractor:
    """
    Factory function to get an extractor instance.
    
    Args:
        extractor_type: Type of extractor ("llm", "gazetteer", "regex")
        provider: LLM provider (for llm extractor only)
        api_key: API key (for llm extractor only)
        model_name: Model name (for llm extractor only)
        
    Returns:
        An instance of the requested extractor.
        
    Raises:
        ValueError: If extractor_type is not recognized.
    """
    if extractor_type == "ner":
        return NERLocationExtractor(model_name=model_name)
    elif extractor_type == "llm":
        return LLMLocationExtractor(
            provider=provider or settings.llm_provider,
            api_key=api_key,
            model_name=model_name
        )
    elif extractor_type == "gazetteer":
        return GazetteerLocationExtractor()
    elif extractor_type == "regex":
        return RegexLocationExtractor()
    else:
        raise ValueError(f"Unknown extractor type: {extractor_type}")


def get_default_extractor() -> LocationExtractor:
    """
    Get the default extractor based on configuration.
    
    Returns NER extractor as default for location extraction.
    """
    return NERLocationExtractor()


__all__ = [
    "LocationExtractor",
    "LLMLocationExtractor",
    "GazetteerLocationExtractor",
    "RegexLocationExtractor",
    "NERLocationExtractor",
    "get_extractor",
    "get_default_extractor"
]
