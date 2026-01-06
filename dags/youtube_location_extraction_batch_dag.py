"""
YouTube to Location Extraction Batch DAG.

This DAG fetches YouTube comments that have been ingested but not yet processed
by location extraction, processes them in batch to maximize API efficiency.

Features:
- Joins youtube_comments with youtube_videos to get video titles
- Combines video title + comment text for better location context
- Source type: youtube_comment
- Source ID: comment_id
- Batch processing for API efficiency
- Uses the location_extraction venv with all required dependencies

Schedule: Every 30 minutes
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

# Define paths
AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")

# Location extraction service paths
LOCATION_EXTRACTION_ROOT = os.path.join(
    AIRFLOW_HOME, 
    "projects/services/processing/tasks/location_extraction"
)
SCRIPTS_PATH = os.path.join(LOCATION_EXTRACTION_ROOT, "scripts")
SETUP_SCRIPT = os.path.join(SCRIPTS_PATH, "setup_venv.sh")
BATCH_SCRIPT = os.path.join(SCRIPTS_PATH, "run_youtube_batch.sh")
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
    # LLM Configuration
    "LLM_PROVIDER": os.environ.get("LLM_PROVIDER", "google"),
    "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
    "LLM_MODEL_NAME": os.environ.get("LLM_MODEL_NAME", "gemini-2.5-flash-lite"),
}

with DAG(
    'youtube_location_extraction_batch_dag',
    default_args=default_args,
    description='Batch process YouTube comments for location extraction',
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['location_extraction', 'youtube', 'batch', 'llm'],
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
        dependencies from requirements.txt (includes SQLAlchemy, LangChain, etc.)
        """
    )

    # Task 2: Run YouTube Batch Processor
    # Fetches unprocessed YouTube comments and extracts locations
    run_batch_processor = BashOperator(
        task_id='run_youtube_batch_processor',
        bash_command=f"bash {BATCH_SCRIPT} ",
        env=batch_env,
        doc_md="""
        ### YouTube Batch Location Extraction
        
        This task:
        1. Queries youtube_comments joined with youtube_videos
        2. Finds comments NOT yet in location_extractions table
        3. Combines video title + comment for better context
        4. Extracts locations using LLM (with gazetteer/regex fallback)
        5. Saves results to location_extractions table
        
        Source identifiers:
        - source_type: youtube_comment
        - source_id: YouTube comment ID
        
        Text format: "[Video: {video_title}] {comment_text}"
        """
    )

    # Execution Flow
    setup_env >> run_batch_processor
