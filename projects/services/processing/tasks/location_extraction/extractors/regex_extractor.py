"""
Regex-based Location Extractor.

Uses regex patterns to extract location mentions.
This is the final fallback when both LLM and gazetteer fail.
"""

import re
import logging
from typing import Any, Dict, List, Set, Tuple

from .base import LocationExtractor

logger = logging.getLogger(__name__)


# Common location indicator patterns
LOCATION_PATTERNS: List[Tuple[str, str, float]] = [
    # Vietnamese patterns
    (r'\b(?:tại|ở|từ|đến|về|qua)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){0,3})', 'unknown', 0.6),
    (r'\b(?:thành phố|tp\.?|thành phố)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){0,2})', 'city', 0.7),
    (r'\b(?:tỉnh)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){0,2})', 'province', 0.7),
    (r'\b(?:quận|huyện)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){0,2})', 'city', 0.65),
    
    # English patterns
    (r'\b(?:in|at|from|to|near|visiting|visited)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})', 'unknown', 0.6),
    (r'\b(?:city of|town of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'city', 0.7),
    (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:city|town)', 'city', 0.7),
    (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:province|state)', 'state', 0.7),
    (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:country)', 'country', 0.7),
    
    # Capitalized words after location indicators
    (r'\b(?:moved to|living in|staying at|based in|located in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})', 'unknown', 0.65),
    
    # Landmark patterns
    (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+(?:beach|bay|island|mountain|river|lake|temple|palace|tower)', 'landmark', 0.7),
    (r'\b(?:beach|bay|island|mountain|temple|palace)\s+(?:of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'landmark', 0.7),
]

# Common false positives to filter out
FALSE_POSITIVES: Set[str] = {
    "the", "a", "an", "i", "you", "he", "she", "it", "we", "they",
    "this", "that", "these", "those", "my", "your", "his", "her",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "today", "yesterday", "tomorrow", "morning", "afternoon", "evening",
    "good", "great", "nice", "beautiful", "amazing", "wonderful",
    "love", "like", "want", "need", "have", "had", "been",
}


class RegexLocationExtractor(LocationExtractor):
    """
    Regex-based location extractor.
    
    Uses pattern matching to identify potential location mentions.
    This is the final fallback extractor.
    """
    
    def __init__(self):
        """Initialize the regex extractor."""
        self._patterns = LOCATION_PATTERNS
        self._false_positives = FALSE_POSITIVES
    
    @property
    def name(self) -> str:
        return "regex"
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract locations using regex patterns.
        
        Args:
            text: Input text to extract locations from.
            
        Returns:
            Extraction result dictionary.
        """
        if not text or not text.strip():
            return self._empty_result()
        
        locations: List[Dict[str, Any]] = []
        seen_names: Set[str] = set()
        
        for pattern, loc_type, confidence in self._patterns:
            matches = re.findall(pattern, text, re.UNICODE)
            
            for match in matches:
                # Clean up the match
                name = match.strip() if isinstance(match, str) else match[0].strip()
                
                # Filter out false positives
                if self._is_false_positive(name):
                    continue
                
                # Normalize the name
                name = self._normalize_name(name)
                
                if name and name.lower() not in seen_names:
                    locations.append({
                        "name": name,
                        "type": loc_type,
                        "confidence": confidence
                    })
                    seen_names.add(name.lower())
        
        # Determine primary location (highest confidence)
        primary_location = None
        if locations:
            locations.sort(key=lambda x: x["confidence"], reverse=True)
            primary_location = {
                "name": locations[0]["name"],
                "confidence": locations[0]["confidence"]
            }
        
        # Calculate overall score
        overall_score = 0.0
        if locations:
            overall_score = sum(loc["confidence"] for loc in locations) / len(locations)
        
        return {
            "locations": locations,
            "primary_location": primary_location,
            "overall_score": overall_score,
            "meta": {
                "extractor": "regex",
                "fallback_used": True
            }
        }
    
    def _is_false_positive(self, name: str) -> bool:
        """Check if the extracted name is a false positive."""
        # Check if it's a known false positive
        if name.lower() in self._false_positives:
            return True
        
        # Check if it's too short
        if len(name) < 2:
            return True
        
        # Check if it's all lowercase (except for known patterns)
        if name.islower() and len(name.split()) == 1:
            return True
        
        # Check if it contains only numbers
        if name.isdigit():
            return True
        
        return False
    
    def _normalize_name(self, name: str) -> str:
        """Normalize the location name."""
        # Remove extra whitespace
        name = " ".join(name.split())
        
        # Remove leading/trailing punctuation
        name = name.strip(".,!?;:'\"()")
        
        # Capitalize properly
        if name:
            words = name.split()
            normalized_words = []
            for word in words:
                if word.lower() in {"of", "the", "and", "in", "at", "on"}:
                    normalized_words.append(word.lower())
                else:
                    normalized_words.append(word.capitalize())
            name = " ".join(normalized_words)
        
        return name
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return an empty but valid result."""
        return {
            "locations": [],
            "primary_location": None,
            "overall_score": 0.0,
            "meta": {
                "extractor": "regex",
                "fallback_used": True
            }
        }
