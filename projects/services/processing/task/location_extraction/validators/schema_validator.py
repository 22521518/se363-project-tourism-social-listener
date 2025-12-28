"""
Schema Validator for Location Extraction results.

Validates extraction output against the JSON schema.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jsonschema import Draft7Validator, ValidationError

logger = logging.getLogger(__name__)


# Path to the schema file
SCHEMA_PATH = Path(__file__).parent.parent / "location_extraction.schema.json"


class SchemaValidator:
    """
    Validates location extraction results against the JSON schema.
    """
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize the schema validator.
        
        Args:
            schema_path: Path to the JSON schema file.
        """
        self._schema_path = schema_path or SCHEMA_PATH
        self._schema: Optional[Dict[str, Any]] = None
        self._validator: Optional[Draft7Validator] = None
    
    def _load_schema(self) -> None:
        """Load the JSON schema from file."""
        if self._schema is not None:
            return
        
        try:
            with open(self._schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
            self._validator = Draft7Validator(self._schema)
        except FileNotFoundError:
            logger.error(f"Schema file not found: {self._schema_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {e}")
            raise
    
    def validate(self, result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate an extraction result against the schema.
        
        Args:
            result: The extraction result to validate.
            
        Returns:
            A tuple of (is_valid, list of error messages).
        """
        self._load_schema()
        
        errors: List[str] = []
        
        if self._validator is None:
            errors.append("Schema validator not initialized")
            return False, errors
        
        for error in self._validator.iter_errors(result):
            error_path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
            errors.append(f"{error_path}: {error.message}")
        
        return len(errors) == 0, errors
    
    def is_valid(self, result: Dict[str, Any]) -> bool:
        """
        Check if an extraction result is valid.
        
        Args:
            result: The extraction result to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        is_valid, _ = self.validate(result)
        return is_valid


def validate_schema(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate an extraction result.
    
    Args:
        result: The extraction result to validate.
        
    Returns:
        A tuple of (is_valid, list of error messages).
    """
    validator = SchemaValidator()
    return validator.validate(result)
