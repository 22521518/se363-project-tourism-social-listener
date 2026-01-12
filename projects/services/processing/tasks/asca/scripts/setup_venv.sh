#!/bin/bash
# ============================================
# ASCA Module - Virtual Environment Setup
# ============================================
# Creates and configures a Python virtual environment for running
# the ASCA extraction service with all required dependencies.
#
# Usage:
#   ./setup_venv.sh              # Standard installation
#   ./setup_venv.sh --no-vncorenlp   # Skip VnCoreNLP download
#
# This script will:
#   1. Create or update the virtual environment
#   2. Install all Python dependencies
#   3. Download VnCoreNLP for Vietnamese processing (optional)
# ============================================

set -e  # Exit on error

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASCA_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$ASCA_DIR/venv"
REQUIREMENTS_FILE="$ASCA_DIR/requirements.txt"
VNCORENLP_DIR="$ASCA_DIR/VnCoreNLP-1.2"

# Check for --no-vncorenlp flag
SKIP_VNCORENLP=false
for arg in "$@"; do
    if [ "$arg" == "--no-vncorenlp" ]; then
        SKIP_VNCORENLP=true
    fi
done

echo "============================================"
echo "ASCA Virtual Environment Setup"
echo "============================================"
echo "ASCA Dir: $ASCA_DIR"
echo "VEnv Dir: $VENV_DIR"

# Check Python availability
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python is not installed or not in PATH!"
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
else
    echo ""
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate" 2>/dev/null

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing requirements..."
if [ -f "$REQUIREMENTS_FILE" ]; then
    pip install -r "$REQUIREMENTS_FILE"
    echo "✅ Requirements installed"
else
    echo "⚠️  Requirements file not found: $REQUIREMENTS_FILE"
    echo "Installing minimal dependencies..."
    pip install pydantic pydantic-settings sqlalchemy psycopg2-binary kafka-python-ng python-dotenv pandas
fi

# Download VnCoreNLP if not skipped
if [ "$SKIP_VNCORENLP" = false ]; then
    echo ""
    echo "Checking VnCoreNLP..."
    "$SCRIPT_DIR/download_vncorenlp.sh"
else
    echo ""
    echo "⏭️  Skipping VnCoreNLP download (--no-vncorenlp flag)"
fi

echo ""
echo "============================================"
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To run the consumer:"
echo "  ./scripts/run_consumer.sh"
echo "============================================"
