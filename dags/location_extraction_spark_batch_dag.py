"""
Location Extraction Spark Batch DAG
===================================

Airflow DAG to orchestrate the Location Extraction Spark batch job.

This DAG:
1. Sets up the Python virtual environment
2. Runs the Spark batch job using spark-submit
3. Processes YouTube comments for location extraction incrementally
4. Limits each run to 50,000 records for manageable batch sizes

Schedule: Every 30 minutes
Source: youtube_comments table
Target: location_extractions table

The Spark job uses the shared library at projects/libs/spark for:
- Standardized Spark session management
- Environment-aware configuration
- Consistent logging and checkpointing
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

# Import shared utilities
from dag_utils import get_db_env, log_database_connection

# ============================================================================
# Configuration
# ============================================================================

AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")
PROJECT_ROOT = os.path.join(AIRFLOW_HOME, "projects")

# Service paths
LOCATION_EXTRACTION_PATH = os.path.join(
    PROJECT_ROOT, "services/processing/tasks/location_extraction"
)
SPARK_BATCH_JOB = os.path.join(
    LOCATION_EXTRACTION_PATH, "batch/spark_batch_job.py"
)
SETUP_SCRIPT = os.path.join(LOCATION_EXTRACTION_PATH, "scripts/setup_venv.sh")
VENV_PATH = os.path.join(LOCATION_EXTRACTION_PATH, ".venv")

# Spark configuration
SPARK_PACKAGES = (
    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
    "org.postgresql:postgresql:42.7.1"
)
CHECKPOINT_DIR = os.path.join(AIRFLOW_HOME, "spark-checkpoints/location-extraction-batch")

# Batch configuration
MAX_ITEMS_PER_RUN = 50000
BATCH_SIZE = 100

# ============================================================================
# Default Arguments
# ============================================================================

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# ============================================================================
# Environment Variables
# ============================================================================

def get_env_vars():
    """Get environment variables for the job."""
    return {
        **os.environ,
        "PYTHONPATH": AIRFLOW_HOME,
        # Database
        "DB_HOST": os.environ.get("DB_HOST", "postgres"),
        "DB_PORT": os.environ.get("DB_PORT", "5432"),
        "DB_NAME": os.environ.get("DB_NAME", "airflow"),
        "DB_USER": os.environ.get("DB_USER", "airflow"),
        "DB_PASSWORD": os.environ.get("DB_PASSWORD", "airflow"),
        # LLM Configuration (for location extraction)
        "LLM_PROVIDER": os.environ.get("LLM_PROVIDER", "google"),
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
        "LLM_MODEL_NAME": os.environ.get("LLM_MODEL_NAME", "gemini-2.5-flash-lite"),
        # Spark
        "SPARK_HOME": os.environ.get("SPARK_HOME", "/opt/spark"),
        "PYSPARK_PYTHON": "python3",
        "PYSPARK_DRIVER_PYTHON": "python3",
    }

# ============================================================================
# DAG Definition
# ============================================================================

with DAG(
    dag_id="location_extraction_spark_batch_dag",
    default_args=default_args,
    description="Run Location Extraction Spark Batch Job - Incremental Processing",
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,  # Only one run at a time
    tags=["location_extraction", "spark", "batch", "incremental"],
    doc_md=__doc__,
) as dag:

    # ========================================================================
    # Task 1: Setup Virtual Environment
    # ========================================================================
    setup_venv = BashOperator(
        task_id="setup_venv",
        bash_command=f"""
            echo "Setting up Location Extraction virtual environment..."
            cd {LOCATION_EXTRACTION_PATH}
            
            if [ -f scripts/setup_venv.sh ]; then
                chmod +x scripts/setup_venv.sh
                ./scripts/setup_venv.sh {VENV_PATH}
            else
                # Fallback: create venv if script doesn't exist
                if [ ! -d {VENV_PATH} ]; then
                    python3 -m venv {VENV_PATH}
                fi
                source {VENV_PATH}/bin/activate
                pip install -q -r requirements.txt
            fi
            
            echo "Virtual environment setup complete!"
        """,
        env=get_env_vars(),
    )

    # ========================================================================
    # Task 2: Run Spark Batch Job
    # ========================================================================
    # Using BashOperator with spark-submit command
    # This is more flexible than SparkSubmitOperator for custom configurations
    
    spark_submit_cmd = f"""
        echo "Starting Location Extraction Spark Batch Job..."
        echo "Max items per run: {MAX_ITEMS_PER_RUN}"
        echo "Batch size: {BATCH_SIZE}"
        
        # Ensure checkpoint directory exists
        mkdir -p {CHECKPOINT_DIR}
        
        # Run spark-submit
        spark-submit \
            --master local[*] \
            --packages {SPARK_PACKAGES} \
            --conf spark.driver.memory=2g \
            --conf spark.executor.memory=2g \
            --conf spark.sql.adaptive.enabled=true \
            --conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
            --conf spark.driver.extraJavaOptions="-Dlog4j.configuration=file://$SPARK_HOME/conf/log4j2.properties" \
            {SPARK_BATCH_JOB} \
            --max_items_per_run {MAX_ITEMS_PER_RUN} \
            --batch_size {BATCH_SIZE} \
            --checkpoint_dir {CHECKPOINT_DIR} \
            --environment airflow
        
        echo "Spark job completed!"
    """
    
    run_spark_batch = BashOperator(
        task_id="run_spark_batch",
        bash_command=spark_submit_cmd,
        env=get_env_vars(),
        execution_timeout=timedelta(minutes=60),
    )

    # ========================================================================
    # Task 3: Log Job Summary
    # ========================================================================
    def log_job_summary(**context):
        """Log job execution summary with database connection info."""
        logger = logging.getLogger(__name__)
        ti = context['ti']
        dag_run = context['dag_run']
        
        # Log database connection info for debugging
        log_database_connection(logger=logger, service_name="Location Extraction Batch")
        
        print("=" * 60)
        print("Location Extraction Batch Job Summary")
        print("=" * 60)
        print(f"DAG Run ID: {dag_run.run_id}")
        print(f"Execution Date: {context['execution_date']}")
        print(f"Max Items: {MAX_ITEMS_PER_RUN}")
        print(f"Batch Size: {BATCH_SIZE}")
        print("=" * 60)
    
    log_summary = PythonOperator(
        task_id="log_summary",
        python_callable=log_job_summary,
        trigger_rule=TriggerRule.ALL_DONE,  # Run even if upstream failed
    )

    # ========================================================================
    # Task Dependencies
    # ========================================================================
    setup_venv >> run_spark_batch >> log_summary
