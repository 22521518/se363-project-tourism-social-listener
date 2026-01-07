from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

# Define paths
# Note: In standard Airflow Docker, dags are in /opt/airflow/dags.
# We need to reach the project scripts from there.
# Assuming proper volume mapping: /opt/airflow/projects refers to the projects folder.
# Adjust the path based on your actual volume mount in docker-compose.
# Here we assume standard relative path from airflow root.

# If running locally or in specific setup, using absolute path might be safer or ENV var.
# We will use a dynamically resolved path assuming the standard 'airflow' directory structure.
AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")
PRODUCER_SCRIPT = os.path.join(AIRFLOW_HOME, "projects/services/processing/tasks/traveling_type/scripts/run_spark_producer.sh")
CONSUMER_SCRIPT = os.path.join(AIRFLOW_HOME, "projects/services/processing/tasks/traveling_type/scripts/run_spark_consumer.sh")
SETUP_SCRIPT = os.path.join(AIRFLOW_HOME, "projects/services/processing/tasks/traveling_type/scripts/setup_venv.sh")
VENV_PATH = os.path.join(AIRFLOW_HOME, "projects/services/processing/tasks/traveling_type/.venv")


# Shared environment variables for all tasks
COMMON_ENV = {
    **os.environ,
    "VENV_DIR": VENV_PATH,
    "KAFKA_BOOTSTRAP_SERVERS": "kafka:9092",
    "KAFKA_TOPIC": "youtube-comments",
    "DB_HOST": "postgres",
    "DB_PORT": "5432",
    "DB_NAME": "airflow",
    "DB_USER": "airflow",
    "DB_PASSWORD": "airflow",
}

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'traveling_type_db_producer',
    default_args=default_args,
    description='Run unprocess traveling_type producer from DB to Kafka',
    schedule_interval=timedelta(minutes=60),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['traveling_type', 'db','unprocessed', 'producer'],
) as dag:

    # Task 0: Setup Environment
    # Creates/Updates the shared virtual environment
    setup_env = BashOperator(
        task_id='setup_env',
        bash_command=f"bash {SETUP_SCRIPT} {VENV_PATH} ",
    )
    
  

    # Task 2: Produce Unprocessed Comments to Kafka
    run_producer = BashOperator(
        task_id='produce_to_kafka',
        bash_command=f"bash {PRODUCER_SCRIPT} --run-once --batch-size 1000",
        env=COMMON_ENV,
    )

    # Execution Flow
    # Setup -> [Producer]
    setup_env >> run_producer 
