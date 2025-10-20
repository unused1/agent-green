# RunPod Experiment Workflow - Cloud Transfer Method

**Date**: 2025-10-20
**Purpose**: Run RQ1 Phase 2 experiments on RunPod using cloud storage for file transfer
**Why**: RunPod's proxy SSH doesn't support scp/sftp, so we use cloud storage as intermediary

---

## Problem & Solution

### Issue
- ❌ Direct SSH to RunPod doesn't work
- ❌ Proxy SSH doesn't support scp/sftp
- ❌ Can't use `scp` or `sftp` for file transfer

### Solution
- ✅ Prepare experiment files as zip locally
- ✅ Upload zip to cloud storage (Dropbox/Google Drive/transfer.sh)
- ✅ Download zip on RunPod via wget/curl
- ✅ Package results as zip on RunPod
- ✅ Upload results zip to cloud, download locally

---

## Quick Start Guide

### Phase 1: Prepare Upload Package (Local)

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Create upload package
bash scripts/prepare_runpod_upload.sh thinking

# This creates: runpod_upload_thinking_YYYYMMDD_HHMMSS.zip (~3MB)
```

### Phase 2: Upload to Cloud Storage

**Option A: Dropbox**
1. Upload zip file via Dropbox web interface
2. Get share link (e.g., `https://www.dropbox.com/s/xxx/file.zip?dl=0`)
3. Change `dl=0` to `dl=1` for direct download

**Option B: Google Drive**
1. Upload zip via Google Drive
2. Get shareable link
3. Use link directly (or use `gdown` on RunPod)

**Option C: transfer.sh (easiest, 7-day expiry)**
```bash
curl --upload-file runpod_upload_thinking_*.zip https://transfer.sh/agent-green.zip
# Returns download URL immediately
```

### Phase 3: Deploy RunPod Pod

1. Go to https://www.runpod.io/console/pods
2. Select **"Deploy"** → **"GPU Cloud"**
3. Choose GPU:
   - For Qwen3-30B-A3B: **A6000 48GB** (~$0.79/hr) or **A100 40GB** (~$1.39/hr)
   - For Qwen3-235B-A22B: **H100 80GB** (~$2.99/hr)
4. Select template: **vLLM** or **PyTorch** base
5. Configure:
   - Container Disk: 50GB minimum
   - Volume: Optional (not needed for short experiments)
6. Deploy pod and wait for it to start
7. Note the **SSH connection command** from pod details

### Phase 4: Setup Pod Environment

SSH into pod (using RunPod's proxy SSH):

```bash
# Copy SSH command from RunPod console -> Pod -> Connect -> "SSH over exposed TCP"
# Example:
ssh root@<pod-id>-<ssh-port>.proxy.runpod.net

# Or use direct connection if available:
ssh root@<POD_IP> -p <PORT> -i ~/.ssh/runpod_ed25519
```

Download and setup experiment files:

```bash
# 1. Download from cloud storage
cd /workspace

# For transfer.sh:
wget <TRANSFER_SH_URL> -O agent-green.zip

# For Dropbox (with dl=1):
wget '<DROPBOX_LINK_WITH_DL=1>' -O agent-green.zip

# For Google Drive (using gdown):
pip install gdown
gdown <GOOGLE_DRIVE_FILE_ID> -O agent-green.zip

# 2. Extract
unzip agent-green.zip

# 3. Setup environment
cd agent-green
bash scripts/setup_runpod_env.sh
```

### Phase 5: Load Model with vLLM

**For Qwen3-30B-A3B-Instruct-2507:**

```bash
# Install vLLM if not already installed
pip install vllm

# Start vLLM server (in background or separate terminal)
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 4096 \
  --dtype bfloat16

# Wait for model to load (check logs for "Uvicorn running")
```

**For Qwen3-30B-A3B-Thinking-2507:**

```bash
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 4096 \
  --dtype bfloat16
```

### Phase 6: Verify Setup

```bash
# Check vLLM is running
curl http://localhost:8000/v1/models

# Should return JSON with model info
```

### Phase 7: Run Test Experiment (10 samples)

```bash
cd /workspace/agent-green

# For Thinking model:
bash scripts/run_rq1_vuln_runpod.sh reasoning zero test

# For Instruct model:
bash scripts/run_rq1_vuln_runpod.sh baseline zero test

# Check results:
ls -lh results/
```

### Phase 8: Run Full Experiments (386 samples)

**For Thinking model pod:**

```bash
# Run both zero-shot and few-shot (~20-40 min on H100, ~1-2 hours on A6000)
bash scripts/run_rq1_vuln_runpod.sh reasoning all full

# Monitor progress:
tail -f results/*_detailed_results.jsonl
```

**For Instruct model pod:**

```bash
bash scripts/run_rq1_vuln_runpod.sh baseline all full
```

### Phase 9: Package Results for Download

```bash
cd /workspace/agent-green

# Create results zip
bash scripts/package_results.sh

# This creates: /workspace/agent-green-results-YYYYMMDD_HHMMSS.zip
```

### Phase 10: Upload Results to Cloud

**Option A: transfer.sh (easiest)**

```bash
curl --upload-file /workspace/agent-green-results-*.zip https://transfer.sh/results.zip

# Copy the returned URL
```

**Option B: Manual upload**
1. Note the zip file path
2. Download it via RunPod's web interface (if available)
3. Or use cloud storage CLI tools

### Phase 11: Download Results Locally

```bash
# On local machine
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Download from transfer.sh
wget <TRANSFER_SH_URL> -O results_phase2_thinking_$(date +%Y%m%d).zip

# Extract
unzip results_phase2_thinking_*.zip
```

### Phase 12: Stop Pod

**IMPORTANT**: Stop pod to avoid charges!

1. Go to RunPod console
2. Click **"Stop"** on the pod
3. Verify billing stopped

---

## Complete Workflow for Phase 2a (Both Models)

### Model 1: Qwen3-30B-A3B-Thinking-2507

```bash
# LOCAL: Prepare upload
bash scripts/prepare_runpod_upload.sh thinking
curl --upload-file runpod_upload_thinking_*.zip https://transfer.sh/thinking.zip
# Note URL: https://transfer.sh/xxxxx/thinking.zip

# RUNPOD POD 1:
ssh root@<pod1-ssh-address>
wget https://transfer.sh/xxxxx/thinking.zip -O /workspace/agent-green.zip
cd /workspace && unzip agent-green.zip
cd agent-green && bash scripts/setup_runpod_env.sh

# Start vLLM with Thinking model
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --port 8000 --gpu-memory-utilization 0.90 --dtype bfloat16

# Run experiments
bash scripts/run_rq1_vuln_runpod.sh reasoning all full

# Package and upload results
bash scripts/package_results.sh
curl --upload-file /workspace/agent-green-results-*.zip https://transfer.sh/thinking-results.zip
# Note URL

# Stop pod
```

### Model 2: Qwen3-30B-A3B-Instruct-2507

```bash
# LOCAL: Prepare upload (same package works for both)
bash scripts/prepare_runpod_upload.sh instruct
curl --upload-file runpod_upload_instruct_*.zip https://transfer.sh/instruct.zip
# Note URL

# RUNPOD POD 2:
ssh root@<pod2-ssh-address>
wget https://transfer.sh/xxxxx/instruct.zip -O /workspace/agent-green.zip
cd /workspace && unzip agent-green.zip
cd agent-green && bash scripts/setup_runpod_env.sh

# Start vLLM with Instruct model
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --port 8000 --gpu-memory-utilization 0.90 --dtype bfloat16

# Run experiments
bash scripts/run_rq1_vuln_runpod.sh baseline all full

# Package and upload results
bash scripts/package_results.sh
curl --upload-file /workspace/agent-green-results-*.zip https://transfer.sh/instruct-results.zip
# Note URL

# Stop pod
```

### Download All Results Locally

```bash
# LOCAL:
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Download Thinking results
wget <THINKING_RESULTS_URL> -O results_30b_thinking_$(date +%Y%m%d).zip
unzip results_30b_thinking_*.zip -d results_phase2a_thinking/

# Download Instruct results
wget <INSTRUCT_RESULTS_URL> -O results_30b_instruct_$(date +%Y%m%d).zip
unzip results_30b_instruct_*.zip -d results_phase2a_instruct/
```

---

## Cost Estimation

### Qwen3-30B-A3B (Phase 2a)

| GPU | $/hour | Experiments | Time | Cost per pod | Total (2 pods) |
|-----|--------|-------------|------|--------------|----------------|
| A6000 48GB | $0.79 | 2 (zero + few) | ~1.5 hours | $1.19 | **$2.38** |
| A100 40GB | $1.39 | 2 (zero + few) | ~1 hour | $1.39 | **$2.78** |
| H100 80GB | $2.99 | 2 (zero + few) | ~30 min | $1.50 | **$3.00** |

**Recommended**: A6000 48GB for best cost/performance

---

## Files Reference

### Local Scripts
- `scripts/prepare_runpod_upload.sh` - Creates upload zip package
- `scripts/package_results.sh` - Packages results on RunPod (copied to pod)

### On RunPod (after extraction)
- `/workspace/agent-green/scripts/setup_runpod_env.sh` - Setup environment
- `/workspace/agent-green/scripts/run_rq1_vuln_runpod.sh` - Run experiments
- `/workspace/agent-green/vuln_database/VulTrial_386_samples_balanced.jsonl` - Dataset
- `/workspace/agent-green/.env` - Configuration

### Result Files (on RunPod)
- `results/*_detailed_results.jsonl` - Per-sample predictions
- `results/*_detailed_results.csv` - CSV format
- `results/*_energy_tracking.json` - CodeCarbon data
- `results/*_summary_vulnerability_metrics.csv` - F1, precision, recall

---

## Troubleshooting

### Issue: wget fails on RunPod

**Solution**: Check URL is direct download link
- Dropbox: Change `?dl=0` to `?dl=1`
- Google Drive: Use `gdown` instead of `wget`
- transfer.sh: Use URL exactly as provided

### Issue: vLLM model won't load

**Solution**: Check GPU memory
```bash
# Check VRAM
nvidia-smi

# Reduce memory utilization
--gpu-memory-utilization 0.85
```

### Issue: Experiments fail with connection error

**Solution**: Verify vLLM is running
```bash
curl http://localhost:8000/v1/models

# Check vLLM process
ps aux | grep vllm
```

### Issue: Can't upload large results zip

**Solution**: Use transfer.sh with longer retention
```bash
# transfer.sh supports up to 10GB
curl --upload-file results.zip https://transfer.sh/results.zip

# Or split into smaller chunks
split -b 100M results.zip results_part_
```

---

## Next Steps After Phase 2a

1. **Analyze results locally**:
   ```bash
   python notebooks/analyze_phase2a.py
   ```

2. **Compare with Phase 1** (4B models):
   - Performance: Does few-shot help 30B models?
   - Energy: How does 30B-A3B compare to 4B?

3. **Decide on Phase 2b** (235B-A22B):
   - If few-shot improves: Run 235B to confirm trend
   - If few-shot still degrades: May skip 235B (trend clear)
   - If inconclusive: Run 235B for additional data

---

**Estimated Timeline**:
- Setup (per pod): 15-20 minutes
- Experiments (per pod): 1-2 hours
- Results transfer: 5 minutes
- **Total**: ~2.5-3 hours for complete Phase 2a

**Estimated Cost**: $2.40-$3.00 for both models
