#!/bin/bash

# Setup RunPod environment for experiments
# Run this ONCE after uploading files to RunPod pod
#
# Usage: bash scripts/setup_runpod_env.sh

set -e

echo "============================================"
echo "RunPod Environment Setup"
echo "============================================"
echo ""

# Check we're in the right directory
if [ ! -f "src/single_agent_vuln.py" ]; then
    echo "Error: Must run from /workspace/agent-green directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

PROJECT_ROOT=$(pwd)
echo "Project root: $PROJECT_ROOT"
echo ""

# Update .env with correct PROJECT_ROOT
echo "Updating .env with PROJECT_ROOT..."
sed -i "s|PROJECT_ROOT=.*|PROJECT_ROOT=$PROJECT_ROOT|g" .env
echo "✓ .env updated"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --quiet autogen
pip install --quiet python-dotenv
pip install --quiet codecarbon
pip install --quiet pandas
pip install --quiet numpy
pip install --quiet scikit-learn

echo "Installing vLLM and HuggingFace tools (this may take a few minutes)..."
pip install --quiet vllm
pip install --quiet hf-transfer
echo "✓ Dependencies installed"
echo ""

# Verify vLLM is running on localhost:8000
echo "Checking vLLM server..."
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo "✓ vLLM server is running"

    # Get model name
    MODEL_NAME=$(curl -s http://localhost:8000/v1/models | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "  Model: $MODEL_NAME"

    # Update .env with correct model configuration
    if [[ "$MODEL_NAME" == *"Thinking"* ]]; then
        echo ""
        echo "Detected THINKING model - configuring for reasoning experiments"
        sed -i 's/ENABLE_REASONING=false/ENABLE_REASONING=true/g' .env
        echo "  Set ENABLE_REASONING=true in .env"
    else
        echo ""
        echo "Detected INSTRUCT model - configuring for baseline experiments"
        echo "  ENABLE_REASONING=false (already set)"
    fi
else
    echo "⚠ Warning: vLLM server not responding on localhost:8000"
    echo "  Make sure vLLM is running before starting experiments"
fi
echo ""

# Create results directory
mkdir -p results
echo "✓ Results directory created"
echo ""

# Verify dataset files
echo "Verifying dataset files..."
if [ -f "vuln_database/VulTrial_386_samples_balanced.jsonl" ]; then
    NUM_FULL=$(wc -l < vuln_database/VulTrial_386_samples_balanced.jsonl)
    echo "✓ Full dataset: $NUM_FULL samples"
else
    echo "✗ Missing: VulTrial_386_samples_balanced.jsonl"
    exit 1
fi

if [ -f "vuln_database/VulTrial_10_samples_test.jsonl" ]; then
    NUM_TEST=$(wc -l < vuln_database/VulTrial_10_samples_test.jsonl)
    echo "✓ Test dataset: $NUM_TEST samples"
else
    echo "✗ Missing: VulTrial_10_samples_test.jsonl"
    exit 1
fi
echo ""

# Test Python imports
echo "Testing Python environment..."
python3 << 'EOF'
import sys
try:
    import autogen
    import dotenv
    import codecarbon
    import pandas
    import numpy
    import sklearn
    import vllm
    print(f"✓ All Python packages imported successfully")
    print(f"  vLLM version: {vllm.__version__}")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
EOF
echo ""

echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Environment ready for experiments."
echo ""
echo "Quick test (10 samples, ~30 seconds):"
echo "  bash scripts/run_rq1_vuln_runpod.sh reasoning zero test"
echo ""
echo "Full experiments (386 samples):"
if [[ "$MODEL_NAME" == *"Thinking"* ]]; then
    echo "  bash scripts/run_rq1_vuln_runpod.sh reasoning all full"
else
    echo "  bash scripts/run_rq1_vuln_runpod.sh baseline all full"
fi
echo ""
echo "Monitor progress:"
echo "  tail -f results/*_detailed_results.jsonl"
echo ""
