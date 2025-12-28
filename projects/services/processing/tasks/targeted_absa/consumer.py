from pyspark.sql import SparkSession
import os
import json
import sys

# Add current dir to path to find modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dao import AbsaDAO
from llm_service import AbsaLocalService

DB_CONN = f'postgresql+psycopg2://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'

# Global model instance
llm_service = None

def get_llm_service():
    global llm_service
    if llm_service is None:
        llm_service = AbsaLocalService()
    return llm_service

def process_batch(batch_df, batch_id):
    if batch_df.isEmpty(): return
    print(f'--- Processing Batch {batch_id} ---')
    
    rows = batch_df.collect()
    
    # Init service on executor
    service = get_llm_service()
    dao = AbsaDAO(DB_CONN)
    
    all_results = []
    
    for row in rows:
        try:
            message = json.loads(row.value)
            text = None
            
            # Extract text based on ingestion format
            raw_payload = message.get('rawPayload', {})
            if isinstance(raw_payload, dict):
                text = raw_payload.get('text') or raw_payload.get('description') or raw_payload.get('title')
            
            if not text: 
                text = message.get('rawText')
            
            cid = message.get('externalId') or 'unknown'
            
            if text:
                results = service.analyze_text(text, cid)
                all_results.extend(results)
        except Exception as e:
            print(f'Row Error: {e}')
            
    if all_results:
        dao.save_batch(all_results)

def run():
    print('Starting Spark Consumer for Targeted ABSA...')
    spark = SparkSession.builder \
        .appName('Targeted-ABSA-Qwen-Worker') \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
        .getOrCreate()
    
    # Subscribe to youtube.comments AND youtube.videos
    df = spark.readStream \
        .format('kafka') \
        .option('kafka.bootstrap.servers', os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')) \
        .option('subscribe', 'youtube.comments,youtube.videos') \
        .option('startingOffsets', 'earliest') \
        .load()
    
    df.selectExpr('CAST(value AS STRING)') \
        .writeStream \
        .foreachBatch(process_batch) \
        .start() \
        .awaitTermination()

if __name__ == '__main__':
    run()
