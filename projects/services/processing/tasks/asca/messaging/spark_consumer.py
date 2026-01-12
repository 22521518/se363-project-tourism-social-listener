#!/usr/bin/env python3
"""
ASCA Extraction - Spark Streaming Consumer
===========================================
A PySpark Structured Streaming consumer for big data processing.

This module uses the shared Spark launcher from projects.libs.spark
to avoid redundant PySpark downloads and handle venv packaging.

Usage (via launcher):
    python -m projects.services.processing.tasks.asca.messaging.spark_consumer

Or with spark-submit directly:
    spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \\
        projects/services/processing/tasks/asca/messaging/spark_consumer.py
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

# PySpark imports (loaded when running under Spark)
SPARK_AVAILABLE = False
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, from_json, to_json, struct, current_timestamp
    from pyspark.sql.types import (
        StructType, StructField, StringType, FloatType, 
        ArrayType, BooleanType
    )
    SPARK_AVAILABLE = True
except ImportError:
    logger.warning("PySpark not available in this environment")

# Import project modules
from projects.services.processing.tasks.asca.config.settings import (
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


def process_batch_and_write_to_db(batch_df, batch_id):
    """
    Process a micro-batch and write results to PostgreSQL.
    
    This function is called for each micro-batch in the streaming query.
    It processes the rows, performs ASCA extraction, and writes to DB.
    """
    from projects.services.processing.tasks.asca.dao.dao import ASCAExtractionDAO
    from projects.services.processing.tasks.asca.dto.persistence import PersistenceASCADTO
    from projects.services.processing.tasks.asca.dto.asca_result import (
        ASCAExtractionResult, ExtractionMeta
    )
    from projects.services.processing.tasks.asca.dto import UnifiedTextEvent
    
    if batch_df.isEmpty():
        logger.info(f"Batch {batch_id}: Empty batch, skipping")
        return
    
    logger.info(f"Batch {batch_id}: Processing {batch_df.count()} rows")
    
    # Initialize DAO
    db_config = DatabaseConfig.from_env()
    dao = ASCAExtractionDAO(db_config)
    
    # Try to load ASCA pipeline
    pipeline = None
    try:
        from projects.services.processing.tasks.asca.pipelines.asca_pipeline import (
            ASCAExtractionPipeline
        )
        pipeline = ASCAExtractionPipeline()
    except Exception as e:
        logger.warning(f"ASCA pipeline not available: {e}")
    
    # Collect rows to driver for processing
    rows = batch_df.collect()
    
    for row in rows:
        try:
            source_id = row['source_id']
            source_type = row['source_type']
            text = row['text']
            
            # Perform extraction
            if pipeline:
                try:
                    event = UnifiedTextEvent(
                        source=source_type,
                        source_type=source_type,
                        external_id=source_id,
                        text=text
                    )
                    extraction_result = pipeline.process(event)
                except Exception as e:
                    logger.error(f"ASCA extraction failed for {source_id}: {e}")
                    extraction_result = ASCAExtractionResult(
                        aspects=[],
                        overall_score=0.0,
                        meta=ExtractionMeta(extractor="asca", language="vi")
                    )
            else:
                # Mock result
                extraction_result = ASCAExtractionResult(
                    aspects=[],
                    overall_score=0.0,
                    meta=ExtractionMeta(extractor="asca", language="vi")
                )
            
            # Save to database
            dto = PersistenceASCADTO(
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


def run_spark_streaming():
    """Main entry point for Spark streaming consumer."""
    if not SPARK_AVAILABLE:
        logger.error("PySpark is required. Install with: pip install pyspark")
        sys.exit(1)
    
    kafka_config = KafkaConfig.from_env()
    
    logger.info(f"Starting Spark Streaming Consumer")
    logger.info(f"Kafka: {kafka_config.bootstrap_servers}")
    logger.info(f"Input Topic: {kafka_config.input_topic}")
    logger.info(f"Output Topic: {kafka_config.output_topic}")
    
    # Create Spark session
    spark = SparkSession.builder \
        .appName("ASCAExtractionConsumer") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoints/asca-extraction") \
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
        .option("checkpointLocation", "/tmp/spark-checkpoints/asca-extraction") \
        .trigger(processingTime="10 seconds") \
        .start()
    
    logger.info("Streaming query started. Waiting for termination...")
    query.awaitTermination()


def main():
    """
    Main entry point - can be called directly or via spark launcher.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="ASCA Spark Streaming Consumer")
    parser.add_argument("--use-launcher", action="store_true", 
                        help="Launch using shared Spark launcher (handles venv)")
    args = parser.parse_args()
    
    if args.use_launcher:
        # Use shared Spark launcher from libs
        try:
            from projects.libs.spark.launcher import launch_spark_job
            
            # Paths
            asca_dir = Path(__file__).resolve().parent.parent
            venv_dir = asca_dir / "venv"
            
            if not venv_dir.exists():
                logger.error(f"Virtual environment not found: {venv_dir}")
                logger.error("Run ./scripts/setup_venv.sh first")
                sys.exit(1)
            
            packages = ",".join([
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
                "org.postgresql:postgresql:42.7.1"
            ])
            
            launch_spark_job(
                venv_dir=str(venv_dir),
                service_code_dir=str(asca_dir),
                project_root=str(project_root),
                consumer_script_path=str(Path(__file__).resolve()),
                packages=packages,
                args=[]  # No additional args
            )
            
        except ImportError:
            logger.error("Spark launcher not found at projects.libs.spark.launcher")
            sys.exit(1)
    else:
        # Run directly (when already inside Spark context)
        run_spark_streaming()


if __name__ == "__main__":
    main()
