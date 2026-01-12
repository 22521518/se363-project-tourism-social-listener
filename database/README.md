# Database Setup & Migration

This directory contains scripts for database initialization and schema management.

## Quick Start

### 1. Fresh Database Setup (Docker)

When you start the database container for the first time, PostgreSQL will automatically run the SQL scripts in `init/`:

```bash
# Start fresh (removes existing data)
docker-compose down -v
docker-compose up -d postgres

# Verify tables were created
docker exec -it <postgres_container> psql -U airflow -d airflow -c "\dt"
```

### 2. Initialize Tables (Python)

Use the Python script when you need more control:

```bash
# From project root
cd database
python init_db.py

# Or with custom connection
python init_db.py -c "postgresql://user:pass@host:5432/dbname"

# List existing tables only
python init_db.py --list-only
```

### 3. Reset Schema (Handle Conflicts)

When your ORM models change and conflict with existing tables:

```bash
# Preview what would be dropped
python reset_schema.py --dry-run

# Reset with backup
python reset_schema.py --backup

# Reset specific tables only
python reset_schema.py --tables intentions traveling_types

# Force reset (no confirmation)
python reset_schema.py --force
```

## Files

| File | Purpose |
|------|---------|
| `init/01_init_all_tables.sql` | SQL schema for all tables (runs on container first start) |
| `init_db.py` | Python script to create tables via SQLAlchemy |
| `reset_schema.py` | Reset tables when schema conflicts occur |

## Tables Overview

| Service | Tables |
|---------|--------|
| YouTube | `youtube_channels`, `youtube_videos`, `youtube_comments`, `youtube_tracked_channels`, `youtube_ingestion_checkpoints` |
| Web Crawl | `crawl_history`, `crawl_result` |
| ASCA | `asca_extractions` |
| Intention | `intentions` |
| Location | `location_extractions` |
| ABSA | `targeted_absa_results` |
| Traveling | `traveling_types` |

## Schema Conflict Resolution

When you change ORM models and get errors like `column X does not exist`:

1. **Option A - Reset specific tables** (loses data in those tables):
   ```bash
   python reset_schema.py --tables intentions --backup
   ```

2. **Option B - Reset all tables** (loses all data):
   ```bash
   python reset_schema.py --backup --force
   ```

3. **Option C - Manual migration** (preserves data):
   ```sql
   -- Connect to database and run ALTER TABLE statements
   ALTER TABLE intentions ADD COLUMN new_column VARCHAR(255);
   ```
