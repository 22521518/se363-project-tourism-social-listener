from pyspark.sql import SparkSession
import os
import json
import sys

# Thêm đường dẫn để import các file module
sys.path.append(os.getcwd())

from dao import AbsaDAO
from llm_service import AbsaLocalService

# Cấu hình DB lấy từ môi trường Docker
DB_CONN = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# Khai báo biến toàn cục cho Model (để không phải load lại mỗi lần batch chạy)
llm_service = None

def get_llm_service():
    global llm_service
    if llm_service is None:
        # Load model Qwen (chạy trên CPU mặc định)
        llm_service = AbsaLocalService()
    return llm_service

def process_batch(batch_df, batch_id):
    """Hàm xử lý từng batch dữ liệu từ Kafka"""
    if batch_df.isEmpty(): return
    
    print(f"--- Đang xử lý Batch {batch_id} ---")
    rows = batch_df.collect()
    
    service = get_llm_service()
    dao = AbsaDAO(DB_CONN)
    
    all_results = []
    
    for row in rows:
        try:
            # Parse JSON từ Kafka
            message = json.loads(row.value)
            
            # Lấy nội dung comment (tùy chỉnh theo format của nhóm bạn)
            # Thường là rawPayload -> text hoặc snippet -> textDisplay
            text = None
            raw_payload = message.get('rawPayload', {})
            if isinstance(raw_payload, dict):
                text = raw_payload.get('text') or raw_payload.get('description')
            
            if not text:
                text = message.get('rawText')

            cid = message.get('externalId') or "unknown"
            
            if text:
                # Gọi AI phân tích
                results = service.analyze_text(text, cid)
                all_results.extend(results)
                
        except Exception as e:
            print(f"Lỗi parse dòng: {e}")

    # Lưu xuống DB
    if all_results:
        dao.save_batch(all_results)

def run():
    spark = SparkSession.builder \
        .appName("Targeted-ABSA-Qwen-Worker") \
        .getOrCreate()
    
    # Đọc từ Kafka topic "youtube.comments"
    # Bạn cần đảm bảo Topic này trùng với Topic mà nhóm bạn đang đẩy dữ liệu vào
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")) \
        .option("subscribe", "youtube.comments") \
        .option("startingOffsets", "latest") \
        .load()
        
    df.selectExpr("CAST(value AS STRING)") \
        .writeStream \
        .foreachBatch(process_batch) \
        .start() \
        .awaitTermination()

if __name__ == "__main__":
    run()