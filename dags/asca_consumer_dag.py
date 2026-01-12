"""
ASCA Consumer DAG
=================
Airflow DAG to run the ASCA extraction Kafka consumer.

The consumer:
1. Consumes messages from the asca-input Kafka topic
2. Processes text with ASCA pipeline (aspect-sentiment extraction)
3. Saves results to PostgreSQL
4. Produces output to asca-output topic

Schedule: Runs every 30 minutes.
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
    load_dotenv(asca_env, override=True)  # Module-specific overrides

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
    "KAFKA_TOPIC_ASCA_OUTPUT": os.getenv("KAFKA_TOPIC_ASCA_OUTPUT", "asca-output"),
    "KAFKA_CONSUMER_GROUP": os.getenv("KAFKA_CONSUMER_GROUP", "asca-consumer"),
    
    # ASCA
    "ASCA_MODEL_PATH": os.getenv("ASCA_MODEL_PATH", "/opt/airflow/models/asca/acsa.pkl"),
    "ASCA_LANGUAGE": os.getenv("ASCA_LANGUAGE", "vi"),
    
    # Paths
    "PYTHONPATH": "/opt/airflow",
}

# DAG definition
with DAG(
    dag_id="asca_consumer_dag",
    default_args=default_args,
    description="Run ASCA extraction Kafka consumer",
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["asca", "kafka", "extraction"],
) as dag:
    
    # Task 1: Install dependencies
    install_deps = BashOperator(
        task_id="install_deps",
        bash_command="""
            echo "Installing ASCA dependencies..."
            pip install --quiet pydantic pydantic-settings kafka-python-ng psycopg2-binary python-dotenv 2>/dev/null || true
            echo "Dependencies installed!"
        """,
        env=env_vars,
    )
    
    # Task 2: Run the consumer
    run_consumer = BashOperator(
        task_id="run_consumer",
        bash_command="""
            echo "Starting ASCA Kafka Consumer..."
            cd /opt/airflow
            python -m projects.services.processing.tasks.asca.messaging.consumer --max-messages 100
            echo "Consumer run complete!"
        """,
        env=env_vars,
    )
    
    # Set task dependencies
    install_deps >> run_consumer
