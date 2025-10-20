#!/bin/bash

# Package RunPod experiment results for download via cloud storage
# Usage: bash scripts/package_results.sh
#
# This script runs ON the RunPod pod to create a zip file of results
# that can be uploaded to cloud storage and downloaded locally.
#
# Workaround for RunPod's SSH proxy not supporting scp/sftp.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "============================================"
echo "Package RunPod Results for Download"
echo "============================================"
echo ""
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if results directory exists
if [ ! -d "$PROJECT_ROOT/results" ]; then
    echo "❌ No results directory found"
    exit 1
fi

# Count result files
RESULT_COUNT=$(find "$PROJECT_ROOT/results" -name "*.jsonl" -o -name "*.csv" -o -name "*.json" | wc -l)
echo "Found $RESULT_COUNT result files"
echo ""

if [ $RESULT_COUNT -eq 0 ]; then
    echo "⚠️  Warning: No result files found"
    echo "Make sure you've run experiments first"
    exit 1
fi

# Create output filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_ZIP="/workspace/agent-green-results-${TIMESTAMP}.zip"

echo "Creating results package..."
echo "Output: $OUTPUT_ZIP"
echo ""

# List what will be packaged
echo "Files to package:"
find "$PROJECT_ROOT/results" -type f | sort
echo ""

# Create zip file
cd "$PROJECT_ROOT"
zip -r "$OUTPUT_ZIP" results/ -q

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✅ Results packaged successfully!"
    echo "============================================"
    echo ""
    echo "File: $OUTPUT_ZIP"
    echo "Size: $(du -h "$OUTPUT_ZIP" | cut -f1)"
    echo ""
    echo "Next steps:"
    echo "1. Upload this zip to cloud storage:"
    echo "   - For Dropbox: Use web interface to upload"
    echo "   - For Google Drive: Use web interface or gdown"
    echo "   - For transfer.sh: curl --upload-file $OUTPUT_ZIP https://transfer.sh/"
    echo ""
    echo "2. Alternative - Use transfer.sh for quick sharing (7 days):"
    echo "   curl --upload-file $OUTPUT_ZIP https://transfer.sh/agent-green-results.zip"
    echo ""
    echo "3. Download on local machine using the cloud link"
    echo ""
else
    echo "❌ Failed to create zip file"
    exit 1
fi
