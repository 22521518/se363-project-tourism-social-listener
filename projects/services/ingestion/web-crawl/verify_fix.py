
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.abspath("."))

print("Starting import check...")

try:
    from core import WebCrawlService, CrawlService, DuplicateUrlError
    print("✅ Successfully imported core components")
    
    from messaging.producer import WebCrawlKafkaProducer
    print("✅ Successfully imported Kafka producer")
    
    from messaging.consumer import WebCrawlKafkaConsumer
    print("✅ Successfully imported Kafka consumer")
    
    import main
    print("✅ Successfully imported main module")
    
    print("\nAll imports successful!")
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
