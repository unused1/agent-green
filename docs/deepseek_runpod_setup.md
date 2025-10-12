# DeepSeek-Coder-33B-Instruct on RunPod

## Overview
This guide provides instructions for deploying DeepSeek-Coder-33B-Instruct on RunPod using vLLM for high-performance inference.

## Model Requirements
- **Model**: DeepSeek-Coder-33B-Instruct
- **Size**: ~66GB (33B parameters in FP16)
- **VRAM Required**: ~70GB (with overhead)
- **Recommended GPU**: A100 80GB, H100 80GB, or multiple GPUs
- **Context Length**: 16K tokens native (we use 8K for memory efficiency)

## RunPod Setup

### Step 1: Create RunPod Account
1. Sign up at [runpod.io](https://runpod.io)
2. Add credits to your account
3. Navigate to "Pods" section

### Step 2: Select GPU Configuration

#### Option A: Single GPU (Recommended)
- **H100 80GB**: Best performance, ~$3.5-4/hour
- **A100 80GB**: Good performance, ~$2-2.5/hour
- **A6000 48GB x2**: May work with quantization

#### Option B: Multi-GPU (If single 80GB not available)
- **2x A100 40GB**: Use tensor parallelism
- **2x A6000 48GB**: Use tensor parallelism

### Step 3: Deploy Pod with vLLM Template

1. **Click "Deploy" and select "vLLM" template** or use custom template

2. **Configure Pod Settings:**

```yaml
Container Image: vllm/vllm-openai:latest
Container Disk: 150 GB (IMPORTANT: DeepSeek-33B needs ~70GB + overhead)
Volume Disk: 100 GB (recommended for model persistence)
Volume Mount Path: /workspace
```

**Volume Configuration Benefits:**
- **/workspace**: Standard RunPod mount point
- Models downloaded here persist across pod restarts
- Useful for storing experiment results and logs
- Can be shared between pods

3. **Set Environment Variables:**
```bash
HUGGING_FACE_HUB_TOKEN=<your_hf_token_if_needed>
HF_HOME=/workspace/huggingface
```

4. **Container Start Command:**

For single GPU (Conservative - 8K context):
```bash
--host 0.0.0.0 \
--port 8000 \
--model deepseek-ai/deepseek-coder-33b-instruct \
--download-dir /workspace/models \
--dtype auto \
--gpu-memory-utilization 0.95 \
--max-model-len 8192 \
--trust-remote-code \
--api-key YOUR_SECURE_API_KEY
```

For single GPU (Full 16K context - requires more VRAM):
```bash
--host 0.0.0.0 \
--port 8000 \
--model deepseek-ai/deepseek-coder-33b-instruct \
--download-dir /workspace/models \
--dtype auto \
--gpu-memory-utilization 0.95 \
--max-model-len 16384 \
--trust-remote-code \
--api-key YOUR_SECURE_API_KEY
```

For troubleshooting/memory issues (with optimizations):
```bash
--host 0.0.0.0 \
--port 8000 \
--model deepseek-ai/deepseek-coder-33b-instruct \
--download-dir /workspace/models \
--dtype bfloat16 \
--gpu-memory-utilization 0.90 \
--max-model-len 4096 \
--enforce-eager \
--trust-remote-code \
--api-key YOUR_SECURE_API_KEY
```

For multi-GPU (2x A100 40GB):
```bash
--host 0.0.0.0 \
--port 8000 \
--model deepseek-ai/deepseek-coder-33b-instruct \
--download-dir /workspace/models \
--dtype auto \
--tensor-parallel-size 2 \
--gpu-memory-utilization 0.95 \
--max-model-len 8192 \
--trust-remote-code \
--api-key YOUR_SECURE_API_KEY
```

**Note**: Replace `YOUR_SECURE_API_KEY` with a strong random string for API authentication.

**Context Length & Optimization Considerations:**
- **8K tokens (8192)**: Recommended for A100 80GB, stable performance, sufficient for most code tasks
- **16K tokens (16384)**: Full native context, requires H100 80GB or careful memory management
- **4K tokens (4096)**: Use if encountering OOM errors on smaller GPUs
- For vulnerability detection/fault localization, 8K is typically sufficient

**When to use optimization flags:**
- **`--dtype bfloat16`**: Use when memory is tight or on H100/A100 (good bfloat16 support)
- **`--enforce-eager`**: Use only if encountering CUDA graph compilation errors or for debugging
- **Default (`--dtype auto`)**: Best for most cases, lets vLLM choose optimal precision
- **Avoid `--enforce-eager` in production**: 10-20% slower inference

**Security flag:**
- **`--trust-remote-code`**: Required for DeepSeek models as they include custom model code
- This flag allows execution of Python code from the model repository
- Safe for official DeepSeek models from `deepseek-ai` organization
- Without this flag, you'll get an error about untrusted remote code

### Step 4: Launch Pod

1. Click "Deploy On-Demand" or "Deploy Spot" (cheaper but can be interrupted)
2. Wait for pod to initialize (5-15 minutes for model download)
3. Monitor logs in RunPod console

### Step 5: Get Endpoint URL

Once deployed, RunPod will provide:
- **Pod ID**: e.g., `abc123def456`
- **Direct URL**: e.g., `https://abc123def456-8000.proxy.runpod.net`

## Testing the Deployment

### From RunPod Web Terminal
```bash
# Check if model is loaded
curl http://localhost:8000/v1/models

# Test inference
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SECURE_API_KEY" \
  -d '{
    "model": "deepseek-ai/deepseek-coder-33b-instruct",
    "messages": [{"role": "user", "content": "Write a Python function to detect SQL injection"}],
    "max_tokens": 100,
    "temperature": 0
  }'
```

### From Your Local Machine
```bash
# Replace with your actual RunPod URL
RUNPOD_URL="https://abc123def456-8000.proxy.runpod.net"
API_KEY="YOUR_SECURE_API_KEY"

# Test connection
curl $RUNPOD_URL/v1/models \
  -H "Authorization: Bearer $API_KEY"

# Test vulnerability detection
curl $RUNPOD_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "deepseek-ai/deepseek-coder-33b-instruct",
    "messages": [{"role": "user", "content": "Is this code vulnerable? void func() { char buffer[10]; gets(buffer); }"}],
    "max_tokens": 150,
    "temperature": 0
  }'
```

## Update Local Environment

### 1. Add to `.env` file:
```bash
# DeepSeek on RunPod
DEEPSEEK_INFERENCE_ENDPOINT=https://abc123def456-8000.proxy.runpod.net/v1
DEEPSEEK_API_KEY=YOUR_SECURE_API_KEY
```

### 2. Update Scripts (Already Done)
The scripts are already configured to use `DEEPSEEK_INFERENCE_ENDPOINT` when running DeepSeek models.

## Cost Optimization

### Spot Instances
- 50-70% cheaper than on-demand
- Can be interrupted (save work frequently)
- Good for batch processing

### Auto-stop Settings
```bash
# In RunPod console, set:
Auto-stop: 30 minutes (stops after idle)
```

### Model Optimizations
If memory is tight:
- Reduce `--max-model-len` to 4096 or 2048
- Use `--dtype bfloat16` instead of auto (better stability, same memory as float16)
- Lower `--gpu-memory-utilization` to 0.90
- Add `--enforce-eager` if encountering CUDA graph issues (slower but more stable)

## Monitoring and Troubleshooting

### Check Pod Status
1. Go to RunPod dashboard
2. Click on your pod
3. View "Logs" tab for real-time output

### Common Issues

#### 1. Disk Quota Exceeded Error
**Error**: `OSError: [Errno 122] Disk quota exceeded`
**Solution**: 
- Increase Container Disk to at least 150GB
- Use Volume Disk (100GB+) with `/workspace` mount
- Ensure `--download-dir /workspace/models` in start command
- DeepSeek-33B requires ~70GB just for model files

#### 2. CUDA Out of Memory
```bash
# Reduce context length
--max-model-len 4096

# Or use quantization
--dtype bfloat16
```

#### 2. Model Download Timeout
- RunPod usually caches popular models
- If not cached, download can take 10-20 minutes
- Check logs for download progress

#### 3. Connection Issues
- Ensure API key matches in request headers
- Check if pod is still running
- Verify endpoint URL is correct

#### 4. Slow Response Times
- Normal for 33B model: ~5-15 tokens/second
- Consider using streaming for better UX

## Running Experiments

### Update Scripts to Use RunPod Endpoint

The scripts will automatically use RunPod when you:
1. Set `DEEPSEEK_INFERENCE_ENDPOINT` in `.env`
2. Select DeepSeek model from the menu
3. Ensure API key is configured

### Example Script Execution
```bash
# Run vulnerability detection
python src/replication/vulnerability_detection/vulnerability_detection_multi_llm_A54.py
# Select option 15 for deepseek-coder-33b-instruct

# Run fault localization
python src/replication/fault_localization/fault_localization_multi_llm.py
# Select option 15 for deepseek-coder-33b-instruct
```

## Cleanup

### Stop Pod
1. Go to RunPod dashboard
2. Click "Stop" to pause (keeps storage)
3. Click "Terminate" to fully remove (deletes everything)

### Billing
- Charged per second while running
- Storage charged separately if pod is stopped
- No charges after termination

## Persistent Storage Options

### Option 1: Pod Volume (Included Above)
- **Path**: `/workspace`
- **Size**: 50-100 GB
- **Persists**: During pod lifecycle
- **Best for**: Single experiment sessions

### Option 2: Network Volume (Recommended for Multiple Runs)
For frequent use:
1. Create a Network Volume in RunPod dashboard
2. Attach to pod during creation
3. Models persist across different pods

```yaml
# Pod Creation Settings
Network Volume: Select your created volume
Volume Mount Path: /workspace
```

**Benefits of Network Volume:**
- Download model once, use many times
- Share models between different pods
- Store experiment results permanently
- Faster pod startup (no re-download)
- Cost-effective for multiple experiments

### Volume Directory Structure
```bash
/workspace/
├── models/           # vLLM model cache
│   └── deepseek-ai/
│       └── deepseek-coder-33b-instruct/
├── results/          # Experiment outputs
├── logs/            # Inference logs
└── huggingface/     # HF cache (if HF_HOME set)
```

## Performance Expectations

- **Inference Speed**: 5-15 tokens/second
- **First Token Latency**: 2-5 seconds
- **Context Processing**: ~1-2 seconds per 1K tokens
- **Batch Size**: 1-4 depending on memory

## Security Notes

1. **API Key**: Use a strong, unique API key
2. **Endpoint**: RunPod provides HTTPS by default
3. **Data**: Be mindful of sending sensitive code
4. **Logs**: Clear logs after experiments if needed

## Support

- RunPod Discord: [discord.gg/runpod](https://discord.gg/runpod)
- RunPod Docs: [docs.runpod.io](https://docs.runpod.io)
- vLLM Issues: [github.com/vllm-project/vllm](https://github.com/vllm-project/vllm)