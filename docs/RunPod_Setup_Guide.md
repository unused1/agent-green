# RunPod Setup Guide for RQ1 Experiments

## Overview
This guide walks you through setting up RunPod with vLLM to run your vulnerability detection experiments 20-30x faster than local execution.

## Prerequisites
- RunPod account (https://www.runpod.io/)
- Credit card for GPU billing (~$0.70-2.90/hour depending on GPU)
- SSH key for secure access

## Step 1: Create RunPod Pod

### 1.1 Select Template
1. Go to https://www.runpod.io/console/pods
2. Click **"Deploy"** → **"GPU Cloud"**
3. Select GPU type:
   - **⭐ RECOMMENDED**: NVIDIA H100 (80GB VRAM) - ~$2.89/hour (3-4x faster than A40, done in ~1 hour)
   - **Budget**: NVIDIA A40 (48GB VRAM) - ~$0.79/hour (2-4 hours)
   - **Budget**: RTX A6000 (48GB VRAM) - ~$0.69/hour (2-4 hours)
   - **Alternative**: NVIDIA A100 (80GB VRAM) - ~$1.89/hour (1.5-3 hours)

### 1.2 Select vLLM Template
1. Search for **"vLLM"** in Community Templates
2. Select: **"RunPod vLLM"** or **"vLLM OpenAI Compatible"**
3. Configure:
   - **Container Disk**: 50 GB (minimum)
   - **Volume Disk**: Not required for this experiment
   - **Expose HTTP Ports**: 8000, 8001 (for vLLM API)
   - **Expose TCP Ports**: 22 (for SSH)

### 1.3 Deploy Pod
1. Click **"Deploy"**
2. Wait for pod to be **"Running"** (usually 1-2 minutes)
3. Note down:
   - **Pod ID** (e.g., `abc123xyz`)
   - **HTTP Endpoint** (e.g., `https://abc123xyz-8000.proxy.runpod.net`)
   - **SSH Connection** (e.g., `ssh root@ssh.runpod.io -p 12345 -i ~/.ssh/id_ed25519`)

## Step 2: Install Model on RunPod

### 2.1 SSH into Pod
```bash
ssh root@ssh.runpod.io -p <YOUR_PORT> -i ~/.ssh/id_ed25519
```

### 2.2 Download Qwen Models
```bash
# Install Hugging Face CLI if not available
pip install huggingface-hub

# Download Qwen2.5-Coder-7B-Instruct (baseline model)
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct --local-dir /workspace/models/Qwen2.5-Coder-7B-Instruct

# Download QwQ-32B-Preview (reasoning model) - OPTIONAL for larger experiments
# huggingface-cli download Qwen/QwQ-32B-Preview --local-dir /workspace/models/QwQ-32B-Preview
```

**Note**: For this experiment, we'll use **Qwen2.5-Coder-7B-Instruct** instead of qwen3:4b-thinking (which is Ollama-specific). The 7B model provides better performance on RunPod.

### 2.3 Start vLLM Server

#### For Baseline Model (Non-Reasoning)
```bash
python -m vllm.entrypoints.openai.api_server \
  --model /workspace/models/Qwen2.5-Coder-7B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9
```

#### For Reasoning Model (if using QwQ-32B)
```bash
python -m vllm.entrypoints.openai.api_server \
  --model /workspace/models/QwQ-32B-Preview \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.95
```

**Tip**: Run vLLM in background with `nohup` or `tmux`:
```bash
tmux new -s vllm
# Run vLLM command above
# Press Ctrl+B, then D to detach
```

## Step 3: Configure Local Environment

### 3.1 Update .env File
```bash
# Copy your .env
cp .env .env.backup

# Update with RunPod endpoints
nano .env
```

Add these lines to `.env`:
```bash
# RunPod Endpoints
RUNPOD_BASELINE_ENDPOINT=https://<YOUR_POD_ID>-8000.proxy.runpod.net/v1
RUNPOD_REASONING_ENDPOINT=https://<YOUR_POD_ID>-8000.proxy.runpod.net/v1

# Use RunPod for experiments
USE_RUNPOD=true

# Model names (vLLM uses model paths)
REASONING_MODEL=Qwen/QwQ-32B-Preview
BASELINE_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
```

### 3.2 Test Connection
```bash
# Test baseline model
curl https://<YOUR_POD_ID>-8000.proxy.runpod.net/v1/models

# Test inference
curl https://<YOUR_POD_ID>-8000.proxy.runpod.net/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
    "prompt": "Hello, world!",
    "max_tokens": 50
  }'
```

## Step 4: Update Config for vLLM

Your existing `src/config.py` needs minor updates to support vLLM's OpenAI-compatible API.

**Key changes needed**:
1. Change `api_type` from `"ollama"` to `"openai"` when using RunPod
2. Use full model names instead of Ollama tags
3. Add API base URL for vLLM endpoint

I'll create an updated config in the next step.

## Step 5: Run Experiments on RunPod

### 5.1 Using the RunPod Script
```bash
# Use the RunPod-specific script (to be created)
bash scripts/run_rq1_vuln_runpod.sh
```

### 5.2 Monitor Progress
```bash
# Watch logs in real-time
tail -f results/*_detailed_results.jsonl

# Check energy tracking
cat results/*_energy_tracking.json
```

## Step 6: Cost Estimation

### GPU Costs (for 4 experiments, 386 samples each)

#### H100 (Recommended)
- **Rate**: $2.89/hour
- **Estimated time**: 0.7-1.5 hours
- **GPU cost**: ~$2.02-4.34
- **Total with storage**: ~$2.20-4.50

#### A40 (Budget)
- **Rate**: $0.79/hour
- **Estimated time**: 2-4 hours
- **GPU cost**: ~$1.58-3.16
- **Total with storage**: ~$1.75-3.35

#### A100 (Alternative)
- **Rate**: $1.89/hour
- **Estimated time**: 1.5-3 hours
- **GPU cost**: ~$2.84-5.67
- **Total with storage**: ~$3.00-5.85

### Storage
- **Model storage**: ~15 GB (Qwen2.5-Coder-7B)
- **Storage cost**: $0.10/GB/month (negligible for short experiment)

### Value Analysis
**H100 is the best choice**: Saves 1-3 hours of your time for only $0.50-1.50 extra vs A40. In research, your time is worth more than the small cost difference.

## Step 7: Cleanup

### 7.1 Download Results
```bash
# From local machine
scp -r -P <YOUR_SSH_PORT> root@ssh.runpod.io:/workspace/results ./results_runpod
```

### 7.2 Stop Pod
1. Go to RunPod console
2. Click **"Stop"** on your pod
3. Verify billing stops (check usage tab)

### 7.3 Delete Pod (Optional)
- Click **"Delete"** if you won't reuse
- Storage is deleted immediately

## Troubleshooting

### Issue: vLLM won't start
**Solution**: Check GPU memory
```bash
nvidia-smi  # Should show available VRAM
```

### Issue: Connection timeout
**Solution**: Verify pod is running and ports are exposed
```bash
curl https://<YOUR_POD_ID>-8000.proxy.runpod.net/health
```

### Issue: Model not found
**Solution**: Re-download model
```bash
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct --local-dir /workspace/models/Qwen2.5-Coder-7B-Instruct --resume-download
```

## Next Steps

1. ✅ Create RunPod pod with vLLM template
2. ✅ Download Qwen models
3. ✅ Start vLLM server
4. ✅ Update local .env with RunPod endpoint
5. ✅ Run test with 10 samples
6. ✅ Run full experiment (386 samples × 4 configs)
7. ✅ Download results and stop pod

---

**Need help?** Check RunPod docs: https://docs.runpod.io/
