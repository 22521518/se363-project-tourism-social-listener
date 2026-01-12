#!/usr/bin/env python3
"""
ASCA Extraction - Spark Batch Job
==================================

A PySpark batch job for processing YouTube comments with ASCA extraction.
Uses the shared Spark library for session management.

This job:
1. Reads unprocessed records from PostgreSQL (incremental via LEFT JOIN)
2. Processes text with ASCA pipeline in micro-batches
3. Saves results to asca_extractions table
4. Supports --max_items_per_run for batch size limiting

Usage (spark-submit via Airflow):
    spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 \
        projects/services/processing/tasks/asca/batch/spark_batch_job.py \
        --max_items_per_run 50000 \
        --batch_size 100

Environment variables:
    - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD - Database configuration
    - ASCA_MODEL_PATH - Path to ASCA model file
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables from root
env_path = Path(__file__).resolve().parents[6] / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_config() -> Dict[str, Any]:
    """Get database configuration from environment."""
    env_dict = {
        "host": os.getenv("DB_HOST", "postgres"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "airflow"),
        "user": os.getenv("DB_USER", "airflow"),
        "password": os.getenv("DB_PASSWORD", "airflow"),
    }

    logger.info(f"Environment variables: {os.getenv()}")
    logger.info(f"Database: {env_dict['host']}:{env_dict['port']}/{env_dict['database']}")

    return env_dict


def get_jdbc_url(config: Dict[str, Any]) -> str:
    """Get JDBC URL from config."""
    return f"jdbc:postgresql://{config['host']}:{config['port']}/{config['database']}"


def create_extraction_pipeline():
    """
    Create the ASCA extraction pipeline.
    """
    try:
        from projects.services.processing.tasks.asca.pipelines.asca_pipeline import ASCAExtractionPipeline
        return ASCAExtractionPipeline()
    except Exception as e:
        logger.error(f"Could not create ASCA pipeline: {e}")
        return None


def main():
    """Main entry point for the Spark batch job."""
    parser = argparse.ArgumentParser(
        description="ASCA Extraction Spark Batch Job"
    )
    parser.add_argument(
        "--max_items_per_run",
        type=int,
        default=50000,
        help="Maximum records to process in this run (default: 50000)"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=100,
        help="Number of records per micro-batch (default: 100)"
    )
    parser.add_argument(
        "--checkpoint_dir",
        type=str,
        default=None,
        help="Checkpoint directory for job state"
    )
    parser.add_argument(
        "--environment",
        type=str,
        choices=["local", "airflow", "cluster"],
        default=None,
        help="Override environment detection"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=4,
        help="Maximum concurrent threads for ASCA processing (default: 4)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Import shared Spark library
    from projects.libs.spark import get_spark_session, SparkConfig
    
    # Configure Spark
    config = SparkConfig(
        app_name="ASCAExtractionBatch",
        checkpoint_dir=args.checkpoint_dir,
        packages="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1",
        log_level="DEBUG" if args.verbose else "WARN",
    )
    
    # Get Spark session from shared library
    spark = get_spark_session(config=config, environment=args.environment)
    
    logger.info("=" * 60)
    logger.info("ASCA Extraction Spark Batch Job")
    logger.info("=" * 60)
    logger.info(f"Max items per run: {args.max_items_per_run}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Max workers: {args.max_workers}")
    logger.info(f"Spark Application ID: {spark.sparkContext.applicationId}")
    
    try:
        # Get database config
        db_config = get_db_config()
        jdbc_url = get_jdbc_url(db_config)
        jdbc_props = {
            "user": db_config["user"],
            "password": db_config["password"],
            "driver": "org.postgresql.Driver",
        }
        
        logger.info(f"Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # Build query for unprocessed records
        limit_clause = f"LIMIT {args.max_items_per_run}" if args.max_items_per_run else ""
        
        query = f"""
            (SELECT 
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
                AND ae.source_type = 'youtube_comment'
            WHERE ae.id IS NULL
            ORDER BY c.published_at DESC
            {limit_clause}) AS unprocessed_comments
        """
        
        # Read data from PostgreSQL
        logger.info("Reading unprocessed records from database...")
        
        input_df = spark.read \
            .jdbc(
                url=jdbc_url,
                table=query,
                properties=jdbc_props
            )
        
        total_records = input_df.count()
        logger.info(f"Found {total_records} unprocessed records")
        
        if total_records == 0:
            logger.info("No unprocessed records found. Exiting.")
            spark.stop()
            return
        
        # Initialize extraction pipeline on driver
        logger.info("Initializing ASCA extraction pipeline...")
        pipeline = create_extraction_pipeline()
        
        if not pipeline:
            logger.error("Failed to create extraction pipeline. Exiting.")
            spark.stop()
            sys.exit(1)
        
        # Process in batches
        logger.info(f"Processing {total_records} records in batches of {args.batch_size}...")
        
        # Collect and process
        all_records = input_df.collect()
        
        from projects.services.processing.tasks.asca.dto import UnifiedTextEvent
        from projects.services.processing.tasks.asca.dto.persistence import PersistenceASCADTO
        from projects.services.processing.tasks.asca.dao.dao import ASCAExtractionDAO
        from projects.services.processing.tasks.asca.config.settings import DatabaseConfig
        
        # Initialize DAO for saving results
        db_settings = DatabaseConfig(
            host=db_config["host"],
            port=int(db_config["port"]),
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        dao = ASCAExtractionDAO(db_settings)
        
        processed_count = 0
        failed_count = 0
        
        def process_single_record(record) -> Tuple[bool, Optional[str]]:
            """
            Process a single record with ASCA extraction.
            VnCoreNLP's HTTP server handles concurrent requests - the Python client is thread-safe
            as long as we do not recreate the object.
            
            Returns:
                Tuple of (success: bool, error_message: Optional[str])
            """
            try:
                # PySpark Row objects don't support .get(), use getattr() instead
                comment_id = record.comment_id
                comment_text = getattr(record, "comment_text", "") or ""
                
                if not comment_text.strip():
                    return (True, None)  # Skip empty records
                
                # Create event
                event = UnifiedTextEvent(
                    source="youtube",
                    source_type="comment",
                    external_id=comment_id,
                    text=comment_text,
                    created_at=getattr(record, "comment_published_at", None),
                    metadata={
                        "video_id": getattr(record, "video_id", None),
                        "video_title": getattr(record, "video_title", ""),
                        "channel_id": getattr(record, "channel_id", None),
                        "author": getattr(record, "author_display_name", None),
                    }
                )
                
                # Extract aspects (VnCoreNLP HTTP client is thread-safe)
                result = pipeline.process(event)
                
                # Save to database
                dto = PersistenceASCADTO(
                    source_id=comment_id,
                    source_type="youtube_comment",
                    raw_text=comment_text,
                    extraction_result=result
                )
                
                saved = dao.save(dto)
                if saved:
                    return (True, None)
                else:
                    return (False, "Failed to save to database")
                    
            except Exception as e:
                record_id = getattr(record, "comment_id", "unknown")
                return (False, f"Error processing {record_id}: {e}")
        
        # Process records in batches using ThreadPoolExecutor
        logger.info(f"Processing with {args.max_workers} worker threads...")
        
        for i in range(0, len(all_records), args.batch_size):
            batch = all_records[i:i + args.batch_size]
            batch_num = (i // args.batch_size) + 1
            
            logger.info(f"Processing batch {batch_num} ({len(batch)} records)...")
            
            # Use ThreadPoolExecutor for concurrent processing
            # VnCoreNLP HTTP server handles concurrent requests - the Python client is thread-safe
            with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
                futures = {executor.submit(process_single_record, record): record for record in batch}
                
                for future in as_completed(futures):
                    success, error_msg = future.result()
                    if success:
                        processed_count += 1
                    else:
                        if error_msg:
                            logger.error(error_msg)
                        failed_count += 1
            
            logger.info(f"Batch {batch_num} complete: {processed_count} processed, {failed_count} failed")
        
        # Summary
        logger.info("=" * 60)
        logger.info("Job Summary")
        logger.info("=" * 60)
        logger.info(f"Total records found: {total_records}")
        logger.info(f"Successfully processed: {processed_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info("Job completed successfully!")
        
        # Exit with error code if all failed
        if total_records > 0 and processed_count == 0:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Job failed with error: {e}", exc_info=True)
        raise
    finally:
        spark.stop()
        logger.info("Spark session stopped.")


if __name__ == "__main__":
    main()
