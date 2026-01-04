"""
Crawl History DAO - CRUD operations for CrawlHistory.
"""
from typing import Optional, List
from sqlalchemy.orm import Session

from orm import CrawlHistory, CrawlStatus


class CrawlHistoryDAO:
    """Data Access Object for CrawlHistory."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(
        self,
        request_id: str,
        url: str,
        content_type: str,
        status: CrawlStatus = CrawlStatus.PENDING,
    ) -> CrawlHistory:
        """Create a new crawl history record."""
        history = CrawlHistory(
            request_id=request_id,
            url=url,
            content_type=content_type,
            status=status,
        )
        self.session.add(history)
        self.session.commit()
        self.session.refresh(history)
        return history
    
    def get_by_id(self, history_id: int) -> Optional[CrawlHistory]:
        """Get history by ID."""
        return self.session.query(CrawlHistory).filter(
            CrawlHistory.id == history_id
        ).first()
    
    def get_by_request_id(self, request_id: str) -> Optional[CrawlHistory]:
        """Get history by request ID."""
        return self.session.query(CrawlHistory).filter(
            CrawlHistory.request_id == request_id
        ).first()
    
    def get_by_url(self, url: str) -> Optional[CrawlHistory]:
        """Get the most recent completed crawl history for a URL."""
        return self.session.query(CrawlHistory).filter(
            CrawlHistory.url == url,
            CrawlHistory.status == CrawlStatus.COMPLETED
        ).order_by(CrawlHistory.crawl_time.desc()).first()
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[CrawlHistory]:
        """List all crawl history records."""
        return self.session.query(CrawlHistory).order_by(
            CrawlHistory.crawl_time.desc()
        ).offset(offset).limit(limit).all()
    
    def update_status(
        self,
        history_id: int,
        status: CrawlStatus,
        error_message: Optional[str] = None,
    ) -> Optional[CrawlHistory]:
        """Update the status of a crawl history record."""
        history = self.get_by_id(history_id)
        if history:
            history.status = status
            if error_message:
                history.error_message = error_message
            self.session.commit()
            self.session.refresh(history)
        return history
    
    def delete(self, history_id: int) -> bool:
        """Delete a crawl history record."""
        history = self.get_by_id(history_id)
        if history:
            self.session.delete(history)
            self.session.commit()
            return True
        return False
