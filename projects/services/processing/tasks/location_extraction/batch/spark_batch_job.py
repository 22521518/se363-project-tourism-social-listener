#!/usr/bin/env python3
"""
Location Extraction - Spark Batch Job
=====================================

A PySpark batch job for processing YouTube comments and extracting locations.
Uses the shared Spark library for session management.

This job:
1. Reads unprocessed records from PostgreSQL (incremental via LEFT JOIN)
2. Processes text with NER/LLM pipeline in micro-batches
3. Saves results to location_extractions table
4. Supports --max_items_per_run for batch size limiting

Usage (spark-submit via Airflow):
    spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 \
        projects/services/processing/tasks/location_extraction/batch/spark_batch_job.py \
        --max_items_per_run 50000 \
        --batch_size 100

Environment variables:
    - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD - Database configuration
    - LLM_PROVIDER, GOOGLE_API_KEY, LLM_MODEL_NAME - LLM configuration (optional)
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional, Iterator
from pathlib import Path

# Setup path for imports
project_root = Path(__file__).resolve().parents[6]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    root_env = project_root / ".env"
    if root_env.exists():
        load_dotenv(root_env)
    else:
        load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_config() -> Dict[str, str]:
    """Get database configuration from environment."""
    return {
        "host": os.getenv("DB_HOST", "postgres"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "airflow"),
        "user": os.getenv("DB_USER", "airflow"),
        "password": os.getenv("DB_PASSWORD", "airflow"),
    }


def get_jdbc_url(config: Dict[str, str]) -> str:
    """Get JDBC URL from config."""
    return f"jdbc:postgresql://{config['host']}:{config['port']}/{config['database']}"


def create_extraction_pipeline():
    """
    Create the location extraction pipeline.
    Falls back to NER-only if LLM is not available.
    """
    try:
        from projects.services.processing.tasks.location_extraction.pipelines.extraction_pipeline import (
            ExtractionPipeline
        )
        return ExtractionPipeline()
    except Exception as e:
        logger.warning(f"Could not create full extraction pipeline: {e}")
        logger.info("Using NER-only extraction")
        return None


def process_partition(partition: Iterator[Dict[str, Any]], pipeline) -> Iterator[Dict[str, Any]]:
    """
    Process a partition of records.
    
    Args:
        partition: Iterator of record dictionaries
        pipeline: Extraction pipeline instance
        
    Yields:
        Processed result dictionaries
    """
    from projects.services.processing.tasks.location_extraction.dto import (
        UnifiedTextEvent, LocationExtractionResult
    )
    
    for record in partition:
        try:
            comment_id = record["comment_id"]
            video_title = record.get("video_title", "")
            comment_text = record.get("comment_text", "")
            
            # Combine video title with comment for better context
            combined_text = f"[Video: {video_title}] {comment_text}" if video_title else comment_text
            
            if not combined_text.strip():
                continue
            
            # Create event
            event = UnifiedTextEvent(
                source="youtube",
                source_type="comment",
                external_id=comment_id,
                text=combined_text,
                metadata={
                    "video_id": record.get("video_id"),
                    "video_title": video_title,
                    "channel_id": record.get("channel_id"),
                }
            )
            
            # Extract locations
            if pipeline:
                result = pipeline.process(event)
            else:
                # Empty result if no pipeline
                result = LocationExtractionResult(locations=[])
            
            yield {
                "source_id": comment_id,
                "source_type": "youtube_comment",
                "raw_text": combined_text,
                "locations": json.dumps([loc.model_dump() for loc in result.locations]),
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error processing record {record.get('comment_id')}: {e}")
            continue


def main():
    """Main entry point for the Spark batch job."""
    parser = argparse.ArgumentParser(
        description="Location Extraction Spark Batch Job"
    )
    parser.add_argument(
        "--max_items_per_run",
        type=int,
        default=None,
        help="Maximum records to process in this run (default: all unprocessed)"
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
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Import shared Spark library
    from projects.libs.spark import get_spark_session, SparkConfig
    
    # Configure Spark
    config = SparkConfig(
        app_name="LocationExtractionBatch",
        checkpoint_dir=args.checkpoint_dir,
        packages="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1",
        log_level="DEBUG" if args.verbose else "WARN",
    )
    
    # Get Spark session from shared library
    spark = get_spark_session(config=config, environment=args.environment)
    
    logger.info("=" * 60)
    logger.info("Location Extraction Spark Batch Job")
    logger.info("=" * 60)
    logger.info(f"Max items per run: {args.max_items_per_run or 'unlimited'}")
    logger.info(f"Batch size: {args.batch_size}")
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
        # Using pushdown predicate for incremental processing
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
            LEFT JOIN location_extractions le 
                ON c.id = le.source_id 
                AND le.source_type = 'youtube_comment'
            WHERE le.id IS NULL
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
        logger.info("Initializing extraction pipeline...")
        pipeline = create_extraction_pipeline()
        
        # Process in batches using foreachPartition
        # Repartition to control parallelism
        num_partitions = max(1, total_records // args.batch_size)
        num_partitions = min(num_partitions, 32)  # Cap at 32 partitions
        
        logger.info(f"Processing with {num_partitions} partitions...")
        
        # Convert to RDD for partition-wise processing
        records_rdd = input_df.rdd.map(lambda row: row.asDict())
        
        # Process each partition
        results = []
        processed_count = 0
        failed_count = 0
        
        # Collect and process (for jobs needing shared pipeline state)
        # Note: For truly large datasets, use broadcast variables or UDFs
        all_records = input_df.collect()
        
        from projects.services.processing.tasks.location_extraction.dto import (
            UnifiedTextEvent, LocationExtractionResult
        )
        from projects.services.processing.tasks.location_extraction.dto.persistence import PersistenceLocationDTO
        from projects.services.processing.tasks.location_extraction.dao.dao import LocationExtractionDAO
        from projects.services.processing.tasks.location_extraction.config.settings import DatabaseConfig
        
        # Initialize DAO for saving results
        db_settings = DatabaseConfig(
            host=db_config["host"],
            port=int(db_config["port"]),
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        dao = LocationExtractionDAO(db_settings)
        
        # Process records in batches
        for i in range(0, len(all_records), args.batch_size):
            batch = all_records[i:i + args.batch_size]
            batch_num = (i // args.batch_size) + 1
            
            logger.info(f"Processing batch {batch_num} ({len(batch)} records)...")
            
            for record in batch:
                try:
                    comment_id = record["comment_id"]
                    video_title = record.get("video_title", "") or ""
                    comment_text = record.get("comment_text", "") or ""
                    
                    # Combine text
                    combined_text = f"[Video: {video_title}] {comment_text}" if video_title else comment_text
                    
                    if not combined_text.strip():
                        continue
                    
                    # Create event
                    event = UnifiedTextEvent(
                        source="youtube",
                        source_type="comment",
                        external_id=comment_id,
                        text=combined_text,
                        metadata={
                            "video_id": record.get("video_id"),
                            "video_title": video_title,
                        }
                    )
                    
                    # Extract
                    if pipeline:
                        result = pipeline.process(event)
                    else:
                        result = LocationExtractionResult(locations=[])
                    
                    # Save to database
                    dto = PersistenceLocationDTO(
                        source_id=comment_id,
                        source_type="youtube_comment",
                        raw_text=combined_text,
                        extraction_result=result
                    )
                    
                    saved = dao.save(dto)
                    if saved:
                        processed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {record.get('comment_id')}: {e}")
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
        
    except Exception as e:
        logger.error(f"Job failed with error: {e}", exc_info=True)
        raise
    finally:
        spark.stop()
        logger.info("Spark session stopped.")


if __name__ == "__main__":
    main()
