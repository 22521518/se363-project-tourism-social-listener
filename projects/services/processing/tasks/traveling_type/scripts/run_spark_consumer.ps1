# Run Spark Consumer on Windows with Venv

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Scripts -> Traveling type 
$ServiceRoot = Split-Path -Parent $ScriptDir
# Airflow root: projects -> services -> processing -> tasks -> traveling type -> airflow
$AirflowRoot = (Resolve-Path "$ServiceRoot\..\..\..\..\..").Path

$VenvDir = "$ServiceRoot\.venv"
$ReqFile = "$ServiceRoot\requirements.txt"
$ConsumerScript = "$ServiceRoot\consumer.py"

# 1. Setup Venv
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment at $VenvDir..."
    python -m venv $VenvDir
}

$VenvActivate = "$VenvDir\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
}

Write-Host "Installing requirements..."
pip install -r $ReqFile

# 2. Zip projects module
Write-Host "Zipping project modules..."
Push-Location $AirflowRoot
if (Test-Path "projects.zip") {
    Remove-Item "projects.zip"
}
Compress-Archive -Path "projects" -DestinationPath "projects.zip" -Force
Pop-Location

# 3. Set Spark Environment to use Venv Python
$VenvPython = "$VenvDir\Scripts\python.exe"
$env:PYSPARK_PYTHON = $VenvPython
$env:PYSPARK_DRIVER_PYTHON = $VenvPython

# 4. Run Spark Submit
$PACKAGES = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.5.0"

Write-Host "Starting Spark Consumer..."
spark-submit `
    --packages $PACKAGES `
    --py-files "$AirflowRoot\projects.zip" `
    "$ConsumerScript"
