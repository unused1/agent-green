#!/bin/bash

# Test script for RunPod/vLLM connection
# Purpose: Verify RunPod endpoint is accessible before running experiments

echo "============================================"
echo "RunPod/vLLM Connection Test"
echo "============================================"
echo ""

# Get project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
else
    echo "ERROR: .env file not found"
    exit 1
fi

# Check if USE_RUNPOD is enabled
if [ "$USE_RUNPOD" != "true" ]; then
    echo "ERROR: USE_RUNPOD is not set to 'true' in .env"
    echo "Please set USE_RUNPOD=true and configure RunPod endpoints"
    exit 1
fi

echo "Configuration:"
echo "  USE_RUNPOD: $USE_RUNPOD"
echo "  ENABLE_REASONING: $ENABLE_REASONING"
echo ""

# Determine which endpoint to test based on ENABLE_REASONING
if [ "$ENABLE_REASONING" = "true" ]; then
    ENDPOINT=$REASONING_ENDPOINT
    MODEL=$REASONING_MODEL
    API_KEY=$REASONING_API_KEY
    echo "Testing REASONING endpoint..."
else
    ENDPOINT=$BASELINE_ENDPOINT
    MODEL=$BASELINE_MODEL
    API_KEY=$BASELINE_API_KEY
    echo "Testing BASELINE endpoint..."
fi

echo "  Endpoint: $ENDPOINT"
echo "  Model: $MODEL"
echo ""

# Test 1: Check /v1/models endpoint
echo "============================================"
echo "Test 1: Check available models"
echo "============================================"
echo ""

MODELS_RESPONSE=$(curl -s "${ENDPOINT%/v1}/v1/models" \
  -H "Authorization: Bearer $API_KEY")
if [ $? -eq 0 ]; then
    echo "✅ Models endpoint accessible"
    echo "Response: $MODELS_RESPONSE" | jq '.' 2>/dev/null || echo "$MODELS_RESPONSE"
else
    echo "❌ Failed to connect to models endpoint"
    echo "Error: Check your ENDPOINT configuration"
    exit 1
fi

echo ""

# Test 2: Test completion endpoint
echo "============================================"
echo "Test 2: Test completion API"
echo "============================================"
echo ""

COMPLETION_RESPONSE=$(curl -s "${ENDPOINT%/v1}/v1/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "{
    \"model\": \"$MODEL\",
    \"prompt\": \"Hello, world! Please respond with 'Connection successful'\",
    \"max_tokens\": 20,
    \"temperature\": 0.0
  }")

if [ $? -eq 0 ]; then
    echo "✅ Completion endpoint accessible"
    echo "Response:"
    echo "$COMPLETION_RESPONSE" | jq '.' 2>/dev/null || echo "$COMPLETION_RESPONSE"
else
    echo "❌ Failed to get completion"
    exit 1
fi

echo ""

# Test 3: Test with Python (using actual experiment code)
echo "============================================"
echo "Test 3: Test with Python AutoGen client"
echo "============================================"
echo ""

python3 << 'EOF'
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import config to test
sys.path.insert(0, os.getenv('PROJECT_ROOT'))
from src import config

print(f"Backend: {'RunPod/vLLM' if config.USE_RUNPOD else 'Local Ollama'}")
print(f"Reasoning: {'ENABLED' if config.ENABLE_REASONING else 'DISABLED'}")
print(f"Model: {config.LLM_MODEL}")
print(f"Endpoint: {config.OLLAMA_HOST}")
print(f"API Type: {config.LLM_SERVICE}")
print("")

# Test with AutoGen
try:
    from autogen import AssistantAgent

    test_agent = AssistantAgent(
        name="test_agent",
        system_message="You are a helpful assistant. Respond concisely.",
        llm_config=config.LLM_CONFIG,
        human_input_mode="NEVER"
    )

    response = test_agent.generate_reply(messages=[{
        "content": "Hello! Please respond with: 'RunPod connection successful'",
        "role": "user"
    }])

    if response and "content" in response:
        print("✅ AutoGen client connection successful!")
        print(f"Response: {response['content']}")
    else:
        print("❌ No valid response from AutoGen")
        sys.exit(1)

except Exception as e:
    print(f"❌ AutoGen test failed: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✅ ALL TESTS PASSED"
    echo "============================================"
    echo ""
    echo "RunPod connection is working correctly!"
    echo "You can now run experiments with:"
    echo "  bash scripts/run_rq1_vuln.sh"
else
    echo ""
    echo "============================================"
    echo "❌ TESTS FAILED"
    echo "============================================"
    echo ""
    echo "Please check:"
    echo "1. RunPod endpoint URLs in .env are correct"
    echo "2. vLLM server is running on RunPod"
    echo "3. Model names match HuggingFace format"
    echo "4. API keys are configured (if required)"
fi
