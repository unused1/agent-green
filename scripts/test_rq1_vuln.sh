#!/bin/bash

# Test script for RQ1 vulnerability detection (10 samples only)
# Purpose: Validate response parsing before running full experiments

echo "============================================"
echo "RQ1 Vulnerability Detection - PARSER TEST"
echo "============================================"
echo ""
echo "Testing with 10 samples to validate parser..."
echo ""

# Get project root (parent of scripts directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Set test dataset (10 samples)
export VULN_DATASET="$PROJECT_ROOT/vuln_database/VulTrial_10_samples_test.jsonl"

echo "Project root: $PROJECT_ROOT"
echo "Test dataset: $VULN_DATASET"
echo "Python: $(which python)"
echo ""

# Test 1: Reasoning model with zero-shot
echo "============================================"
echo "[TEST] Reasoning model (qwen3:4b-thinking) - Zero-shot"
echo "============================================"
export ENABLE_REASONING=true
python "$PROJECT_ROOT/src/single_agent_vuln.py" SA-zero

echo ""
echo "============================================"
echo "TEST COMPLETE"
echo "============================================"
echo ""
echo "Check the output above for:"
echo "  1. [Warning] Unclear response format - should be MINIMAL or ZERO"
echo "  2. Predictions should show mix of 0s and 1s (not all zeros)"
echo "  3. Accuracy should be > 0% (baseline is ~50% for random)"
echo ""
echo "If warnings persist, the parser needs further adjustment."
echo "If no warnings, proceed with full experiment using run_rq1_vuln.sh"
echo ""
