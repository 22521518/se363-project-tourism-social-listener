"""
Crawl Result DTO - Output schema for crawling results.
"""
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ReviewDTO(BaseModel):
    """Review data extracted from the page."""
    author: Optional[str] = None
    text: str
    rating: Optional[float] = None


class CommentDTO(BaseModel):
    """Comment/discussion data extracted from forums."""
    author: Optional[str] = None
    text: str


class BlogSectionDTO(BaseModel):
    """Blog section with heading and content."""
    heading: str
    text: str


class AgencyInfoDTO(BaseModel):
    """Travel agency/tour information."""
    tour_name: Optional[str] = None
    price: Optional[str] = None
    duration: Optional[str] = None
    included_services: List[str] = Field(default_factory=list)


class ContentDTO(BaseModel):
    """Extracted content container."""
    title: Optional[str] = None
    information: Optional[str] = None
    reviews: List[ReviewDTO] = Field(default_factory=list)
    comments: List[CommentDTO] = Field(default_factory=list)
    blog_sections: List[BlogSectionDTO] = Field(default_factory=list)
    agency_info: Optional[AgencyInfoDTO] = None


class CrawlMetaDTO(BaseModel):
    """Metadata about the crawl operation."""
    crawl_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="ISO-8601 timestamp of when the crawl was performed"
    )
    language: Optional[str] = None
    crawl_strategy: Literal["single", "deep"] = "single"
    extraction_strategy: Literal["css", "llm"] = "llm"
    detected_sections: List[str] = Field(
        default_factory=list,
        description="List of detected content sections: review, comment, information, pricing, etc."
    )


class CrawlResultDTO(BaseModel):
    """Complete crawl result matching the output contract."""
    request_id: str = Field(..., description="Unique identifier for this crawl request")
    url: str = Field(..., description="The URL that was crawled")
    content_type: str = Field(..., description="The content type used for extraction")
    from_cache: bool = Field(
        default=False,
        description="True if result was returned from database cache"
    )
    meta: CrawlMetaDTO = Field(default_factory=CrawlMetaDTO)
    content: ContentDTO = Field(default_factory=ContentDTO)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    "url": "https://www.tripadvisor.com/Hotel_Review-xxx",
                    "content_type": "review",
                    "meta": {
                        "crawl_time": "2024-12-29T15:00:00Z",
                        "language": "en",
                        "crawl_strategy": "single",
                        "extraction_strategy": "llm",
                        "detected_sections": ["review", "information"]
                    },
                    "content": {
                        "title": "Amazing Beach Resort",
                        "information": "A luxury resort located in Da Nang...",
                        "reviews": [
                            {"author": "John D.", "text": "Great experience!", "rating": 4.5}
                        ],
                        "comments": [],
                        "blog_sections": [],
                        "agency_info": None
                    }
                }
            ]
        }
    }
