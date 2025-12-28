
import os
import sys
import shutil
import zipfile
import subprocess
import time
from typing import List, Optional

def zip_venv(venv_dir: str, zip_path: str):
    """Zips the virtual environment directory."""
    print(f"Zipping Venv {venv_dir} -> {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(venv_dir):
            for f in files:
                abs_file = os.path.join(root, f)
                # content at root of zip
                arcname = os.path.relpath(abs_file, venv_dir)
                z.write(abs_file, arcname)

def zip_code(source_dir: str, zip_path: str, project_root: str):
    """
    Zips the source code preserving the package structure relative to project_root.
    Also includes __init__.py files from project_root down to source_dir.
    """
    print(f"Zipping Code {source_dir} -> {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        
        # 1. Add __init__.py files from root down to target
        target_rel = os.path.relpath(source_dir, project_root)
        parts = target_rel.split(os.sep)
        
        curr = project_root
        for p in parts:
            curr = os.path.join(curr, p)
            init = os.path.join(curr, "__init__.py")
            if os.path.exists(init):
                 z.write(init, os.path.relpath(init, project_root))
        
        # 2. Add contents of source_dir
        for root, dirs, files in os.walk(source_dir):
            # Exclude unwanted directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('venv', 'env', '__pycache__', 'streamlit', 'examples', '.venv')]
            files = [f for f in files if not f.startswith('.') and not f.endswith('.pyc')]
            
            for f in files:
                abs_f = os.path.join(root, f)
                z.write(abs_f, os.path.relpath(abs_f, project_root))

def launch_spark_job(
    venv_dir: str,
    service_code_dir: str,
    project_root: str,
    consumer_script_path: str,
    packages: str,
    args: List[str]
):
    """
    Prepares the environment (zips venv and code) and runs spark-submit.
    
    Args:
        venv_dir: Absolute path to the virtual environment folder.
        service_code_dir: Absolute path to the service code directory (to be zipped).
        project_root: Absolute path to the root of the project (e.g. .../airflow).
                      The code zip will contain paths relative to this root (e.g. projects/services/...).
        consumer_script_path: Absolute path to the python script to run with Spark.
        packages: Comma-separated list of maven coordinates for --packages.
        args: List of arguments to pass to the consumer script.
    """
    
    if not os.path.exists(venv_dir):
        raise FileNotFoundError(f"Virtual environment not found at {venv_dir}")

    # Determine python executable in venv for Spark
    if os.path.exists(os.path.join(venv_dir, "Scripts")):
        venv_python_rel = "Scripts/python.exe" # Windows
    elif os.path.exists(os.path.join(venv_dir, "bin")):
        venv_python_rel = "bin/python" # Linux/Unix
    else:
        raise FileNotFoundError("Could not detect Scripts or bin in .venv")

    timestamp = int(time.time())
    # Create zips in project root temporarily
    venv_zip = os.path.join(project_root, f"spark_venv_{timestamp}.zip")
    code_zip = os.path.join(project_root, f"spark_code_{timestamp}.zip")

    try:
        # 1. Zip Venv
        zip_venv(venv_dir, venv_zip)

        # 2. Zip Code
        zip_code(service_code_dir, code_zip, project_root)

        # 3. Prepare Spark Command
        cmd = [
            "spark-submit",
            "--packages", packages,
            "--archives", f"{venv_zip}#venv",
            "--py-files", code_zip,
            # Config Spark to use python from the unzipped archive
            "--conf", f"spark.pyspark.python=./venv/{venv_python_rel}",
            "--conf", f"spark.pyspark.driver.python=./venv/{venv_python_rel}",
            consumer_script_path
        ] + args

        env = os.environ.copy()
        # Clean conflicting env vars
        env.pop('PYSPARK_PYTHON', None)
        env.pop('PYSPARK_DRIVER_PYTHON', None)

        print("-" * 50)
        print("Launching Spark Job via Lib")
        print(f"Command: {' '.join(cmd)}")
        print("-" * 50)
        
        subprocess.run(cmd, env=env, check=True)

    finally:
        # Cleanup
        if os.path.exists(venv_zip):
            os.remove(venv_zip)
        if os.path.exists(code_zip):
            os.remove(code_zip)
