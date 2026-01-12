"""
ASCA Spark Consumer DAG
========================
Airflow DAG to run the ASCA extraction Spark Streaming consumer.

The Spark consumer:
1. Consumes messages from Kafka using Spark Structured Streaming
2. Processes text with ASCA pipeline in micro-batches
3. Saves results to PostgreSQL using foreachBatch
4. Scales for big data workloads

Schedule: Runs daily to process batch data.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Default arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

# Project paths
ASCA_PROJECT_DIR = "/opt/airflow/projects/services/processing/tasks/asca"

# Environment variables
env_vars = {
    # Database
    "DB_HOST": "{{ var.value.get('DB_HOST', 'postgres') }}",
    "DB_PORT": "{{ var.value.get('DB_PORT', '5432') }}",
    "DB_USER": "{{ var.value.get('DB_USER', 'airflow') }}",
    "DB_PASSWORD": "{{ var.value.get('DB_PASSWORD', 'airflow') }}",
    "DB_NAME": "{{ var.value.get('DB_NAME', 'airflow') }}",
    
    # Kafka
    "KAFKA_BOOTSTRAP_SERVERS": "{{ var.value.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092') }}",
    "KAFKA_TOPIC_ASCA_INPUT": "{{ var.value.get('KAFKA_TOPIC_ASCA_INPUT', 'asca-input') }}",
    "KAFKA_TOPIC_ASCA_OUTPUT": "{{ var.value.get('KAFKA_TOPIC_ASCA_OUTPUT', 'asca-output') }}",
    
    # ASCA
    "ASCA_MODEL_PATH": "{{ var.value.get('ASCA_MODEL_PATH', '/opt/airflow/models/asca/acsa.pkl') }}",
    "ASCA_LANGUAGE": "{{ var.value.get('ASCA_LANGUAGE', 'vi') }}",
    
    # Spark
    "SPARK_HOME": "{{ var.value.get('SPARK_HOME', '/opt/spark') }}",
    
    # Paths
    "PYTHONPATH": "/opt/airflow",
}

# DAG definition
with DAG(
    dag_id="asca_spark_consumer_dag",
    default_args=default_args,
    description="Run ASCA extraction Spark Streaming consumer",
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["asca", "kafka", "spark", "extraction"],
) as dag:
    
    # Task 1: Setup virtual environment
    setup_venv = BashOperator(
        task_id="setup_venv",
        bash_command=f"""
            echo "Setting up ASCA virtual environment..."
            cd {ASCA_PROJECT_DIR}
            chmod +x scripts/setup_venv.sh
            ./scripts/setup_venv.sh --no-vncorenlp
            echo "Setup complete!"
        """,
        env=env_vars,
    )
    
    # Task 2: Run Spark consumer
    run_spark_consumer = BashOperator(
        task_id="run_spark_consumer",
        bash_command=f"""
            echo "Starting ASCA Spark Streaming Consumer..."
            cd {ASCA_PROJECT_DIR}
            chmod +x scripts/run_spark_consumer.sh
            
            # Run for limited time in DAG context (timeout after 10 minutes)
            timeout 600 ./scripts/run_spark_consumer.sh || true
            
            echo "Spark consumer run complete!"
        """,
        env=env_vars,
        execution_timeout=timedelta(minutes=15),
    )
    
    # Set task dependencies
    setup_venv >> run_spark_consumer
