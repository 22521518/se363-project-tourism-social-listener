# Shared Spark Library

This module provides centralized Spark session management and utilities for all Spark jobs across the Tourism Social Listener project.

## Overview

The shared Spark library eliminates redundant PySpark configurations and provides:

- **Standardized Spark Session Management**: Single point of initialization for all Spark applications
- **Environment-Aware Configuration**: Automatic detection and configuration for local, Airflow, and cluster environments
- **Consistent Checkpointing**: Unified checkpoint directory management
- **Kafka/JDBC Utilities**: Helper functions for common data source connections
- **Launcher Utilities**: Tools for packaging and submitting Spark jobs

## Installation

The library is part of the project and doesn't require separate installation. Ensure your Python path includes the project root:

```python
import sys
sys.path.insert(0, "/opt/airflow")  # or your project root
```

## Quick Start

### Basic Usage

```python
from projects.libs.spark import get_spark_session

# Simple usage with app name
spark = get_spark_session(app_name="location_extraction")

# Use the spark session
df = spark.read.jdbc(...)
```

### Advanced Configuration

```python
from projects.libs.spark import get_spark_session, SparkConfig

# Create custom configuration
config = SparkConfig(
    app_name="my_app",
    checkpoint_dir="/custom/checkpoints",
    driver_memory="4g",
    executor_memory="4g",
    executor_cores=4,
    extra_configs={
        "spark.sql.shuffle.partitions": "200"
    }
)

# Get session with custom config
spark = get_spark_session(config=config)
```

## API Reference

### `get_spark_session()`

Main entry point for obtaining a Spark session.

**Parameters:**

- `app_name` (str, optional): Application name
- `config` (SparkConfig, optional): Full configuration object
- `environment` (str, optional): Override environment detection ("local", "airflow", "cluster")

**Returns:** `SparkSession`

### `SparkConfig`

Configuration dataclass for Spark session.

**Attributes:**

- `app_name`: Application name (default: "SparkApplication")
- `master`: Spark master URL (auto-detected if None)
- `checkpoint_dir`: Directory for streaming checkpoints
- `enable_hive`: Enable Hive support (default: False)
- `log_level`: Spark log level (default: "WARN")
- `driver_memory`: Driver memory (default: "2g")
- `executor_memory`: Executor memory (default: "2g")
- `executor_cores`: Executor cores (default: 2)
- `packages`: Maven packages (comma-separated)
- `extra_configs`: Additional Spark configurations (dict)

### Helper Functions

```python
from projects.libs.spark.session import get_jdbc_properties, get_kafka_options

# Get JDBC connection properties
jdbc_props = get_jdbc_properties(
    db_host="postgres",
    db_name="airflow"
)
# Returns: {'url': 'jdbc:postgresql://...', 'user': '...', 'password': '...', 'driver': '...'}

# Get Kafka options for Structured Streaming
kafka_opts = get_kafka_options(
    bootstrap_servers="kafka:9092",
    topic="my-topic",
    starting_offsets="earliest"
)
```

## Environment Detection

The library automatically detects the execution environment:

| Environment | Detection Method                 | Default Master               |
| ----------- | -------------------------------- | ---------------------------- |
| `local`     | No specific env vars             | `local[*]`                   |
| `airflow`   | `AIRFLOW_HOME` present           | `local[*]` or `SPARK_MASTER` |
| `cluster`   | `SPARK_HOME` + `HADOOP_CONF_DIR` | `yarn`                       |

## Checkpoint Management

Checkpoints are automatically managed per application:

```
/tmp/spark-checkpoints/              # local
/opt/airflow/spark-checkpoints/      # airflow
hdfs:///spark-checkpoints/           # cluster
    └── {app_name}/                  # per-application subdirectory
```

## Example: Batch Job

```python
#!/usr/bin/env python3
"""Example Spark batch job using shared library."""

import argparse
from projects.libs.spark import get_spark_session, SparkConfig

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_items_per_run", type=int, default=50000)
    args = parser.parse_args()

    # Get Spark session from shared library
    config = SparkConfig(
        app_name="MyBatchJob",
        packages="org.postgresql:postgresql:42.7.1"
    )
    spark = get_spark_session(config=config)

    try:
        # Your processing logic here
        df = spark.read.jdbc(...)
        # ...process data...
        df.write.jdbc(...)
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
```

## Example: Streaming Job

```python
#!/usr/bin/env python3
"""Example Spark streaming job using shared library."""

from projects.libs.spark import get_spark_session, SparkConfig
from projects.libs.spark.session import get_kafka_options

def main():
    config = SparkConfig(
        app_name="MyStreamingJob",
        packages="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"
    )
    spark = get_spark_session(config=config)

    kafka_opts = get_kafka_options(topic="my-input-topic")

    # Read from Kafka
    df = spark.readStream \
        .format("kafka") \
        .options(**kafka_opts) \
        .load()

    # Process and write
    query = df.writeStream \
        .foreachBatch(process_batch) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
```

## Integration with Airflow

The DAGs use `spark-submit` to run jobs that import this library:

```bash
spark-submit \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
    projects/services/processing/tasks/location_extraction/batch/spark_batch_job.py \
    --max_items_per_run 50000
```

The job script imports the shared library:

```python
from projects.libs.spark import get_spark_session
spark = get_spark_session(app_name="LocationExtractionBatch")
```

## Best Practices

1. **Always use the shared library** - Don't create SparkSession.builder manually
2. **Pass app_name** - Helps identify jobs in Spark UI
3. **Use environment detection** - Don't hardcode master URLs
4. **Clean up** - Call `spark.stop()` when done
5. **Use checkpoints** - For streaming jobs, let the library manage checkpoints

## Troubleshooting

### ImportError: No module named 'pyspark'

Ensure PySpark is installed in your environment:

```bash
pip install pyspark
```

### Cannot find driver org.postgresql.Driver

Add PostgreSQL driver to packages:

```python
config = SparkConfig(packages="org.postgresql:postgresql:42.7.1")
```

### Checkpoint location not set

The library sets checkpoints automatically. If you need a custom location:

```python
config = SparkConfig(checkpoint_dir="/my/custom/checkpoints")
```
