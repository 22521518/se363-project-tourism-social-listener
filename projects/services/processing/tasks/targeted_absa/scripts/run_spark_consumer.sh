#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(dirname "$SCRIPT_DIR")"
AIRFLOW_ROOT="$(dirname "$(dirname "$(dirname "$(dirname "$(dirname "$SERVICE_ROOT")")")")")"

VENV_DIR="${VENV_DIR:-$SERVICE_ROOT/.venv_unified}"
CONSUMER_SCRIPT="$SERVICE_ROOT/consumer.py"

source "$VENV_DIR/bin/activate"

# Tạo zip file chứa code task của bạn để Spark thấy
TIMESTAMP=$(date +%s)
ZIP_FILE="projects_targeted_absa_${TIMESTAMP}.zip"

cd "$AIRFLOW_ROOT"
rm -f projects_targeted_absa_*.zip

python3 - <<'EOF'
import zipfile
import os

target = "projects/services/processing/tasks/targeted_absa"
zip_name = os.environ['ZIP_FILE']

with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', '.venv')]
        for f in files:
            if not f.startswith('.') and not f.endswith('.pyc'):
                file_path = os.path.join(root, f)
                arcname = os.path.relpath(file_path, os.getcwd())
                z.write(file_path, arcname)
print(f"Created {zip_name}")
EOF

export PYSPARK_PYTHON="$VENV_DIR/bin/python"
export PYSPARK_DRIVER_PYTHON="$VENV_DIR/bin/python"

# Packages cần thiết (có thể thêm nếu bạn cần huggingface hub, torch, v.v.)

PACKAGES="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.5.0"

spark-submit \
    --packages "$PACKAGES" \
    --py-files "$AIRFLOW_ROOT/$ZIP_FILE" \
    "$CONSUMER_SCRIPT" \
    "$@"

rm -f "$AIRFLOW_ROOT/$ZIP_FILE"