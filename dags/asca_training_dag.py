"""
ASCA Training DAG
==================
Airflow DAG to retrain the ASCA model using approved records.

This DAG:
1. Exports approved records from the database to CSV
2. Triggers training using the ASCA training pipeline
3. Compares new model performance with existing model
4. Updates model if new one is better
5. Saves training reports

Schedule: Weekly training runs.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

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
ASCA_SRC_DIR = "/opt/airflow/nlp/asca"  # Original ASCA source
EXPORT_DIR = "/opt/airflow/data/asca/exports"
MODELS_DIR = "/opt/airflow/models/asca"
REPORTS_DIR = "/opt/airflow/reports/asca"

# Environment variables
env_vars = {
    # Database
    "DB_HOST": "{{ var.value.get('DB_HOST', 'postgres') }}",
    "DB_PORT": "{{ var.value.get('DB_PORT', '5432') }}",
    "DB_USER": "{{ var.value.get('DB_USER', 'airflow') }}",
    "DB_PASSWORD": "{{ var.value.get('DB_PASSWORD', 'airflow') }}",
    "DB_NAME": "{{ var.value.get('DB_NAME', 'airflow') }}",
    
    # Paths
    "PYTHONPATH": "/opt/airflow",
    "ASCA_MODEL_PATH": f"{MODELS_DIR}/acsa.pkl",
}


def export_approved_records(**context):
    """Export approved records from database to CSV."""
    import sys
    sys.path.insert(0, "/opt/airflow")
    
    from projects.services.processing.tasks.asca.config.settings import DatabaseConfig
    from projects.services.processing.tasks.asca.dao.dao import ASCAExtractionDAO
    from projects.services.processing.tasks.asca.utils.export_utils import export_for_training
    import os
    
    # Create export directory
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    # Export
    db_config = DatabaseConfig.from_env()
    dao = ASCAExtractionDAO(db_config)
    
    result = export_for_training(
        dao,
        output_dir=EXPORT_DIR,
        train_ratio=0.8,
        val_ratio=0.1,
        test_ratio=0.1,
        limit=10000
    )
    
    print(f"Exported: {result}")
    context['ti'].xcom_push(key='export_result', value=result)
    
    return result


def compare_and_update_model(**context):
    """Compare new model with existing and update if better."""
    import os
    import json
    import shutil
    from datetime import datetime
    
    # Get training result from XCom
    ti = context['ti']
    eval_result = ti.xcom_pull(task_ids='train_model', key='eval_result')
    
    if not eval_result:
        print("No evaluation result found")
        return False
    
    new_f1 = eval_result.get('overall_f1', 0)
    
    # Load existing model's F1 score
    existing_report_path = f"{REPORTS_DIR}/current_report.json"
    existing_f1 = 0
    
    if os.path.exists(existing_report_path):
        with open(existing_report_path, 'r') as f:
            existing_report = json.load(f)
            existing_f1 = existing_report.get('overall_f1', 0)
    
    print(f"Existing model F1: {existing_f1}")
    print(f"New model F1: {new_f1}")
    
    # Update if new model is better
    if new_f1 > existing_f1:
        print("New model is better! Updating...")
        
        # Backup old model
        old_model_path = f"{MODELS_DIR}/acsa.pkl"
        if os.path.exists(old_model_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy(old_model_path, f"{MODELS_DIR}/acsa_backup_{timestamp}.pkl")
        
        # Copy new model
        new_model_path = f"{EXPORT_DIR}/new_model.pkl"
        if os.path.exists(new_model_path):
            shutil.copy(new_model_path, old_model_path)
        
        # Save new report as current
        os.makedirs(REPORTS_DIR, exist_ok=True)
        with open(existing_report_path, 'w') as f:
            json.dump(eval_result, f, indent=2)
        
        return True
    else:
        print("Existing model is better or equal. Keeping current model.")
        return False


# DAG definition
with DAG(
    dag_id="asca_training_dag",
    default_args=default_args,
    description="Retrain ASCA model with approved records",
    schedule_interval=timedelta(weeks=1),  # Weekly
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["asca", "training", "ml"],
) as dag:
    
    # Task 1: Export approved records to CSV
    export_records = PythonOperator(
        task_id="export_records",
        python_callable=export_approved_records,
    )
    
    # Task 2: Train model using ASCA training script
    train_model = BashOperator(
        task_id="train_model",
        bash_command=f"""
            echo "Training ASCA model..."
            
            cd {ASCA_SRC_DIR}
            
            # Check if training data exists
            if [ ! -f "{EXPORT_DIR}/train.csv" ]; then
                echo "No training data found. Skipping training."
                exit 0
            fi
            
            # Preprocess data
            python scripts/preprocess.py \\
                --input "{EXPORT_DIR}/train.csv" \\
                --output "{EXPORT_DIR}/train.pkl" \\
                --lang vi --overwrite
            
            python scripts/preprocess.py \\
                --input "{EXPORT_DIR}/val.csv" \\
                --output "{EXPORT_DIR}/val.pkl" \\
                --lang vi --overwrite
            
            # Train model
            python scripts/train.py \\
                --train "{EXPORT_DIR}/train.pkl" \\
                --val "{EXPORT_DIR}/val.pkl" \\
                --output "{EXPORT_DIR}/new_model.pkl"
            
            # Evaluate model
            python scripts/evaluate.py \\
                --model "{EXPORT_DIR}/new_model.pkl" \\
                --test "{EXPORT_DIR}/val.pkl" \\
                --output "{REPORTS_DIR}/new_eval_report.json"
            
            echo "Training complete!"
        """,
        env=env_vars,
    )
    
    # Task 3: Compare and update model
    compare_update = PythonOperator(
        task_id="compare_and_update",
        python_callable=compare_and_update_model,
    )
    
    # Set task dependencies
    export_records >> train_model >> compare_update
