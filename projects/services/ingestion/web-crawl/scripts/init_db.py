#!/usr/bin/env python3
"""
Initialize database tables for Web Crawl service.
"""
import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add service root to path
script_path = Path(__file__).resolve()
service_root = script_path.parent.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

try:
    from dotenv import load_dotenv
    from orm.base import init_db, engine
    # Import models to ensure they are registered with Base metadata
    from orm import crawl_history_model, crawl_result_model
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you are running this script within the service virtual environment.")
    sys.exit(1)

def main():
    """Main function to initialize database."""
    # Load environment variables
    load_dotenv(service_root / ".env")
    
    logger.info(f"Initializing database tables for Web Crawl service...")
    logger.info(f"Database URL: {engine.url}")
    
    try:
        init_db()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
