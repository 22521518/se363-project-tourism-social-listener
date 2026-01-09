"""
ASCA Streaming Producer DAG
============================
Airflow DAG to run the YouTube streaming producer that reads comments
from the database and sends them to Kafka for ASCA processing.

Flow:
    [DB: youtube_comments] → [Streaming Producer] → [Kafka: asca-input]
                                                         ↓
                                           [ASCA Consumer (separate DAG)]
                                                         ↓
                                           [DB: asca_extractions]
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from airflow import DAG
from airflow.operators.bash import BashOperator

# Load environment from .env files
from dotenv import load_dotenv

# Load shared .env first, then module-specific
shared_env = Path("/opt/airflow/projects/.env")
asca_env = Path("/opt/airflow/projects/services/processing/tasks/asca/.env")

if shared_env.exists():
    load_dotenv(shared_env)
if asca_env.exists():
    load_dotenv(asca_env, override=True)

# Default arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Environment variables from .env
env_vars = {
    # Database
    "DB_HOST": os.getenv("DB_HOST", "postgres"),
    "DB_PORT": os.getenv("DB_PORT", "5432"),
    "DB_USER": os.getenv("DB_USER", "airflow"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD", "airflow"),
    "DB_NAME": os.getenv("DB_NAME", "airflow"),
    
    # Kafka
    "KAFKA_BOOTSTRAP_SERVERS": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    "KAFKA_TOPIC_ASCA_INPUT": os.getenv("KAFKA_TOPIC_ASCA_INPUT", "asca-input"),
    
    # Streaming settings
    "BATCH_SIZE": os.getenv("BATCH_SIZE", "100"),
    "CHECK_INTERVAL": os.getenv("CHECK_INTERVAL", "5"),
    
    # Paths
    "PYTHONPATH": "/opt/airflow",
}

# DAG definition
with DAG(
    dag_id="asca_streaming_producer_dag",
    default_args=default_args,
    description="Stream YouTube comments to Kafka for ASCA processing",
    schedule_interval=timedelta(hours=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["asca", "kafka", "streaming", "producer"],
) as dag:
    
    # Task 1: Install dependencies
    install_deps = BashOperator(
        task_id="install_deps",
        bash_command="""
            echo "Installing dependencies..."
            pip install --quiet pydantic pydantic-settings kafka-python-ng psycopg2-binary python-dotenv 2>/dev/null || true
            echo "Done!"
        """,
        env=env_vars,
    )
    
    # Task 2: Run streaming producer
    run_streaming_producer = BashOperator(
        task_id="run_streaming_producer",
        bash_command="""
            echo "Starting YouTube Streaming Producer for ASCA..."
            cd /opt/airflow
            python -m projects.services.processing.tasks.asca.streaming.youtube_streaming_producer --max-messages 500 --batch-size 100 --interval 5
            echo "Streaming producer run complete!"
        """,
        env=env_vars,
        execution_timeout=timedelta(minutes=30),
    )
    
    # Set task dependencies
    install_deps >> run_streaming_producer
