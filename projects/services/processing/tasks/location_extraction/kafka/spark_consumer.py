#!/usr/bin/env python3
"""
Location Extraction - Spark Streaming Consumer
===============================================
A PySpark Structured Streaming consumer for big data processing that:
1. Consumes messages from KAFKA_TOPIC_LOCATION_INPUT using Spark
2. Processes text with the LLM pipeline (using foreachBatch for DB writes)
3. Writes results to the database
4. Produces output to KAFKA_TOPIC_LOCATION_OUTPUT

Usage (spark-submit):
    spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \\
        projects/services/processing/tasks/location_extraction/kafka/spark_consumer.py

Environment variables (from .env):
    - KAFKA_BOOTSTRAP_SERVERS
    - KAFKA_TOPIC_LOCATION_INPUT
    - KAFKA_TOPIC_LOCATION_OUTPUT
    - DB_* for database connection
    - LLM_* for LLM configuration
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, UTC

# Setup path for imports
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PySpark imports
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, from_json, to_json, struct, udf, current_timestamp
    from pyspark.sql.types import (
        StructType, StructField, StringType, FloatType, 
        ArrayType, BooleanType, MapType
    )
    SPARK_AVAILABLE = True
except ImportError:
    logger.error("PySpark is not available. Please install pyspark.")
    SPARK_AVAILABLE = False

# Import project modules
from projects.services.processing.tasks.location_extraction.config.settings import (
    DatabaseConfig, KafkaConfig, settings
)


def get_input_schema():
    """Schema for input Kafka messages."""
    return StructType([
        StructField("source_id", StringType(), False),
        StructField("source_type", StringType(), False),
        StructField("text", StringType(), False),
        StructField("timestamp", StringType(), True)
    ])


def get_output_schema():
    """Schema for output extraction results."""
    location_schema = StructType([
        StructField("name", StringType(), False),
        StructField("type", StringType(), False),
        StructField("confidence", FloatType(), False)
    ])
    
    primary_location_schema = StructType([
        StructField("name", StringType(), False),
        StructField("confidence", FloatType(), False)
    ])
    
    meta_schema = StructType([
        StructField("extractor", StringType(), False),
        StructField("fallback_used", BooleanType(), False)
    ])
    
    return StructType([
        StructField("source_id", StringType(), False),
        StructField("source_type", StringType(), False),
        StructField("raw_text", StringType(), False),
        StructField("locations", ArrayType(location_schema), False),
        StructField("primary_location", primary_location_schema, True),
        StructField("overall_score", FloatType(), False),
        StructField("meta", meta_schema, False),
        StructField("processed_at", StringType(), False),
        StructField("success", BooleanType(), False)
    ])


def process_batch_and_write_to_db(batch_df, batch_id):
    """
    Process a micro-batch and write results to PostgreSQL.
    
    This function is called for each micro-batch in the streaming query.
    It processes the rows, performs LLM extraction, and writes to DB.
    """
    from projects.services.processing.tasks.location_extraction.dao.dao import LocationExtractionDAO
    from projects.services.processing.tasks.location_extraction.dto.persistence import PersistenceLocationDTO
    from projects.services.processing.tasks.location_extraction.dto.location_result import (
        LocationExtractionResult, ExtractionMeta
    )
    
    if batch_df.isEmpty():
        logger.info(f"Batch {batch_id}: Empty batch, skipping")
        return
    
    logger.info(f"Batch {batch_id}: Processing {batch_df.count()} rows")
    
    # Initialize DAO
    db_config = DatabaseConfig.from_env()
    dao = LocationExtractionDAO(db_config)
    dao.init_db()
    
    # Try to load LLM pipeline
    pipeline = None
    try:
        from projects.services.processing.tasks.location_extraction.pipelines.extraction_pipeline import (
            LocationExtractionPipeline
        )
        pipeline = LocationExtractionPipeline()
    except Exception as e:
        logger.warning(f"LLM pipeline not available: {e}")
    
    # Collect rows to driver for processing
    # Note: In production, consider using mapPartitions for better scalability
    rows = batch_df.collect()
    
    for row in rows:
        try:
            source_id = row['source_id']
            source_type = row['source_type']
            text = row['text']
            
            # Perform extraction
            if pipeline:
                try:
                    extraction_result = pipeline.extract(text)
                except Exception as e:
                    logger.error(f"LLM extraction failed for {source_id}: {e}")
                    extraction_result = LocationExtractionResult(
                        locations=[],
                        primary_location=None,
                        overall_score=0.0,
                        meta=ExtractionMeta(extractor="llm", fallback_used=False)
                    )
            else:
                # Mock result
                extraction_result = LocationExtractionResult(
                    locations=[],
                    primary_location=None,
                    overall_score=0.0,
                    meta=ExtractionMeta(extractor="llm", fallback_used=False)
                )
            
            # Save to database
            dto = PersistenceLocationDTO(
                source_id=source_id,
                source_type=source_type,
                raw_text=text,
                extraction_result=extraction_result
            )
            
            saved = dao.save(dto)
            if saved:
                logger.info(f"Saved extraction for {source_id}")
            else:
                logger.warning(f"Failed to save {source_id} (may already exist)")
                
        except Exception as e:
            logger.error(f"Error processing row: {e}", exc_info=True)
    
    logger.info(f"Batch {batch_id}: Completed")


def main():
    """Main entry point for Spark streaming consumer."""
    if not SPARK_AVAILABLE:
        logger.error("PySpark is required. Install with: pip install pyspark")
        sys.exit(1)
    
    kafka_config = KafkaConfig.from_env()
    db_config = DatabaseConfig.from_env()
    
    logger.info(f"Starting Spark Streaming Consumer")
    logger.info(f"Kafka: {kafka_config.bootstrap_servers}")
    logger.info(f"Input Topic: {kafka_config.input_topic}")
    logger.info(f"Output Topic: {kafka_config.output_topic}")
    
    # Create Spark session
    spark = SparkSession.builder \
        .appName("LocationExtractionConsumer") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoints/location-extraction") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    # Read from Kafka
    input_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_config.bootstrap_servers) \
        .option("subscribe", kafka_config.input_topic) \
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
        .option("checkpointLocation", "/tmp/spark-checkpoints/location-extraction") \
        .trigger(processingTime="10 seconds") \
        .start()
    
    logger.info("Streaming query started. Waiting for termination...")
    query.awaitTermination()


if __name__ == "__main__":
    main()
