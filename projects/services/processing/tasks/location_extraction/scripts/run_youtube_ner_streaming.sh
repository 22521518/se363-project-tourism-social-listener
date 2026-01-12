#!/bin/bash
# Run YouTube NER Streaming Processor
# 
# Combines batch processing (historical data) with Kafka streaming (new data):
# 1. Phase 1: Process ALL unprocessed YouTube comments from database
# 2. Phase 2: Once caught up, start Kafka consumer and run indefinitely
#
# Usage: ./run_youtube_ner_streaming.sh [--skip-batch] [--batch-only] [--batch-size N]
#
# Environment Variables:
#   VENV_DIR - Path to virtual environment
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD - Database configuration
#   KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_LOCATION_INPUT - Kafka configuration
#   BATCH_SIZE - Number of records per batch (default: 100)

set -e

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(dirname "$SCRIPT_DIR")"
AIRFLOW_ROOT="$(dirname "$(dirname "$(dirname "$(dirname "$(dirname "$SERVICE_ROOT")")")")")"

# Use provided VENV_DIR or default
VENV_DIR="${VENV_DIR:-$SERVICE_ROOT/.venv}"

echo "=================================================="
echo "YouTube NER Streaming Processor"
echo "Model: Davlan/xlm-roberta-base-ner-hrl"
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
export BATCH_SIZE="${BATCH_SIZE:-100}"

# Kafka defaults
export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"
export KAFKA_TOPIC_LOCATION_INPUT="${KAFKA_TOPIC_LOCATION_INPUT:-location-extraction-input}"
export KAFKA_TOPIC_LOCATION_OUTPUT="${KAFKA_TOPIC_LOCATION_OUTPUT:-location-extraction-output}"
export KAFKA_CONSUMER_GROUP="${KAFKA_CONSUMER_GROUP:-location-extraction-streaming}"

echo "Database: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
echo "Kafka: $KAFKA_BOOTSTRAP_SERVERS"
echo "Kafka Input Topic: $KAFKA_TOPIC_LOCATION_INPUT"
echo "Batch Size: $BATCH_SIZE"
echo "=================================================="

# Run the streaming processor module
python -m projects.services.processing.tasks.location_extraction.batch.youtube_ner_streaming_processor "$@"

echo "=================================================="
echo "YouTube NER Streaming Processor Stopped"
echo "=================================================="
