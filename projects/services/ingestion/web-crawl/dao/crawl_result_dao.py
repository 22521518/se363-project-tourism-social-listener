"""
Crawl Result DAO - CRUD operations for CrawlResult.
"""
from typing import Optional, List
from sqlalchemy.orm import Session

from ..orm import CrawlResult


class CrawlResultDAO:
    """Data Access Object for CrawlResult."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(
        self,
        crawl_history_id: int,
        title: Optional[str] = None,
        information: Optional[str] = None,
        language: Optional[str] = None,
        reviews_json: Optional[list] = None,
        comments_json: Optional[list] = None,
        blog_sections_json: Optional[list] = None,
        agency_info_json: Optional[dict] = None,
        detected_sections: Optional[list] = None,
        crawl_strategy: str = "single",
        extraction_strategy: str = "llm",
    ) -> CrawlResult:
        """Create a new crawl result record."""
        result = CrawlResult(
            crawl_history_id=crawl_history_id,
            title=title,
            information=information,
            language=language,
            reviews_json=reviews_json or [],
            comments_json=comments_json or [],
            blog_sections_json=blog_sections_json or [],
            agency_info_json=agency_info_json,
            detected_sections=detected_sections or [],
            crawl_strategy=crawl_strategy,
            extraction_strategy=extraction_strategy,
        )
        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)
        return result
    
    def get_by_id(self, result_id: int) -> Optional[CrawlResult]:
        """Get result by ID."""
        return self.session.query(CrawlResult).filter(
            CrawlResult.id == result_id
        ).first()
    
    def get_by_history_id(self, crawl_history_id: int) -> Optional[CrawlResult]:
        """Get result by crawl history ID."""
        return self.session.query(CrawlResult).filter(
            CrawlResult.crawl_history_id == crawl_history_id
        ).first()
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[CrawlResult]:
        """List all crawl results."""
        return self.session.query(CrawlResult).offset(offset).limit(limit).all()
    
    def update(
        self,
        result_id: int,
        **kwargs,
    ) -> Optional[CrawlResult]:
        """Update a crawl result record."""
        result = self.get_by_id(result_id)
        if result:
            for key, value in kwargs.items():
                if hasattr(result, key):
                    setattr(result, key, value)
            self.session.commit()
            self.session.refresh(result)
        return result
    
    def delete(self, result_id: int) -> bool:
        """Delete a crawl result record."""
        result = self.get_by_id(result_id)
        if result:
            self.session.delete(result)
            self.session.commit()
            return True
        return False
