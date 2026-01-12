"""
YouTube NER Location Extraction Batch DAG.

This DAG fetches YouTube comments that have been ingested but not yet processed
by location extraction, processes them using NER model (Davlan/xlm-roberta-base-ner-hrl).

Features:
- Uses HuggingFace Transformers NER pipeline
- Model: Davlan/xlm-roberta-base-ner-hrl (multilingual)
- Extracts LOC entities from text
- No API key required (runs locally)

Schedule: Every 30 minutes
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables explicitly
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
NER_BATCH_SCRIPT = os.path.join(SCRIPTS_PATH, "run_youtube_ner_batch.sh")
VENV_PATH = os.path.join(LOCATION_EXTRACTION_ROOT, ".venv")

# Default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Environment variables for the batch processor
batch_env = {
    **os.environ,
    "VENV_DIR": VENV_PATH,
    # Database - use Docker service names
    "DB_HOST": "postgres",
    "DB_PORT": "5432",
    "DB_NAME": "airflow",
    "DB_USER": "airflow",
    "DB_PASSWORD": "airflow",
    # Batch processing settings
    "BATCH_SIZE": os.environ.get("BATCH_SIZE", "50"),
    "MAX_RECORDS": os.environ.get("MAX_RECORDS", "500"),
    # HuggingFace cache directory (optional)
    "HF_HOME": os.environ.get("HF_HOME", "/opt/airflow/.cache/huggingface"),
}

with DAG(
    'youtube_ner_location_extraction_dag',
    default_args=default_args,
    description='Batch process YouTube comments for location extraction using NER',
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['location_extraction', 'youtube', 'batch', 'ner', 'transformers'],
    doc_md=__doc__,
) as dag:

    # Task 1: Setup Environment
    # Creates/updates the virtual environment with all required dependencies
    setup_env = BashOperator(
        task_id='setup_env',
        bash_command=f"bash {SETUP_SCRIPT} {VENV_PATH} ",
        doc_md="""
        ### Setup Environment
        Creates or updates the Python virtual environment with all required 
        dependencies from requirements.txt (includes transformers, torch, etc.)
        """
    )

    # Task 2: Run YouTube NER Batch Processor
    # Fetches unprocessed YouTube comments and extracts locations using NER
    run_ner_batch_processor = BashOperator(
        task_id='run_youtube_ner_batch_processor',
        bash_command=f"bash {NER_BATCH_SCRIPT} ",
        env=batch_env,
        doc_md="""
        ### YouTube NER Batch Location Extraction
        
        This task:
        1. Queries youtube_comments joined with youtube_videos
        2. Finds comments NOT yet in location_extractions table
        3. Combines video title + comment for better context
        4. Extracts locations using NER (Davlan/xlm-roberta-base-ner-hrl)
        5. Saves results to location_extractions table
        
        Source identifiers:
        - source_type: youtube_comment
        - source_id: YouTube comment ID
        
        Output format:
        - locations: [{word, score, entity_group, start, end}, ...]
        
        Note: First run will download the model (~1GB). Subsequent runs use cache.
        """
    )

    # Execution Flow
    setup_env >> run_ner_batch_processor
