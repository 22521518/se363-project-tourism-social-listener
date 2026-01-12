"""
Spark Session Management
========================

Centralized Spark session creation and configuration for all Spark jobs.

This module provides:
- Environment-aware configuration (local / airflow / cluster)
- Consistent Spark session initialization
- Checkpoint management
- Logging configuration

Usage:
    from projects.libs.spark import get_spark_session
    
    # Simple usage
    spark = get_spark_session(app_name="location_extraction")
    
    # With custom config
    from projects.libs.spark import SparkConfig, get_spark_session
    config = SparkConfig(
        app_name="my_app",
        checkpoint_dir="/tmp/my-checkpoints",
        enable_hive=False
    )
    spark = get_spark_session(config=config)
"""

import os
import sys
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment detection
Environment = Literal["local", "airflow", "cluster"]


def detect_environment() -> Environment:
    """
    Detect the current execution environment.
    
    Returns:
        Environment: 'local', 'airflow', or 'cluster'
    """
    # Check for Airflow environment
    if os.getenv("AIRFLOW_HOME") or os.getenv("AIRFLOW__CORE__DAGS_FOLDER"):
        return "airflow"
    
    # Check for cluster environment (YARN, Kubernetes, etc.)
    if os.getenv("SPARK_HOME") and os.getenv("HADOOP_CONF_DIR"):
        return "cluster"
    
    # Check for Kubernetes
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return "cluster"
    
    return "local"


@dataclass
class SparkConfig:
    """
    Configuration for Spark session creation.
    
    Attributes:
        app_name: Name of the Spark application
        master: Spark master URL (auto-detected if not provided)
        checkpoint_dir: Directory for streaming checkpoints
        enable_hive: Whether to enable Hive support
        log_level: Spark log level (WARN, INFO, ERROR, DEBUG)
        extra_configs: Additional Spark configurations
        packages: Maven packages to include (comma-separated)
        jars: JAR files to include
    """
    app_name: str = "SparkApplication"
    master: Optional[str] = None
    checkpoint_dir: Optional[str] = None
    enable_hive: bool = False
    log_level: str = "WARN"
    extra_configs: Dict[str, str] = field(default_factory=dict)
    packages: Optional[str] = None
    jars: Optional[str] = None
    
    # Streaming configs
    streaming_trigger_interval: str = "30 seconds"
    streaming_watermark: str = "10 minutes"
    
    # Memory configs
    driver_memory: str = "2g"
    executor_memory: str = "2g"
    executor_cores: int = 2
    
    # Kafka configs (commonly used)
    kafka_packages: str = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"
    
    def get_master(self, environment: Environment) -> str:
        """Get Spark master URL based on environment."""
        if self.master:
            return self.master
        
        # Environment-specific defaults
        master_map = {
            "local": "local[*]",
            "airflow": os.getenv("SPARK_MASTER", "local[*]"),
            "cluster": os.getenv("SPARK_MASTER", "yarn"),
        }
        return master_map.get(environment, "local[*]")
    
    def get_checkpoint_dir(self, environment: Environment) -> str:
        """Get checkpoint directory based on environment."""
        if self.checkpoint_dir:
            return self.checkpoint_dir
        
        # Environment-specific defaults
        base_dirs = {
            "local": "/tmp/spark-checkpoints",
            "airflow": "/opt/airflow/spark-checkpoints",
            "cluster": "hdfs:///spark-checkpoints",
        }
        base = base_dirs.get(environment, "/tmp/spark-checkpoints")
        app_safe_name = self.app_name.replace(" ", "_").lower()
        return f"{base}/{app_safe_name}"


# Global session reference for singleton pattern
_spark_session = None


def get_spark_session(
    app_name: Optional[str] = None,
    config: Optional[SparkConfig] = None,
    environment: Optional[Environment] = None,
) -> "SparkSession":
    """
    Get or create a Spark session with standardized configuration.
    
    This is the primary entry point for obtaining a Spark session.
    It handles environment detection, configuration, and session management.
    
    Args:
        app_name: Application name (ignored if config is provided)
        config: Full SparkConfig object (optional)
        environment: Override environment detection (optional)
    
    Returns:
        SparkSession: Configured Spark session
    
    Example:
        # Simple usage
        spark = get_spark_session(app_name="location_extraction")
        
        # With config
        config = SparkConfig(app_name="asca", checkpoint_dir="/custom/path")
        spark = get_spark_session(config=config)
    """
    global _spark_session
    
    # Import PySpark (fail fast if not available)
    try:
        from pyspark.sql import SparkSession
    except ImportError as e:
        logger.error("PySpark is not available. Please install pyspark.")
        raise ImportError(
            "PySpark is required. Install with: pip install pyspark"
        ) from e
    
    # Build config if not provided
    if config is None:
        config = SparkConfig(app_name=app_name or "SparkApplication")
    
    # Detect environment
    env = environment or detect_environment()
    logger.info(f"Detected environment: {env}")
    
    # Get master and checkpoint dir
    master = config.get_master(env)
    checkpoint_dir = config.get_checkpoint_dir(env)
    
    logger.info(f"Creating Spark session: app={config.app_name}, master={master}")
    logger.info(f"Checkpoint directory: {checkpoint_dir}")
    
    # Build Spark session
    builder = SparkSession.builder \
        .appName(config.app_name) \
        .master(master)
    
    # Core configurations
    builder = builder \
        .config("spark.sql.streaming.checkpointLocation", checkpoint_dir) \
        .config("spark.driver.memory", config.driver_memory) \
        .config("spark.executor.memory", config.executor_memory) \
        .config("spark.executor.cores", str(config.executor_cores))
    
    # Streaming configurations
    builder = builder \
        .config("spark.sql.streaming.schemaInference", "true") \
        .config("spark.sql.adaptive.enabled", "true")
    
    # Serialization for better performance
    builder = builder \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    
    # Environment-specific configs
    if env == "airflow":
        # Airflow/Docker specific configs
        builder = builder \
            .config("spark.driver.host", os.getenv("SPARK_DRIVER_HOST", "localhost")) \
            .config("spark.driver.bindAddress", "0.0.0.0")
    
    # Add Kafka packages if needed
    if config.packages:
        builder = builder.config("spark.jars.packages", config.packages)
    elif config.kafka_packages:
        # Default Kafka packages for streaming jobs
        builder = builder.config("spark.jars.packages", config.kafka_packages)
    
    # Add custom JARs
    if config.jars:
        builder = builder.config("spark.jars", config.jars)
    
    # Apply extra configurations
    for key, value in config.extra_configs.items():
        builder = builder.config(key, value)
    
    # Enable Hive if requested
    if config.enable_hive:
        builder = builder.enableHiveSupport()
    
    # Get or create session
    spark = builder.getOrCreate()
    
    # Set log level
    spark.sparkContext.setLogLevel(config.log_level)
    
    # Store global reference
    _spark_session = spark
    
    logger.info(f"Spark session created successfully: {spark.sparkContext.applicationId}")
    
    return spark


def get_or_create_spark_session(
    app_name: str = "SparkApplication",
    **kwargs
) -> "SparkSession":
    """
    Convenience method to get or create a Spark session.
    
    This is an alias for get_spark_session() with keyword arguments.
    
    Args:
        app_name: Application name
        **kwargs: Additional arguments passed to SparkConfig
    
    Returns:
        SparkSession: Configured Spark session
    """
    config = SparkConfig(app_name=app_name, **kwargs)
    return get_spark_session(config=config)


def stop_spark_session():
    """
    Stop the current Spark session.
    
    Should be called when the application is done to clean up resources.
    """
    global _spark_session
    
    if _spark_session is not None:
        try:
            _spark_session.stop()
            logger.info("Spark session stopped successfully")
        except Exception as e:
            logger.warning(f"Error stopping Spark session: {e}")
        finally:
            _spark_session = None
    else:
        logger.debug("No active Spark session to stop")


# Database helper for JDBC connections
def get_jdbc_properties(
    db_host: str = None,
    db_port: int = None,
    db_name: str = None,
    db_user: str = None,
    db_password: str = None,
) -> Dict[str, str]:
    """
    Get JDBC connection properties for PostgreSQL.
    
    Args:
        db_host: Database host (defaults to env var DB_HOST)
        db_port: Database port (defaults to env var DB_PORT)
        db_name: Database name (defaults to env var DB_NAME)
        db_user: Database user (defaults to env var DB_USER)
        db_password: Database password (defaults to env var DB_PASSWORD)
    
    Returns:
        Dict with 'url', 'user', 'password', 'driver' keys
    """
    host = db_host or os.getenv("DB_HOST", "postgres")
    port = db_port or int(os.getenv("DB_PORT", "5432"))
    name = db_name or os.getenv("DB_NAME", "airflow")
    user = db_user or os.getenv("DB_USER", "airflow")
    password = db_password or os.getenv("DB_PASSWORD", "airflow")
    
    return {
        "url": f"jdbc:postgresql://{host}:{port}/{name}",
        "user": user,
        "password": password,
        "driver": "org.postgresql.Driver",
    }


def get_kafka_options(
    bootstrap_servers: str = None,
    topic: str = None,
    consumer_group: str = None,
    starting_offsets: str = "latest",
) -> Dict[str, str]:
    """
    Get Kafka options for Spark Structured Streaming.
    
    Args:
        bootstrap_servers: Kafka bootstrap servers
        topic: Kafka topic to subscribe to
        consumer_group: Consumer group ID
        starting_offsets: Starting offsets ('earliest', 'latest', or specific offsets)
    
    Returns:
        Dict with Kafka options
    """
    servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    
    options = {
        "kafka.bootstrap.servers": servers,
        "startingOffsets": starting_offsets,
        "failOnDataLoss": "false",
    }
    
    if topic:
        options["subscribe"] = topic
    
    if consumer_group:
        options["kafka.group.id"] = consumer_group
    
    return options
