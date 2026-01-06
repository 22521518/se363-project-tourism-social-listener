"""
Crawl Request DTO - Input schema for web crawling requests.
"""
from typing import Literal
from pydantic import BaseModel, HttpUrl, Field


class CrawlRequestDTO(BaseModel):
    """Input contract for crawling requests."""
    
    url: HttpUrl = Field(
        ...,
        description="The URL to crawl for tourism-related content"
    )
    content_type: Literal["forum", "review", "blog", "agency", "auto"] = Field(
        default="auto",
        description="Website archetype to guide extraction focus"
    )
    force_refresh: bool = Field(
        default=False,
        description="If True, re-crawl even if URL exists in database"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://www.tripadvisor.com/Hotel_Review-xxx",
                    "content_type": "review"
                },
                {
                    "url": "https://travel-blog.example.com/vietnam-guide",
                    "content_type": "blog"
                }
            ]
        }
    }
