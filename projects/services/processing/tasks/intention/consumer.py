from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import sys
import os
import json
from datetime import datetime
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError




# Add the root directory to path so we can import our modules
# When running with spark-submit --py-files, the zip is added to path
sys.path.append(os.getcwd())

import logging

logger = logging.getLogger(__name__)

try:
    from projects.services.processing.tasks.intention.langchain.langchain import IntentionExtractionService
    from projects.services.processing.tasks.intention.config import ConsumerConfig
    from projects.services.processing.tasks.intention.dao import IntentionDAO
    from projects.services.processing.tasks.intention.dto import IntentionDTO, ModelIntentionDTO
    from projects.services.processing.tasks.intention.models import IntentionType
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Make sure to run with --py-files projects.zip")
    sys.exit(1)

# UDF to parse ISO dates (satisfying "use udf" requirement)
# Although Spark has native checks, this ensures our Python parsing logic matches



payload_schema = StructType([
    StructField("source", StringType()),
    StructField("externalId", StringType()),
    StructField("rawText", StringType()),
    StructField("createdAt", StringType()),
    StructField("entityType", StringType()),
    StructField(
        "rawPayload",
        StructType([
            StructField("text", StringType()),
            StructField("video_id", StringType()),
        ])
    )
])

def normalize_intention_type(value) -> IntentionType:
    if isinstance(value, IntentionType):
        return value

    if isinstance(value, str):
        try:
            return IntentionType(value)
        except ValueError:
            return IntentionType.OTHER

    return IntentionType.OTHER
      
def ensure_topics_exist(kafka_cfg):
    """Ensure Kafka topics exist before Spark tries to read them."""
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=kafka_cfg.bootstrap_servers,
            client_id=f"{kafka_cfg.client_id}_admin"
        )
        
        topics = [
            # Main topic for other modules
            NewTopic(name=kafka_cfg.topic, num_partitions=1, replication_factor=1),
            # Unprocessed topic specifically for intention extraction
            NewTopic(name=kafka_cfg.unprocessed_topic, num_partitions=1, replication_factor=1),
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



  # Process Batch Logic
def process_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        print(f"[Batch {batch_id}] Empty batch, skipping")
        return
    
    print(f"[Batch {batch_id}] Processing batch")
    
    # Load consumer config for DB connection
    consumer_cfg = ConsumerConfig.from_env()
    dao = IntentionDAO(consumer_cfg.database)
    # 1️⃣ Collect batch rows (small batches only!)
    rows = batch_df.collect()
    
    print(f"[Batch {batch_id}] Collected {len(rows)} rows")
    
    # 2️⃣ Convert rows → DTOs
    items: list[ModelIntentionDTO] = []
    for row in rows:
        items.append(
            ModelIntentionDTO(
                text=row.text,
                source_id=row.source_id,
                source_type=row.source_type,
            )
        )
        
    if items:
        print(
            f"[Batch {batch_id}] First sample text (truncated): "
            f"{items[0].text[:200]}"
        )
        
    # 3️⃣ ONE LLM CALL
    service = IntentionExtractionService(model_config=consumer_cfg.model)
    results = service.batch_extract_intentions(items)
    
    intention_dtos: list[IntentionDTO] = []
    for dto, result in zip(items, results):
       intention_dtos.append(IntentionDTO(
            source_id=dto.source_id,
            source_type=dto.source_type,
            raw_text=dto.text,
            intention_type=normalize_intention_type(
                result.get("intention_type")
            ),
        ))
    try:
        dao.save_batch(intention_dtos)
        print(
            f"[Batch {batch_id}] Saved {len(intention_dtos)} intentions"
        )
    except Exception as e:
        print(
            f"[Batch {batch_id}] Failed while saving intentions: {e}"
        )
                 
def run_spark_consumer():
    spark = SparkSession.builder \
        .appName("IntentionExtractionConsumer") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoints/intention-extraction") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")
    
    # Load configs
    try:
        consumer_cfg = ConsumerConfig.from_env()
        
        # Ensure topics exist
        ensure_topics_exist(consumer_cfg.kafka)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    # Subscribe to all topics
    topics = f"{consumer_cfg.kafka.topic},{consumer_cfg.kafka.unprocessed_topic}"
    
    print(f"Subscribing to topics: {topics}")
    
    # Read Stream
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", consumer_cfg.kafka.bootstrap_servers) \
        .option("subscribe", topics) \
        .option("startingOffsets", "earliest") \
        .option("maxOffsetsPerTrigger", consumer_cfg.kafka.max_offsets_per_trigger) \
        .load()

    # Parse Key and Value
    # Using UDF here would be an option, but cast is sufficient. 
    # We will use the UDF just to demonstrate usage on a computed column if needed, 
    # but for structured streaming, native ops are preferred.
    
    processed_df = (
    df
    .select(from_json(col("value").cast("string"), payload_schema).alias("data"))
    .select(
        col("data.rawText").alias("text"),
        col("data.externalId").alias("source_id"),
        col("data.entityType").alias("source_type"),
    )
    )
    
        
      # Write Stream
    writer = processed_df \
        .writeStream \
        .outputMode("append") \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", "/tmp/spark_checkpoint_intention_extraction") \
        .trigger(processingTime=consumer_cfg.kafka.processing_time)
        
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
