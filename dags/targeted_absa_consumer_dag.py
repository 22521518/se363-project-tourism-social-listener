from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")

SCRIPTS_PATH = os.path.join(AIRFLOW_HOME, "projects/services/processing/tasks/targeted_absa/scripts")
SETUP_SCRIPT = os.path.join(SCRIPTS_PATH, "setup_venv.sh")
SPARK_CONSUMER_SCRIPT = os.path.join(SCRIPTS_PATH, "run_spark_consumer.sh")
VENV_PATH = os.path.join(AIRFLOW_HOME, "projects/services/processing/tasks/targeted_absa/.venv_unified")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'targeted_absa_consumer_dag',
    default_args=default_args,
    description='Run Targeted ABSA Spark Consumer',
    schedule_interval=timedelta(minutes=15),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['absa', 'sentiment', 'spark'],
) as dag:

    setup_env = BashOperator(
        task_id='setup_env',
        bash_command=f"bash {SETUP_SCRIPT} {VENV_PATH}",
    )

    run_spark_consumer = BashOperator(
        task_id='run_spark_consumer',
        bash_command=f"bash {SPARK_CONSUMER_SCRIPT}",
        env={
            **os.environ, 
            "VENV_DIR": VENV_PATH,
            "KAFKA_BOOTSTRAP_SERVERS": "kafka:9092",
            "DB_HOST": "postgres"
        },
    )

    setup_env >> run_spark_consumer