#!/usr/bin/env python3
"""
Script to diagnose and fix schema issues with YouTube tables.
Specifically checks for duplicate IDs that would prevent adding PRIMARY KEY.

Usage:
    python fix_schema.py [--dry-run]

    --dry-run: Only check for issues, don't apply fixes.
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to python path
project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, text, inspect

def get_engine():
    """Create SQLAlchemy engine from environment."""
    load_dotenv()
    
    # Fallback to loading from projects/.env if direct env vars not set
    projects_env = Path(__file__).resolve().parents[1] / ".env"
    if projects_env.exists():
        load_dotenv(projects_env)
    
    from projects.services.ingestion.youtube.config import DatabaseConfig
    config = DatabaseConfig.from_env()
    logger.info(f"Connecting to: {config.host}:{config.port}/{config.database}")
    return create_engine(config.connection_string)


def check_duplicates(engine, table_name: str, id_column: str = "id"):
    """Check for duplicate IDs in a table."""
    query = text(f"""
        SELECT {id_column}, COUNT(*) as cnt 
        FROM {table_name} 
        GROUP BY {id_column} 
        HAVING COUNT(*) > 1
        LIMIT 10
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()
    
    if rows:
        logger.warning(f"Found {len(rows)}+ duplicate IDs in {table_name}:")
        for row in rows[:5]:
            logger.warning(f"  ID: {row[0]}, Count: {row[1]}")
        return True
    else:
        logger.info(f"No duplicate IDs found in {table_name}")
        return False


def check_primary_key(engine, table_name: str):
    """Check if table has a primary key."""
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        logger.info(f"Table {table_name} does not exist")
        return None
    
    pk = inspector.get_pk_constraint(table_name)
    if pk and pk.get("constrained_columns"):
        logger.info(f"Table {table_name} has PRIMARY KEY on: {pk['constrained_columns']}")
        return True
    else:
        logger.warning(f"Table {table_name} is MISSING PRIMARY KEY!")
        return False


def deduplicate_table(engine, table_name: str, id_column: str = "id"):
    """Remove duplicate rows, keeping the latest one (by updated_at or ctid)."""
    logger.info(f"Deduplicating {table_name}...")
    
    # Use ctid (PostgreSQL row identifier) to keep one row per id
    # This keeps the first physical row for each id
    dedup_query = text(f"""
        DELETE FROM {table_name} a
        USING {table_name} b
        WHERE a.{id_column} = b.{id_column}
        AND a.ctid < b.ctid
    """)
    
    with engine.connect() as conn:
        result = conn.execute(dedup_query)
        conn.commit()
        logger.info(f"Deleted {result.rowcount} duplicate rows from {table_name}")
    
    return result.rowcount


def add_primary_key(engine, table_name: str, id_column: str = "id"):
    """Add primary key to table."""
    logger.info(f"Adding PRIMARY KEY to {table_name}...")
    
    query = text(f"ALTER TABLE {table_name} ADD PRIMARY KEY ({id_column})")
    
    try:
        with engine.connect() as conn:
            conn.execute(query)
            conn.commit()
        logger.info(f"Successfully added PRIMARY KEY to {table_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to add PRIMARY KEY to {table_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Fix YouTube schema issues")
    parser.add_argument("--dry-run", action="store_true", help="Only check, don't fix")
    args = parser.parse_args()
    
    engine = get_engine()
    
    tables = ["youtube_channels", "youtube_videos", "youtube_comments"]
    
    for table in tables:
        logger.info(f"\n=== Checking {table} ===")
        
        has_pk = check_primary_key(engine, table)
        if has_pk is None:
            continue  # Table doesn't exist
        
        if not has_pk:
            has_dups = check_duplicates(engine, table)
            
            if args.dry_run:
                if has_dups:
                    logger.info(f"[DRY RUN] Would remove duplicates from {table}")
                logger.info(f"[DRY RUN] Would add PRIMARY KEY to {table}")
            else:
                if has_dups:
                    deduplicate_table(engine, table)
                add_primary_key(engine, table)
    
    logger.info("\n=== Done ===")


if __name__ == "__main__":
    main()
