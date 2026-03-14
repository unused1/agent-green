#!/bin/bash

# Mars Docker Setup Script - Run vLLM + Experiments in Same Container
# This ensures CodeCarbon can measure GPU energy consumption

set -e

CONTAINER_NAME=$1
GPU_ID=$2
MODEL_NAME=$3
PORT=$4

if [ $# -lt 4 ]; then
    echo "Usage: bash mars_docker_setup.sh <container_name> <gpu_id> <model_name> <port>"
    echo ""
    echo "Examples:"
    echo "  bash mars_docker_setup.sh qwen-thinking 1 Qwen/Qwen3-4B-Thinking-2507 8000"
    echo "  bash mars_docker_setup.sh qwen-baseline 3 Qwen/Qwen3-4B-Instruct-2507 8001"
    exit 1
fi

echo "============================================"
echo "Mars Docker Setup"
echo "============================================"
echo "Container: $CONTAINER_NAME"
echo "GPU: $GPU_ID"
echo "Model: $MODEL_NAME"
echo "Port: $PORT"
echo ""

# Start container with vLLM, but keep it running for experiments
docker run -d \
    --name $CONTAINER_NAME \
    --gpus "\"device=$GPU_ID\"" \
    --shm-size=16g \
    -v /mnt/hdd2/huabengtan/agent-green:/workspace/agent-green \
    -p $PORT:8000 \
    --restart unless-stopped \
    --entrypoint /bin/bash \
    vllm/vllm-openai:latest \
    -c "
    # Start vLLM in background
    python3 -m vllm.entrypoints.openai.api_server \
        --model $MODEL_NAME \
        --download-dir /workspace/agent-green/models \
        --gpu-memory-utilization 0.85 \
        --max-model-len 32768 \
        --dtype auto \
        --host 0.0.0.0 \
        --port 8000 &

    # Wait for vLLM to start
    sleep 10

    # Install experiment dependencies
    pip install autogen-agentchat python-dotenv codecarbon pandas numpy scikit-learn

    # Keep container running
    tail -f /dev/null
    "

echo ""
echo "✓ Container started: $CONTAINER_NAME"
echo ""
echo "Next steps:"
echo "1. Wait for vLLM to load (~5 minutes):"
echo "   docker logs -f $CONTAINER_NAME"
echo ""
echo "2. Enter container to run experiments:"
echo "   docker exec -it $CONTAINER_NAME bash"
echo ""
echo "3. Inside container, run experiments:"
echo "   cd /workspace/agent-green"
echo "   export ENABLE_REASONING=true  # or false for baseline"
echo "   python3 src/single_agent_vuln.py SA-zero"
echo ""
