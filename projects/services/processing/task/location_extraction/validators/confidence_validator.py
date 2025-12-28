"""
Confidence Validator for Location Extraction results.

Validates confidence values and primary location constraints.
"""

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ConfidenceValidator:
    """
    Validates confidence values and primary location constraints.
    """
    
    def __init__(self, min_confidence: float = 0.0, max_confidence: float = 1.0):
        """
        Initialize the confidence validator.
        
        Args:
            min_confidence: Minimum allowed confidence value.
            max_confidence: Maximum allowed confidence value.
        """
        self._min = min_confidence
        self._max = max_confidence
    
    def validate(self, result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate confidence values in an extraction result.
        
        Args:
            result: The extraction result to validate.
            
        Returns:
            A tuple of (is_valid, list of error messages).
        """
        errors: List[str] = []
        
        # Validate locations
        locations = result.get("locations", [])
        if not isinstance(locations, list):
            errors.append("locations must be a list")
        else:
            for i, loc in enumerate(locations):
                if not isinstance(loc, dict):
                    errors.append(f"locations[{i}] must be an object")
                    continue
                
                confidence = loc.get("confidence")
                if confidence is None:
                    errors.append(f"locations[{i}].confidence is required")
                elif not isinstance(confidence, (int, float)):
                    errors.append(f"locations[{i}].confidence must be a number")
                elif not (self._min <= confidence <= self._max):
                    errors.append(
                        f"locations[{i}].confidence ({confidence}) must be between "
                        f"{self._min} and {self._max}"
                    )
        
        # Validate primary_location
        primary = result.get("primary_location")
        if primary is not None:
            if not isinstance(primary, dict):
                errors.append("primary_location must be an object or null")
            else:
                confidence = primary.get("confidence")
                if confidence is None:
                    errors.append("primary_location.confidence is required")
                elif not isinstance(confidence, (int, float)):
                    errors.append("primary_location.confidence must be a number")
                elif not (self._min <= confidence <= self._max):
                    errors.append(
                        f"primary_location.confidence ({confidence}) must be between "
                        f"{self._min} and {self._max}"
                    )
        
        # Validate overall_score
        overall_score = result.get("overall_score")
        if overall_score is None:
            errors.append("overall_score is required")
        elif not isinstance(overall_score, (int, float)):
            errors.append("overall_score must be a number")
        elif not (self._min <= overall_score <= self._max):
            errors.append(
                f"overall_score ({overall_score}) must be between "
                f"{self._min} and {self._max}"
            )
        
        return len(errors) == 0, errors
    
    def validate_primary_in_locations(self, result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that primary_location exists in the locations list.
        
        Args:
            result: The extraction result to validate.
            
        Returns:
            A tuple of (is_valid, list of error messages).
        """
        errors: List[str] = []
        
        primary = result.get("primary_location")
        locations = result.get("locations", [])
        
        if primary is None:
            # No primary location is valid
            return True, errors
        
        if not isinstance(primary, dict):
            errors.append("primary_location must be an object")
            return False, errors
        
        primary_name = primary.get("name", "").lower()
        if not primary_name:
            errors.append("primary_location.name is required")
            return False, errors
        
        # Check if primary exists in locations
        location_names = [
            loc.get("name", "").lower() 
            for loc in locations 
            if isinstance(loc, dict)
        ]
        
        if primary_name not in location_names:
            errors.append(
                f"primary_location '{primary.get('name')}' must exist in locations list"
            )
        
        return len(errors) == 0, errors


def validate_confidence(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate confidence values.
    
    Args:
        result: The extraction result to validate.
        
    Returns:
        A tuple of (is_valid, list of error messages).
    """
    validator = ConfidenceValidator()
    return validator.validate(result)


def validate_primary_location(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate primary_location constraint.
    
    Args:
        result: The extraction result to validate.
        
    Returns:
        A tuple of (is_valid, list of error messages).
    """
    validator = ConfidenceValidator()
    return validator.validate_primary_in_locations(result)


def validate_all(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Run all confidence-related validations.
    
    Args:
        result: The extraction result to validate.
        
    Returns:
        A tuple of (is_valid, list of all error messages).
    """
    validator = ConfidenceValidator()
    
    all_errors: List[str] = []
    
    is_valid_confidence, confidence_errors = validator.validate(result)
    all_errors.extend(confidence_errors)
    
    is_valid_primary, primary_errors = validator.validate_primary_in_locations(result)
    all_errors.extend(primary_errors)
    
    return len(all_errors) == 0, all_errors
