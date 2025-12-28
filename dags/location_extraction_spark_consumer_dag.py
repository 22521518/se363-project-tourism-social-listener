from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

# Define paths
# In standard Airflow Docker, dags are in /opt/airflow/dags.
# We use AIRFLOW_HOME to dynamically resolve paths.
AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")
SCRIPTS_PATH = os.path.join(AIRFLOW_HOME, "projects/services/processing/tasks/location_extraction/scripts")
SETUP_SCRIPT = os.path.join(SCRIPTS_PATH, "setup_venv.sh")
SPARK_CONSUMER_SCRIPT = os.path.join(SCRIPTS_PATH, "run_spark_consumer.sh")
VENV_PATH = os.path.join(AIRFLOW_HOME, "projects/services/processing/tasks/location_extraction/.venv")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'location_extraction_spark_consumer_dag',
    default_args=default_args,
    description='Run Location Extraction Spark Streaming Consumer',
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['location_extraction', 'spark', 'consumer', 'kafka'],
) as dag:

    # Task 1: Setup Environment
    # Creates/Updates the shared virtual environment with Spark dependencies
    setup_env = BashOperator(
        task_id='setup_env',
        bash_command=f"bash {SETUP_SCRIPT} {VENV_PATH} ",
    )

    # Task 2: Run Spark Consumer
    # Uses spark-submit to run the Spark Streaming consumer
    # Consumes messages from Kafka, processes with LLM, saves to database
    # Environment variables for Docker connectivity
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
        "KAFKA_TOPIC_LOCATION_INPUT": "location-extraction-input",
        "KAFKA_TOPIC_LOCATION_OUTPUT": "location-extraction-output",
        "KAFKA_CONSUMER_GROUP": "location-extraction-consumer",
        # LLM Configuration
        "LLM_PROVIDER": os.environ.get("LLM_PROVIDER", "google"),
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
        "LLM_MODEL_NAME": os.environ.get("LLM_MODEL_NAME", "gemini-2.5-flash-lite"),
    }
    
    run_spark_consumer = BashOperator(
        task_id='run_spark_consumer',
        bash_command=f"bash {SPARK_CONSUMER_SCRIPT} ",
        env=consumer_env,
    )

    # Execution Flow
    # Setup -> Spark Consumer
    setup_env >> run_spark_consumer
