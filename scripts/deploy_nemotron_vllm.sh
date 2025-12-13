#!/bin/bash
# ============================================================================
# Llama-Nemotron vLLM Deployment Script
# ============================================================================
# This script deploys Llama-Nemotron models on RunPod H100 GPUs using vLLM.
#
# Models:
#   - Nano-8B: nvidia/Llama-3.1-Nemotron-Nano-8B-v1 (FP16, ~16GB VRAM)
#   - Super-49B: nvidia/Llama-3_3-Nemotron-Super-49B-v1_5 (FP8, ~50GB VRAM)
#
# Usage:
#   ./scripts/deploy_nemotron_vllm.sh [8b|49b]
#
# Reference: docs/Cross_Architecture_Validation_Plan.md
# ============================================================================

set -e

MODEL_SIZE="${1:-8b}"

echo "=============================================="
echo "Llama-Nemotron vLLM Deployment"
echo "=============================================="
echo "Model size: $MODEL_SIZE"
echo ""

# Common settings
GPU_MEMORY_UTILIZATION=0.9
TENSOR_PARALLEL_SIZE=1

case "$MODEL_SIZE" in
    "8b"|"8B"|"nano")
        MODEL_NAME="nvidia/Llama-3.1-Nemotron-Nano-8B-v1"
        MAX_MODEL_LEN=65536
        QUANTIZATION=""
        echo "Deploying: Llama-3.1-Nemotron-Nano-8B-v1"
        echo "  Precision: FP16 (native)"
        echo "  Context: 64K tokens"
        echo "  VRAM: ~16GB"
        ;;

    "49b"|"49B"|"super")
        MODEL_NAME="nvidia/Llama-3_3-Nemotron-Super-49B-v1_5"
        MAX_MODEL_LEN=65536
        QUANTIZATION="--quantization fp8"
        GPU_MEMORY_UTILIZATION=0.95
        TENSOR_PARALLEL_SIZE=2  # REQUIRED: 49B needs 2× H100 80GB
        echo "Deploying: Llama-3.3-Nemotron-Super-49B-v1.5"
        echo "  Precision: FP8 (quantized)"
        echo "  Context: 64K tokens"
        echo "  VRAM: ~80GB/GPU with tensor parallelism"
        echo ""
        echo "  IMPORTANT: Requires 2× H100 80GB GPUs!"
        echo "  Single H100 80GB will OOM at ~79GB during weight loading."
        ;;

    *)
        echo "ERROR: Unknown model size '$MODEL_SIZE'"
        echo "Usage: $0 [8b|49b]"
        exit 1
        ;;
esac

echo ""
echo "Thinking Mode Toggle:"
if [[ "$MODEL_SIZE" == "49b" || "$MODEL_SIZE" == "49B" || "$MODEL_SIZE" == "super" ]]; then
    echo "  - Thinking ON: (default, empty system prompt)"
    echo "  - Thinking OFF: '/no_think' in system prompt"
else
    echo "  - Thinking ON: 'detailed thinking on' in system prompt"
    echo "  - Thinking OFF: 'detailed thinking off' in system prompt"
fi
echo ""

# Check if vLLM is installed
if ! python3 -c "import vllm" 2>/dev/null; then
    echo "Installing vLLM..."
    pip install vllm --break-system-packages
fi

# Check if requests is installed (for validation script)
if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing requests..."
    pip install requests --break-system-packages
fi

echo ""
echo "Starting vLLM server..."
echo "=============================================="

# Build the command
VLLM_CMD="python3 -m vllm.entrypoints.openai.api_server \
    --model $MODEL_NAME \
    --trust-remote-code \
    --max-model-len $MAX_MODEL_LEN \
    --tensor-parallel-size $TENSOR_PARALLEL_SIZE \
    --gpu-memory-utilization $GPU_MEMORY_UTILIZATION \
    --enforce-eager"

# Add quantization if specified
if [ -n "$QUANTIZATION" ]; then
    VLLM_CMD="$VLLM_CMD $QUANTIZATION"
fi

echo "Command: $VLLM_CMD"
echo ""

# Run vLLM
eval $VLLM_CMD
