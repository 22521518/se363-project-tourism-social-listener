"""
ASCA Processing Module
======================
Aspect Category Sentiment Analysis for Airflow pipeline.

Categories: LOCATION, PRICE, ACCOMMODATION, FOOD, SERVICE, AMBIENCE
Sentiments: positive, negative, neutral
"""

# Core imports
from .config import settings, DatabaseConfig, KafkaConfig, ASCAConfig, detect_language
from .dto import (
    UnifiedTextEvent, 
    ASCAExtractionResult, 
    AspectSentiment, 
    PersistenceASCADTO
)

__version__ = "1.0.0"

__all__ = [
    # Config
    "settings",
    "DatabaseConfig",
    "KafkaConfig", 
    "ASCAConfig",
    "detect_language",
    # DTOs
    "UnifiedTextEvent",
    "ASCAExtractionResult",
    "AspectSentiment",
    "PersistenceASCADTO",
]
