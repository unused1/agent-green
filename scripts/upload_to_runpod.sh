#!/bin/bash

# Upload experiment files to RunPod pod
# Usage: bash scripts/upload_to_runpod.sh <IP_ADDRESS> <PORT> [thinking|instruct]
#
# Examples:
#   bash scripts/upload_to_runpod.sh 213.181.122.135 19442 thinking    # Upload to thinking model pod
#   bash scripts/upload_to_runpod.sh 213.181.122.136 19443 instruct    # Upload to instruct model pod

set -e

if [ $# -lt 2 ]; then
    echo "Usage: bash scripts/upload_to_runpod.sh <IP_ADDRESS> <PORT> [thinking|instruct]"
    echo ""
    echo "Examples:"
    echo "  bash scripts/upload_to_runpod.sh 213.181.122.135 19442 thinking"
    echo "  bash scripts/upload_to_runpod.sh 213.181.122.136 19443 instruct"
    echo ""
    echo "Get IP address and port from RunPod console -> Pod -> Connect -> TCP Port Mappings"
    exit 1
fi

POD_IP=$1
POD_PORT=$2
MODEL_TYPE=${3:-thinking}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "============================================"
echo "Upload Experiment Files to RunPod"
echo "============================================"
echo ""
echo "Pod IP: $POD_IP"
echo "Pod Port: $POD_PORT"
echo "Model type: $MODEL_TYPE"
echo "Project root: $PROJECT_ROOT"
echo ""

# Create temporary directory for files to upload
TEMP_DIR=$(mktemp -d)
echo "Creating temporary upload directory: $TEMP_DIR"

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

echo "Files prepared for upload"
echo ""

# Upload to RunPod
echo "Uploading to RunPod (root@$POD_IP:$POD_PORT)..."
scp -P $POD_PORT -i ~/.ssh/runpod_ed25519 -r "$TEMP_DIR/agent-green" root@$POD_IP:/workspace/

if [ $? -eq 0 ]; then
    echo "✓ Upload completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. SSH into pod:"
    echo "   ssh root@$POD_IP -p $POD_PORT -i ~/.ssh/runpod_ed25519"
    echo ""
    echo "2. Setup environment:"
    echo "   cd /workspace/agent-green"
    echo "   bash scripts/setup_runpod_env.sh"
    echo ""
    echo "3. Run test (10 samples):"
    if [ "$MODEL_TYPE" = "thinking" ]; then
        echo "   bash scripts/run_rq1_vuln_runpod.sh reasoning zero test"
        echo "   bash scripts/run_rq1_vuln_runpod.sh reasoning few test"
    else
        echo "   bash scripts/run_rq1_vuln_runpod.sh baseline zero test"
        echo "   bash scripts/run_rq1_vuln_runpod.sh baseline few test"
    fi
    echo ""
    echo "4. Run full experiments (386 samples):"
    if [ "$MODEL_TYPE" = "thinking" ]; then
        echo "   bash scripts/run_rq1_vuln_runpod.sh reasoning all full"
    else
        echo "   bash scripts/run_rq1_vuln_runpod.sh baseline all full"
    fi
else
    echo "✗ Upload failed"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"
echo ""
echo "Temporary files cleaned up"
