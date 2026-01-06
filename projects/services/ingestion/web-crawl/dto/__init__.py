"""DTO package for web crawl ingestion module."""
from .crawl_request_dto import CrawlRequestDTO
from .crawl_result_dto import (
    CrawlResultDTO,
    CrawlMetaDTO,
    ContentDTO,
    ReviewDTO,
    CommentDTO,
    BlogSectionDTO,
    AgencyInfoDTO,
)

__all__ = [
    "CrawlRequestDTO",
    "CrawlResultDTO",
    "CrawlMetaDTO",
    "ContentDTO",
    "ReviewDTO",
    "CommentDTO",
    "BlogSectionDTO",
    "AgencyInfoDTO",
]
