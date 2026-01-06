#!/bin/bash
# Run YouTube Full History Ingestion Service
# Usage: ./run_full_ingestion.sh <channel_id_or_handle>
set -e

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Go up to YouTube root: scripts -> youtube
SERVICE_ROOT="$(dirname "$SCRIPT_DIR")"
# Airflow root: projects -> services -> ingestion -> youtube -> airflow
AIRFLOW_ROOT="$(dirname "$(dirname "$(dirname "$(dirname "$SERVICE_ROOT")")")")"

# Use provided VENV_DIR or default
VENV_DIR="${VENV_DIR:-$SERVICE_ROOT/.venv_service}"
MAIN_SCRIPT="$SERVICE_ROOT/produce_full_history.py"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run setup_venv.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Run the python script with passed arguments
export PYTHONPATH="$AIRFLOW_ROOT"
echo "Running: python $MAIN_SCRIPT $@"
python "$MAIN_SCRIPT" "$@"
