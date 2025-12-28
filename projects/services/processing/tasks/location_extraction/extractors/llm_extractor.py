"""
LLM-based Location Extractor using LangChain.

Supports Google Gemini and TogetherAI as LLM providers.
"""

import json
import logging
from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .base import LocationExtractor

try:
    from ..config import settings, LLMProvider
except ImportError:
    # Fallback for standalone execution (when module root is in sys.path)
    from config import settings, LLMProvider

logger = logging.getLogger(__name__)


# System prompt as defined in AGENTS.md
SYSTEM_PROMPT = """You are a geographic information extraction system.
You must extract real-world geographic locations mentioned in the text.
Respond ONLY with valid JSON. Do not include explanations."""

# User prompt template as defined in AGENTS.md
# NOTE: All JSON braces must be escaped ({{ and }}) except for template variables like {text}
USER_PROMPT_TEMPLATE = """{{{{
  "task": "location_extraction",
  "instructions": [
    "Identify all geographic locations mentioned in the text",
    "Resolve aliases and abbreviations if possible",
    "If a location is ambiguous and cannot be resolved from context, mark type as 'unknown' and reduce confidence",
    "Choose one primary location if the intent is clear",
    "If no location exists, return empty arrays"
  ],
  "text": "{text}",
  "output_schema": {{{{
    "locations": [
      {{{{
        "name": "string",
        "type": "country|city|state|province|landmark|unknown",
        "confidence": "float (0-1)"
      }}}}
    ],
    "primary_location": {{{{
      "name": "string",
      "confidence": "float (0-1)"
    }}}} | null,
    "overall_score": "float (0-1)"
  }}}}
}}}}

Text to analyze: {text}

Respond with ONLY the JSON output, no markdown formatting, no code blocks:"""


class LLMLocationExtractor(LocationExtractor):
    """
    LLM-based location extractor using LangChain.
    
    Supports multiple LLM providers:
    - Google Gemini (default, free tier available)
    - TogetherAI (free tier available)
    """
    
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        Initialize the LLM extractor.
        
        Args:
            provider: LLM provider to use (defaults to settings.llm_provider)
            api_key: API key (defaults to settings based on provider)
            model_name: Model name (defaults to settings.llm_model_name)
            temperature: Temperature setting (defaults to settings.llm_temperature)
        """
        self._provider = provider or settings.llm_provider
        self._api_key = api_key
        self._model_name = model_name or settings.llm_model_name
        self._temperature = temperature if temperature is not None else settings.llm_temperature
        self._llm = None
        self._chain = None
    
    @property
    def name(self) -> str:
        return "llm"
    
    def _get_api_key(self) -> str:
        """Get API key for the configured provider."""
        if self._api_key:
            return self._api_key
        return settings.get_api_key()
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider configuration."""
        if self._llm is not None:
            return
        
        api_key = self._get_api_key()
        
        if self._provider == LLMProvider.GOOGLE:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self._llm = ChatGoogleGenerativeAI(
                model=self._model_name,
                google_api_key=api_key,
                temperature=self._temperature,
                max_output_tokens=settings.llm_max_tokens
            )
        elif self._provider == LLMProvider.TOGETHERAI:
            from langchain_together import ChatTogether
            self._llm = ChatTogether(
                model=self._model_name,
                together_api_key=api_key,
                temperature=self._temperature,
                max_tokens=settings.llm_max_tokens
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self._provider}")
        
        # Build the chain
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT_TEMPLATE)
        ])
        
        self._chain = prompt | self._llm | StrOutputParser()
    
    def is_available(self) -> bool:
        """Check if the LLM extractor is properly configured."""
        try:
            self._get_api_key()
            return True
        except ValueError:
            return False
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract locations from text using LLM.
        
        Args:
            text: Input text to extract locations from.
            
        Returns:
            Extraction result dictionary matching the schema.
        """
        if not text or not text.strip():
            return self._empty_result()
        
        try:
            self._initialize_llm()
            
            # Invoke the chain
            response = self._chain.invoke({"text": text})
            
            # Parse the JSON response
            result = self._parse_response(response)
            
            # Add metadata
            result["meta"] = {
                "extractor": "llm",
                "fallback_used": False
            }
            
            return result
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            raise
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data."""
        # Clean up response - remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response}")
            return self._empty_result()
        
        # Validate and normalize the result
        return self._normalize_result(result)
    
    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate the extraction result."""
        # Ensure locations is a list
        locations = result.get("locations", [])
        if not isinstance(locations, list):
            locations = []
        
        # Normalize each location
        normalized_locations = []
        for loc in locations:
            if not isinstance(loc, dict):
                continue
            
            name = loc.get("name", "").strip()
            if not name:
                continue
            
            loc_type = loc.get("type", "unknown")
            valid_types = ["country", "city", "state", "province", "landmark", "unknown"]
            if loc_type not in valid_types:
                loc_type = "unknown"
            
            confidence = loc.get("confidence", 0.5)
            try:
                confidence = float(confidence)
                confidence = max(0.0, min(1.0, confidence))
            except (TypeError, ValueError):
                confidence = 0.5
            
            normalized_locations.append({
                "name": name,
                "type": loc_type,
                "confidence": confidence
            })
        
        # Handle primary_location
        primary = result.get("primary_location")
        normalized_primary = None
        if primary and isinstance(primary, dict):
            name = primary.get("name", "").strip()
            if name:
                confidence = primary.get("confidence", 0.8)
                try:
                    confidence = float(confidence)
                    confidence = max(0.0, min(1.0, confidence))
                except (TypeError, ValueError):
                    confidence = 0.8
                normalized_primary = {
                    "name": name,
                    "confidence": confidence
                }
        
        # Calculate overall score
        overall_score = result.get("overall_score", 0.0)
        try:
            overall_score = float(overall_score)
            overall_score = max(0.0, min(1.0, overall_score))
        except (TypeError, ValueError):
            # Calculate from locations if not provided
            if normalized_locations:
                overall_score = sum(loc["confidence"] for loc in normalized_locations) / len(normalized_locations)
            else:
                overall_score = 0.0
        
        return {
            "locations": normalized_locations,
            "primary_location": normalized_primary,
            "overall_score": overall_score
        }
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return an empty but valid result."""
        return {
            "locations": [],
            "primary_location": None,
            "overall_score": 0.0,
            "meta": {
                "extractor": "llm",
                "fallback_used": False
            }
        }
