#!/bin/bash

# RQ1 Vulnerability Detection Experiments
# Compares reasoning-enabled vs baseline Qwen3 models

echo "============================================"
echo "RQ1 Vulnerability Detection Experiments"
echo "============================================"
echo ""

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo "Python: $(which python)"
echo ""

# Experiment 1: Reasoning + Zero-shot
echo "[1/4] Reasoning model (qwen3:4b-thinking) with zero-shot..."
export ENABLE_REASONING=true
python src/single_agent_vuln.py SA-zero
if [ $? -eq 0 ]; then
    echo "✓ Completed"
else
    echo "✗ Failed"
    exit 1
fi
echo ""

# Experiment 2: Baseline + Zero-shot
echo "[2/4] Baseline model (qwen3:4b) with zero-shot..."
export ENABLE_REASONING=false
python src/single_agent_vuln.py SA-zero
if [ $? -eq 0 ]; then
    echo "✓ Completed"
else
    echo "✗ Failed"
    exit 1
fi
echo ""

# Experiment 3: Reasoning + Few-shot
echo "[3/4] Reasoning model (qwen3:4b-thinking) with few-shot..."
export ENABLE_REASONING=true
python src/single_agent_vuln.py SA-few
if [ $? -eq 0 ]; then
    echo "✓ Completed"
else
    echo "✗ Failed"
    exit 1
fi
echo ""

# Experiment 4: Baseline + Few-shot
echo "[4/4] Baseline model (qwen3:4b) with few-shot..."
export ENABLE_REASONING=false
python src/single_agent_vuln.py SA-few
if [ $? -eq 0 ]; then
    echo "✓ Completed"
else
    echo "✗ Failed"
    exit 1
fi
echo ""

echo "============================================"
echo "All experiments completed!"
echo "Results saved in: $PROJECT_ROOT/results/"
echo "============================================"
