"""
Web Crawl Consumer DAG - Airflow DAG for web crawl ingestion.

Runs the web crawl service to process pending crawl requests.
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

# Paths
AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")
SERVICE_ROOT = os.path.join(AIRFLOW_HOME, "projects/services/ingestion/web-crawl")
SETUP_SCRIPT = os.path.join(SERVICE_ROOT, "scripts/setup_venv.sh")
SERVICE_SCRIPT = os.path.join(SERVICE_ROOT, "scripts/run_crawl_service.sh")
VENV_PATH = os.path.join(SERVICE_ROOT, ".venv")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'web_crawl_consumer',
    default_args=default_args,
    description='Run Web Crawl Service (Kafka Consumer mode)',
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['webcrawl', 'ingestion', 'consumer'],
) as dag:
    
    # Task 0: Setup Environment
    setup_env = BashOperator(
        task_id='setup_env',
        bash_command=f"bash {SETUP_SCRIPT} {VENV_PATH}",
    )
    
    # Task 1: Run Consumer (processes crawl requests from Kafka)
    run_consumer = BashOperator(
        task_id='run_consumer',
        bash_command=f"bash {SERVICE_SCRIPT} --consume",
        env={
            **os.environ,
            "VENV_DIR": VENV_PATH,
            "KAFKA_BOOTSTRAP_SERVERS": "kafka:9092",
            "DB_HOST": "postgres",
        },
        execution_timeout=timedelta(minutes=25),  # Stop before next run
    )
    
    # Execution flow
    setup_env >> run_consumer
