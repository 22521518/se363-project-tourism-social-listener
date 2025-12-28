#!/bin/bash
# Run Spark Consumer with Venv
# Usage: ./run_spark_consumer.sh
set -e

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Scripts -> YouTube
SERVICE_ROOT="$(dirname "$SCRIPT_DIR")"
# Airflow root: projects -> services -> processing -> tasks -> intention -> airflow
AIRFLOW_ROOT="$(dirname "$(dirname "$(dirname "$(dirname "$(dirname "$SERVICE_ROOT")")")")")"

# Use provided VENV_DIR or default
VENV_DIR="${VENV_DIR:-$SERVICE_ROOT/.venv_spark}"
CONSUMER_SCRIPT="$SERVICE_ROOT/consumer.py"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run setup_venv.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Create unique zip file to avoid Spark caching collisions
TIMESTAMP=$(date +%s)
export ZIP_FILE="projects_intention_extraction_spark_${TIMESTAMP}.zip"

echo "Zipping projects module (Intention Extraction Service only) into $ZIP_FILE..."
cd "$AIRFLOW_ROOT"

# Cleanup old zip files to save space
rm -f projects.zip projects_intention_extraction_spark_*.zip

# Python script to zip selectively
python3 - <<'EOF'
import zipfile
import os
import sys

def zip_service(zip_name, target_dir, root_dir):
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add parent __init__.py files if they exist (to maintain package structure)
        # We traverse up from target_dir to root_dir
        
        # Calculate relative path components
        rel_path = os.path.relpath(target_dir, root_dir)
        parts = rel_path.split(os.sep)
        
        current_path = root_dir
        # Add 'projects', 'projects/services', etc. init files
        # We only iterate up to the parent of the target, because the target's own init 
        # will be added by the os.walk loop below.
        for part in parts[:-1]:
            current_path = os.path.join(current_path, part)
            init_file = os.path.join(current_path, '__init__.py')
            if os.path.exists(init_file):
                arcname = os.path.relpath(init_file, root_dir)
                print(f'Adding {arcname}')
                zipf.write(init_file, arcname)

        # Add all files in the target directory
        print(f'Adding contents of {target_dir}...')
        for root, dirs, files in os.walk(target_dir):
            # Skip hidden files/dirs (like .venv, .git) and venv folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('venv', 'env', '__pycache__')]
            files = [f for f in files if not f.startswith('.') and not f.endswith('.pyc')]
            
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, root_dir)
                zipf.write(file_path, arcname)

# Target: projects/services/processing/tasks/intention
target_service = os.path.join(os.getcwd(), 'projects', 'services', 'processing','tasks', 'intention')
zip_filename = os.environ.get('ZIP_FILE', 'projects.zip')
zip_path = os.path.join(os.getcwd(), zip_filename)
zip_service(zip_path, target_service, os.getcwd())
print(f'Successfully created {zip_path}')
EOF

# Verify zip file was created
if [ ! -f "$AIRFLOW_ROOT/$ZIP_FILE" ]; then
    echo "ERROR: Failed to create zip file at $AIRFLOW_ROOT/$ZIP_FILE"
    exit 1
fi

echo "Zip file created successfully at: $AIRFLOW_ROOT/$ZIP_FILE"
ls -lh "$AIRFLOW_ROOT/$ZIP_FILE"

# Set Spark to use the venv python
export PYSPARK_PYTHON="$VENV_DIR/bin/python"
export PYSPARK_DRIVER_PYTHON="$VENV_DIR/bin/python"

# Spark Packages
# PySpark 4.0.1 uses Scala 2.13, so we need _2.13 versions
PACKAGES="org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.1,org.postgresql:postgresql:42.5.0"

echo "Starting Spark Consumer..."
echo "Zip file: $AIRFLOW_ROOT/$ZIP_FILE"
echo "Consumer script: $CONSUMER_SCRIPT"
echo "Arguments: $@"

# We pass the unique zip via --py-files so it's added to PYTHONPATH on driver and executors
# Forward all script arguments to the consumer script (e.g., --run-once)
spark-submit \
    --packages "$PACKAGES" \
    --py-files "$AIRFLOW_ROOT/$ZIP_FILE" \
    "$CONSUMER_SCRIPT" \
    "$@"

EXIT_CODE=$?

# Cleanup zip file after spark job completes
echo "Cleaning up zip file..."
rm -f "$AIRFLOW_ROOT/$ZIP_FILE"

exit $EXIT_CODE

