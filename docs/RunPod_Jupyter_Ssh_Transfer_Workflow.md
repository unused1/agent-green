# Phase 2 Workflow - Direct SSH & Jupyter Method

**Date**: 2025-10-20
**Status**: ✅ Phase 2a COMPLETE (4 experiments successful)
**Discovery**: Jupyter/PyTorch template provides BOTH direct SSH access AND Jupyter UI!
**Method**: Automated scp upload/download scripts + Jupyter UI backup
**Models**: Qwen3-30B-A3B-Instruct-2507 & Qwen3-30B-A3B-Thinking-2507
**GPU**: H100 SXM 80GB recommended (A6000 48GB insufficient - requires ~60GB with vLLM overhead)
**Storage**: 100GB Volume Disk (persistent storage for /workspace with model files)
**Approach**: 4 pods in parallel (one per experiment) for clean isolation and faster completion
**Actual Cost**: $9.96 for complete Phase 2a (4 pods × ~1 hr @ $2.49/hr)
**Download**: Method 1 (vLLM auto-download) worked successfully on H100 without XET CDN errors
**Results**: All 4 experiments completed with 386 samples, 17 files per experiment downloaded

---

## Key Discovery

The RunPod **Jupyter Notebook + PyTorch** template provides:
- ✅ Direct SSH access (not proxy)
- ✅ scp/sftp support for automated file transfers
- ✅ Jupyter UI for visual file management (backup)
- ✅ Minimal overhead (<0.5% energy, <0.1% GPU energy)

This means we can use the **original upload/download scripts** that were prepared earlier!

---

## Complete Workflow (~1 hour wall-clock time with 4 pods in parallel)

### Step 1: Deploy 4 RunPod Pods (5 min)

**Deploy 4 H100 pods in parallel - one for each experiment:**
- Pod 1: Thinking zero-shot
- Pod 2: Instruct zero-shot
- Pod 3: Thinking few-shot
- Pod 4: Instruct few-shot

1. Go to https://www.runpod.io/console/pods
2. Click **Deploy** → **GPU Cloud**
3. Select GPU: **H100 SXM 80GB** (~$2.49/hr, recommended)
   - Alternative: A100 SXM 80GB (~$1.39/hr) also works
   - Note: A6000 48GB is insufficient (requires ~60GB with vLLM overhead)
   - **H100 benefit**: Better network connectivity → Method 1 download works reliably without XET CDN errors
4. Template: **Jupyter Notebook + PyTorch**
5. **Volume Disk: 100GB** (persistent storage mounted to /workspace)
   - Model files: ~20GB
   - Git-lfs temporary space: ~20GB during download
   - System/packages: ~10GB
   - Results: ~10-20GB
   - **Note**: Use Volume Disk (not Container Disk) as it persists when pod is stopped
6. Container Disk: Can leave at default (temporary storage)
7. Deploy and wait for pod to start
8. Note **IP address** and **SSH port** from pod details

**Example**:
- IP: 157.66.254.33
- SSH Port: 10839
- Jupyter URL: https://z54gw8lkjhuz84-8888.proxy.runpod.net

---

### Step 2: Upload Experiment Files (1 min)

From your local machine:

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Upload files (automatically uses .env.runpod.phase2 for Phase 2)
bash scripts/upload_to_runpod.sh 157.157.221.29 13196 thinking

# ✓ Upload completed successfully!
# Total time: ~30-60 seconds for ~3MB
```

**What gets uploaded**:
- Python source code (`src/`)
- Experiment scripts (`scripts/`)
- VulTrial dataset (386 samples)
- Phase 2 configuration (`.env.runpod.phase2` → `.env`)
- Requirements file

---

### Step 3: Setup Pod Environment (10 min)

SSH into the pod:

```bash
ssh root@157.157.221.29 -p 13196 -i ~/.ssh/runpod_ed25519

# Setup Python environment
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh
```

**What this does**:
- Installs Python dependencies (autogen, codecarbon, etc.)
- Creates empty results directory
- Displays next steps

---

### Step 4: Download and Start Model (5-15 min)

Try methods sequentially - start with Method 1, fall back to Method 2 or 3 if issues occur.

---

**Method 1 (Fastest): vLLM with Automatic Download**

Try this first - vLLM automatically downloads the model:

```bash
# Create models directory
mkdir -p /workspace/agent-green/models

# Start vLLM - it will auto-download the model
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 &

# Wait for "Uvicorn running on http://0.0.0.0:8000"
# First download takes ~5-10 min (~20GB model)
```

**If you see XET CDN errors** (Status Code: 500 from cas-server.xethub.hf.co), proceed to Method 2.

---

**Method 2 (Fallback): HuggingFace CLI Download**

If Method 1 fails with XET CDN errors:

```bash
# Kill any running vLLM process
pkill -f vllm

# Disable XET accelerated downloads
export HF_HUB_ENABLE_HF_TRANSFER=0
export HF_HUB_DISABLE_XET=1

# Pre-download using huggingface-cli
huggingface-cli download Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --cache-dir /workspace/agent-green/models

# Then start vLLM pointing to downloaded model
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 &
```

**If this still fails**, proceed to Method 3.

---

**Method 3 (Most Reliable): Git-LFS Clone**

If both methods above fail, use git-lfs for most reliable download:

```bash
# Kill any running processes
pkill -f vllm

# Install git-lfs
apt-get update && apt-get install -y git-lfs
git lfs install

# Clone model repository with git-lfs
cd /workspace/agent-green/models
GIT_LFS_SKIP_SMUDGE=0 git clone https://huggingface.co/Qwen/Qwen3-30B-A3B-Thinking-2507

# If interrupted, resume with:
# cd Qwen3-30B-A3B-Thinking-2507 && git lfs pull

# Start vLLM pointing to local clone
python -m vllm.entrypoints.openai.api_server \
  --model /workspace/agent-green/models/Qwen3-30B-A3B-Thinking-2507 \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 &
```

---

**Verify vLLM is Running**:

```bash
curl http://localhost:8000/v1/models
# Should return JSON with model info
```

---

### Step 5: Repeat for Instruct Model (on second pod)

Deploy a second A100 80GB pod (100GB Volume Disk) and repeat Steps 2-4 with the Instruct model.

Use the same sequential approach - try Method 1, fall back to Method 2 or 3 if needed:

```bash
# Method 1 (try first)
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 &

# If XET CDN errors, try Method 2 (huggingface-cli)
# If still failing, use Method 3 (git-lfs clone)
```

---

### Step 6: Run Test Experiment (2 min)

**On Thinking pod**:

```bash
cd /workspace/agent-green

# Quick test (10 samples)
bash scripts/run_rq1_vuln_runpod.sh reasoning zero test

# Check results
ls -lh results/
cat results/*_summary_vulnerability_metrics.csv
```

**On Instruct pod**:

```bash
bash scripts/run_rq1_vuln_runpod.sh baseline zero test
```

---

### Step 7: Run All 4 Experiments in Parallel (~30-60 min)

**Run all 4 experiments simultaneously - each pod gets one experiment:**

**Pod 1 (Thinking zero-shot)**:
```bash
bash scripts/run_rq1_vuln_runpod.sh reasoning zero full
```

**Pod 2 (Instruct zero-shot)**:
```bash
bash scripts/run_rq1_vuln_runpod.sh baseline zero full
```

**Pod 3 (Thinking few-shot)**:
```bash
bash scripts/run_rq1_vuln_runpod.sh reasoning few full
```

**Pod 4 (Instruct few-shot)**:
```bash
bash scripts/run_rq1_vuln_runpod.sh baseline few full
```

**Monitor progress on any pod**:
```bash
# Count samples processed
wc -l results/*_detailed_results.jsonl

# Watch live progress
tail -f results/*_detailed_results.jsonl

# Check energy consumption
cat results/*_energy_tracking.json | python3 -m json.tool
```

**Benefits of 4-pod approach:**
- ✅ **Faster**: All experiments complete in ~30-60 min (vs 1-2 hours sequential)
- ✅ **Cleaner isolation**: Each experiment gets a completely fresh pod (no vLLM state carryover)
- ✅ **Same cost**: 4 pods × 1 hr ≈ 2 pods × 2 hr (~$9.96 total)

---

### Step 8: Download Results from All 4 Pods (2-3 min)

From your **local machine**:

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Download from Pod 1 (Thinking zero-shot)
bash scripts/download_from_runpod.sh <POD1_IP> <POD1_PORT> thinking_zero

# Download from Pod 2 (Instruct zero-shot)
bash scripts/download_from_runpod.sh <POD2_IP> <POD2_PORT> instruct_zero

# Download from Pod 3 (Thinking few-shot)
bash scripts/download_from_runpod.sh <POD3_IP> <POD3_PORT> thinking_few

# Download from Pod 4 (Instruct few-shot)
bash scripts/download_from_runpod.sh <POD4_IP> <POD4_PORT> instruct_few

# All results saved to separate directories:
# - results_runpod_thinking_zero_20251020_HHMMSS/
# - results_runpod_instruct_zero_20251020_HHMMSS/
# - results_runpod_thinking_few_20251020_HHMMSS/
# - results_runpod_instruct_few_20251020_HHMMSS/
```

---

### Step 9: Stop All 4 Pods ⚠️ CRITICAL

**Don't forget or you'll keep getting charged!**

1. Go to https://www.runpod.io/console/pods
2. Click **Stop** on all 4 pods
3. Verify billing stopped for all instances

---

## Complete Command Sequence (4 Pods in Parallel)

### On Local Machine:

```bash
# ===== DEPLOY ALL 4 PODS =====
# Deploy 4× H100 80GB pods in RunPod web console with Jupyter/PyTorch template
# Note IP and port for each

# Upload files to all 4 pods
bash scripts/upload_to_runpod.sh <POD1_IP> <POD1_PORT> thinking  # Zero-shot
bash scripts/upload_to_runpod.sh <POD2_IP> <POD2_PORT> instruct  # Zero-shot
bash scripts/upload_to_runpod.sh <POD3_IP> <POD3_PORT> thinking  # Few-shot
bash scripts/upload_to_runpod.sh <POD4_IP> <POD4_PORT> instruct  # Few-shot
```

### On Pod 1 (Thinking Zero-shot):

```bash
ssh root@<POD1_IP> -p <POD1_PORT> -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green && bash scripts/setup_runpod_env.sh

# Start vLLM with Thinking model
mkdir -p /workspace/agent-green/models
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 --dtype auto --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 --port 8000 &

# Run zero-shot experiment
curl http://localhost:8000/v1/models
bash scripts/run_rq1_vuln_runpod.sh reasoning zero full
```

### On Pod 2 (Instruct Zero-shot):

```bash
ssh root@<POD2_IP> -p <POD2_PORT> -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green && bash scripts/setup_runpod_env.sh

# Start vLLM with Instruct model
mkdir -p /workspace/agent-green/models
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 --dtype auto --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 --port 8000 &

# Run zero-shot experiment
curl http://localhost:8000/v1/models
bash scripts/run_rq1_vuln_runpod.sh baseline zero full
```

### On Pod 3 (Thinking Few-shot):

```bash
ssh root@<POD3_IP> -p <POD3_PORT> -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green && bash scripts/setup_runpod_env.sh

# Start vLLM with Thinking model
mkdir -p /workspace/agent-green/models
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 --dtype auto --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 --port 8000 &

# Run few-shot experiment
curl http://localhost:8000/v1/models
bash scripts/run_rq1_vuln_runpod.sh reasoning few full
```

### On Pod 4 (Instruct Few-shot):

```bash
ssh root@<POD4_IP> -p <POD4_PORT> -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green && bash scripts/setup_runpod_env.sh

# Start vLLM with Instruct model
mkdir -p /workspace/agent-green/models
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 --dtype auto --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 --port 8000 &

# Run few-shot experiment
curl http://localhost:8000/v1/models
bash scripts/run_rq1_vuln_runpod.sh baseline few full
```

### Back on Local Machine (after experiments complete):

```bash
# Download results from all 4 pods
bash scripts/download_from_runpod.sh <POD1_IP> <POD1_PORT> thinking_zero
bash scripts/download_from_runpod.sh <POD2_IP> <POD2_PORT> instruct_zero
bash scripts/download_from_runpod.sh <POD3_IP> <POD3_PORT> thinking_few
bash scripts/download_from_runpod.sh <POD4_IP> <POD4_PORT> instruct_few

# Stop all 4 pods in RunPod console!
```

---

## Backup Option: Jupyter UI

If you prefer visual file management:

**Upload**:
1. Open Jupyter URL in browser: https://g77al0xoeq32cm-8888.proxy.runpod.net
2. Navigate to `/workspace/`
3. Click Upload button
4. Drag and drop files

**Download**:
1. Navigate to `/workspace/agent-green/results/`
2. Select files
3. Right-click → Download

---

## Timeline & Cost

| Task | Time | Cost (A100 @$1.39/hr) |
|------|------|------------------------|
| Deploy pod | 5 min | - |
| Upload files (scp) | 1 min | $0.02 |
| Setup environment | 10 min | $0.23 |
| Load model | 5-10 min | $0.12-0.23 |
| Test experiment | 2 min | $0.05 |
| **Full experiments** | **1-2 hours** | **$1.39-2.78** |
| Download results (scp) | 1 min | $0.02 |
| **TOTAL (per pod)** | **~1.5-2.5 hours** | **~$1.83-3.45** |
| **Both pods** | **~1.5-2.5 hours** | **~$3.66-$6.90** |

**Note**: Pods can run in parallel, so wall-clock time is ~1.5-2.5 hours total

---

## Expected Results

After downloading, you'll have:

```
results_runpod_thinking_YYYYMMDD_HHMMSS/
├── qwen3_30b_thinking_zero_shot_detailed_results.jsonl
├── qwen3_30b_thinking_zero_shot_detailed_results.csv
├── qwen3_30b_thinking_zero_shot_energy_tracking.json
├── qwen3_30b_thinking_zero_shot_summary_vulnerability_metrics.csv
├── qwen3_30b_thinking_few_shot_detailed_results.jsonl
├── qwen3_30b_thinking_few_shot_detailed_results.csv
├── qwen3_30b_thinking_few_shot_energy_tracking.json
└── qwen3_30b_thinking_few_shot_summary_vulnerability_metrics.csv

results_runpod_instruct_YYYYMMDD_HHMMSS/
├── qwen3_30b_instruct_zero_shot_detailed_results.jsonl
├── qwen3_30b_instruct_zero_shot_detailed_results.csv
├── qwen3_30b_instruct_zero_shot_energy_tracking.json
├── qwen3_30b_instruct_zero_shot_summary_vulnerability_metrics.csv
├── qwen3_30b_instruct_few_shot_detailed_results.jsonl
├── qwen3_30b_instruct_few_shot_detailed_results.csv
├── qwen3_30b_instruct_few_shot_energy_tracking.json
└── qwen3_30b_instruct_few_shot_summary_vulnerability_metrics.csv
```

**Total**: 16 result files (4 experiments × 4 files each)

---

## Troubleshooting

### Issue: scp upload fails

```bash
# Test SSH connection first
ssh root@<POD_IP> -p <PORT> -i ~/.ssh/runpod_ed25519 "ls /workspace"

# Check SSH key permissions
chmod 600 ~/.ssh/runpod_ed25519

# Try manual upload
scp -P <PORT> -i ~/.ssh/runpod_ed25519 test.txt root@<POD_IP>:/workspace/
```

### Issue: vLLM won't start

```bash
# Check GPU memory
nvidia-smi

# Kill any existing vLLM processes
pkill -f vllm

# Reduce memory utilization
--gpu-memory-utilization 0.85
```

### Issue: Model download is slow

This is normal for first download (~20GB model):
- H100: ~2-5 min
- A6000: ~5-10 min
- Watch logs: `tail -f ~/.cache/huggingface/hub/models--*.log`

---

## Advantages of This Method

✅ **Fastest**: Automated scp transfers (~1 min vs 5-10 min manual)
✅ **Most reliable**: Direct SSH (no proxy issues)
✅ **Scriptable**: Can automate entire workflow
✅ **Backup option**: Jupyter UI still available
✅ **Minimal overhead**: <0.5% energy from Jupyter
✅ **Proven**: Scripts already tested and working

---

## Next Steps After Download

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Analyze Phase 2a results
# Compare with Phase 1 (4B models)

# Key questions:
# 1. Does few-shot help 30B-A3B (unlike 4B)?
# 2. How does energy scale from 4B to 30B-A3B?
# 3. Thinking vs Instruct performance gap at 30B scale?
```

---

## Summary

**Best solution found**: Jupyter/PyTorch template gives us EVERYTHING:
- Direct SSH for automated scripts
- scp for fast file transfers
- Jupyter UI for manual management
- Minimal energy overhead (<0.5%)

**Ready to proceed with Phase 2a!** 🚀
