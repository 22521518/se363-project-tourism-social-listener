"""
Shared Configuration for Airflow DAGs
=====================================

This module provides shared configuration, environment variables, and utilities
for all Airflow DAGs in the project.

Usage:
    from dag_utils import get_spark_config, get_db_env, get_kafka_env
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# ============================================================================
# Load Environment Variables from .env file
# ============================================================================
AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")

def load_env_files():
    """Load .env files from multiple possible locations in order of priority."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Possible .env locations in order of priority:
    possible_paths = [
        # 1. projects/.env (most specific for services)
        os.path.join(project_root, "projects", ".env"),
        # 2. airflow root .env
        os.path.join(project_root, ".env"),
        # 3. Docker paths
        "/opt/airflow/projects/.env",
        "/opt/airflow/.env",
    ]
    
    loaded = False
    for env_path in possible_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            print(f"✅ DAG Utils: Loaded .env from: {env_path}")
            loaded = True
            break
    
    if not loaded:
        # Fallback to default dotenv search
        load_dotenv()
        print("⚠️ DAG Utils: Using default dotenv search")

load_env_files()

# ============================================================================
# Path Configuration
# ============================================================================

PROJECT_ROOT = os.path.join(AIRFLOW_HOME, "projects")
SERVICES_ROOT = os.path.join(PROJECT_ROOT, "services")
LIBS_ROOT = os.path.join(PROJECT_ROOT, "libs")

# Service paths
PROCESSING_TASKS = os.path.join(SERVICES_ROOT, "processing/tasks")
INGESTION_SERVICES = os.path.join(SERVICES_ROOT, "ingestion")

# Specific task paths
LOCATION_EXTRACTION_PATH = os.path.join(PROCESSING_TASKS, "location_extraction")
ASCA_PATH = os.path.join(PROCESSING_TASKS, "asca")
YOUTUBE_PATH = os.path.join(INGESTION_SERVICES, "youtube")
WEB_CRAWL_PATH = os.path.join(INGESTION_SERVICES, "web-crawl")

# Checkpoint paths
SPARK_CHECKPOINTS = os.path.join(AIRFLOW_HOME, "spark-checkpoints")

# ============================================================================
# Default Arguments
# ============================================================================

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": "timedelta(minutes=5)",  # Use string, eval in DAG
}

# ============================================================================
# Environment Variables
# ============================================================================

def get_db_env() -> Dict[str, str]:
    """Get database environment variables."""
    return {
        "DB_HOST": os.environ.get("DB_HOST", "postgres"),
        "DB_PORT": os.environ.get("DB_PORT", "5432"),
        "DB_NAME": os.environ.get("DB_NAME", "airflow"),
        "DB_USER": os.environ.get("DB_USER", "airflow"),
        "DB_PASSWORD": os.environ.get("DB_PASSWORD", "airflow"),
    }


def log_database_connection(logger=None, service_name: str = "Unknown") -> Dict[str, str]:
    """
    Log database connection information for debugging.
    
    Args:
        logger: Optional logger instance. If None, uses print.
        service_name: Name of the service for identification.
        
    Returns:
        The database environment dictionary.
    """
    db_env = get_db_env()
    
    # Build connection info (mask password)
    conn_info = f"postgresql://{db_env['DB_USER']}:****@{db_env['DB_HOST']}:{db_env['DB_PORT']}/{db_env['DB_NAME']}"
    
    log_lines = [
        "=" * 60,
        f"[{service_name}] Database Connection Info",
        "=" * 60,
        f"  Host    : {db_env['DB_HOST']}",
        f"  Port    : {db_env['DB_PORT']}",
        f"  Database: {db_env['DB_NAME']}",
        f"  User    : {db_env['DB_USER']}",
        f"  URL     : {conn_info}",
        "=" * 60,
    ]
    
    if logger:
        for line in log_lines:
            logger.info(line)
    else:
        for line in log_lines:
            print(line)
    
    return db_env


def get_db_connection_bash_command(service_name: str = "Service") -> str:
    """
    Generate a bash command to log database connection info.
    
    Args:
        service_name: Name of the service for identification.
        
    Returns:
        Bash command string that logs database connection details.
    """
    return f'''
echo "============================================================"
echo "[{service_name}] Database Connection Info"
echo "============================================================"
echo "  Host    : $DB_HOST"
echo "  Port    : $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User    : $DB_USER"
echo "  URL     : postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$DB_NAME"
echo "============================================================"
'''


def get_kafka_env() -> Dict[str, str]:
    """Get Kafka environment variables."""
    return {
        "KAFKA_BOOTSTRAP_SERVERS": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    }


def get_llm_env() -> Dict[str, str]:
    """Get LLM/API environment variables."""
    return {
        "LLM_PROVIDER": os.environ.get("LLM_PROVIDER", "google"),
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
        "LLM_MODEL_NAME": os.environ.get("LLM_MODEL_NAME", "gemini-2.5-flash-lite"),
    }


def get_spark_env() -> Dict[str, str]:
    """Get Spark environment variables."""
    return {
        "SPARK_HOME": os.environ.get("SPARK_HOME", "/opt/spark"),
        "PYTHONPATH": AIRFLOW_HOME,
        "PYSPARK_PYTHON": "python3",
        "PYSPARK_DRIVER_PYTHON": "python3",
    }


def get_full_env() -> Dict[str, str]:
    """Get all environment variables combined."""
    env = dict(os.environ)
    env.update(get_db_env())
    env.update(get_kafka_env())
    env.update(get_llm_env())
    env.update(get_spark_env())
    return env


# ============================================================================
# Spark Configuration
# ============================================================================

# Default Spark packages
SPARK_KAFKA_PACKAGE = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"
SPARK_POSTGRES_PACKAGE = "org.postgresql:postgresql:42.7.1"
SPARK_DEFAULT_PACKAGES = f"{SPARK_KAFKA_PACKAGE},{SPARK_POSTGRES_PACKAGE}"

# Default Spark configuration
SPARK_DEFAULT_CONFIG = {
    "spark.driver.memory": "2g",
    "spark.executor.memory": "2g",
    "spark.executor.cores": "2",
    "spark.sql.adaptive.enabled": "true",
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
}


def get_spark_submit_config(
    app_name: str,
    packages: str = SPARK_DEFAULT_PACKAGES,
    extra_config: Dict[str, str] = None,
) -> Dict[str, str]:
    """
    Get Spark submit configuration for SparkSubmitOperator.
    
    Args:
        app_name: Application name
        packages: Maven packages (comma-separated)
        extra_config: Additional Spark configurations
        
    Returns:
        Dictionary with Spark submit configuration
    """
    config = {
        "name": app_name,
        "packages": packages,
        **SPARK_DEFAULT_CONFIG,
    }
    
    if extra_config:
        config.update(extra_config)
    
    return config


# ============================================================================
# Batch Processing Configuration
# ============================================================================

# Default batch sizes
DEFAULT_MAX_ITEMS_PER_RUN = 50000
DEFAULT_BATCH_SIZE = 100

# Timeouts
SPARK_JOB_TIMEOUT_MINUTES = 60
