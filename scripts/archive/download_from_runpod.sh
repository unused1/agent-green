#!/bin/bash

# Download experiment results from RunPod pod
# Usage: bash scripts/download_from_runpod.sh <IP_ADDRESS> <PORT> [thinking|instruct]
#
# Examples:
#   bash scripts/download_from_runpod.sh 213.181.122.135 19442 thinking    # Download from thinking model pod
#   bash scripts/download_from_runpod.sh 213.181.122.136 19443 instruct    # Download from instruct model pod

set -e

if [ $# -lt 2 ]; then
    echo "Usage: bash scripts/download_from_runpod.sh <IP_ADDRESS> <PORT> [thinking|instruct]"
    echo ""
    echo "Examples:"
    echo "  bash scripts/download_from_runpod.sh 213.181.122.135 19442 thinking"
    echo "  bash scripts/download_from_runpod.sh 213.181.122.136 19443 instruct"
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
echo "Download Results from RunPod"
echo "============================================"
echo ""
echo "Pod IP: $POD_IP"
echo "Pod Port: $POD_PORT"
echo "Model type: $MODEL_TYPE"
echo ""

# Create local results directory with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$PROJECT_ROOT/results/runpod"
LOCAL_RESULTS_DIR="$PROJECT_ROOT/results/runpod/${MODEL_TYPE}_${TIMESTAMP}"
mkdir -p "$LOCAL_RESULTS_DIR"

echo "Downloading results..."
echo "From: root@$POD_IP:$POD_PORT:/workspace/agent-green/results/"
echo "To: $LOCAL_RESULTS_DIR"
echo ""

# Download results
scp -P $POD_PORT -i ~/.ssh/runpod_ed25519 -r root@$POD_IP:/workspace/agent-green/results/* "$LOCAL_RESULTS_DIR/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Download completed successfully!"
    echo ""
    echo "Results saved to: $LOCAL_RESULTS_DIR"
    echo ""

    # Show summary of downloaded files
    echo "Downloaded files:"
    ls -lh "$LOCAL_RESULTS_DIR"
    echo ""

    # Count result files
    NUM_JSONL=$(find "$LOCAL_RESULTS_DIR" -name "*_detailed_results.jsonl" | wc -l | tr -d ' ')
    NUM_CSV=$(find "$LOCAL_RESULTS_DIR" -name "*_detailed_results.csv" | wc -l | tr -d ' ')
    NUM_ENERGY=$(find "$LOCAL_RESULTS_DIR" -name "*_energy_tracking.json" | wc -l | tr -d ' ')

    echo "Summary:"
    echo "  JSONL files: $NUM_JSONL"
    echo "  CSV files: $NUM_CSV"
    echo "  Energy tracking files: $NUM_ENERGY"
    echo ""

    # Show energy consumption if available
    if [ $NUM_ENERGY -gt 0 ]; then
        echo "Energy consumption:"
        for energy_file in "$LOCAL_RESULTS_DIR"/*_energy_tracking.json; do
            if [ -f "$energy_file" ]; then
                echo "  $(basename $energy_file):"
                total_emissions=$(grep -o '"total_emissions": [0-9.]*' "$energy_file" | cut -d' ' -f2)
                sessions=$(grep -o '"sessions": [0-9]*' "$energy_file" | cut -d' ' -f2)
                echo "    Total: ${total_emissions} kg CO2 (${sessions} sessions)"
            fi
        done
        echo ""
    fi

    echo "Next steps:"
    echo "1. Review results:"
    echo "   cat $LOCAL_RESULTS_DIR/*_detailed_results.csv"
    echo ""
    echo "2. Analyze with Python:"
    echo "   python src/analyze_results.py $LOCAL_RESULTS_DIR"
    echo ""
else
    echo "✗ Download failed"
    exit 1
fi
