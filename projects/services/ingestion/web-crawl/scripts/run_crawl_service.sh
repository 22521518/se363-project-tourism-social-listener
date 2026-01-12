#!/bin/bash
# Run Web Crawl Service (Producer mode)
# Usage: ./run_crawl_service.sh [--url URL] [--content-type TYPE]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(dirname "$SCRIPT_DIR")"
AIRFLOW_ROOT="$(dirname "$(dirname "$(dirname "$(dirname "$SERVICE_ROOT")")")")"

# Use provided VENV_DIR or default
VENV_DIR="${VENV_DIR:-$SERVICE_ROOT/.venv}"
MAIN_SCRIPT="$SERVICE_ROOT/main.py"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run setup_venv.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Set PYTHONPATH
export PYTHONPATH="$AIRFLOW_ROOT"


echo "Initializing database tables..."
python "$SCRIPT_DIR/init_db.py"

echo "Running web crawl service..."
python "$MAIN_SCRIPT" "$@"
