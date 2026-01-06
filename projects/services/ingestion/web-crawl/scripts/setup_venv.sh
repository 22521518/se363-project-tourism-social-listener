#!/usr/bin/env bash
# Setup Virtual Environment for Web Crawl
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
python -m pip install -r "${REQ_FILE}"

# Install Playwright browsers (required by crawl4ai)
echo "Installing Playwright browsers..."
python -m playwright install chromium
# Also install system dependencies if possible (may require sudo)
python -m playwright install-deps chromium 2>/dev/null || echo "Note: Could not install system deps (may need sudo). Browser should still work."

echo "Environment setup complete."
