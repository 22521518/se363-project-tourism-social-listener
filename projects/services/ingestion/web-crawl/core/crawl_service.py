"""
Crawl Service - Orchestrates the web crawling process.

Integrates crawler, extraction router, and data persistence.
"""
import uuid
import logging
from typing import List, Optional, Union
from datetime import datetime

from dto import (
    CrawlRequestDTO, 
    CrawlResultDTO, 
    ContentDTO, 
    CrawlMetaDTO,
    ReviewDTO,
    CommentDTO,
    BlogSectionDTO,
    AgencyInfoDTO
)
from dao import CrawlHistoryDAO, CrawlResultDAO, JsonFileWriter
from orm import SessionLocal, CrawlStatus
from .crawler import TourismCrawler
from .extraction_router import get_extraction_config, detect_sections_from_content

logger = logging.getLogger(__name__)


class DuplicateUrlError(Exception):
    """Exception raised when a URL has already been crawled and force_refresh is False."""
    pass


class CrawlService:
    """Service to handle web crawling and data extraction."""
    
    def __init__(self):
        self.crawler = TourismCrawler()
        self.file_writer = JsonFileWriter()
    
    async def crawl(
        self, 
        request: Union[CrawlRequestDTO, str], 
        content_type: str = "auto", 
        force_refresh: bool = False
    ) -> CrawlResultDTO:
        """
        Crawl a URL and return structured data.
        
        Args:
            request: Either a CrawlRequestDTO or a URL string.
            content_type: Content type if request is a URL string.
            force_refresh: If True, re-crawl even if URL exists in database.
            
        Returns:
            CrawlResultDTO containing extracted data and metadata.
        """
        # Handle both DTO and raw params for backward compatibility
        if isinstance(request, CrawlRequestDTO):
            url = str(request.url)
            content_type = request.content_type
            force_refresh = request.force_refresh
        else:
            url = request
            
        logger.info(f"Starting crawl request for: {url} (type: {content_type}, force: {force_refresh})")
        
        request_id = str(uuid.uuid4())
        
        with SessionLocal() as session:
            history_dao = CrawlHistoryDAO(session)
            result_dao = CrawlResultDAO(session)
            
            # Check for existing completed crawl if force_refresh is False
            if not force_refresh:
                existing_history = history_dao.get_by_url(url)
                if existing_history:
                    logger.info(f"Found existing crawl for {url}, returning from cache.")
                    existing_result = result_dao.get_by_history_id(existing_history.id)
                    if existing_result:
                        return self._map_to_dto(existing_history, existing_result, from_cache=True)
            
            # Create a new history record
            history = history_dao.create(
                request_id=request_id,
                url=url,
                content_type=content_type,
                status=CrawlStatus.IN_PROGRESS
            )
            
            # Save history backup status - IN_PROGRESS
            self._save_history_backup(history)
            
            try:
                # Get extraction config
                extraction_config = get_extraction_config(content_type)
                
                # Perform the crawl
                extracted_data = await self.crawler.crawl(url, extraction_config)
                
                # Detect sections
                detected_sections = detect_sections_from_content(extracted_data)
                
                # Save result to file (JSON backup)
                self.file_writer.save_result(history.request_id, extracted_data)
                
                # Save result to database
                result = result_dao.create(
                    crawl_history_id=history.id,
                    title=extracted_data.get("title"),
                    information=extracted_data.get("information"),
                    language=extracted_data.get("language", "en"),
                    reviews_json=extracted_data.get("reviews", []),
                    comments_json=extracted_data.get("comments", []),
                    blog_sections_json=extracted_data.get("blog_sections", []),
                    agency_info_json=extracted_data.get("agency_info"),
                    detected_sections=detected_sections,
                    crawl_strategy=extraction_config.crawl_strategy,
                    extraction_strategy=extraction_config.extraction_strategy
                )
                
                # Update history status
                history_dao.update_status(history.id, CrawlStatus.COMPLETED)
                
                # Save history backup status - COMPLETED
                # We need to refresh/update the history object status for the file backup
                history.status = CrawlStatus.COMPLETED
                self._save_history_backup(history)
                
                logger.info(f"Successfully completed crawl for {url}")
                return self._map_to_dto(history, result, from_cache=False)
                
            except Exception as e:
                logger.error(f"Crawl failed for {url}: {e}")
                
                # Save full error to file
                self.file_writer.save_error(history.request_id, {"error": str(e), "url": url})
                
                # Truncate error message for DB to avoid StringDataRightTruncation
                error_msg = str(e)
                if len(error_msg) > 1000:
                    error_msg = error_msg[:1000] + "..."
                
                
                history_dao.update_status(history.id, CrawlStatus.FAILED, error_message=error_msg)
                
                # Save history backup status - FAILED
                history.status = CrawlStatus.FAILED
                history.error_message = str(e) # Save full error in history file too? Or truncated? 
                # Let's save the full error in the JSON file since it's a file
                self._save_history_backup(history)
                raise
    
    async def crawl_batch(self, requests: List[CrawlRequestDTO], batch_size: int = 3) -> List[CrawlResultDTO]:
        """
        Crawl multiple URLs in batches.
        
        Args:
            requests: List of crawl requests.
            batch_size: Number of URLs per batch.
            
        Returns:
            List of results matching the input requests.
        """
        results = []
        for req in requests:
            try:
                result = await self.crawl(req)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch crawl failed for {req.url}: {e}")
                results.append(self._create_empty_result(str(req.url), req.content_type))
        return results

    def _map_to_dto(self, history, result, from_cache: bool = False) -> CrawlResultDTO:
        """Map ORM models to DTO."""
        return CrawlResultDTO(
            request_id=history.request_id,
            url=history.url,
            content_type=history.content_type,
            from_cache=from_cache,
            meta=CrawlMetaDTO(
                crawl_time=history.crawl_time,
                language=result.language,
                crawl_strategy=result.crawl_strategy,
                extraction_strategy=result.extraction_strategy,
                detected_sections=result.detected_sections
            ),
            content=ContentDTO(
                title=result.title,
                information=result.information,
                reviews=[ReviewDTO(**r) if isinstance(r, dict) else r for r in result.reviews_json],
                comments=[CommentDTO(**c) if isinstance(c, dict) else c for c in result.comments_json],
                blog_sections=[BlogSectionDTO(**b) if isinstance(b, dict) else b for b in result.blog_sections_json],
                agency_info=AgencyInfoDTO(**result.agency_info_json) if result.agency_info_json else None
            )
        )

    def _create_empty_result(self, url: str, content_type: str) -> CrawlResultDTO:
        """Create an empty result shell for failed crawls."""
        return CrawlResultDTO(
            request_id="failed",
            url=url,
            content_type=content_type,
            from_cache=False,
            meta=CrawlMetaDTO(
                crawl_time=datetime.utcnow(),
                detected_sections=[]
            ),
            content=ContentDTO()
        )

    
    def _save_history_backup(self, history):
        """Helper to save history object to JSON file."""
        try:
            history_data = {
                "request_id": history.request_id,
                "url": history.url,
                "content_type": history.content_type,
                "crawl_time": history.crawl_time,
                "status": history.status.value if hasattr(history.status, 'value') else str(history.status),
                "error_message": getattr(history, "error_message", None)
            }
            self.file_writer.save_history(history.request_id, history_data)
        except Exception as e:
            logger.error(f"Failed to save history backup for {history.request_id}: {e}")

class WebCrawlService(CrawlService):
    """Alias for CrawlService to maintain backward compatibility with main.py."""
    pass
