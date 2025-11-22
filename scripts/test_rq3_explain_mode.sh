#!/bin/bash

# Test RQ3 Explain-Before Mode
# This script runs small test samples to verify the explain-before implementation

set -e  # Exit on error

echo "========================================================================"
echo "RQ3 EXPLAIN-BEFORE MODE TEST"
echo "========================================================================"
echo ""
echo "This script tests the RQ3 explain-before implementation by running:"
echo "  1. SA-zero-explain on 2 vulnerability samples"
echo "  2. SA-zero-explain on 2 code generation samples"
echo ""
echo "Purpose: Verify prompts, extraction logic, and faithfulness metrics"
echo "========================================================================"
echo ""

# Check we're in the right directory
if [ ! -f "src/single_agent_vuln.py" ]; then
    echo "Error: Must run from project root directory"
    exit 1
fi

# Create test results directory
TEST_RESULTS_DIR="results/test_rq3"
mkdir -p "$TEST_RESULTS_DIR"

echo "[1/4] Testing Vulnerability Detection (SA-zero-explain)..."
echo "--------------------------------------------------------"

# Create a small test dataset (first 2 samples)
echo "Creating test dataset with 2 vulnerability samples..."
head -n 2 datasets/vulnerability_detection/vulnerability_dataset.jsonl > "$TEST_RESULTS_DIR/test_vuln_2samples.jsonl"

# Run vulnerability detection in explain mode
echo "Running SA-zero-explain on 2 samples..."
# Note: We'll need to temporarily modify the script to accept a custom dataset path
# For now, we'll just show what the command would be

echo ""
echo "Test command for vulnerability detection:"
echo "  python3 src/single_agent_vuln.py SA-zero-explain"
echo ""
echo "Note: To test with only 2 samples, you would need to:"
echo "  1. Backup the original dataset"
echo "  2. Replace with 2-sample test dataset"
echo "  3. Run the experiment"
echo "  4. Restore original dataset"
echo ""
echo "For safety, manual execution recommended."
echo ""

echo "[2/4] Testing Code Generation (SA-zero-explain)..."
echo "--------------------------------------------------------"

# Create a small test dataset (first 2 samples)
echo "Creating test dataset with 2 code generation samples..."
head -n 2 datasets/code_generation/HumanEval.jsonl > "$TEST_RESULTS_DIR/test_codegen_2samples.jsonl"

echo ""
echo "Test command for code generation:"
echo "  python3 src/single_agent_code_generation.py SA-zero-explain"
echo ""
echo "Note: Same manual process as vulnerability detection."
echo ""

echo "[3/4] Demonstrating Faithfulness Metrics..."
echo "--------------------------------------------------------"

echo ""
echo "Once experiments complete, compute faithfulness metrics with:"
echo "  python3 src/compute_faithfulness.py <results_file> vuln"
echo "  python3 src/compute_faithfulness.py <results_file> codegen"
echo ""

echo "[4/4] Expected Output Verification..."
echo "--------------------------------------------------------"

echo ""
echo "For vulnerability detection, expect output like:"
echo ""
echo "  Sample 1: HumanEval/0"
echo "  REASONING: [Step-by-step analysis of the code...]"
echo "  DECISION: YES or NO"
echo ""
echo "For code generation, expect output like:"
echo ""
echo "  Sample 1: HumanEval/0"
echo "  REASONING: [Step-by-step plan for implementation...]"
echo "  CODE: [Python code implementation]"
echo ""

echo "========================================================================"
echo "RQ3 TEST GUIDE COMPLETE"
echo "========================================================================"
echo ""
echo "RECOMMENDED MANUAL TEST PROCEDURE:"
echo ""
echo "1. Test Vulnerability Detection:"
echo "   a. cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green"
echo "   b. cp datasets/vulnerability_detection/vulnerability_dataset.jsonl datasets/vulnerability_detection/vulnerability_dataset.jsonl.backup"
echo "   c. head -n 2 datasets/vulnerability_detection/vulnerability_dataset.jsonl > temp.jsonl"
echo "   d. mv temp.jsonl datasets/vulnerability_detection/vulnerability_dataset.jsonl"
echo "   e. python3 src/single_agent_vuln.py SA-zero-explain"
echo "   f. mv datasets/vulnerability_detection/vulnerability_dataset.jsonl.backup datasets/vulnerability_detection/vulnerability_dataset.jsonl"
echo "   g. Check results file for REASONING: and DECISION: format"
echo ""
echo "2. Test Code Generation:"
echo "   a. Same process as above, but with:"
echo "      - HumanEval dataset instead of vulnerability dataset"
echo "      - python3 src/single_agent_code_generation.py SA-zero-explain"
echo "      - Check for REASONING: and CODE: format"
echo ""
echo "3. Test Faithfulness Metrics:"
echo "   a. python3 src/compute_faithfulness.py <results_file> vuln"
echo "   b. python3 src/compute_faithfulness.py <results_file> codegen"
echo "   c. Verify metrics JSON output is generated"
echo ""
echo "========================================================================"
