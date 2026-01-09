"""
Pipelines module for ASCA.
"""

from .asca_pipeline import (
    ASCAExtractionPipeline,
    extract_aspects,
    extract_aspects_from_text
)

__all__ = [
    "ASCAExtractionPipeline",
    "extract_aspects",
    "extract_aspects_from_text"
]
