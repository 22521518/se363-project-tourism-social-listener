"""Core package for web crawl ingestion module."""
from .extraction_router import get_extraction_config, ExtractionConfig, detect_sections_from_content
from .crawler import TourismCrawler
from .crawl_service import WebCrawlService, CrawlService, DuplicateUrlError

__all__ = [
    "get_extraction_config",
    "ExtractionConfig",
    "detect_sections_from_content",
    "TourismCrawler",
    "WebCrawlService",
    "CrawlService",
    "DuplicateUrlError",
]
