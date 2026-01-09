"""
DTO module for ASCA.
"""

from .unified_text_event import UnifiedTextEvent
from .asca_result import (
    AspectSentiment,
    ExtractionMeta,
    ASCAExtractionResult,
    CategoryType,
    SentimentType,
    ExtractorType
)
from .persistence import PersistenceASCADTO

__all__ = [
    "UnifiedTextEvent",
    "AspectSentiment",
    "ExtractionMeta",
    "ASCAExtractionResult",
    "CategoryType",
    "SentimentType",
    "ExtractorType",
    "PersistenceASCADTO"
]
