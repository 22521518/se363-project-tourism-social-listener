"""
Shared Spark Library for Tourism Social Listener
================================================

This module provides centralized Spark session management and utilities
for all Spark jobs across the project.

Usage:
    from projects.libs.spark import get_spark_session, SparkConfig
    
    spark = get_spark_session(app_name="my_app")
    # or with custom config
    config = SparkConfig(app_name="my_app", checkpoint_dir="/tmp/checkpoints")
    spark = get_spark_session(config=config)
"""

from .session import (
    SparkConfig,
    get_spark_session,
    get_or_create_spark_session,
    stop_spark_session,
)

from .launcher import (
    zip_venv,
    zip_code,
    launch_spark_job,
)

__all__ = [
    # Session management
    "SparkConfig",
    "get_spark_session",
    "get_or_create_spark_session",
    "stop_spark_session",
    # Launcher utilities
    "zip_venv",
    "zip_code", 
    "launch_spark_job",
]
