"""
Location Extraction Pipeline.

Simplified pipeline using NER extractor.
"""

import logging
from typing import Any, Dict, Optional

try:
    from ..dto import UnifiedTextEvent, LocationExtractionResult, Location
    from ..extractors import (
        LocationExtractor,
        NERLocationExtractor
    )
except ImportError:
    # Fallback for standalone execution (when module root is in sys.path)
    from dto import UnifiedTextEvent, LocationExtractionResult, Location
    from extractors import (
        LocationExtractor,
        NERLocationExtractor
    )

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """
    Simplified extraction pipeline using NER model.
    
    Uses Davlan/xlm-roberta-base-ner-hrl for location extraction.
    """
    
    def __init__(
        self,
        ner_extractor: Optional[LocationExtractor] = None
    ):
        """
        Initialize the extraction pipeline.
        
        Args:
            ner_extractor: Custom NER extractor (defaults to NERLocationExtractor)
        """
        self._ner_extractor = ner_extractor or NERLocationExtractor()
    
    def process(self, event: UnifiedTextEvent) -> LocationExtractionResult:
        """
        Process a UnifiedTextEvent and extract locations.
        
        Args:
            event: The input event to process.
            
        Returns:
            LocationExtractionResult with extracted locations.
        """
        # Check if record is already validated - skip processing
        if event.validated:
            logger.info(f"Skipping validated record: {event.external_id}")
            return LocationExtractionResult.empty()
        
        # Extract text
        text = event.text.strip() if event.text else ""
        
        if not text:
            logger.debug(f"Empty text for record: {event.external_id}")
            return LocationExtractionResult.empty()
        
        # Extract locations using NER
        try:
            result = self._ner_extractor.extract(text)
            return self._to_result(result)
        except Exception as e:
            logger.error(f"NER extraction failed for record {event.external_id}: {e}")
            return LocationExtractionResult.empty()
    
    def _to_result(self, data: Dict[str, Any]) -> LocationExtractionResult:
        """Convert dictionary to LocationExtractionResult."""
        locations = [
            Location(
                word=loc["word"],
                score=loc["score"],
                entity_group=loc.get("entity_group", "LOC"),
                start=loc.get("start", 0),
                end=loc.get("end", 0)
            )
            for loc in data.get("locations", [])
        ]
        
        return LocationExtractionResult(locations=locations)


def extract_locations(event: UnifiedTextEvent) -> LocationExtractionResult:
    """
    Convenience function to extract locations from an event.
    
    Args:
        event: The input event to process.
        
    Returns:
        LocationExtractionResult with extracted locations.
    """
    pipeline = ExtractionPipeline()
    return pipeline.process(event)


def extract_locations_from_text(text: str) -> LocationExtractionResult:
    """
    Convenience function to extract locations from raw text.
    
    Args:
        text: The text to extract locations from.
        
    Returns:
        LocationExtractionResult with extracted locations.
    """
    event = UnifiedTextEvent(
        source="direct",
        source_type="text",
        external_id="direct-input",
        text=text
    )
    return extract_locations(event)
