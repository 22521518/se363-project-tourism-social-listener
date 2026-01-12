"""
Batch Processor for ASCA.

Fetches unprocessed records from database and processes them in batches.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from pathlib import Path

# Setup path for imports
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load .env from root
root_env_path = project_root / ".env"
if root_env_path.exists():
    load_dotenv(root_env_path)
else:
    load_dotenv()

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
    from projects.services.processing.tasks.asca.dto import UnifiedTextEvent, ASCAExtractionResult
    from projects.services.processing.tasks.asca.dto.persistence import PersistenceASCADTO
    from projects.services.processing.tasks.asca.pipelines.asca_pipeline import ASCAExtractionPipeline
    from projects.services.processing.tasks.asca.dao.dao import ASCAExtractionDAO
    from projects.services.processing.tasks.asca.config.settings import DatabaseConfig, settings
except ImportError:
    from projects.services.processing.tasks.asca.dto import UnifiedTextEvent, ASCAExtractionResult
    from projects.services.processing.tasks.asca.dto.persistence import PersistenceASCADTO
    from projects.services.processing.tasks.asca.pipelines.asca_pipeline import ASCAExtractionPipeline
    from projects.services.processing.tasks.asca.dao.dao import ASCAExtractionDAO
    from projects.services.processing.tasks.asca.config.settings import DatabaseConfig, settings


class BatchProcessor:
    """
    Batch processor for ASCA extraction from database records.
    
    Fetches records from source tables (e.g., youtube_comments),
    processes them with ASCA pipeline, and saves results.
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
        self.db_config = db_config or DatabaseConfig.from_env()
        
        # Initialize database engine
        self.engine = create_engine(self.db_config.connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize extraction pipeline and DAO
        self.pipeline = ASCAExtractionPipeline()
        self.dao = ASCAExtractionDAO(self.db_config)
        
        logger.info(f"BatchProcessor initialized - batch_size={batch_size}, max_records={max_records}")
    
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
        Fetch YouTube comments that haven't been processed for ASCA extraction.
        
        Args:
            limit: Maximum number of records to fetch
            
        Returns:
            List of comment dictionaries
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
            LEFT JOIN asca_extractions ae 
                ON c.id = ae.source_id 
                AND ae.source_type = :source_type
            WHERE ae.id IS NULL
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
                logger.info(f"Fetched {len(comments)} unprocessed comments")
                return comments
                
        except Exception as e:
            logger.error(f"Error fetching comments: {e}", exc_info=True)
            return []
    
    def process_comment(self, comment: Dict[str, Any]) -> Optional[PersistenceASCADTO]:
        """
        Process a single comment for ASCA extraction.
        
        Args:
            comment: Comment dictionary from fetch_unprocessed_comments
            
        Returns:
            PersistenceASCADTO if successful, None otherwise
        """
        comment_id = comment.get("comment_id")
        
        try:
            comment_text = comment.get("comment_text", "").strip()
            
            if not comment_text:
                logger.debug(f"Skipping comment {comment_id}: empty text")
                return None
            
            # Create UnifiedTextEvent
            event = UnifiedTextEvent(
                source="youtube",
                source_type="comment",
                external_id=comment_id,
                text=comment_text,
                created_at=comment.get("comment_published_at"),
                metadata={
                    "video_id": comment.get("video_id"),
                    "video_title": comment.get("video_title"),
                    "channel_id": comment.get("channel_id"),
                    "author": comment.get("author_display_name")
                }
            )
            
            # Extract aspects
            result = self.pipeline.process(event)
            
            # Create persistence DTO
            dto = PersistenceASCADTO(
                source_id=comment_id,
                source_type=self.SOURCE_TYPE,
                raw_text=comment_text,
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
                    saved = self.dao.save(dto)
                    if saved:
                        successful += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error in batch: {e}", exc_info=True)
        
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
        
        logger.info("Starting ASCA batch extraction...")
        
        try:
            all_comments = self.fetch_unprocessed_comments()
        except Exception as e:
            logger.error(f"Failed to fetch comments: {e}", exc_info=True)
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
            
            logger.info(f"Batch {batch_num}: {successful} successful, {failed} failed")
        
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
        description="Process YouTube comments for ASCA extraction in batch"
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
    
    processor = BatchProcessor(
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
