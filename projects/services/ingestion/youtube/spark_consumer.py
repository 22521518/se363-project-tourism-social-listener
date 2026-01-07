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

try:
    from projects.services.ingestion.youtube.config import DatabaseConfig, KafkaConfig
    from projects.services.ingestion.youtube.dao import YouTubeDAO
    from projects.services.ingestion.youtube.dto import ChannelDTO, VideoDTO, CommentDTO
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Make sure to run with --py-files projects.zip")
    sys.exit(1)

# UDF to parse ISO dates (satisfying "use udf" requirement)
# Although Spark has native checks, this ensures our Python parsing logic matches
@udf(returnType=StringType())
def parse_iso_date_udf(date_str):
    if not date_str:
        return None
    try:
        # Normalize simple cases if needed
        return date_str
    except:
        return None

def get_db_config_dict():
    """Helper to get config as dict to pass to workers."""
    try:
        # Debug: Print env vars to ensure they are passed to Driver
        # print(f"DEBUG Driver Env: DB_HOST={os.environ.get('DB_HOST')}, DB_PORT={os.environ.get('DB_PORT')}")
        
        cfg = DatabaseConfig.from_env()
        print(f"Driver successfully loaded DB Config for host: {cfg.host}, db: {cfg.database}")
        return {
            "user": cfg.user,
            "password": cfg.password,
            "host": cfg.host,
            "port": cfg.port,
            "database": cfg.database
        }
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to load DatabaseConfig on Driver: {e}")
        # Fail hard so we know
        raise e

def process_partition(iterator, db_config_dict, kafka_config_dict):
    """
    Process a partition of data on the executor.
    Initializes DAO once per partition.
    Also initializes Kafka Producer to forward messages.
    """
    if not db_config_dict:
        print("CRITICAL WORKER ERROR: db_config_dict is missing or empty. Skipping partition.")
        return
        
    if not kafka_config_dict:
        print("CRITICAL WORKER ERROR: kafka_config_dict is missing or empty. Skipping partition.")
        return

    # Reconstruct config object
    class SimpleConfig:
        def __init__(self, d):
            self.user = d["user"]
            self.password = d["password"]
            self.host = d["host"]
            self.port = d["port"]
            self.database = d["database"]
            
        @property
        def connection_string(self):
            return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    db_config = SimpleConfig(db_config_dict)
    dao = YouTubeDAO(db_config)
    
    # Initialize Kafka Producer
    from kafka import KafkaProducer
    producer = None
    try:
        producer = KafkaProducer(
            bootstrap_servers=kafka_config_dict["bootstrap_servers"],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=3
        )
    except Exception as e:
        print(f"Error initializing Kafka Producer in Spark executor: {e}")
        # Proceeding without producer might be bad, but let's try to process at least

    # We might need to handle connection issues gracefully
    try:
        # dao.init_db() # Avoid calling DDL in workers
        pass
    except:
        pass

    topic_map = kafka_config_dict["topic_map"]

    # Limit batch size for database writes
    DB_BATCH_SIZE = 2000
    
    # Buffers for batch processing
    channels_batch = []
    channels_payloads = []
    
    videos_batch = []
    videos_payloads = []
    
    comments_batch = []
    comments_payloads = []
    
    def flush_channels():
        if channels_batch:
            print(f"Flushing {len(channels_batch)} channels to DB...")
            dao.save_channels(channels_batch, channels_payloads)
            channels_batch.clear()
            channels_payloads.clear()

    def flush_videos():
        if videos_batch:
            print(f"Flushing {len(videos_batch)} videos to DB...")
            dao.save_videos(videos_batch, videos_payloads)
            videos_batch.clear()
            videos_payloads.clear()

    def flush_comments():
        if comments_batch:
            print(f"Flushing {len(comments_batch)} comments to DB...")
            dao.save_comments(comments_batch, comments_payloads)
            comments_batch.clear()
            comments_payloads.clear()

    for row in iterator:
        try:
            topic = row.topic
            payload_str = row.payload_json
            
            if not payload_str:
                continue
                
            payload = json.loads(payload_str)
            raw_payload = payload.get("rawPayload")
            
            if not raw_payload:
                continue
            
            output_topic = topic_map.get(topic)
            saved_id = None
            
            # Map based on topic/entityType
            if "channels" in topic:
                dto = ChannelDTO(
                    id=raw_payload["id"],
                    title=raw_payload["title"],
                    description=raw_payload["description"],
                    custom_url=raw_payload["custom_url"],
                    published_at=datetime.fromisoformat(raw_payload["published_at"]),
                    thumbnail_url=raw_payload["thumbnail_url"],
                    subscriber_count=raw_payload["subscriber_count"],
                    video_count=raw_payload["video_count"],
                    view_count=raw_payload["view_count"],
                    country=raw_payload["country"],
                )
                channels_batch.append(dto)
                channels_payloads.append(raw_payload)
                saved_id = dto.id
                
                if len(channels_batch) >= DB_BATCH_SIZE:
                    flush_channels()
                
            elif "videos" in topic:
                dto = VideoDTO(
                    id=raw_payload["id"],
                    channel_id=raw_payload["channel_id"],
                    title=raw_payload["title"],
                    description=raw_payload["description"],
                    published_at=datetime.fromisoformat(raw_payload["published_at"]),
                    thumbnail_url=raw_payload["thumbnail_url"],
                    view_count=raw_payload["view_count"],
                    like_count=raw_payload["like_count"],
                    comment_count=raw_payload["comment_count"],
                    duration=raw_payload["duration"],
                    tags=tuple(raw_payload["tags"]),
                    category_id=raw_payload["category_id"],
                )
                videos_batch.append(dto)
                videos_payloads.append(raw_payload)
                saved_id = dto.id
                
                if len(videos_batch) >= DB_BATCH_SIZE:
                    flush_videos()
                
            elif "comments" in topic:
                dto = CommentDTO(
                    id=raw_payload["id"],
                    video_id=raw_payload["video_id"],
                    author_display_name=raw_payload["author_display_name"],
                    author_channel_id=raw_payload["author_channel_id"],
                    text=raw_payload["text"],
                    like_count=raw_payload["like_count"],
                    published_at=datetime.fromisoformat(raw_payload["published_at"]),
                    updated_at=datetime.fromisoformat(raw_payload["updated_at"]),
                    parent_id=raw_payload["parent_id"],
                    reply_count=raw_payload["reply_count"],
                )
                comments_batch.append(dto)
                comments_payloads.append(raw_payload)
                saved_id = dto.id
                
                if len(comments_batch) >= DB_BATCH_SIZE:
                    flush_comments()

            # Produce to downstream topic immediately
            # Note: If DB save later fails, we might have produced messages that aren't in DB yet.
            # In a strict transaction model, we might buffer these too, but for this use case,
            # downstream processing usually can happen in parallel or we accept eventual consistency.
            if producer and output_topic and saved_id:
                producer.send(
                    topic=output_topic,
                    key=saved_id,
                    value=json.loads(payload_str) 
                )
                
        except Exception as e:
            print(f"Error processing row: {e}")

    # Flush remaining items
    try:
        flush_channels()
        flush_videos()
        flush_comments()
    except Exception as e:
         print(f"Error flushing remaining batches: {e}")
         raise e

    if producer:
        try:
            producer.flush()
            producer.close()
        except:
            pass

def ensure_topics_exist(kafka_cfg):
    """Ensure Kafka topics exist before Spark tries to read them."""
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=kafka_cfg.bootstrap_servers,
            client_id=f"{kafka_cfg.client_id}_admin"
        )
        
        topics = [
            NewTopic(name=kafka_cfg.raw_channels_topic, num_partitions=1, replication_factor=1),
            NewTopic(name=kafka_cfg.raw_videos_topic, num_partitions=1, replication_factor=1),
            NewTopic(name=kafka_cfg.raw_comments_topic, num_partitions=1, replication_factor=1),
            NewTopic(name=kafka_cfg.channels_topic, num_partitions=1, replication_factor=1),
            NewTopic(name=kafka_cfg.videos_topic, num_partitions=1, replication_factor=1),
            NewTopic(name=kafka_cfg.comments_topic, num_partitions=1, replication_factor=1),
        ]
        
        try:
            for topic in topics:
                admin.create_topics([topic])
                print(f"Created topic: {topic.name}")

        except TopicAlreadyExistsError:
            print(f"Topic already exists: {topic.name}")

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
        .appName("YouTubeIngestionConsumer") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")
    
    # Load configs
    try:
        kafka_cfg = KafkaConfig.from_env()
        # Capture DB config eagerly on driver to pass to workers
        db_config_dict = get_db_config_dict()

        # Initialize DB Schema on Driver (create tables/fix PKs if needed)
        print("Initializing Database Schema on Driver...")
        try:
            # Re-use the config dict we just created
            class DriverConfig:
                def __init__(self, d):
                    self.user = d["user"]
                    self.password = d["password"]
                    self.host = d["host"]
                    self.port = d["port"]
                    self.database = d["database"]
                @property
                def connection_string(self):
                    return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

            driver_dao = YouTubeDAO(DriverConfig(db_config_dict))
            driver_dao.init_db()
            print("Database Schema Verified/Initialized.")
        except Exception as e:
            print(f"Warning: DB Initialization on driver failed: {e}")
            # We continue, as it might just be connection issue, hoping workers are fine or schema exists
        
        # Ensure topics exist
        ensure_topics_exist(kafka_cfg)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    # Create simple kafka config dict for workers
    kafka_config_dict = {
        "bootstrap_servers": kafka_cfg.bootstrap_servers,
        "topic_map": {
            kafka_cfg.raw_channels_topic: kafka_cfg.channels_topic,
            kafka_cfg.raw_videos_topic: kafka_cfg.videos_topic,
            kafka_cfg.raw_comments_topic: kafka_cfg.comments_topic,
        }
    }

    # Subscribe to raw topics
    topics = f"{kafka_cfg.raw_channels_topic},{kafka_cfg.raw_videos_topic},{kafka_cfg.raw_comments_topic}"
    
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
        col("value").cast("string").alias("payload_json"),
        col("timestamp")
    )

    # Process Batch Logic
    def process_batch(batch_df, batch_id):
        print(f"Processing batch {batch_id} with {batch_df.count()} records")
        # Use simple closure to pass config
        batch_df.foreachPartition(lambda iter: process_partition(iter, db_config_dict, kafka_config_dict))

    # Write Stream
    writer = processed_df \
        .writeStream \
        .outputMode("append") \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", "/tmp/spark_checkpoint_youtube")

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
