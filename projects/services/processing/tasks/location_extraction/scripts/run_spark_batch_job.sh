#!/bin/bash
# ============================================================================
# Location Extraction Spark Batch Job Runner
# ============================================================================
# 
# This script runs the Location Extraction Spark batch job.
# It uses the shared Spark library for session management.
#
# Usage:
#   ./run_spark_batch_job.sh [OPTIONS]
#
# Options:
#   --max_items_per_run N   Maximum records to process (default: 50000)
#   --batch_size N          Records per batch (default: 100)
#   --environment ENV       local/airflow/cluster (default: auto-detect)
#
# Environment Variables:
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD - Database config
#   LLM_PROVIDER, GOOGLE_API_KEY - LLM configuration
#   SPARK_HOME - Spark installation path
#
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(cd "$TASK_DIR/../../../../.." && pwd)"

# Default values
MAX_ITEMS_PER_RUN=${MAX_ITEMS_PER_RUN:-50000}
BATCH_SIZE=${BATCH_SIZE:-100}
ENVIRONMENT=${ENVIRONMENT:-""}
CHECKPOINT_DIR=${CHECKPOINT_DIR:-"/tmp/spark-checkpoints/location-extraction-batch"}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --max_items_per_run)
            MAX_ITEMS_PER_RUN="$2"
            shift 2
            ;;
        --batch_size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --checkpoint_dir)
            CHECKPOINT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --max_items_per_run N   Maximum records to process (default: 50000)"
            echo "  --batch_size N          Records per batch (default: 100)"
            echo "  --environment ENV       local/airflow/cluster"
            echo "  --checkpoint_dir PATH   Checkpoint directory"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=============================================="
echo "Location Extraction Spark Batch Job"
echo "=============================================="
echo "Project Root: $PROJECT_ROOT"
echo "Task Directory: $TASK_DIR"
echo "Max Items Per Run: $MAX_ITEMS_PER_RUN"
echo "Batch Size: $BATCH_SIZE"
echo "Checkpoint Dir: $CHECKPOINT_DIR"
echo "=============================================="

# Set up Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Ensure checkpoint directory exists
mkdir -p "$CHECKPOINT_DIR"

# Activate virtual environment if exists
VENV_PATH="$TASK_DIR/.venv"
if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
fi

# Build spark-submit arguments
SPARK_ARGS=(
    --master "local[*]"
    --packages "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1"
    --conf "spark.driver.memory=2g"
    --conf "spark.executor.memory=2g"
    --conf "spark.sql.adaptive.enabled=true"
)

JOB_ARGS=(
    --max_items_per_run "$MAX_ITEMS_PER_RUN"
    --batch_size "$BATCH_SIZE"
    --checkpoint_dir "$CHECKPOINT_DIR"
)

if [ -n "$ENVIRONMENT" ]; then
    JOB_ARGS+=(--environment "$ENVIRONMENT")
fi

# Run spark-submit
echo "Running spark-submit..."
spark-submit "${SPARK_ARGS[@]}" \
    "$TASK_DIR/batch/spark_batch_job.py" \
    "${JOB_ARGS[@]}"

echo "=============================================="
echo "Job completed!"
echo "=============================================="
