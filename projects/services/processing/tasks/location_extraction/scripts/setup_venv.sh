#!/usr/bin/env bash
# Setup Virtual Environment for Location Extraction
# Usage: ./setup_venv.sh <VENV_DIR>

set -euo pipefail

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(dirname "${SCRIPT_DIR}")"
REQ_FILE="${SERVICE_ROOT}/requirements.txt"

VENV_DIR="${1:-}"

if [[ -z "${VENV_DIR}" ]]; then
    echo "Usage: $0 <VENV_DIR>"
    exit 1
fi

if [[ ! -f "${REQ_FILE}" ]]; then
    echo "Requirements file not found: ${REQ_FILE}"
    exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
    echo "Creating virtual environment at ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
else
    echo "Virtual environment exists at ${VENV_DIR}"
fi

# Activate venv
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo "Installing/Updating requirements..."
python -m pip install --upgrade pip

# Check if NVIDIA GPU is available
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    echo "GPU detected. Installing PyTorch with CUDA support..."
    # Install default PyTorch with CUDA support
    python -m pip install torch>=2.0.0
else
    echo "No GPU detected. Installing CPU-only PyTorch..."
    # Install CPU-only PyTorch to avoid libcudnn.so.9 errors
    python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
fi

# Install remaining requirements (torch will be skipped as it's already installed)
python -m pip install -r "${REQ_FILE}"

echo "Environment setup complete."
