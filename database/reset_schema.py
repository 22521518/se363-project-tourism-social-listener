#!/usr/bin/env python3
"""
Database Schema Reset Script
Handles schema conflicts by dropping and recreating tables.

USE WITH CAUTION: This will delete data!

Usage:
    python reset_schema.py --dry-run          # Preview what would be dropped
    python reset_schema.py                     # Reset all tables
    python reset_schema.py --tables intentions traveling_types  # Specific tables
    python reset_schema.py --backup            # Backup to CSV before dropping
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Add project root to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import create_engine, text, inspect, MetaData

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# All known tables in dependency order (parents first)
ALL_TABLES = [
    # YouTube (dependency order)
    'youtube_ingestion_checkpoints',
    'youtube_tracked_channels', 
    'youtube_comments',
    'youtube_videos',
    'youtube_channels',
    # Web Crawl
    'crawl_result',
    'crawl_history',
    # Processing tasks (no dependencies between them)
    'asca_extractions',
    'intentions',
    'location_extractions',
    'targeted_absa_results',
    'traveling_types',
]

# Enum types to drop before tables (for complete reset)
ENUM_TYPES = [
    'crawl_status',
    'intention_type', 
    'traveling_type',
    'intentiontype',       # SQLAlchemy may create with different name
    'travelingtype',       # SQLAlchemy may create with different name
]


def get_default_connection_string():
    """Get connection string from environment or use defaults."""
    return os.environ.get(
        'DATABASE_URL',
        os.environ.get(
            'DB_CONNECTION_STRING',
            'postgresql://airflow:airflow@localhost:5432/airflow'
        )
    )


def get_existing_tables(engine):
    """Get list of tables that exist in the database."""
    inspector = inspect(engine)
    return inspector.get_table_names()


def backup_table_to_csv(engine, table_name: str, backup_dir: str):
    """Backup a table to CSV file."""
    import pandas as pd
    
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(backup_dir, f"{table_name}_{timestamp}.csv")
    
    try:
        df = pd.read_sql_table(table_name, engine)
        df.to_csv(filepath, index=False)
        logger.info(f"  ✓ Backed up {table_name} ({len(df)} rows) to {filepath}")
        return True
    except Exception as e:
        logger.warning(f"  ⚠ Could not backup {table_name}: {e}")
        return False


def drop_table(engine, table_name: str, dry_run: bool = False):
    """Drop a single table."""
    if dry_run:
        logger.info(f"  [DRY-RUN] Would drop table: {table_name}")
        return True
    
    try:
        with engine.connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
            conn.commit()
        logger.info(f"  ✓ Dropped table: {table_name}")
        return True
    except Exception as e:
        logger.error(f"  ✗ Failed to drop {table_name}: {e}")
        return False


def drop_enum_type(engine, enum_name: str, dry_run: bool = False):
    """Drop an enum type."""
    if dry_run:
        logger.info(f"  [DRY-RUN] Would drop enum type: {enum_name}")
        return True
    
    try:
        with engine.connect() as conn:
            conn.execute(text(f'DROP TYPE IF EXISTS "{enum_name}" CASCADE'))
            conn.commit()
        logger.info(f"  ✓ Dropped enum type: {enum_name}")
        return True
    except Exception as e:
        logger.warning(f"  ⚠ Could not drop enum {enum_name}: {e}")
        return False


def reset_schema(
    connection_string: str = None,
    tables: list = None,
    dry_run: bool = False,
    backup: bool = False,
    drop_enums: bool = True
):
    """
    Reset database schema by dropping and recreating tables.
    
    Args:
        connection_string: Database connection string
        tables: List of specific tables to reset (None = all)
        dry_run: If True, only show what would be done
        backup: If True, backup tables to CSV before dropping
        drop_enums: If True, also drop enum types
    """
    if connection_string is None:
        connection_string = get_default_connection_string()
    
    logger.info("="*60)
    logger.info("DATABASE SCHEMA RESET")
    logger.info("="*60)
    
    if dry_run:
        logger.info("MODE: DRY-RUN (no changes will be made)")
    else:
        logger.warning("MODE: LIVE (tables will be dropped!)")
    
    engine = create_engine(connection_string)
    
    # Get existing tables
    existing_tables = get_existing_tables(engine)
    logger.info(f"\nExisting tables: {len(existing_tables)}")
    
    # Determine which tables to drop
    tables_to_drop = tables if tables else ALL_TABLES
    tables_to_drop = [t for t in tables_to_drop if t in existing_tables]
    
    if not tables_to_drop:
        logger.info("No tables to drop (none exist or specified tables not found)")
        return True
    
    logger.info(f"Tables to drop: {len(tables_to_drop)}")
    for t in tables_to_drop:
        logger.info(f"  - {t}")
    
    # Backup if requested
    if backup and not dry_run:
        logger.info("\n--- BACKING UP DATA ---")
        backup_dir = os.path.join(SCRIPT_DIR, 'backups')
        for table in tables_to_drop:
            backup_table_to_csv(engine, table, backup_dir)
    
    # Drop tables
    logger.info("\n--- DROPPING TABLES ---")
    for table in tables_to_drop:
        drop_table(engine, table, dry_run)
    
    # Drop enum types if doing a full reset
    if drop_enums and (tables is None or len(tables) == len(ALL_TABLES)):
        logger.info("\n--- DROPPING ENUM TYPES ---")
        for enum_type in ENUM_TYPES:
            drop_enum_type(engine, enum_type, dry_run)
    
    # Recreate tables
    if not dry_run:
        logger.info("\n--- RECREATING TABLES ---")
        from init_db import init_all_tables
        init_all_tables(connection_string)
    
    logger.info("\n" + "="*60)
    logger.info("RESET COMPLETE")
    logger.info("="*60)
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Reset database schema (drops and recreates tables)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reset_schema.py --dry-run              # Preview what would happen
  python reset_schema.py                        # Reset all tables
  python reset_schema.py --tables intentions    # Reset specific table
  python reset_schema.py --backup               # Backup to CSV first
        """
    )
    
    parser.add_argument(
        "--connection-string", "-c",
        help="Database connection string"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Only show what would be done, don't actually drop tables"
    )
    parser.add_argument(
        "--backup", "-b",
        action="store_true",
        help="Backup tables to CSV before dropping"
    )
    parser.add_argument(
        "--tables", "-t",
        nargs="+",
        choices=ALL_TABLES,
        help="Specific tables to reset (default: all)"
    )
    parser.add_argument(
        "--no-enums",
        action="store_true",
        help="Don't drop enum types"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    # Safety confirmation
    if not args.dry_run and not args.force:
        print("\n" + "!"*60)
        print("WARNING: This will DELETE data from your database!")
        print("!"*60)
        print(f"\nTables to drop: {args.tables or 'ALL'}")
        response = input("\nType 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(1)
    
    success = reset_schema(
        connection_string=args.connection_string,
        tables=args.tables,
        dry_run=args.dry_run,
        backup=args.backup,
        drop_enums=not args.no_enums
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
