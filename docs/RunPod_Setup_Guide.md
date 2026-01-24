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

### 2.2 Install Required Packages
```bash
# Install hf_transfer for fast model downloads
pip install hf_transfer --break-system-packages

# Install experiment dependencies
pip install autogen python-dotenv codecarbon pandas numpy evaluate scikit-learn python-Levenshtein --break-system-packages

pip install vllm --break-system-packages
```

**Note**: vLLM will automatically download models from HuggingFace when you start the server. No need to pre-download.

### 2.3 Start vLLM Server

#### For 30B Baseline Model (Instruct - Non-Reasoning)
```bash
# Create project structure
cd /workspace
mkdir -p agent-green/src agent-green/vuln_database agent-green/results

# Start vLLM server
cd /workspace/agent-green
nohup python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --served-model-name "Qwen/Qwen3-30B-A3B-Instruct-2507" \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 65536 \
  --gpu-memory-utilization 0.9 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  > /workspace/vllm_instruct.log 2>&1 &

# Monitor startup (wait for "Application startup complete")
tail -f /workspace/vllm_instruct.log
```

#### For 30B Reasoning Model (Thinking)
```bash
# Create project structure
cd /workspace
mkdir -p agent-green/src agent-green/vuln_database agent-green/results

# Start vLLM server
cd /workspace/agent-green
nohup python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --served-model-name "Qwen/Qwen3-30B-A3B-Thinking-2507" \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 65536 \
  --gpu-memory-utilization 0.9 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  > /workspace/vllm_thinking.log 2>&1 &

# Monitor startup (wait for "Application startup complete")
tail -f /workspace/vllm_thinking.log
```

#### For 4B Baseline Model (Instruct - Non-Reasoning)
```bash
# Start vLLM server with 4B model
cd /workspace/agent-green
nohup python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-4B \
  --served-model-name "Qwen/Qwen3-4B-Instruct-2507" \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 40960 \
  --gpu-memory-utilization 0.9 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  > /workspace/vllm_instruct.log 2>&1 &

# Monitor startup
tail -f /workspace/vllm_instruct.log
```

#### For 4B Reasoning Model (Thinking)
```bash
# Start vLLM server with 4B Thinking model
cd /workspace/agent-green
nohup python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-4B \
  --served-model-name "Qwen/Qwen3-4B-Thinking-2507" \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 40960 \
  --gpu-memory-utilization 0.9 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  > /workspace/vllm_thinking.log 2>&1 &

# Monitor startup
tail -f /workspace/vllm_thinking.log
```

**Important Notes**:
- Port 8000 is standard vLLM API port
- `--served-model-name` ensures vLLM serves the model with the correct HuggingFace name
- **Max model length varies by model size:**
  - **30B models**: `--max-model-len 65536` (64K context)
  - **4B models**: `--max-model-len 40960` (40K context - model limit)
- `--gpu-memory-utilization 0.9` uses 90% of GPU VRAM for optimal performance
- Model downloads automatically from HuggingFace (~5-10 minutes for 4B, ~15-20 minutes for 30B)

**Verify Server is Running**:
```bash
curl http://localhost:8000/v1/models
# Should show "id": "Qwen/Qwen3-30B-A3B-Instruct-2507" (exact match)
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

### 5.0 Running Log Analysis Experiments (RQ1/RQ2)

#### 5.0.1 Setup Environment File
Upload `.env.qwen3-4b-log` to the pod as `.env`:
```bash
# From local machine
scp -P <PORT> -i ~/.ssh/runpod_ed25519 \
  /path/to/agent-green/.env.qwen3-4b-log \
  root@<IP>:/workspace/agent-green/.env
```

Or create `.env` on the pod:
```bash
cd /workspace/agent-green
cat > .env << 'EOF'
# Qwen3-4B Log Analysis Environment Variables
PROJECT_ROOT=/workspace/agent-green
USE_RUNPOD=true
LLM_SERVICE=openai
LLM_API_BASE=http://localhost:8000/v1
OPENAI_API_KEY=dummy-key
BASELINE_MODEL=Qwen/Qwen3-4B-Instruct-2507
BASELINE_ENDPOINT=http://localhost:8000/v1
BASELINE_API_KEY=dummy-key
REASONING_MODEL=Qwen/Qwen3-4B-Thinking-2507
REASONING_ENDPOINT=http://localhost:8000/v1
REASONING_API_KEY=dummy-key
ENABLE_REASONING=false
EOF
```

#### 5.0.2 Source Environment and Run Experiments
```bash
cd /workspace/agent-green

# Source environment variables (IMPORTANT: use set -a to export all variables)
set -a && source .env && set +a

# Verify variables are set
echo "USE_RUNPOD=$USE_RUNPOD, ENABLE_REASONING=$ENABLE_REASONING"
```

**For Qwen3-4B-Instruct (Zero-shot):**
```bash
# Ensure ENABLE_REASONING=false for Instruct model
export ENABLE_REASONING=false

# Run full (385 sessions)
python src/single_agent_log_analysis.py --shot zero
```

**For Qwen3-4B-Thinking (Zero-shot):**
```bash
# Switch to Thinking model
export ENABLE_REASONING=true

# Restart vLLM with Thinking model first, then:
python src/single_agent_log_analysis.py --shot zero
```

**For Few-shot variants:**
```bash
python src/single_agent_log_analysis.py --shot few
```

#### 5.0.3 Resume Capability
The script saves progress incrementally and can resume from interruptions:
```bash
# If interrupted, simply run the same command again
python src/single_agent_log_analysis.py --shot zero

# The script will:
# - Detect existing results in results/log-analysis_SA-zero_*.jsonl
# - Skip already-processed sessions
# - Continue from where it left off
```

**Environment Variables Explained:**
| Variable | Value | Purpose |
|----------|-------|---------|
| `PROJECT_ROOT` | `/workspace/agent-green` | Sets correct paths for data/results |
| `USE_RUNPOD` | `true` | Switches to OpenAI-compatible API (vLLM) |
| `ENABLE_REASONING` | `false` / `true` | Selects Instruct or Thinking model |
| `LLM_MODEL` | `Qwen/Qwen3-4B-Instruct-2507` | HuggingFace model identifier |
| `LLM_API_BASE` | `http://localhost:8000/v1` | vLLM endpoint |
| `OPENAI_API_KEY` | `dummy-key` | Required by OpenAI client (vLLM ignores it) |

**Correct Model Names for Log Analysis:**
| Short Name | HuggingFace Model ID |
|------------|---------------------|
| Qwen3-4B-Instruct | `Qwen/Qwen3-4B-Instruct-2507` |
| Qwen3-4B-Thinking | `Qwen/Qwen3-4B-Thinking-2507` |
| Qwen3-30B-A3B-Instruct | `Qwen/Qwen3-30B-A3B-Instruct-2507` |
| Qwen3-30B-A3B-Thinking | `Qwen/Qwen3-30B-A3B-Thinking-2507` |

### 5.1 Running Vulnerability Detection Experiments (CRITICAL Environment Variables)

**When running experiments directly on RunPod pods**, you MUST set these environment variables:

#### For 30B Instruct Model (Baseline):
```bash
cd /workspace

# Install required dependencies if missing
pip3 install ollama fix-busted-json

# Set environment variables
export ENABLE_REASONING=false
export USE_RUNPOD=true
export BASELINE_MODEL="Qwen/Qwen3-30B-A3B-Instruct-2507"
export OLLAMA_HOST="http://localhost:11434"

# Run experiment
python3 src/single_agent_vuln.py SA-few
```

#### For 30B Thinking Model (Reasoning):
```bash
cd /workspace

# Install required dependencies if missing
pip3 install ollama fix-busted-json

# Set environment variables
export ENABLE_REASONING=true
export USE_RUNPOD=true
export REASONING_MODEL="Qwen/Qwen3-30B-A3B-Thinking-2507"
export OLLAMA_HOST="http://localhost:11434"

# Run experiment
python3 src/single_agent_vuln.py SA-few
```

**Why these variables are critical**:
- `USE_RUNPOD=true` - Switches AutoGen to OpenAI-compatible API mode (required for vLLM)
- `BASELINE_MODEL` / `REASONING_MODEL` - Overrides default `qwen3:4b` → prevents 404 errors
- `OLLAMA_HOST` - Points to vLLM server at port 11434
- `ENABLE_REASONING` - Controls which model/prompt to use

**Without these variables**: Script will request `qwen3:4b` which vLLM isn't serving → all samples fail with 404 errors.

### 5.2 Using the RunPod Script (from local machine)
```bash
# Use the RunPod-specific script (requires .env configuration)
bash scripts/run_rq1_vuln_runpod.sh
```

### 5.3 Monitor Progress
```bash
# Watch logs in real-time
tail -f results/*_detailed_results.jsonl

# Check energy tracking
cat results/*_energy_tracking.json

# Count completed samples
wc -l results/*_detailed_results.jsonl
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
