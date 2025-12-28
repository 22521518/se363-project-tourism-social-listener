"""
Location Extraction Pipeline.

Orchestrates the extraction process with fallback strategy.
"""

import logging
from typing import Any, Dict, Optional

try:
    from ..dto import UnifiedTextEvent, LocationExtractionResult
    from ..extractors import (
        LocationExtractor,
        LLMLocationExtractor,
        GazetteerLocationExtractor,
        RegexLocationExtractor
    )
    from ..validators import validate_schema, validate_all
    from ..config import settings
except ImportError:
    # Fallback for standalone execution (when module root is in sys.path)
    from dto import UnifiedTextEvent, LocationExtractionResult
    from extractors import (
        LocationExtractor,
        LLMLocationExtractor,
        GazetteerLocationExtractor,
        RegexLocationExtractor
    )
    from validators import validate_schema, validate_all
    from config import settings

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """
    Main extraction pipeline with fallback strategy.
    
    Fallback order: LLM → Gazetteer → Regex
    
    If a record is marked as validated=True, processing is skipped.
    """
    
    def __init__(
        self,
        llm_extractor: Optional[LocationExtractor] = None,
        gazetteer_extractor: Optional[LocationExtractor] = None,
        regex_extractor: Optional[LocationExtractor] = None
    ):
        """
        Initialize the extraction pipeline.
        
        Args:
            llm_extractor: Custom LLM extractor (defaults to LLMLocationExtractor)
            gazetteer_extractor: Custom gazetteer extractor (defaults to GazetteerLocationExtractor)
            regex_extractor: Custom regex extractor (defaults to RegexLocationExtractor)
        """
        self._llm_extractor = llm_extractor
        self._gazetteer_extractor = gazetteer_extractor or GazetteerLocationExtractor()
        self._regex_extractor = regex_extractor or RegexLocationExtractor()
        
        # Lazy initialization of LLM extractor
        self._llm_initialized = False
    
    def _get_llm_extractor(self) -> Optional[LocationExtractor]:
        """Get or initialize the LLM extractor."""
        if self._llm_extractor is not None:
            return self._llm_extractor
        
        if not self._llm_initialized:
            self._llm_initialized = True
            try:
                extractor = LLMLocationExtractor()
                if extractor.is_available():
                    self._llm_extractor = extractor
                    logger.info(f"LLM extractor initialized with provider: {settings.llm_provider}")
                else:
                    logger.warning("LLM extractor not available (API key not configured)")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM extractor: {e}")
        
        return self._llm_extractor
    
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
            return LocationExtractionResult.empty(extractor="llm", fallback_used=False)
        
        # Extract text
        text = event.text.strip() if event.text else ""
        
        if not text:
            logger.debug(f"Empty text for record: {event.external_id}")
            return LocationExtractionResult.empty(extractor="llm", fallback_used=False)
        
        # Try extraction with fallback strategy
        result = self._extract_with_fallback(text)
        
        # Validate result
        if not self._validate_result(result):
            logger.warning(f"Invalid extraction result for record: {event.external_id}")
            result = self._empty_result()
        
        return self._to_result(result)
    
    def _extract_with_fallback(self, text: str) -> Dict[str, Any]:
        """
        Extract locations with fallback strategy.
        
        Tries extractors in order: LLM → Gazetteer → Regex
        """
        # Try LLM extractor first
        llm_extractor = self._get_llm_extractor()
        if llm_extractor is not None:
            try:
                result = llm_extractor.extract(text)
                if result.get("locations") or result.get("primary_location"):
                    logger.debug("LLM extraction successful")
                    return result
                logger.debug("LLM extraction returned empty result, trying fallback")
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}")
        
        # Try gazetteer extractor
        try:
            result = self._gazetteer_extractor.extract(text)
            if result.get("locations") or result.get("primary_location"):
                logger.debug("Gazetteer extraction successful")
                return result
            logger.debug("Gazetteer extraction returned empty result, trying regex")
        except Exception as e:
            logger.warning(f"Gazetteer extraction failed: {e}")
        
        # Try regex extractor
        try:
            result = self._regex_extractor.extract(text)
            logger.debug("Regex extraction completed")
            return result
        except Exception as e:
            logger.warning(f"Regex extraction failed: {e}")
        
        # Return empty result
        return self._empty_result()
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate the extraction result."""
        # Schema validation
        is_valid_schema, schema_errors = validate_schema(result)
        if not is_valid_schema:
            logger.warning(f"Schema validation failed: {schema_errors}")
            return False
        
        # Confidence validation
        is_valid_confidence, confidence_errors = validate_all(result)
        if not is_valid_confidence:
            logger.warning(f"Confidence validation failed: {confidence_errors}")
            return False
        
        return True
    
    def _to_result(self, data: Dict[str, Any]) -> LocationExtractionResult:
        """Convert dictionary to LocationExtractionResult."""
        try:
            from ..dto import Location, PrimaryLocation, ExtractionMeta
        except ImportError:
            from dto import Location, PrimaryLocation, ExtractionMeta
        
        locations = [
            Location(
                name=loc["name"],
                type=loc["type"],
                confidence=loc["confidence"]
            )
            for loc in data.get("locations", [])
        ]
        
        primary = data.get("primary_location")
        primary_location = None
        if primary:
            primary_location = PrimaryLocation(
                name=primary["name"],
                confidence=primary["confidence"]
            )
        
        meta_data = data.get("meta", {"extractor": "llm", "fallback_used": False})
        meta = ExtractionMeta(
            extractor=meta_data.get("extractor", "llm"),
            fallback_used=meta_data.get("fallback_used", False)
        )
        
        return LocationExtractionResult(
            locations=locations,
            primary_location=primary_location,
            overall_score=data.get("overall_score", 0.0),
            meta=meta
        )
    
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
