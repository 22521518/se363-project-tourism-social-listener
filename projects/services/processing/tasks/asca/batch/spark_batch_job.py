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
import gc
import signal
import atexit
import logging
import argparse
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables - try multiple paths in order of priority
def load_env_files():
    """Load .env files from multiple possible locations."""
    current_file = Path(__file__).resolve()
    
    # Possible .env locations in order of priority:
    possible_paths = [
        # 1. ASCA's local .env (projects/services/processing/tasks/asca/.env)
        current_file.parent.parent / ".env",
        # 2. projects/.env
        current_file.parents[4] / ".env",  # batch -> asca -> tasks -> processing -> services -> projects
        # 3. airflow root .env (for local development)
        current_file.parents[5] / ".env",  # projects -> airflow
        # 4. Docker paths
        Path("/opt/airflow/.env"),
        Path("/opt/airflow/projects/.env"),
        Path("/opt/airflow/projects/services/processing/tasks/asca/.env"),
    ]
    
    loaded = False
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            print(f"✅ Loaded .env from: {env_path}")
            loaded = True
            break
    
    if not loaded:
        # Fallback to default dotenv search
        load_dotenv()
        print("⚠️ Using default dotenv search")

load_env_files()

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

    logger.info(f"Database: {env_dict['host']}:{env_dict['port']}/{env_dict['database']}")

    return env_dict


def get_jdbc_url(config: Dict[str, Any]) -> str:
    """Get JDBC URL from config."""
    return f"jdbc:postgresql://{config['host']}:{config['port']}/{config['database']}"


def create_extraction_pipeline():
    """
    Get the singleton ASCA extraction pipeline instance.
    
    Uses the singleton pattern to ensure only ONE VnCoreNLP server runs.
    """
    try:
        from projects.services.processing.tasks.asca.pipelines.asca_pipeline import get_pipeline_instance
        return get_pipeline_instance()
    except Exception as e:
        logger.error(f"Could not get ASCA pipeline instance: {e}")
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
        default=2,
        help="Maximum concurrent threads for ASCA processing (default: 2)"
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
    
    pipeline = None  # Initialize pipeline variable for cleanup in finally block
    
    def cleanup_resources():
        """Cleanup function to release all resources."""
        nonlocal pipeline, spark
        logger.info("🧹 Cleaning up resources...")
        
        # Clean up ASCA pipeline (including VnCoreNLP server)
        if pipeline is not None:
            try:
                logger.info("Closing ASCA pipeline (including VnCoreNLP server)...")
                pipeline.close()
                logger.info("✅ ASCA pipeline closed successfully.")
            except Exception as e:
                logger.warning(f"⚠️ Error closing ASCA pipeline: {e}")
        
        # Stop Spark session
        try:
            if spark is not None:
                spark.stop()
                logger.info("✅ Spark session stopped.")
        except Exception as e:
            logger.warning(f"⚠️ Error stopping Spark: {e}")
    
    def signal_handler(signum, frame):
        """Handle termination signals gracefully."""
        sig_name = signal.Signals(signum).name
        logger.info(f"⚠️ Received signal {sig_name}, initiating graceful shutdown...")
        cleanup_resources()
        sys.exit(128 + signum)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Also register atexit for cleanup
    atexit.register(cleanup_resources)
    
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
        
        total_batches = (len(all_records) + args.batch_size - 1) // args.batch_size
        
        for i in range(0, len(all_records), args.batch_size):
            batch = all_records[i:i + args.batch_size]
            batch_num = (i // args.batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)...")
            
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
                
                # Clear futures dictionary to release references
                futures.clear()
            
            # Explicit memory cleanup after each batch
            del batch
            
            # Run garbage collection every 10 batches to reclaim memory
            if batch_num % 10 == 0:
                gc.collect()
                logger.info(f"🧹 GC collected after batch {batch_num}")
            
            logger.info(f"Batch {batch_num} complete: {processed_count} processed, {failed_count} failed")
        
        # Final cleanup - release all_records
        del all_records
        gc.collect()
        logger.info("🧹 Final GC collected after all batches")
        
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
        # Unregister atexit to avoid double cleanup
        try:
            atexit.unregister(cleanup_resources)
        except:
            pass
        # Perform cleanup
        cleanup_resources()


if __name__ == "__main__":
    main()
