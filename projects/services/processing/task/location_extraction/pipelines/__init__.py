"""
Pipelines module for Location Extraction.
"""

from .extraction_pipeline import (
    ExtractionPipeline,
    extract_locations,
    extract_locations_from_text
)

__all__ = [
    "ExtractionPipeline",
    "extract_locations",
    "extract_locations_from_text"
]
