#!/bin/bash
# Run Web Crawl Spark Consumer (using shared libs/spark)
# Usage: ./run_spark_consumer.sh [args]
set -e

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(dirname "$SCRIPT_DIR")"
# airflow/projects/services/ingestion/web-crawl -> airflow
AIRFLOW_ROOT="$(dirname "$(dirname "$(dirname "$(dirname "$SERVICE_ROOT")")")")"

# Pass arguments to python script
ARGS="$@"

echo "Running Web Crawl Spark Consumer via Shared Library..."

python3 - <<EOF
import sys
import os

# Paths provided by Bash wrapper
airflow_root = r"$AIRFLOW_ROOT"
service_root = r"$SERVICE_ROOT"

# args passed from bash
args_str = r"$ARGS"
args = args_str.split(" ") if args_str else []

# Add airflow root to sys.path to allow importing 'projects.libs...'
if airflow_root not in sys.path:
    sys.path.insert(0, airflow_root)

try:
    from projects.libs.spark.launcher import launch_spark_job
except ImportError as e:
    print(f"Error importing spark launcher lib: {e}")
    sys.exit(1)

# Configuration
venv_dir = os.environ.get("VENV_DIR", os.path.join(service_root, ".venv"))
consumer_script = os.path.join(service_root, "kafka", "spark_consumer.py")
packages = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0"

# Launch
launch_spark_job(
    venv_dir=venv_dir,
    service_code_dir=service_root,
    project_root=airflow_root,
    consumer_script_path=consumer_script,
    packages=packages,
    args=args
)
EOF
