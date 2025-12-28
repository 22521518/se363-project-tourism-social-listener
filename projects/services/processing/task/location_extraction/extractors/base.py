"""
Base Extractor Interface.

All location extractors must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class LocationExtractor(ABC):
    """
    Abstract base class for location extractors.
    
    All extractors (LLM, gazetteer, regex) must inherit from this class
    and implement the extract method.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the extractor name (e.g., 'llm', 'gazetteer', 'regex')."""
        pass
    
    @abstractmethod
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract locations from the given text.
        
        Args:
            text: The input text to extract locations from.
            
        Returns:
            A dictionary matching the location extraction schema:
            {
                "locations": [...],
                "primary_location": {...} | None,
                "overall_score": float,
                "meta": {
                    "extractor": str,
                    "fallback_used": bool
                }
            }
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if this extractor is available and properly configured.
        
        Override this method to add configuration checks.
        Returns True by default.
        """
        return True
