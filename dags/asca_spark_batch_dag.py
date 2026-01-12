"""
ASCA Extraction Batch DAG
=========================

Airflow DAG to orchestrate the ASCA (Aspect Category Sentiment Analysis) batch job.

This DAG:
1. Sets up the Python virtual environment
2. Runs the batch processor directly via PythonOperator
3. Processes YouTube comments for aspect-based sentiment analysis incrementally
4. Limits each run to 50,000 records for manageable batch sizes

Schedule: Every 30 minutes
Source: youtube_comments table
Target: asca_extractions table

Uses the BatchProcessor from projects/services/processing/tasks/asca/batch/
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
import os
import sys
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
ASCA_PATH = os.path.join(PROJECT_ROOT, "services/processing/tasks/asca")
SETUP_SCRIPT = os.path.join(ASCA_PATH, "scripts/setup_venv.sh")
VENV_PATH = os.path.join(ASCA_PATH, ".venv")

# Model paths
ASCA_MODEL_PATH = os.path.join(AIRFLOW_HOME, "models/asca/acsa.pkl")

# Batch configuration
MAX_RECORDS = 50000
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
    env_dict = {
        **os.environ,
        "PYTHONPATH": AIRFLOW_HOME,
        # Database
        "DB_HOST": os.environ.get("DB_HOST", "postgres"),
        "DB_PORT": os.environ.get("DB_PORT", "5432"),
        "DB_NAME": os.environ.get("DB_NAME", "airflow"),
        "DB_USER": os.environ.get("DB_USER", "airflow"),
        "DB_PASSWORD": os.environ.get("DB_PASSWORD", "airflow"),
        # ASCA Configuration
        "ASCA_MODEL_PATH": ASCA_MODEL_PATH,
        "ASCA_LANGUAGE": os.environ.get("ASCA_LANGUAGE", "vi"),
    }
    logger = logging.getLogger(__name__)
    logger.info("Environment variables: %s", env_dict)

    return env_dict

# ============================================================================
# Python Callable
# ============================================================================

def run_asca_batch_processor(**context):
    """
    Run the ASCA batch processor.
    
    This function imports and runs the BatchProcessor from the ASCA service.
    """
    logger = logging.getLogger(__name__)
    
    # Ensure project root is in path
    if AIRFLOW_HOME not in sys.path:
        sys.path.insert(0, AIRFLOW_HOME)
    
    # Set environment variables
    os.environ["ASCA_MODEL_PATH"] = ASCA_MODEL_PATH
    
    # Log database connection info for debugging
    log_database_connection(logger=logger, service_name="ASCA Batch")
    
    logger.info("=" * 60)
    logger.info("Starting ASCA Batch Extraction")
    logger.info("=" * 60)
    logger.info(f"Max Records: {MAX_RECORDS}")
    logger.info(f"Batch Size: {BATCH_SIZE}")
    logger.info(f"Model Path: {ASCA_MODEL_PATH}")
    
    try:
        # Import the BatchProcessor
        from projects.services.processing.tasks.asca.batch.batch_processor import BatchProcessor
        
        # Create and run the processor
        processor = BatchProcessor(
            batch_size=BATCH_SIZE,
            max_records=MAX_RECORDS
        )
        
        stats = processor.run()
        
        logger.info("=" * 60)
        logger.info("ASCA Batch Job Complete")
        logger.info("=" * 60)
        logger.info(f"Total Fetched: {stats.get('total_fetched', 0)}")
        logger.info(f"Total Successful: {stats.get('total_successful', 0)}")
        logger.info(f"Total Failed: {stats.get('total_failed', 0)}")
        logger.info(f"Duration: {stats.get('duration_seconds', 0)} seconds")
        
        # Push stats to XCom for downstream tasks
        context['ti'].xcom_push(key='batch_stats', value=stats)
        
        # Raise if all records failed
        if stats.get('total_fetched', 0) > 0 and stats.get('total_successful', 0) == 0:
            raise RuntimeError("All records failed to process")
        
        return stats
        
    except ImportError as e:
        logger.error(f"Failed to import BatchProcessor: {e}")
        raise
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise

# DAG Definition
# ============================================================================

# Spark configuration
SPARK_PACKAGES = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1"
SPARK_BATCH_JOB = os.path.join(ASCA_PATH, "batch/spark_batch_job.py")

with DAG(
    dag_id="asca_spark_batch_dag",
    default_args=default_args,
    description="Run ASCA Extraction Spark Batch Job - Incremental Processing",
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,  # Only one run at a time
    tags=["asca", "spark", "batch", "incremental", "sentiment"],
    doc_md=__doc__,
) as dag:

    # ========================================================================
    # Task 1: Check Spark and Dependencies
    # ========================================================================
    check_deps = BashOperator(
        task_id="check_dependencies",
        bash_command=f"""
            echo "Checking ASCA Spark dependencies..."
            echo "Python version: $(python3 --version)"
            echo "ASCA module path: {ASCA_PATH}"
            echo "Spark batch job: {SPARK_BATCH_JOB}"
            
            # Check if spark-submit is available
            if command -v spark-submit &> /dev/null; then
                echo "✅ spark-submit is available"
                spark-submit --version 2>&1 | head -5
            else
                echo "⚠️  spark-submit not found in PATH"
            fi
            
            # Verify key imports are available
            python3 -c "import pyspark; import sqlalchemy; import pydantic; print('✅ Core dependencies available')" || {{
                echo "⚠️  Some dependencies may be missing"
            }}
            
            echo "Dependency check complete!"
        """,
        env=get_env_vars(),
    )

    # ========================================================================
    # Task 2: Verify Model Exists
    # ========================================================================
    verify_model = BashOperator(
        task_id="verify_model",
        bash_command=f"""
            echo "Verifying ASCA model..."
            
            if [ -f {ASCA_MODEL_PATH} ]; then
                echo "✅ Model found at {ASCA_MODEL_PATH}"
                ls -lh {ASCA_MODEL_PATH}
            else
                echo "⚠️  Warning: Model not found at {ASCA_MODEL_PATH}"
                echo "The job may use default/fallback model"
            fi
        """,
        env=get_env_vars(),
    )

    # ========================================================================
    # Task 3: Run Spark Batch Job (spark-submit)
    # ========================================================================
    run_spark_batch = BashOperator(
        task_id="run_spark_batch_job",
        bash_command=f"""
            echo "=============================================="
            echo "Starting ASCA Spark Batch Job"
            echo "=============================================="
            echo "Max Records: {MAX_RECORDS}"
            echo "Batch Size: {BATCH_SIZE}"
            echo "Model Path: {ASCA_MODEL_PATH}"
            echo "Spark Job: {SPARK_BATCH_JOB}"
            echo "=============================================="
            
            # Run spark-submit
            spark-submit \
                --master local[*] \
                --packages {SPARK_PACKAGES} \
                --conf "spark.driver.memory=2g" \
                --conf "spark.executor.memory=2g" \
                --conf "spark.sql.adaptive.enabled=true" \
                {SPARK_BATCH_JOB} \
                --max_items_per_run {MAX_RECORDS} \
                --batch_size {BATCH_SIZE} \
                --environment airflow
            
            echo "=============================================="
            echo "Spark job completed!"
            echo "=============================================="
        """,
        env=get_env_vars(),
        execution_timeout=timedelta(minutes=120),
    )

    # ========================================================================
    # Task 4: Log Job Summary
    # ========================================================================
    def log_job_summary(**context):
        """Log job execution summary."""
        dag_run = context['dag_run']
        
        print("=" * 60)
        print("ASCA Extraction Spark Batch Job Summary")
        print("=" * 60)
        print(f"DAG Run ID: {dag_run.run_id}")
        print(f"Execution Date: {context['execution_date']}")
        print(f"Max Records: {MAX_RECORDS}")
        print(f"Batch Size: {BATCH_SIZE}")
        print(f"Model Path: {ASCA_MODEL_PATH}")
        print("-" * 60)
        print("Check spark-submit logs above for detailed processing stats.")
        print("=" * 60)
    
    log_summary = PythonOperator(
        task_id="log_summary",
        python_callable=log_job_summary,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    # ========================================================================
    # Task Dependencies
    # ========================================================================
    check_deps >> verify_model >> run_spark_batch >> log_summary

