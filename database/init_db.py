#!/usr/bin/env python3
"""
Database Initialization Script
Initializes all database tables using SQLAlchemy ORM models.

Usage:
    python init_db.py
    python init_db.py --connection-string "postgresql://user:pass@host:5432/db"
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

load_dotenv()

# Add project root to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import create_engine, text, inspect

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_default_connection_string():
    """Get connection string from environment or use defaults."""
    return os.environ.get(
        'DATABASE_URL',
        os.environ.get(
            'DB_CONNECTION_STRING',
            'postgresql://airflow:airflow@localhost:5432/airflow'
        )
    )


def init_youtube_tables(engine):
    """Initialize YouTube ingestion tables."""
    try:
        from projects.services.ingestion.youtube.models import Base as YouTubeBase
        YouTubeBase.metadata.create_all(engine, checkfirst=True)
        logger.info("✓ YouTube tables initialized")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize YouTube tables: {e}")
        return False


def init_webcrawl_tables(engine):
    """Initialize Web Crawl tables."""
    try:
        from projects.services.ingestion.webcrawl.orm import Base as WebCrawlBase
        WebCrawlBase.metadata.create_all(engine, checkfirst=True)
        logger.info("✓ Web Crawl tables initialized")
        return True
    except Exception as e:
        logger.warning(f"⚠ Could not initialize Web Crawl tables (may need different import): {e}")
        return False


def init_asca_tables(engine):
    """Initialize ASCA extraction tables."""
    try:
        from projects.services.processing.tasks.asca.orm.models import Base as ASCABase
        ASCABase.metadata.create_all(engine, checkfirst=True)
        logger.info("✓ ASCA tables initialized")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize ASCA tables: {e}")
        return False


def init_intention_tables(engine):
    """Initialize Intention tables."""
    try:
        from projects.services.processing.tasks.intention.models import Base as IntentionBase
        IntentionBase.metadata.create_all(engine, checkfirst=True)
        logger.info("✓ Intention tables initialized")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize Intention tables: {e}")
        return False


def init_location_tables(engine):
    """Initialize Location Extraction tables."""
    try:
        from projects.services.processing.tasks.location_extraction.orm.models import Base as LocationBase
        LocationBase.metadata.create_all(engine, checkfirst=True)
        logger.info("✓ Location Extraction tables initialized")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize Location Extraction tables: {e}")
        return False


def init_targeted_absa_tables(engine):
    """Initialize Targeted ABSA tables."""
    try:
        from projects.services.processing.tasks.targeted_absa.models import Base as ABSABase
        ABSABase.metadata.create_all(engine, checkfirst=True)
        logger.info("✓ Targeted ABSA tables initialized")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize Targeted ABSA tables: {e}")
        return False


def init_traveling_type_tables(engine):
    """Initialize Traveling Type tables."""
    try:
        from projects.services.processing.tasks.traveling_type.models import Base as TravelingBase
        TravelingBase.metadata.create_all(engine, checkfirst=True)
        logger.info("✓ Traveling Type tables initialized")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize Traveling Type tables: {e}")
        return False


def list_tables(engine):
    """List all tables in the database."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return tables


def init_all_tables(connection_string: str = None):
    """Initialize all database tables."""
    if connection_string is None:
        connection_string = get_default_connection_string()
    
    logger.info(f"Connecting to database...")
    logger.info(f"Connection: {connection_string.split('@')[-1]}")  # Log without password
    
    engine = create_engine(connection_string)
    
    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False
    
    # Create UUID extension
    try:
        with engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            conn.commit()
        logger.info("✓ UUID extension enabled")
    except Exception as e:
        logger.warning(f"⚠ Could not create UUID extension: {e}")
    
    # Initialize all tables
    results = []
    results.append(("YouTube", init_youtube_tables(engine)))
    results.append(("Web Crawl", init_webcrawl_tables(engine)))
    results.append(("ASCA", init_asca_tables(engine)))
    results.append(("Intention", init_intention_tables(engine)))
    results.append(("Location Extraction", init_location_tables(engine)))
    results.append(("Targeted ABSA", init_targeted_absa_tables(engine)))
    results.append(("Traveling Type", init_traveling_type_tables(engine)))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("INITIALIZATION SUMMARY")
    logger.info("="*50)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for name, success in results:
        status = "✓" if success else "✗"
        logger.info(f"  {status} {name}")
    
    logger.info(f"\nTables initialized: {success_count}/{total_count}")
    
    # List all tables
    tables = list_tables(engine)
    logger.info(f"\nTables in database ({len(tables)}):")
    for table in sorted(tables):
        logger.info(f"  - {table}")
    
    return success_count == total_count


def main():
    parser = argparse.ArgumentParser(description="Initialize database tables")
    parser.add_argument(
        "--connection-string", "-c",
        help="Database connection string (default: from env or localhost)"
    )
    parser.add_argument(
        "--list-only", "-l",
        action="store_true",
        help="Only list existing tables, don't create"
    )
    
    args = parser.parse_args()
    
    connection_string = args.connection_string or get_default_connection_string()
    
    if args.list_only:
        engine = create_engine(connection_string)
        tables = list_tables(engine)
        print(f"Tables in database ({len(tables)}):")
        for table in sorted(tables):
            print(f"  - {table}")
        return
    
    success = init_all_tables(connection_string)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
