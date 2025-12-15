# Run YouTube Ingestion Service (Producer or Consumer)
# Usage: .\run_youtube_service.ps1 -Args "--mode smart --run-once"

param (
    [string]$ScriptArgs = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Go up to YouTube root: scripts -> youtube
$ServiceRoot = Split-Path -Parent $ScriptDir
# Airflow root: projects -> services -> ingestion -> youtube -> airflow
$AirflowRoot = (Resolve-Path "$ServiceRoot\..\..\..\..").Path

$VenvDir = "$ServiceRoot\.venv"
$ReqFile = "$ServiceRoot\requirements.youtube.txt"
$MainScript = "$ServiceRoot\main.py"

# Function to setup venv
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment at $VenvDir..."
    python -m venv $VenvDir
}

# Activate venv
$VenvActivate = "$VenvDir\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
} else {
    Write-Error "Could not find activate script at $VenvActivate"
}

Write-Host "Installing requirements..."
pip install -r $ReqFile

# Run the python script
$env:PYTHONPATH = $AirflowRoot
Write-Host "Running: python $MainScript $ScriptArgs"

# Invoke python with arguments splitting
# We use Invoke-Expression or Start-Process to handle args correctly
$Cmd = "python `"$MainScript`" $ScriptArgs"
Invoke-Expression $Cmd
