#!/usr/bin/env python3
"""
Web Crawl - Spark Streaming Consumer
=====================================
A PySpark Structured Streaming consumer for web crawl requests that:
1. Consumes messages from webcrawl.requests topic using Spark
2. Processes crawl requests with the WebCrawlService
3. Writes results to PostgreSQL and JSON files
4. Produces output to webcrawl.results topic

Usage (spark-submit):
    spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
        projects/services/ingestion/web-crawl/messaging/spark_consumer.py

Environment variables (from .env):
    - KAFKA_BOOTSTRAP_SERVERS
    - DB_* for database connection
    - GEMINI_API_KEY for LLM extraction
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, UTC

# Setup path for imports
project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

service_root = Path(__file__).resolve().parent.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

from dotenv import load_dotenv

# Load environment variables - try multiple paths in order of priority
def load_env_files():
    """Load .env files from multiple possible locations."""
    current_file = Path(__file__).resolve()
    
    possible_paths = [
        # 1. Local .env (web-crawl/.env)
        current_file.parent.parent / ".env",
        # 2. projects/.env
        current_file.parents[3] / ".env",  # messaging -> web-crawl -> ingestion -> services -> projects
        # 3. airflow root .env
        current_file.parents[4] / ".env",  # projects -> airflow
        # 4. Docker paths
        Path("/opt/airflow/projects/services/ingestion/web-crawl/.env"),
        Path("/opt/airflow/projects/.env"),
        Path("/opt/airflow/.env"),
    ]
    
    loaded = False
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            print(f"✅ Web Crawl Spark Consumer: Loaded .env from: {env_path}")
            loaded = True
            break
    
    if not loaded:
        load_dotenv()
        print("⚠️ Web Crawl Spark Consumer: Using default dotenv search")

load_env_files()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PySpark imports
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, from_json, to_json, struct, current_timestamp
    from pyspark.sql.types import (
        StructType, StructField, StringType, BooleanType, TimestampType
    )
    SPARK_AVAILABLE = True
except ImportError:
    logger.error("PySpark is not available. Please install pyspark.")
    SPARK_AVAILABLE = False

# Import project modules
from config import KafkaConfig, DatabaseConfig


def get_input_schema():
    """Schema for input Kafka messages (crawl requests)."""
    return StructType([
        StructField("event_type", StringType(), True),
        StructField("url", StringType(), False),
        StructField("content_type", StringType(), False),
        StructField("force_refresh", BooleanType(), True),
        StructField("timestamp", StringType(), True),
    ])


def get_output_schema():
    """Schema for output extraction results."""
    return StructType([
        StructField("request_id", StringType(), False),
        StructField("url", StringType(), False),
        StructField("status", StringType(), False),
        StructField("title", StringType(), True),
        StructField("content_type", StringType(), True),
        StructField("extracted_sections", StringType(), True),
        StructField("processed_at", StringType(), False),
        StructField("success", BooleanType(), False),
        StructField("error_message", StringType(), True),
    ])


def process_batch_and_write_to_db(batch_df, batch_id):
    """
    Process a micro-batch of crawl requests and write results to PostgreSQL.
    
    This function is called for each micro-batch in the streaming query.
    It processes crawl requests, performs crawling with LLM extraction, and writes to DB.
    """
    from core import WebCrawlService, DuplicateUrlError
    from dao.json_file_writer import JsonFileWriter
    from messaging.producer import WebCrawlKafkaProducer
    
    if batch_df.isEmpty():
        logger.info(f"Batch {batch_id}: Empty batch, skipping")
        return
    
    row_count = batch_df.count()
    logger.info(f"Batch {batch_id}: Processing {row_count} crawl requests")
    
    # Initialize services
    service = WebCrawlService()
    json_writer = JsonFileWriter()
    
    # Collect rows to driver for processing
    rows = batch_df.collect()
    
    results = []
    for row in rows:
        try:
            url = row['url']
            content_type = row['content_type'] or 'auto'
            force_refresh = row.get('force_refresh', False) or False
            
            logger.info(f"Processing crawl request: {url}")
            
            # Perform crawl asynchronously
            try:
                result = asyncio.run(
                    service.crawl(url, content_type, force_refresh=force_refresh)
                )
                
                # Convert result to dict for JSON storage
                result_dict = result.model_dump(mode="json")
                
                # Save to JSON files
                json_writer.save_history(result.request_id, {
                    "request_id": result.request_id,
                    "url": url,
                    "content_type": content_type,
                    "status": result.meta.status,
                    "crawl_time": result.meta.crawl_time.isoformat() if result.meta.crawl_time else None,
                })
                json_writer.save_result(result.request_id, result_dict)
                
                # Publish result to Kafka
                try:
                    with WebCrawlKafkaProducer() as producer:
                        producer.produce_crawl_result(result_dict)
                except Exception as kafka_err:
                    logger.warning(f"Failed to publish to Kafka: {kafka_err}")
                
                results.append({
                    "request_id": result.request_id,
                    "url": url,
                    "status": result.meta.status,
                    "title": result.content.title if result.content else None,
                    "content_type": content_type,
                    "extracted_sections": json.dumps(result.meta.detected_sections) if result.meta.detected_sections else None,
                    "processed_at": datetime.now(UTC).isoformat(),
                    "success": True,
                    "error_message": None,
                })
                
                logger.info(f"Completed crawl: {url} -> {result.request_id}")
                
            except DuplicateUrlError as dup_err:
                logger.warning(f"URL already exists: {url}")
                results.append({
                    "request_id": None,
                    "url": url,
                    "status": "DUPLICATE",
                    "title": None,
                    "content_type": content_type,
                    "extracted_sections": None,
                    "processed_at": datetime.now(UTC).isoformat(),
                    "success": False,
                    "error_message": str(dup_err),
                })
                
            except Exception as crawl_err:
                logger.error(f"Crawl failed for {url}: {crawl_err}")
                results.append({
                    "request_id": None,
                    "url": url,
                    "status": "FAILED",
                    "title": None,
                    "content_type": content_type,
                    "extracted_sections": None,
                    "processed_at": datetime.now(UTC).isoformat(),
                    "success": False,
                    "error_message": str(crawl_err),
                })
                
        except Exception as e:
            logger.error(f"Error processing row: {e}", exc_info=True)
    
    logger.info(f"Batch {batch_id}: Completed. Processed {len(results)} requests.")


def main():
    """Main entry point for Spark streaming consumer."""
    if not SPARK_AVAILABLE:
        logger.error("PySpark is required. Install with: pip install pyspark")
        sys.exit(1)
    
    kafka_config = KafkaConfig.from_env()
    db_config = DatabaseConfig.from_env()
    
    logger.info(f"Starting Web Crawl Spark Streaming Consumer")
    logger.info(f"Kafka: {kafka_config.bootstrap_servers}")
    logger.info(f"Input Topic: {kafka_config.requests_topic}")
    logger.info(f"Output Topic: {kafka_config.results_topic}")
    logger.info(f"Database: {db_config.host}:{db_config.port}/{db_config.database}")
    
    # Create Spark session
    spark = SparkSession.builder \
        .appName("WebCrawlConsumer") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoints/webcrawl") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    # Read from Kafka
    input_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_config.bootstrap_servers) \
        .option("subscribe", kafka_config.requests_topic) \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Parse JSON value
    input_schema = get_input_schema()
    
    parsed_df = input_df \
        .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)") \
        .select(
            col("key").alias("kafka_key"),
            from_json(col("value"), input_schema).alias("data")
        ) \
        .select("kafka_key", "data.*")
    
    # Process using foreachBatch for DB writes
    query = parsed_df \
        .writeStream \
        .foreachBatch(process_batch_and_write_to_db) \
        .option("checkpointLocation", "/tmp/spark-checkpoints/webcrawl") \
        .trigger(processingTime="10 seconds") \
        .start()
    
    logger.info("Streaming query started. Waiting for termination...")
    query.awaitTermination()


if __name__ == "__main__":
    main()
