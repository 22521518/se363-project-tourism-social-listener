"""
Web Crawl Spark Consumer DAG - Airflow DAG for Spark-based web crawl processing.

Runs the web crawl service using Spark Structured Streaming to process
crawl requests from Kafka, perform crawling with LLM extraction,
and save results to PostgreSQL and JSON files.
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

# Paths
AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")
SERVICE_ROOT = os.path.join(AIRFLOW_HOME, "projects/services/ingestion/web-crawl")
SCRIPTS_PATH = os.path.join(SERVICE_ROOT, "scripts")
SETUP_SCRIPT = os.path.join(SCRIPTS_PATH, "setup_venv.sh")
SPARK_CONSUMER_SCRIPT = os.path.join(SCRIPTS_PATH, "run_spark_consumer.sh")
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
    'web_crawl_spark_consumer_dag',
    default_args=default_args,
    description='Run Web Crawl Spark Streaming Consumer',
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['webcrawl', 'ingestion', 'spark', 'consumer', 'kafka'],
) as dag:

    # Task 1: Setup Environment
    # Creates/Updates the shared virtual environment with Spark dependencies
    setup_env = BashOperator(
        task_id='setup_env',
        bash_command=f"bash {SETUP_SCRIPT} {VENV_PATH} ",
    )

    # Task 2: Run Spark Consumer
    # Uses spark-submit to run the Spark Streaming consumer
    # Consumes crawl requests from Kafka, performs crawling, saves to DB + JSON
    consumer_env = {
        **os.environ,
        "VENV_DIR": VENV_PATH,
        # Database - use Docker service names
        "DB_HOST": "postgres",
        "DB_PORT": "5432",
        "DB_NAME": "airflow",
        "DB_USER": "airflow",
        "DB_PASSWORD": "airflow",
        # Kafka - use Docker service name
        "KAFKA_BOOTSTRAP_SERVERS": "kafka:9092",
        # LLM Configuration
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
    }
    
    run_spark_consumer = BashOperator(
        task_id='run_spark_consumer',
        bash_command=f"bash {SPARK_CONSUMER_SCRIPT} ",
        env=consumer_env,
        execution_timeout=timedelta(minutes=25),  # Stop before next run
    )

    # Execution Flow
    # Setup -> Spark Consumer
    setup_env >> run_spark_consumer
