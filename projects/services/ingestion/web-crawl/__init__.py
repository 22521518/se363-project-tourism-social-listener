"""
Web Crawl Ingestion Module - Tourism-focused web crawler.

Library API:
    from projects.services.ingestion.webcrawl import WebCrawlService
    
    service = WebCrawlService()
    result = await service.crawl(url, content_type="blog")

Features:
    - crawl() / recrawl(): Crawl URLs with different content types
    - get_history() / list_history(): Query crawl history
    - get_result() / update_result(): Manage crawl results
    
Content Types: forum, review, blog, agency, auto
"""
from .core import WebCrawlService, CrawlService, DuplicateUrlError
from .config import WebCrawlConfig, GeminiConfig, KafkaConfig, DatabaseConfig

__all__ = [
    "WebCrawlService",
    "CrawlService",
    "DuplicateUrlError",
    "WebCrawlConfig",
    "GeminiConfig",
    "KafkaConfig",
    "DatabaseConfig",
]
