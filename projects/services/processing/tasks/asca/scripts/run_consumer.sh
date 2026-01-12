#!/bin/bash
# ============================================
# ASCA Module - Run Raw Kafka Consumer
# ============================================
# Runs the standard Python Kafka consumer for ASCA extraction.
#
# Usage:
#   ./run_consumer.sh                # Normal run
#   ./run_consumer.sh --no-pipeline  # Run without ASCA pipeline (mock mode)
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASCA_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$ASCA_DIR/venv"
AIRFLOW_HOME="${AIRFLOW_HOME:-$(dirname $(dirname $(dirname $(dirname $(dirname "$ASCA_DIR")))))}"

echo "============================================"
echo "ASCA Consumer Startup"
echo "============================================"
echo "ASCA Dir: $ASCA_DIR"
echo "Airflow Home: $AIRFLOW_HOME"

# Load environment variables from root .env
if [ -f "$AIRFLOW_HOME/.env" ]; then
    echo "Loading .env from: $AIRFLOW_HOME/.env"
    set -a
    source "$AIRFLOW_HOME/.env"
    set +a
elif [ -f "$ASCA_DIR/.env" ]; then
    echo "Loading .env from: $ASCA_DIR/.env"
    set -a
    source "$ASCA_DIR/.env"
    set +a
else
    echo "⚠️  No .env file found. Using environment variables."
fi

# Activate virtual environment
if [ -d "$VENV_DIR/bin" ]; then
    source "$VENV_DIR/bin/activate"
    echo "✅ Activated venv (Linux/Mac)"
elif [ -d "$VENV_DIR/Scripts" ]; then
    source "$VENV_DIR/Scripts/activate"
    echo "✅ Activated venv (Windows/Git Bash)"
else
    echo "⚠️  Virtual environment not found. Running with system Python."
    echo "   Run ./setup_venv.sh first to create the virtual environment."
fi

# Add AIRFLOW_HOME to PYTHONPATH for imports
export PYTHONPATH="$AIRFLOW_HOME:$PYTHONPATH"
echo "PYTHONPATH: $PYTHONPATH"

# Run the consumer
echo ""
echo "Starting ASCA Consumer..."
echo "============================================"

python -m projects.services.processing.tasks.asca.messaging.consumer "$@"
