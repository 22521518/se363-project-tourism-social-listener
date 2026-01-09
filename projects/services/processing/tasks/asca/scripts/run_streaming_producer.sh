#!/bin/bash
# ============================================
# ASCA Module - Run YouTube Streaming Producer
# ============================================
# Runs the streaming producer to read YouTube comments from database
# and send them to Kafka for ASCA processing.
#
# Usage:
#   ./run_streaming_producer.sh                  # Continuous streaming
#   ./run_streaming_producer.sh --once           # Run once and exit
#   ./run_streaming_producer.sh --max-messages 1000  # Limit messages
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASCA_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$ASCA_DIR/venv"
AIRFLOW_HOME="${AIRFLOW_HOME:-$(dirname $(dirname $(dirname $(dirname $(dirname "$ASCA_DIR")))))}"

echo "============================================"
echo "ASCA YouTube Streaming Producer"
echo "============================================"
echo "ASCA Dir: $ASCA_DIR"
echo "Airflow Home: $AIRFLOW_HOME"

# Load environment variables
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
fi

# Activate virtual environment if exists
if [ -d "$VENV_DIR/bin" ]; then
    source "$VENV_DIR/bin/activate"
    echo "✅ Activated venv (Linux/Mac)"
elif [ -d "$VENV_DIR/Scripts" ]; then
    source "$VENV_DIR/Scripts/activate"
    echo "✅ Activated venv (Windows/Git Bash)"
fi

# Add AIRFLOW_HOME to PYTHONPATH
export PYTHONPATH="$AIRFLOW_HOME:$PYTHONPATH"

echo ""
echo "Starting YouTube Streaming Producer..."
echo "============================================"

python -m projects.services.processing.tasks.asca.streaming.youtube_streaming_producer "$@"
