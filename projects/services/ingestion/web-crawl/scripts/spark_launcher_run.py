#!/usr/bin/env python3
"""
Spark Launcher Runner - CLI wrapper for projects/libs/spark/launcher.py

Launches spark-submit with proper venv/code packaging.
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Launch Spark job with venv/code packaging")
    parser.add_argument("--venv-dir", required=True, help="Path to virtual environment")
    parser.add_argument("--service-dir", required=True, help="Path to service code directory")
    parser.add_argument("--project-root", required=True, help="Path to project root (airflow)")
    parser.add_argument("--consumer-script", required=True, help="Path to consumer script")
    parser.add_argument("--packages", required=True, help="Maven packages for spark-submit")
    parser.add_argument("extra_args", nargs="*", help="Additional arguments to pass to consumer script")
    
    args = parser.parse_args()
    
    # Add libs/spark to path
    libs_spark = Path(args.project_root) / "projects" / "libs" / "spark"
    sys.path.insert(0, str(libs_spark))
    
    from launcher import launch_spark_job
    
    launch_spark_job(
        venv_dir=args.venv_dir,
        service_code_dir=args.service_dir,
        project_root=args.project_root,
        consumer_script_path=args.consumer_script,
        packages=args.packages,
        args=args.extra_args or [],
    )


if __name__ == "__main__":
    main()
