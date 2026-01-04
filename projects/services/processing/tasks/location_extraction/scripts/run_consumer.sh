#!/bin/bash
# Run Location Extraction Kafka Consumer
# Usage: ./run_consumer.sh [--no-llm] [--max-messages N]
set -e

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Scripts -> location_extraction
SERVICE_ROOT="$(dirname "$SCRIPT_DIR")"
# Airflow root: projects -> services -> processing -> tasks -> location_extraction -> airflow
AIRFLOW_ROOT="$(dirname "$(dirname "$(dirname "$(dirname "$(dirname "$SERVICE_ROOT")")")")")"

# Use provided VENV_DIR or default
VENV_DIR="${VENV_DIR:-$SERVICE_ROOT/.venv}"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run setup_venv.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Set PYTHONPATH to include airflow root for imports
export PYTHONPATH="$AIRFLOW_ROOT"

echo "Running Location Extraction Kafka Consumer..."
echo "PYTHONPATH: $PYTHONPATH"
echo "Arguments: $@"

# Run the consumer module
python -m projects.services.processing.tasks.location_extraction.messaging.consumer "$@"
