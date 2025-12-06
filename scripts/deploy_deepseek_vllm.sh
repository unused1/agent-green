#!/bin/bash
# DeepSeek R1 Distill vLLM Deployment Script
# Reference: docs/Cross_Architecture_Validation_Plan.md
#
# Usage:
#   ./scripts/deploy_deepseek_vllm.sh 8b    # Deploy 8B model
#   ./scripts/deploy_deepseek_vllm.sh 70b   # Deploy 70B model (INT8)
#
# Prerequisites:
#   - NVIDIA H100 80GB GPU
#   - vLLM >= 0.9.0 (for enable_thinking support)
#   - CUDA 12.x

set -e

MODEL_SIZE="${1:-8b}"
PORT="${2:-8000}"

echo "=============================================="
echo "DeepSeek R1 Distill vLLM Deployment"
echo "=============================================="
echo "Model Size: ${MODEL_SIZE}"
echo "Port: ${PORT}"
echo ""

# Model configurations
case "${MODEL_SIZE}" in
    "8b"|"8B")
        MODEL_NAME="deepseek-ai/DeepSeek-R1-Distill-Llama-8B"
        # 8B fits comfortably on H100 80GB in FP16
        # Using 64K context to match Qwen3 experiments for fair comparison
        VLLM_ARGS=(
            "--dtype" "float16"
            "--max-model-len" "65536"
            "--gpu-memory-utilization" "0.90"
        )
        echo "Configuration: FP16, 64K context"
        ;;

    "70b"|"70B")
        MODEL_NAME="deepseek-ai/DeepSeek-R1-Distill-Llama-70B"
        # 70B requires INT8 quantization for single H100 80GB
        # Trying 64K context for consistency with 8B experiments
        # If OOM occurs, reduce to 32768
        VLLM_ARGS=(
            "--dtype" "auto"
            "--quantization" "bitsandbytes"
            "--load-format" "bitsandbytes"
            "--max-model-len" "65536"
            "--gpu-memory-utilization" "0.95"
        )
        echo "Configuration: INT8 (bitsandbytes), 64K context"
        echo "Note: If OOM occurs, reduce --max-model-len to 32768"
        ;;

    *)
        echo "Error: Unknown model size '${MODEL_SIZE}'"
        echo "Usage: $0 [8b|70b] [port]"
        exit 1
        ;;
esac

echo "Model: ${MODEL_NAME}"
echo ""

# Check vLLM version
echo "Checking vLLM version..."
VLLM_VERSION=$(python -c "import vllm; print(vllm.__version__)" 2>/dev/null || echo "not installed")
echo "vLLM version: ${VLLM_VERSION}"

if [[ "${VLLM_VERSION}" == "not installed" ]]; then
    echo "Error: vLLM not installed. Please install with: pip install vllm>=0.9.0"
    exit 1
fi

# Check for reasoning parser support (vLLM 0.9.0+)
echo ""
echo "Note: For enable_thinking support, ensure vLLM >= 0.9.0"
echo ""

# Start vLLM server
echo "=============================================="
echo "Starting vLLM server..."
echo "=============================================="
echo ""
echo "Command:"
echo "  vllm serve ${MODEL_NAME} \\"
for arg in "${VLLM_ARGS[@]}"; do
    echo "    ${arg} \\"
done
echo "    --port ${PORT} \\"
echo "    --enable-reasoning \\"
echo "    --reasoning-parser deepseek_r1"
echo ""

# Confirm before starting
read -p "Start server? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Run vLLM serve
vllm serve "${MODEL_NAME}" \
    "${VLLM_ARGS[@]}" \
    --port "${PORT}" \
    --enable-reasoning \
    --reasoning-parser deepseek_r1
