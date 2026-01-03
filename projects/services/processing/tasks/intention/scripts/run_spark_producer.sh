#!/bin/bash
# Run Unprocess Producer - Fetch unprocessed comments and send to Kafka
# Usage: ./run_producer.sh [--batch-size N] [--run-once] [--interval N]
set -e

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(dirname "$SCRIPT_DIR")"
# Airflow root: projects -> services -> processing -> tasks -> intention -> airflow
AIRFLOW_ROOT="$(dirname "$(dirname "$(dirname "$(dirname "$(dirname "$SERVICE_ROOT")")")")")"

# Use provided VENV_DIR or default
VENV_DIR="${VENV_DIR:-$SERVICE_ROOT/.venv_service}"
PRODUCER_SCRIPT="$SERVICE_ROOT/producer.py"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run setup_venv.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

if [ ! -f "$PRODUCER_SCRIPT" ]; then
    echo "Error: Producer script not found at $PRODUCER_SCRIPT"
    exit 1
fi

# Set PYTHONPATH
export PYTHONPATH="$AIRFLOW_ROOT"

# Run the producer with passed arguments
echo "Running: python $PRODUCER_SCRIPT $@"
python "$PRODUCER_SCRIPT" "$@"