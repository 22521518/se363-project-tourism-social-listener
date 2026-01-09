#!/bin/bash
# ============================================
# ASCA Module - VnCoreNLP Download Script
# ============================================
# Downloads VnCoreNLP for Vietnamese text processing.
#
# VnCoreNLP is required for Vietnamese tokenization and
# word segmentation in the ASCA pipeline.
#
# Usage:
#   ./download_vncorenlp.sh
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASCA_DIR="$(dirname "$SCRIPT_DIR")"
VNCORENLP_DIR="$ASCA_DIR/VnCoreNLP-1.2"
VNCORENLP_JAR="$VNCORENLP_DIR/VnCoreNLP-1.2.jar"
DOWNLOAD_URL="https://github.com/vncorenlp/VnCoreNLP/archive/refs/tags/v1.2.zip"
ZIP_FILE="$ASCA_DIR/vncorenlp_temp.zip"

echo "Checking VnCoreNLP installation..."

# Check if already downloaded
if [ -f "$VNCORENLP_JAR" ]; then
    echo "✅ VnCoreNLP already installed at: $VNCORENLP_DIR"
    exit 0
fi

echo "VnCoreNLP not found. Downloading..."

# Create directory if needed
mkdir -p "$ASCA_DIR"

# Download using curl or wget
if command -v curl &> /dev/null; then
    echo "Downloading with curl..."
    curl -L -o "$ZIP_FILE" "$DOWNLOAD_URL"
elif command -v wget &> /dev/null; then
    echo "Downloading with wget..."
    wget -O "$ZIP_FILE" "$DOWNLOAD_URL"
else
    echo "❌ Neither curl nor wget found. Please install one of them."
    echo ""
    echo "Manual installation:"
    echo "1. Download from: $DOWNLOAD_URL"
    echo "2. Extract to: $VNCORENLP_DIR"
    exit 1
fi

# Check download success
if [ ! -f "$ZIP_FILE" ]; then
    echo "❌ Download failed!"
    exit 1
fi

echo "Extracting..."

# Extract using unzip
if command -v unzip &> /dev/null; then
    unzip -q -o "$ZIP_FILE" -d "$ASCA_DIR"
    # The zip extracts to VnCoreNLP-1.2 folder
    if [ ! -d "$VNCORENLP_DIR" ]; then
        # Try alternative folder name
        mv "$ASCA_DIR/VnCoreNLP-"* "$VNCORENLP_DIR" 2>/dev/null || true
    fi
else
    echo "❌ unzip not found. Please install unzip."
    rm -f "$ZIP_FILE"
    exit 1
fi

# Cleanup
rm -f "$ZIP_FILE"

# Verify installation
if [ -f "$VNCORENLP_JAR" ]; then
    echo "✅ VnCoreNLP installed successfully!"
    echo "   Path: $VNCORENLP_DIR"
else
    echo "⚠️  VnCoreNLP installation may be incomplete."
    echo "   Expected JAR: $VNCORENLP_JAR"
    echo ""
    echo "Manual installation:"
    echo "1. Download from: $DOWNLOAD_URL"
    echo "2. Extract to: $VNCORENLP_DIR"
fi
