from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import sys
import os
import json
from datetime import datetime
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from .langchain.langchain import IntentionExtractionService
from .dto import ModelIntentionDTO 

# Add the root directory to path so we can import our modules
# When running with spark-submit --py-files, the zip is added to path
sys.path.append(os.getcwd())

try:
    from .config import DatabaseConfig, KafkaConfig
    from .dao import IntentionDAO
    from .dto import IntentionDTO
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Make sure to run with --py-files projects.zip")
    sys.exit(1)

# UDF to parse ISO dates (satisfying "use udf" requirement)
# Although Spark has native checks, this ensures our Python parsing logic matches


def get_db_config_dict():
    """Helper to get config as dict to pass to workers."""
    try:
        cfg = DatabaseConfig.from_env()
        return {
            "user": cfg.user,
            "password": cfg.password,
            "host": cfg.host,
            "port": cfg.port,
            "database": cfg.database
        }
    except Exception:
        # Fallback or fail
        return {}

            
def ensure_topics_exist(kafka_cfg):
    """Ensure Kafka topics exist before Spark tries to read them."""
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=kafka_cfg.bootstrap_servers,
            client_id=f"{kafka_cfg.client_id}_admin"
        )
        
        topics = [
            NewTopic(name=kafka_cfg.topic, num_partitions=1, replication_factor=1),
        ]
        
        admin.create_topics(topics)
        print("Created Kafka topics via Spark Consumer init")
        
    except TopicAlreadyExistsError:
        print("Kafka topics already exist")
    except Exception as e:
        print(f"Warning: Could not ensure topics exist: {e}")
    finally:
        try:
            admin.close()
        except:
            pass


            
def run_spark_consumer():
    spark = SparkSession.builder \
        .appName("IntentionExtraction") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")
    
    # Load configs
    try:
        kafka_cfg = KafkaConfig.from_env()
        # Capture DB config eagerly on driver to pass to workers
        db_config_dict = get_db_config_dict()
        
        # Ensure topics exist
        ensure_topics_exist(kafka_cfg)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    # Subscribe to all topics
    topics = f"{kafka_cfg.topic}"
    
    print(f"Subscribing to topics: {topics}")
    
    # Read Stream
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_cfg.bootstrap_servers) \
        .option("subscribe", topics) \
        .option("startingOffsets", "earliest") \
        .load()

    # Parse Key and Value
    # Using UDF here would be an option, but cast is sufficient. 
    # We will use the UDF just to demonstrate usage on a computed column if needed, 
    # but for structured streaming, native ops are preferred.
    
    processed_df = df.select(
        col("topic"),
        col("value").cast("string").alias("payload_json")
    )
    
    # Write Stream
    writer = processed_df \
        .writeStream \
        .outputMode("append") \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", "/tmp/spark_checkpoint_intention_extraction")


    # Process Batch Logic
    def process_batch(batch_df, batch_id):
        if batch_df.isEmpty():
            return

        logger.info(f"Processing batch {batch_id}")
        
        dao = IntentionDAO(db_config_dict)

        # 1️⃣ Collect batch rows (small batches only!)
        rows = batch_df.collect()

        # 2️⃣ Convert rows → DTOs
        items: list[ModelIntentionDTO] = []
        for row in rows:
            items.append(
                ModelIntentionDTO(
                    text=row.text,
                    video_title=row.video_title or "Unknown",
                    source_id=row.id,
                    source_type="comment",
                )
            )

        # 3️⃣ ONE LLM CALL
        service = IntentionExtractionService()
        results = service.batch_extract_intentions(items)

        # 4️⃣ Persist results
        now = datetime.utcnow()
        
        intention_dtos: list[IntentionDTO] = []
        for dto, result in zip(items, results):
           intention_dtos.append(IntentionDTO(
                source_id=dto.source_id,
                source_type=dto.source_type,
                raw_text=dto.text,
                intention_type=result["intention_type"],
                sentiment=result["sentiment"],
                confidence_score=1.0,  # GPT structured output → high confidence
                processed_at=now,
                model_used=result["model_used"],
                processing_time_ms=0,
                entities=[],
                topics=[],
            ))
        dao.save_batch(intention_dtos)
        
    # Check for run-once mode
    run_once = "--run-once" in sys.argv
    if run_once:
        print("Running in ONE-SHOT mode (availableNow=True)...")
        query = writer.trigger(availableNow=True).start()
    else:
        query = writer.start()

    query.awaitTermination()

if __name__ == "__main__":
    run_spark_consumer()
