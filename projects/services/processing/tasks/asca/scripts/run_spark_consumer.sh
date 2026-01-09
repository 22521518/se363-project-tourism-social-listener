#!/bin/bash
# ============================================
# ASCA Module - Run Spark Streaming Consumer
# ============================================
# Runs the PySpark Structured Streaming consumer for ASCA extraction.
# Uses shared Spark launcher from projects.libs.spark for venv handling.
#
# Usage:
#   ./run_spark_consumer.sh              # Use shared launcher
#   ./run_spark_consumer.sh --direct     # Run with spark-submit directly
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASCA_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$ASCA_DIR/venv"
AIRFLOW_HOME="${AIRFLOW_HOME:-$(dirname $(dirname $(dirname $(dirname $(dirname "$ASCA_DIR")))))}"

echo "============================================"
echo "ASCA Spark Consumer Startup"
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

# Add AIRFLOW_HOME to PYTHONPATH
export PYTHONPATH="$AIRFLOW_HOME:$PYTHONPATH"

# Activate venv for initial Python execution
if [ -d "$VENV_DIR/bin" ]; then
    source "$VENV_DIR/bin/activate"
elif [ -d "$VENV_DIR/Scripts" ]; then
    source "$VENV_DIR/Scripts/activate"
fi

echo ""
echo "Starting ASCA Spark Consumer..."
echo "============================================"

# Check for --direct flag
if [ "$1" == "--direct" ]; then
    # Direct spark-submit (without launcher)
    SPARK_KAFKA_PACKAGE="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"
    POSTGRES_DRIVER_PACKAGE="org.postgresql:postgresql:42.7.1"
    
    spark-submit \
        --master local[*] \
        --packages "$SPARK_KAFKA_PACKAGE,$POSTGRES_DRIVER_PACKAGE" \
        --conf "spark.sql.streaming.checkpointLocation=/tmp/spark-checkpoints/asca" \
        "$ASCA_DIR/messaging/spark_consumer.py"
else
    # Use shared launcher (handles venv packaging)
    python -m projects.services.processing.tasks.asca.messaging.spark_consumer --use-launcher
fi
