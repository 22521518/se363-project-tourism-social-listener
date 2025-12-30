#!/bin/bash
# Run YouTube Batch Processor for Location Extraction
# 
# This script processes YouTube comments that have been ingested but not yet
# processed by location extraction, combining video titles with comments.
#
# Usage: ./run_youtube_batch.sh [--batch-size N] [--max-records N] [--verbose]
#
# Environment Variables:
#   VENV_DIR - Path to virtual environment (optional, uses service .venv if not set)
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD - Database configuration
#   LLM_PROVIDER, GOOGLE_API_KEY, LLM_MODEL_NAME - LLM configuration
#   BATCH_SIZE - Number of records per batch (default: 50)
#   MAX_RECORDS - Maximum total records to process (default: 500)

set -e

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Scripts -> location_extraction
SERVICE_ROOT="$(dirname "$SCRIPT_DIR")"
# Airflow root: projects -> services -> processing -> tasks -> location_extraction -> airflow
AIRFLOW_ROOT="$(dirname "$(dirname "$(dirname "$(dirname "$(dirname "$SERVICE_ROOT")")")")")"

# Use provided VENV_DIR or default
VENV_DIR="${VENV_DIR:-$SERVICE_ROOT/.venv}"

echo "=================================================="
echo "YouTube Batch Location Extraction Processor"
echo "=================================================="
echo "Service Root: $SERVICE_ROOT"
echo "Airflow Root: $AIRFLOW_ROOT"
echo "Virtual Env:  $VENV_DIR"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run setup_venv.sh first."
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set PYTHONPATH to include airflow root for imports
export PYTHONPATH="$AIRFLOW_ROOT"

echo "PYTHONPATH: $PYTHONPATH"
echo "Arguments: $@"
echo "=================================================="

# Default environment variables if not set
export DB_HOST="${DB_HOST:-localhost}"
export DB_PORT="${DB_PORT:-5432}"
export DB_NAME="${DB_NAME:-airflow}"
export DB_USER="${DB_USER:-airflow}"
export DB_PASSWORD="${DB_PASSWORD:-airflow}"
export BATCH_SIZE="${BATCH_SIZE:-50}"
export MAX_RECORDS="${MAX_RECORDS:-500}"

echo "Database: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
echo "Batch Size: $BATCH_SIZE"
echo "Max Records: $MAX_RECORDS"
echo "=================================================="

# Run the batch processor module
python -m projects.services.processing.tasks.location_extraction.batch.youtube_batch_processor "$@"

echo "=================================================="
echo "YouTube Batch Processing Complete"
echo "=================================================="
