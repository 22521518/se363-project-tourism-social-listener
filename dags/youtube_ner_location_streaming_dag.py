"""
YouTube NER Location Extraction Streaming DAG.

This DAG combines batch processing with Kafka streaming:
1. Phase 1 (Batch): Process ALL unprocessed YouTube comments from database
2. Phase 2 (Streaming): Once caught up, consume new data from Kafka continuously

Features:
- Uses HuggingFace Transformers NER pipeline (Davlan/xlm-roberta-base-ner-hrl)
- Batch catch-up: Processes all historical data before switching to streaming
- Streaming: Runs indefinitely, consuming from Kafka topic
- No API key required (runs locally)

WARNING: This DAG runs indefinitely once started. It will only stop when:
- Manually stopped from Airflow UI
- Container/worker is restarted
- Error occurs (with retries configured)

Schedule: None (manual trigger only)
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

# Define paths
AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")

# Location extraction service paths
LOCATION_EXTRACTION_ROOT = os.path.join(
    AIRFLOW_HOME, 
    "projects/services/processing/tasks/location_extraction"
)
SCRIPTS_PATH = os.path.join(LOCATION_EXTRACTION_ROOT, "scripts")
SETUP_SCRIPT = os.path.join(SCRIPTS_PATH, "setup_venv.sh")
STREAMING_SCRIPT = os.path.join(SCRIPTS_PATH, "run_youtube_ner_streaming.sh")
VENV_PATH = os.path.join(LOCATION_EXTRACTION_ROOT, ".venv")

# Default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Environment variables for the streaming processor
streaming_env = {
    **os.environ,
    "VENV_DIR": VENV_PATH,
    # Database - use Docker service names
    "DB_HOST": os.environ.get("DB_HOST", "postgres"),
    "DB_PORT": os.environ.get("DB_PORT", "5432"),
    "DB_NAME": os.environ.get("DB_NAME", "airflow"),
    "DB_USER": os.environ.get("DB_USER", "airflow"),
    "DB_PASSWORD": os.environ.get("DB_PASSWORD", "airflow"),
    # Kafka - use Docker service names
    "KAFKA_BOOTSTRAP_SERVERS": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    "KAFKA_TOPIC_LOCATION_INPUT": os.environ.get("KAFKA_TOPIC_LOCATION_INPUT", "location-extraction-input"),
    "KAFKA_TOPIC_LOCATION_OUTPUT": os.environ.get("KAFKA_TOPIC_LOCATION_OUTPUT", "location-extraction-output"),
    "KAFKA_CONSUMER_GROUP": os.environ.get("KAFKA_CONSUMER_GROUP", "location-extraction-streaming"),
    # Batch processing settings
    "BATCH_SIZE": os.environ.get("BATCH_SIZE", "100"),
    # HuggingFace cache directory
    "HF_HOME": os.environ.get("HF_HOME", "/opt/airflow/.cache/huggingface"),
}

with DAG(
    'youtube_ner_location_streaming_dag',
    default_args=default_args,
    description='Combined batch + streaming location extraction for YouTube (runs indefinitely)',
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['location_extraction', 'youtube', 'streaming', 'ner', 'kafka', 'long-running'],
    doc_md=__doc__,
) as dag:

    # Task 1: Setup Environment
    setup_env = BashOperator(
        task_id='setup_env',
        bash_command=f"bash {SETUP_SCRIPT} {VENV_PATH} ",
        doc_md="""
        ### Setup Environment
        Creates or updates the Python virtual environment with all required 
        dependencies from requirements.txt (includes transformers, torch, kafka-python, etc.)
        """
    )

    # Task 2: Run Streaming Processor
    # This task runs indefinitely - combines batch catch-up with Kafka streaming
    run_streaming = BashOperator(
        task_id='run_streaming_processor',
        bash_command=f"bash {STREAMING_SCRIPT} ",
        env=streaming_env,
        execution_timeout=None,  # No timeout - runs indefinitely
        doc_md="""
        ### YouTube NER Streaming Processor
        
        **Phase 1 - Batch Catch-up:**
        - Queries youtube_comments joined with youtube_videos
        - Finds comments NOT yet in location_extractions table
        - Processes ALL unprocessed records (no limit)
        - Extracts locations using NER (Davlan/xlm-roberta-base-ner-hrl)
        
        **Phase 2 - Kafka Streaming:**
        - Once all historical data is processed, starts Kafka consumer
        - Consumes from `location-extraction-input` topic
        - Processes new messages in real-time
        - Runs indefinitely until manually stopped
        
        **Output:**
        - Saves results to `location_extractions` table
        - Produces output to `location-extraction-output` Kafka topic
        
        **Warning:** This task runs indefinitely. Stop manually via Airflow UI when needed.
        """
    )

    # Execution Flow
    setup_env >> run_streaming
