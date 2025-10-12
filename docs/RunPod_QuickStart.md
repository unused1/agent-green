# RunPod Quick Start Guide

## Summary
Run your RQ1 vulnerability detection experiments 20-30x faster on RunPod with vLLM.

**Time savings**: 26 hours (local) → **0.7-1.5 hours (H100)** or 2-4 hours (A40)
**Cost estimate**: $2-5 for complete experiments

---

## Step 1: Create RunPod Pod (5 minutes)

### 1.1 Deploy Pod
1. Go to https://www.runpod.io/console/pods
2. Click **"Deploy"** → **"GPU Cloud"**
3. Select GPU (choose one):
   - **NVIDIA H100 (80GB)** - $2.89/hour ⭐ **RECOMMENDED** (3-4x faster, done in ~1 hour)
   - NVIDIA A40 (48GB) - $0.79/hour (budget option, 2-4 hours)
   - RTX A6000 (48GB) - $0.69/hour (budget option, 2-4 hours)
4. Template: Search "vLLM" → Select **"RunPod vLLM"**
5. Configure:
   - Container Disk: 50 GB
   - Expose HTTP: 8000, 8001
   - Expose TCP: 22
6. Click **"Deploy"**
7. Wait for status: **"Running"**

### 1.2 Note Your Credentials
From the pod dashboard, copy:
- **HTTP Endpoint**: `https://abc123xyz-8000.proxy.runpod.net`
- **SSH Command**: `ssh root@ssh.runpod.io -p 12345 -i ~/.ssh/id_ed25519`

---

## Step 2: Install Model on RunPod (10-15 minutes)

### 2.1 SSH into Pod
```bash
ssh root@ssh.runpod.io -p <YOUR_PORT> -i ~/.ssh/id_ed25519
```

### 2.2 Download Model
```bash
# Install HuggingFace CLI
pip install huggingface-hub

# Download Qwen2.5-Coder-7B-Instruct (baseline model, ~14 GB)
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct \
  --local-dir /workspace/models/Qwen2.5-Coder-7B-Instruct
```

**Note**: For reasoning experiments, you can also download QwQ-32B-Preview (~64 GB), but the 7B model is sufficient for initial testing.

### 2.3 Start vLLM Server
```bash
# Start in tmux to keep running
tmux new -s vllm

# Run vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model /workspace/models/Qwen2.5-Coder-7B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9

# Press Ctrl+B, then D to detach from tmux
```

**Verify server is running**:
```bash
curl https://<YOUR_POD_ID>-8000.proxy.runpod.net/v1/models
```

---

## Step 3: Configure Local Environment (2 minutes)

### 3.1 Update .env File
```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Edit .env
nano .env
```

Add these lines (replace `<YOUR_POD_ID>` with actual value):
```bash
# Enable RunPod
USE_RUNPOD=true

# RunPod Endpoints
REASONING_ENDPOINT=https://<YOUR_POD_ID>-8000.proxy.runpod.net/v1
BASELINE_ENDPOINT=https://<YOUR_POD_ID>-8000.proxy.runpod.net/v1

# Model names (HuggingFace format)
REASONING_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
BASELINE_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct

# Reasoning toggle (this will be changed by experiment script)
ENABLE_REASONING=false
```

**Save and exit**: Ctrl+O, Enter, Ctrl+X

---

## Step 4: Test Connection (1 minute)

```bash
bash scripts/test_runpod_connection.sh
```

**Expected output**:
```
✅ Models endpoint accessible
✅ Completion endpoint accessible
✅ AutoGen client connection successful!
✅ ALL TESTS PASSED
```

If tests fail, check:
- Pod is running (check RunPod dashboard)
- vLLM server is running (SSH into pod, run `tmux attach -t vllm`)
- Endpoint URL is correct in .env

---

## Step 5: Run Experiments (0.7-1.5 hours on H100, 2-4 hours on A40)

### 5.1 Test with 10 Samples (< 1 minute on H100, 2-3 minutes on A40)
```bash
# Uses test dataset (10 samples)
export VULN_DATASET="$PWD/vuln_database/VulTrial_10_samples_test.jsonl"
bash scripts/run_rq1_vuln.sh
```

### 5.2 Run Full Experiments (0.7-1.5 hours on H100, 2-4 hours on A40)
```bash
# Remove test dataset override to use full 386 samples
unset VULN_DATASET
bash scripts/run_rq1_vuln.sh
```

This will run all 4 experiments:
1. Reasoning + Zero-shot (386 samples)
2. Baseline + Zero-shot (386 samples)
3. Reasoning + Few-shot (386 samples)
4. Baseline + Few-shot (386 samples)

### 5.3 Monitor Progress
```bash
# Watch results in real-time
tail -f results/*_detailed_results.jsonl

# Check latest energy consumption
cat results/*_energy_tracking.json | jq '.total_emissions'
```

---

## Step 6: Download Results & Cleanup (5 minutes)

### 6.1 Results Location
Results are saved locally in `results/` directory:
- `*_detailed_results.jsonl` - All predictions with reasoning
- `*_detailed_results.csv` - CSV format for analysis
- `*_energy_tracking.json` - Energy consumption data
- `*_summary_vulnerability_metrics.csv` - Accuracy metrics

### 6.2 Stop RunPod Pod
1. Go to https://www.runpod.io/console/pods
2. Click **"Stop"** on your pod (billing stops immediately)
3. Optional: Click **"Delete"** if you won't reuse

### 6.3 Verify Billing
Check **Usage** tab to confirm:
- **H100**: Total GPU hours ~0.7-1.5 hours, cost ~$2.00-4.35
- **A40**: Total GPU hours ~2-4 hours, cost ~$1.60-3.15

---

## Troubleshooting

### Issue: Connection timeout
**Solution**: Check vLLM server is running
```bash
ssh root@ssh.runpod.io -p <YOUR_PORT>
tmux attach -t vllm  # Should show vLLM logs
```

### Issue: "Model not found"
**Solution**: Verify model path
```bash
ls /workspace/models/Qwen2.5-Coder-7B-Instruct  # Should show model files
```

### Issue: Out of memory
**Solution**: Reduce max_model_len
```bash
# Stop vLLM (Ctrl+C in tmux)
# Restart with smaller context
python -m vllm.entrypoints.openai.api_server \
  --model /workspace/models/Qwen2.5-Coder-7B-Instruct \
  --max-model-len 4096  # Reduced from 8192
  --gpu-memory-utilization 0.85  # Reduced from 0.9
```

---

## Cost Breakdown

### H100 (Recommended)
| Item | Rate | Quantity | Cost |
|------|------|----------|------|
| H100 GPU | $2.89/hour | 0.7-1.5 hours | $2.02-4.34 |
| Storage | $0.10/GB/month | 50 GB × 1 day | $0.17 |
| **Total** | | | **$2.20-4.50** |

### A40 (Budget Option)
| Item | Rate | Quantity | Cost |
|------|------|----------|------|
| A40 GPU | $0.79/hour | 2-4 hours | $1.58-3.16 |
| Storage | $0.10/GB/month | 50 GB × 1 day | $0.17 |
| **Total** | | | **$1.75-3.35** |

**Value Analysis**: H100 saves 2-3 hours for only $0.50-1.50 extra → **Best for research where time matters**

---

## Next Steps

After completing experiments:

1. **Analyze Results**
   ```bash
   python src/analyze_results.py  # If available
   # Or manually compare CSV files
   ```

2. **Compare Reasoning vs Baseline**
   - Check accuracy differences
   - Compare energy consumption
   - Analyze reasoning quality from detailed_results.jsonl

3. **Extend to Other Tasks**
   - Log parsing (use log parsing scripts)
   - Code generation (use code generation scripts)
   - Technical debt detection

4. **Document Findings**
   - Update your research notes
   - Prepare results for your professor

---

## Summary Checklist

- [ ] Create RunPod pod with vLLM template
- [ ] Download Qwen2.5-Coder-7B-Instruct model
- [ ] Start vLLM server (in tmux)
- [ ] Update .env with USE_RUNPOD=true and endpoint
- [ ] Test connection with test_runpod_connection.sh
- [ ] Run test with 10 samples
- [ ] Run full experiments (386 samples × 4 configs)
- [ ] Download results
- [ ] Stop/delete RunPod pod
- [ ] Analyze and document findings

**Total time (H100)**: ~30 minutes setup + 0.7-1.5 hours experiments = **1-2 hours**
**Total time (A40)**: ~30 minutes setup + 2-4 hours experiments = **2.5-4.5 hours**
**Total cost**: **$2-5** (H100: $2.20-4.50, A40: $1.75-3.35)

---

For detailed setup instructions, see: [RunPod_Setup_Guide.md](RunPod_Setup_Guide.md)
