"""
Web Crawl Main - CLI entry point for the web crawl module.

Usage:
    python main.py --url URL [--content-type TYPE] [--force]
    python main.py --consume  # Run Kafka consumer
"""
import asyncio
import argparse
import sys
import os
import logging

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables - try multiple paths in order of priority
def load_env_files():
    """Load .env files from multiple possible locations."""
    current_file = Path(__file__).resolve()
    webcrawl_dir = current_file.parent  # web-crawl/
    
    possible_paths = [
        # 1. Local .env (web-crawl/.env)
        webcrawl_dir / ".env",
        # 2. projects/.env
        webcrawl_dir.parents[2] / ".env",  # web-crawl -> ingestion -> services -> projects
        # 3. airflow root .env
        webcrawl_dir.parents[3] / ".env",  # projects -> airflow
        # 4. Docker paths
        Path("/opt/airflow/projects/services/ingestion/web-crawl/.env"),
        Path("/opt/airflow/projects/.env"),
        Path("/opt/airflow/.env"),
    ]
    
    loaded = False
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            print(f"✅ Web Crawl Main: Loaded .env from: {env_path}")
            loaded = True
            break
    
    if not loaded:
        load_dotenv()
        print("⚠️ Web Crawl Main: Using default dotenv search")

load_env_files()

from core import WebCrawlService, DuplicateUrlError
from messaging.producer import WebCrawlKafkaProducer
from messaging.consumer import WebCrawlKafkaConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def crawl_url(url: str, content_type: str, force: bool) -> None:
    """Crawl a single URL."""
    service = WebCrawlService()
    
    try:
        result = await service.crawl(url, content_type, force_refresh=force)
        
        print(f"\n✅ Crawl Successful!")
        print(f"   Request ID: {result.request_id}")
        print(f"   Title: {result.content.title}")
        print(f"   Detected Sections: {result.meta.detected_sections}")
        
        # Publish to Kafka
        with WebCrawlKafkaProducer() as producer:
            producer.produce_crawl_result(result.model_dump(mode="json"))
            print(f"   Published to Kafka ✓")
            
    except DuplicateUrlError as e:
        print(f"\n⚠️ {e}")
        print("   Use --force to re-crawl")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def run_consumer() -> None:
    """Run Kafka consumer to process crawl requests."""
    
    async def process_request(message: dict):
        """Process a crawl request from Kafka."""
        url = message.get("url")
        content_type = message.get("content_type", "auto")
        force = message.get("force_refresh", False)
        
        logger.info(f"Processing crawl request: {url}")
        
        service = WebCrawlService()
        try:
            result = await service.crawl(url, content_type, force_refresh=force)
            
            # Publish result
            with WebCrawlKafkaProducer() as producer:
                producer.produce_crawl_result(result.model_dump(mode="json"))
            
            logger.info(f"Completed crawl: {url}")
            
        except DuplicateUrlError:
            logger.warning(f"URL already exists: {url}")
        except Exception as e:
            logger.error(f"Crawl failed: {url} - {e}")
    
    def sync_callback(message: dict):
        """Sync wrapper for async process."""
        asyncio.run(process_request(message))
    
    print("Starting Kafka consumer...")
    with WebCrawlKafkaConsumer() as consumer:
        consumer.consume(sync_callback)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Web Crawl Service")
    parser.add_argument("--url", help="URL to crawl")
    parser.add_argument("--content-type", default="auto",
                       choices=["forum", "review", "blog", "agency", "auto"],
                       help="Content type for extraction")
    parser.add_argument("--force", action="store_true",
                       help="Force re-crawl even if URL exists")
    parser.add_argument("--consume", action="store_true",
                       help="Run as Kafka consumer")
    args = parser.parse_args()
    
    if args.consume:
        run_consumer()
    elif args.url:
        asyncio.run(crawl_url(args.url, args.content_type, args.force))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
