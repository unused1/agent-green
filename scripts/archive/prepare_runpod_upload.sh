#!/bin/bash

# Prepare experiment files for RunPod upload via cloud storage
# Usage: bash scripts/prepare_runpod_upload.sh [thinking|instruct]
#
# This script creates a zip file that can be uploaded to cloud storage
# (Dropbox, Google Drive, etc.) and then downloaded on RunPod.
#
# Workaround for RunPod's SSH proxy not supporting scp/sftp.

set -e

MODEL_TYPE=${1:-thinking}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "============================================"
echo "Prepare RunPod Upload Package"
echo "============================================"
echo ""
echo "Model type: $MODEL_TYPE"
echo "Project root: $PROJECT_ROOT"
echo ""

# Create temporary directory for files to upload
TEMP_DIR=$(mktemp -d)
echo "Creating temporary directory: $TEMP_DIR"

# Create directory structure
mkdir -p "$TEMP_DIR/agent-green"
mkdir -p "$TEMP_DIR/agent-green/src"
mkdir -p "$TEMP_DIR/agent-green/scripts"
mkdir -p "$TEMP_DIR/agent-green/vuln_database"
mkdir -p "$TEMP_DIR/agent-green/results"

# Copy necessary files
echo "Copying files..."

# Python source files
cp "$PROJECT_ROOT/src/single_agent_vuln.py" "$TEMP_DIR/agent-green/src/"
cp "$PROJECT_ROOT/src/config.py" "$TEMP_DIR/agent-green/src/"
cp "$PROJECT_ROOT/src/vuln_evaluation.py" "$TEMP_DIR/agent-green/src/"

# Scripts
cp "$PROJECT_ROOT/scripts/run_rq1_vuln_runpod.sh" "$TEMP_DIR/agent-green/scripts/"
cp "$PROJECT_ROOT/scripts/setup_runpod_env.sh" "$TEMP_DIR/agent-green/scripts/"
cp "$PROJECT_ROOT/scripts/package_results.sh" "$TEMP_DIR/agent-green/scripts/"
chmod +x "$TEMP_DIR/agent-green/scripts/"*.sh

# Datasets
cp "$PROJECT_ROOT/vuln_database/VulTrial_386_samples_balanced.jsonl" "$TEMP_DIR/agent-green/vuln_database/"
cp "$PROJECT_ROOT/vuln_database/VulTrial_10_samples_test.jsonl" "$TEMP_DIR/agent-green/vuln_database/"

# Environment configuration (RunPod version)
# For Phase 2 (30B-A3B models), use .env.runpod.phase2 if it exists
if [ -f "$PROJECT_ROOT/.env.runpod.phase2" ]; then
    echo "Using Phase 2 configuration (.env.runpod.phase2)"
    cp "$PROJECT_ROOT/.env.runpod.phase2" "$TEMP_DIR/agent-green/.env"
elif [ -f "$PROJECT_ROOT/.env.runpod" ]; then
    echo "Using default RunPod configuration (.env.runpod)"
    cp "$PROJECT_ROOT/.env.runpod" "$TEMP_DIR/agent-green/.env"
else
    echo "Warning: No .env.runpod or .env.runpod.phase2 found"
fi

# Requirements
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    cp "$PROJECT_ROOT/requirements.txt" "$TEMP_DIR/agent-green/"
fi

# Create README with setup instructions
cat > "$TEMP_DIR/agent-green/README_RUNPOD.md" << 'EOFREADME'
# RunPod Setup Instructions

## Extract and Setup

```bash
# 1. Extract the uploaded zip file
cd /workspace
unzip agent-green.zip

# 2. Setup environment
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh

# 3. Verify vLLM is running
curl http://localhost:8000/v1/models
```

## Run Test (10 samples, ~30 seconds)

For **Thinking model pod**:
```bash
bash scripts/run_rq1_vuln_runpod.sh reasoning zero test
bash scripts/run_rq1_vuln_runpod.sh reasoning few test
```

For **Instruct model pod**:
```bash
bash scripts/run_rq1_vuln_runpod.sh baseline zero test
bash scripts/run_rq1_vuln_runpod.sh baseline few test
```

## Run Full Experiments (386 samples)

For **Thinking model pod**:
```bash
bash scripts/run_rq1_vuln_runpod.sh reasoning all full
```

For **Instruct model pod**:
```bash
bash scripts/run_rq1_vuln_runpod.sh baseline all full
```

## Package Results for Download

```bash
cd /workspace/agent-green
bash scripts/package_results.sh
```

This creates `/workspace/agent-green-results-TIMESTAMP.zip` ready for cloud download.
EOFREADME

echo "Files prepared"
echo ""

# Create zip file
OUTPUT_ZIP="$PROJECT_ROOT/runpod_upload_${MODEL_TYPE}_$(date +%Y%m%d_%H%M%S).zip"
echo "Creating zip file: $OUTPUT_ZIP"

cd "$TEMP_DIR"
zip -r "$OUTPUT_ZIP" agent-green/ -q

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "============================================"
echo "✅ Upload package ready!"
echo "============================================"
echo ""
echo "File: $OUTPUT_ZIP"
echo "Size: $(du -h "$OUTPUT_ZIP" | cut -f1)"
echo ""
echo "Next steps:"
echo "1. Upload this zip file to cloud storage (Dropbox/Google Drive/etc.)"
echo "2. Get a direct download link from cloud storage"
echo "3. On RunPod pod, SSH in (with proxy) and run:"
echo "   wget '<cloud-download-link>' -O /workspace/agent-green.zip"
echo "   cd /workspace"
echo "   unzip agent-green.zip"
echo "   cd agent-green"
echo "   bash scripts/setup_runpod_env.sh"
echo ""
echo "For Dropbox: Share link, change 'dl=0' to 'dl=1' for direct download"
echo "For Google Drive: Use 'Download' link directly or use gdown"
echo ""
