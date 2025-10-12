#!/bin/bash

# RQ1 Vulnerability Detection - RunPod Execution Script
# Usage: bash run_rq1_vuln_runpod.sh [reasoning|baseline] [zero|few] [test|full]
#
# Examples:
#   bash run_rq1_vuln_runpod.sh reasoning zero test    # Reasoning + zero-shot, 10 samples
#   bash run_rq1_vuln_runpod.sh baseline few full      # Baseline + few-shot, 386 samples
#   bash run_rq1_vuln_runpod.sh all all full           # Run all 4 experiments, 386 samples

set -e  # Exit on error

# Parse arguments
MODEL_TYPE="${1:-all}"      # reasoning | baseline | all
SHOT_TYPE="${2:-all}"        # zero | few | all
DATASET_SIZE="${3:-test}"    # test (10 samples) | full (386 samples)

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

echo "============================================"
echo "RQ1 Vulnerability Detection - RunPod"
echo "============================================"
echo ""
echo "Configuration:"
echo "  Model: $MODEL_TYPE"
echo "  Shot: $SHOT_TYPE"
echo "  Dataset: $DATASET_SIZE"
echo "  Project root: $PROJECT_ROOT"
echo "  Python: $(which python3)"
echo ""

# Set dataset based on size argument
if [ "$DATASET_SIZE" = "test" ]; then
    export VULN_DATASET="$PROJECT_ROOT/vuln_database/VulTrial_10_samples_test.jsonl"
    echo "Using TEST dataset: 10 samples"
else
    export VULN_DATASET="$PROJECT_ROOT/vuln_database/VulTrial_386_samples_balanced.jsonl"
    echo "Using FULL dataset: 386 samples"
fi
echo ""

# Function to run a single experiment
run_experiment() {
    local reasoning=$1
    local design=$2
    local exp_num=$3
    local exp_total=$4

    local model_name
    if [ "$reasoning" = "true" ]; then
        model_name="Reasoning (Qwen3-4B-Thinking)"
    else
        model_name="Baseline (Qwen3-4B-Instruct)"
    fi

    local shot_name
    if [ "$design" = "SA-zero" ]; then
        shot_name="zero-shot"
    else
        shot_name="few-shot"
    fi

    echo "[$exp_num/$exp_total] $model_name with $shot_name..."
    echo "  Reasoning mode: $reasoning"
    echo "  Design: $design"

    export ENABLE_REASONING=$reasoning
    python3 src/single_agent_vuln.py $design

    if [ $? -eq 0 ]; then
        echo "✓ Completed"
    else
        echo "✗ Failed"
        exit 1
    fi
    echo ""
}

# Determine which experiments to run
experiments=()

if [ "$MODEL_TYPE" = "all" ] && [ "$SHOT_TYPE" = "all" ]; then
    # Run all 4 experiments
    experiments+=("true SA-zero 1 4")
    experiments+=("false SA-zero 2 4")
    experiments+=("true SA-few 3 4")
    experiments+=("false SA-few 4 4")
elif [ "$MODEL_TYPE" = "all" ]; then
    # Run both models with specified shot type
    if [ "$SHOT_TYPE" = "zero" ]; then
        experiments+=("true SA-zero 1 2")
        experiments+=("false SA-zero 2 2")
    else
        experiments+=("true SA-few 1 2")
        experiments+=("false SA-few 2 2")
    fi
elif [ "$SHOT_TYPE" = "all" ]; then
    # Run both shot types with specified model
    if [ "$MODEL_TYPE" = "reasoning" ]; then
        experiments+=("true SA-zero 1 2")
        experiments+=("true SA-few 2 2")
    else
        experiments+=("false SA-zero 1 2")
        experiments+=("false SA-few 2 2")
    fi
else
    # Run single experiment
    local reasoning
    local design

    if [ "$MODEL_TYPE" = "reasoning" ]; then
        reasoning="true"
    else
        reasoning="false"
    fi

    if [ "$SHOT_TYPE" = "zero" ]; then
        design="SA-zero"
    else
        design="SA-few"
    fi

    experiments+=("$reasoning $design 1 1")
fi

# Run experiments
for exp in "${experiments[@]}"; do
    run_experiment $exp
done

echo "============================================"
echo "All experiments completed!"
echo "============================================"
echo ""
echo "Results saved in: $PROJECT_ROOT/results/"
echo ""
echo "To download results to local machine:"
echo "  scp -P <SSH_PORT> -i ~/.ssh/id_ed25519 -r root@ssh.runpod.io:/workspace/agent-green/results ./results_runpod"
echo ""
