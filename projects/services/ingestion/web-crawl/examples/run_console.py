"""
Run Console - Example script to test the web crawl module.

Usage:
    cd examples
    pip install -r requirements.txt
    crawl4ai-setup
    python run_console.py
    
    # For batch mode:
    python run_console.py --batch
    
    # To force re-crawl even if cached:
    python run_console.py --force
"""
import asyncio
import json
import sys
import os
import argparse

# Fix Windows console encoding to support Unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables from project root
# Navigate up from examples -> web-crawl -> ingestion -> services -> projects -> airflow
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

from dto import CrawlRequestDTO
from core import CrawlService

# Directory for saving JSON results (same folder as this script)
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def sanitize_filename(url: str) -> str:
    """Convert URL to a safe filename."""
    import re
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    # Use domain + path, remove special characters
    name = f"{parsed.netloc}{parsed.path}"
    name = re.sub(r'[^\w\-_]', '_', name)
    name = re.sub(r'_+', '_', name)  # Collapse multiple underscores
    name = name.strip('_')[:100]  # Limit length
    return name


def save_result_to_json(result, prefix: str = "crawl") -> str:
    """
    Save crawl result to a JSON file in the examples folder.
    
    Args:
        result: CrawlResultDTO object
        prefix: Filename prefix (default: 'crawl')
        
    Returns:
        Path to the saved JSON file
    """
    from datetime import datetime
    
    # Generate filename from URL and timestamp
    url_part = sanitize_filename(result.url)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{url_part}_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Save to JSON
    output = result.model_dump(mode="json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved: {filename}")
    return filepath


async def single_crawl(force_refresh: bool = False):
    """Run a single URL crawl."""
    print("=" * 60)
    print("Single URL Crawl Mode")
    print("=" * 60)
    
    test = {
        "url": "https://en.wikivoyage.org/wiki/Ho_Chi_Minh_City",
        "content_type": "blog",
    }
    
    print(f"\nURL: {test['url']}")
    print(f"Content Type: {test['content_type']}")
    print("-" * 60)
    
    service = CrawlService()
    
    # First check if URL exists in cache (if not forcing refresh)
    if not force_refresh:
        # Create request without force_refresh to check cache
        check_request = CrawlRequestDTO(
            url=test["url"],
            content_type=test["content_type"],
            force_refresh=False,
        )
        
        result = await service.crawl(check_request)
        
        if result.from_cache:
            print("\n📦 URL already exists in database!")
            print(f"   Cached on: {result.meta.crawl_time}")
            print_result(result, brief=True)
            
            # Ask user if they want to re-crawl
            user_input = input("\n🔄 Re-crawl this URL? [y/N]: ").strip().lower()
            if user_input == 'y':
                print("\n🔄 Re-crawling...")
                request = CrawlRequestDTO(
                    url=test["url"],
                    content_type=test["content_type"],
                    force_refresh=True,
                )
                result = await service.crawl(request)
            else:
                print("\n✅ Using cached result.")
                save_result_to_json(result, prefix="cached")
                return
    else:
        # Force refresh requested
        request = CrawlRequestDTO(
            url=test["url"],
            content_type=test["content_type"],
            force_refresh=True,
        )
        result = await service.crawl(request)
    
    print("\n✅ Crawl Successful!\n")
    print_result(result)
    
    # Save result to JSON file
    save_result_to_json(result, prefix="single")


async def batch_crawl():
    """Run batch URL crawl (optimized for rate limits)."""
    print("=" * 60)
    print("Batch URL Crawl Mode (Optimized for Rate Limits)")
    print("=" * 60)
    
    # Multiple URLs to crawl in a single batch
    test_urls = [
        {"url": "https://en.wikivoyage.org/wiki/Ho_Chi_Minh_City", "content_type": "blog"},
        # {"url": "https://en.wikivoyage.org/wiki/Hanoi", "content_type": "blog"},
        # {"url": "https://en.wikivoyage.org/wiki/Da_Nang", "content_type": "blog"},
    ]
    
    print(f"\nBatch crawling {len(test_urls)} URLs:")
    for i, t in enumerate(test_urls, 1):
        print(f"  {i}. {t['url']}")
    print("-" * 60)
    
    requests = [
        CrawlRequestDTO(url=t["url"], content_type=t["content_type"])
        for t in test_urls
    ]
    
    service = CrawlService()
    results = await service.crawl_batch(requests, batch_size=3)
    
    print(f"\n✅ Batch Crawl Successful! ({len(results)} results)\n")
    
    for i, result in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"Result {i}/{len(results)}: {result.url}")
        print(f"{'='*60}")
        print_result(result, brief=True)
        
        # Save each result to JSON file
        save_result_to_json(result, prefix=f"batch_{i}")


def print_result(result, brief=False):
    """Print crawl result."""
    if not brief:
        output = result.model_dump(mode="json")
        print("Structured Output (JSON):")
        print("-" * 60)
        print(json.dumps(output, indent=2, ensure_ascii=False))
    
    print("\n" + "-" * 60)
    print("📊 Summary:")
    print(f"  - Request ID: {result.request_id}")
    print(f"  - From Cache: {'Yes ✅' if result.from_cache else 'No (Fresh crawl)'}")
    print(f"  - Detected Sections: {result.meta.detected_sections}")
    print(f"  - Reviews Found: {len(result.content.reviews)}")
    print(f"  - Comments Found: {len(result.content.comments)}")
    print(f"  - Blog Sections Found: {len(result.content.blog_sections)}")
    print(f"  - Has Agency Info: {result.content.agency_info is not None}")
    
    if result.content.title:
        print(f"  - Title: {result.content.title}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Web Crawl Tourism Content Extractor")
    parser.add_argument("--batch", action="store_true", help="Use batch crawling mode")
    parser.add_argument("--force", action="store_true", help="Force re-crawl even if cached")
    args = parser.parse_args()
    
    # Check API key early
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_key:
        print("\n[ERROR] No API key found!")
        print("Please set GEMINI_API_KEY in your .env file.")
        return
    
    print(f"[INFO] Gemini API Key loaded: {gemini_key[:10]}...{gemini_key[-4:]}")
    
    print(f"[INFO] Results will be saved to: {OUTPUT_DIR}")
    
    try:
        if args.batch:
            await batch_crawl()
        else:
            await single_crawl(force_refresh=args.force)
            
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nMake sure to set GEMINI_API_KEY environment variable!")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Crawl Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
