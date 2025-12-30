"""
YouTube Batch Processor for Location Extraction.

Fetches YouTube comments that have been ingested but not yet processed by
location extraction, and processes them in batch to maximize API efficiency.

Usage:
    python -m projects.services.processing.tasks.location_extraction.batch.youtube_batch_processor
    
Environment Variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD - Database configuration
    LLM_PROVIDER, GOOGLE_API_KEY, LLM_MODEL_NAME - LLM configuration
    BATCH_SIZE - Number of records to process per batch (default: 50)
    MAX_RECORDS - Maximum total records to process (default: 500)
"""

import os
import sys
import logging
import argparse
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try module imports
try:
    from ..dto import UnifiedTextEvent, LocationExtractionResult
    from ..dto.persistence import PersistenceLocationDTO
    from ..pipelines.extraction_pipeline import ExtractionPipeline
    from ..dao.dao import LocationExtractionDAO
    from ..config.settings import DatabaseConfig
except ImportError:
    # Fallback for standalone execution
    from projects.services.processing.tasks.location_extraction.dto import UnifiedTextEvent, LocationExtractionResult
    from projects.services.processing.tasks.location_extraction.dto.persistence import PersistenceLocationDTO
    from projects.services.processing.tasks.location_extraction.pipelines.extraction_pipeline import ExtractionPipeline
    from projects.services.processing.tasks.location_extraction.dao.dao import LocationExtractionDAO
    from projects.services.processing.tasks.location_extraction.config.settings import DatabaseConfig


class YouTubeBatchProcessor:
    """
    Batch processor for YouTube comments location extraction.
    
    Joins youtube_comments with youtube_videos to get video titles,
    concatenates them for better location context, and processes
    only records not yet in location_extractions table.
    """
    
    SOURCE_TYPE = "youtube_comment"
    
    def __init__(
        self,
        batch_size: int = 50,
        max_records: int = 500,
        db_config: Optional[DatabaseConfig] = None
    ):
        """
        Initialize the batch processor.
        
        Args:
            batch_size: Number of records to process per batch
            max_records: Maximum total records to process in one run
            db_config: Database configuration (uses env vars if not provided)
        """
        self.batch_size = batch_size
        self.max_records = max_records
        
        # Initialize database configuration
        if db_config:
            self.db_config = db_config
        else:
            self.db_config = DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                user=os.getenv("DB_USER", "airflow"),
                password=os.getenv("DB_PASSWORD", "airflow"),
                database=os.getenv("DB_NAME", "airflow")
            )
        
        # Initialize database engine
        self.engine = create_engine(self.db_config.connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize extraction pipeline and DAO
        self.pipeline = ExtractionPipeline()
        self.dao = LocationExtractionDAO(self.db_config)  # auto_init=True by default
        
        # Ensure location_extractions table exists before any queries
        self._ensure_tables_exist()
        
        logger.info(f"YouTubeBatchProcessor initialized - batch_size={batch_size}, max_records={max_records}")
    
    def _ensure_tables_exist(self) -> None:
        """
        Ensure location_extractions table exists before running queries.
        This is called automatically during initialization.
        """
        try:
            # Import ORM models and create tables if not exist
            from ..orm.models import Base
            Base.metadata.create_all(self.engine, checkfirst=True)
            logger.debug("Ensured location_extractions table exists")
        except ImportError:
            from projects.services.processing.tasks.location_extraction.orm.models import Base
            Base.metadata.create_all(self.engine, checkfirst=True)
            logger.debug("Ensured location_extractions table exists")
        except Exception as e:
            logger.warning(f"Could not auto-create location_extractions table: {e}", exc_info=True)
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def fetch_unprocessed_comments(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Fetch YouTube comments that haven't been processed for location extraction.
        
        Joins youtube_comments with youtube_videos to get video titles.
        Excludes comments already in location_extractions table.
        
        Args:
            limit: Maximum number of records to fetch (defaults to max_records)
            
        Returns:
            List of comment dictionaries with video title included
        """
        limit = limit or self.max_records
        
        query = text("""
            SELECT 
                c.id AS comment_id,
                c.video_id,
                c.text AS comment_text,
                c.author_display_name,
                c.published_at AS comment_published_at,
                v.title AS video_title,
                v.channel_id
            FROM youtube_comments c
            INNER JOIN youtube_videos v ON c.video_id = v.id
            LEFT JOIN location_extractions le 
                ON c.id = le.source_id 
                AND le.source_type = :source_type
            WHERE le.id IS NULL
            ORDER BY c.published_at DESC
            LIMIT :limit
        """)
        
        try:
            with self.get_session() as session:
                result = session.execute(
                    query, 
                    {"source_type": self.SOURCE_TYPE, "limit": limit}
                )
                rows = result.fetchall()
                columns = result.keys()
                
                comments = [dict(zip(columns, row)) for row in rows]
                logger.info(f"Fetched {len(comments)} unprocessed YouTube comments")
                return comments
                
        except Exception as e:
            logger.error(f"Error fetching unprocessed comments: {e}", exc_info=True)
            return []
    
    def prepare_text_for_extraction(self, comment: Dict[str, Any]) -> str:
        """
        Prepare combined text for location extraction.
        
        Combines video title with comment text for better context.
        Format: "[Video: {video_title}] {comment_text}"
        
        Args:
            comment: Comment dictionary with video_title and comment_text
            
        Returns:
            Combined text string for extraction
        """
        video_title = comment.get("video_title", "").strip()
        comment_text = comment.get("comment_text", "").strip()
        
        if video_title and comment_text:
            return f"[Video: {video_title}] {comment_text}"
        elif comment_text:
            return comment_text
        else:
            return ""
    
    def process_comment(self, comment: Dict[str, Any]) -> Optional[PersistenceLocationDTO]:
        """
        Process a single comment for location extraction.
        
        Args:
            comment: Comment dictionary from fetch_unprocessed_comments
            
        Returns:
            PersistenceLocationDTO if successful, None otherwise
        """
        comment_id = comment.get("comment_id")
        
        try:
            # Prepare combined text
            combined_text = self.prepare_text_for_extraction(comment)
            
            if not combined_text:
                logger.debug(f"Skipping comment {comment_id}: empty text")
                return None
            
            # Create UnifiedTextEvent
            event = UnifiedTextEvent(
                source="youtube",
                source_type="comment",
                external_id=comment_id,
                text=combined_text,
                created_at=comment.get("comment_published_at"),
                metadata={
                    "video_id": comment.get("video_id"),
                    "video_title": comment.get("video_title"),
                    "channel_id": comment.get("channel_id"),
                    "author": comment.get("author_display_name"),
                    "original_comment": comment.get("comment_text")
                }
            )
            
            # Extract locations
            result = self.pipeline.process(event)
            
            # Create persistence DTO
            dto = PersistenceLocationDTO(
                source_id=comment_id,
                source_type=self.SOURCE_TYPE,
                raw_text=combined_text,
                extraction_result=result
            )
            
            return dto
            
        except Exception as e:
            logger.error(f"Error processing comment {comment_id}: {e}", exc_info=True)
            return None
    
    def process_batch(self, comments: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Process a batch of comments.
        
        Args:
            comments: List of comment dictionaries
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        for comment in comments:
            try:
                dto = self.process_comment(comment)
                
                if dto:
                    try:
                        saved = self.dao.save(dto)
                        if saved:
                            successful += 1
                            logger.debug(f"Saved extraction for comment {comment.get('comment_id')}")
                        else:
                            failed += 1
                            logger.warning(f"Failed to save extraction for comment {comment.get('comment_id')}")
                    except Exception as save_error:
                        failed += 1
                        logger.error(f"Exception saving comment {comment.get('comment_id')}: {save_error}", exc_info=True)
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                logger.error(f"Exception in process_batch for comment {comment.get('comment_id')}: {e}", exc_info=True)
        
        return successful, failed
    
    def run(self) -> Dict[str, Any]:
        """
        Run the batch processing.
        
        Returns:
            Dictionary with processing statistics
        """
        start_time = datetime.now(UTC)
        total_successful = 0
        total_failed = 0
        batches_processed = 0
        
        logger.info("Starting YouTube batch location extraction...")
        
        try:
            # Fetch all unprocessed comments
            all_comments = self.fetch_unprocessed_comments()
        except Exception as e:
            logger.error(f"Failed to fetch unprocessed comments: {e}", exc_info=True)
            raise
        
        if not all_comments:
            logger.info("No unprocessed comments found.")
            return {
                "status": "completed",
                "total_fetched": 0,
                "total_successful": 0,
                "total_failed": 0,
                "batches_processed": 0,
                "duration_seconds": 0
            }
        
        # Process in batches
        for i in range(0, len(all_comments), self.batch_size):
            batch = all_comments[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            logger.info(f"Processing batch {batch_num} ({len(batch)} comments)...")
            
            successful, failed = self.process_batch(batch)
            total_successful += successful
            total_failed += failed
            batches_processed += 1
            
            logger.info(
                f"Batch {batch_num} complete: {successful} successful, {failed} failed"
            )
        
        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()
        
        stats = {
            "status": "completed",
            "total_fetched": len(all_comments),
            "total_successful": total_successful,
            "total_failed": total_failed,
            "batches_processed": batches_processed,
            "duration_seconds": round(duration, 2),
            "records_per_second": round(len(all_comments) / duration, 2) if duration > 0 else 0
        }
        
        logger.info(f"Batch processing complete: {stats}")
        return stats


def main():
    """Main entry point for the batch processor."""
    parser = argparse.ArgumentParser(
        description="Process YouTube comments for location extraction in batch"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("BATCH_SIZE", "50")),
        help="Number of records per batch (default: 50)"
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=int(os.getenv("MAX_RECORDS", "500")),
        help="Maximum total records to process (default: 500)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    processor = YouTubeBatchProcessor(
        batch_size=args.batch_size,
        max_records=args.max_records
    )
    
    stats = processor.run()
    
    # Exit with error code if all records failed
    if stats["total_fetched"] > 0 and stats["total_successful"] == 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
