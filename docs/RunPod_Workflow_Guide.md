# RunPod Experiment Workflow Guide

## Overview

This guide shows how to run RQ1 experiments **directly on RunPod pods** to capture accurate energy metrics with CodeCarbon on the actual H100 GPU.

**Why run ON RunPod instead of calling API?**
- ✅ **Accurate energy metrics**: CodeCarbon measures actual GPU consumption
- ✅ **Faster execution**: No network latency
- ✅ **Lower cost**: No data transfer overhead
- ✅ **Better control**: Direct access to vLLM server

---

## Architecture

You'll run experiments on **TWO separate RunPod pods**:

1. **Pod 1 (Thinking Model)**: Runs `Qwen3-4B-Thinking-2507`
   - For reasoning experiments (zero-shot + few-shot)

2. **Pod 2 (Instruct Model)**: Runs `Qwen3-4B-Instruct-2507`
   - For baseline experiments (zero-shot + few-shot)

Each pod:
- Runs vLLM server on `localhost:8000`
- Has experiment code uploaded
- Captures CodeCarbon metrics locally
- Saves results to `/workspace/agent-green/results/`

---

## Prerequisites

1. ✅ Two RunPod pods deployed with vLLM
   - Pod 1: `Qwen/Qwen3-4B-Thinking-2507` model
   - Pod 2: `Qwen/Qwen3-4B-Instruct-2507` model

2. ✅ SSH access configured
   - Note IP addresses and ports for both pods (from RunPod console -> Pod -> Connect -> TCP Port Mappings)
   - SSH key at `~/.ssh/runpod_ed25519`

3. ✅ vLLM servers running on both pods

---

## Workflow Steps

### Step 1: Upload Experiment Files to Pod 1 (Thinking)

From your local machine:

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Replace with your pod's IP address and port
bash scripts/upload_to_runpod.sh 213.181.122.135 19442 thinking
```

**What this does:**
- Creates temporary directory with minimal required files
- Uploads to `/workspace/agent-green/` on Pod 1
- Shows next steps

### Step 2: Upload Experiment Files to Pod 2 (Instruct)

```bash
# Replace with your pod's IP address and port
bash scripts/upload_to_runpod.sh 213.181.122.136 19443 instruct
```

### Step 3: Setup Pod 1 (Thinking Model)

SSH into Pod 1:

```bash
ssh root@213.181.122.135 -p 19442 -i ~/.ssh/runpod_ed25519
```

Setup environment:

```bash
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh
```

**What this does:**
- Installs Python dependencies (autogen, codecarbon, etc.)
- Verifies vLLM server is running
- Detects model type and configures .env
- Verifies datasets are uploaded

### Step 4: Setup Pod 2 (Instruct Model)

SSH into Pod 2:

```bash
ssh root@213.181.122.136 -p 19443 -i ~/.ssh/runpod_ed25519
```

Setup environment:

```bash
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh
```

---

## Running Experiments

### Quick Test (10 samples, ~30 seconds)

**On Pod 1 (Thinking):**

```bash
# Test zero-shot
bash scripts/run_rq1_vuln_runpod.sh reasoning zero test

# Test few-shot
bash scripts/run_rq1_vuln_runpod.sh reasoning few test
```

**On Pod 2 (Instruct):**

```bash
# Test zero-shot
bash scripts/run_rq1_vuln_runpod.sh baseline zero test

# Test few-shot
bash scripts/run_rq1_vuln_runpod.sh baseline few test
```

### Full Experiments (386 samples)

#### Option A: Run sequentially on each pod

**On Pod 1 (Thinking):**

```bash
# Run both zero-shot and few-shot (~20-40 minutes on H100)
bash scripts/run_rq1_vuln_runpod.sh reasoning all full
```

**On Pod 2 (Instruct):**

```bash
# Run both zero-shot and few-shot (~20-40 minutes on H100)
bash scripts/run_rq1_vuln_runpod.sh baseline all full
```

#### Option B: Run experiments individually

**Individual experiments:**

```bash
# Reasoning + zero-shot only
bash scripts/run_rq1_vuln_runpod.sh reasoning zero full

# Reasoning + few-shot only
bash scripts/run_rq1_vuln_runpod.sh reasoning few full

# Baseline + zero-shot only
bash scripts/run_rq1_vuln_runpod.sh baseline zero full

# Baseline + few-shot only
bash scripts/run_rq1_vuln_runpod.sh baseline few full
```

---

## Monitoring Progress

### Watch results in real-time

```bash
# On the RunPod pod
tail -f results/*_detailed_results.jsonl
```

### Check energy consumption

```bash
# View energy tracking
cat results/*_energy_tracking.json | python3 -m json.tool
```

### Check sample processing

```bash
# Count completed samples
wc -l results/*_detailed_results.jsonl
```

---

## Downloading Results

### From Pod 1 (Thinking Model)

From your local machine:

```bash
bash scripts/download_from_runpod.sh 213.181.122.135 19442 thinking
```

Results saved to: `results_runpod_thinking_TIMESTAMP/`

### From Pod 2 (Instruct Model)

```bash
bash scripts/download_from_runpod.sh 213.181.122.136 19443 instruct
```

Results saved to: `results_runpod_instruct_TIMESTAMP/`

---

## Result Files

Each experiment generates:

1. **`*_detailed_results.jsonl`** - All predictions with reasoning (one JSON per line)
2. **`*_detailed_results.csv`** - CSV format for analysis
3. **`*_energy_tracking.json`** - CodeCarbon energy consumption data
4. **`*_summary_vulnerability_metrics.csv`** - Accuracy, precision, recall, F1

---

## Expected Timing & Cost

### H100 GPU (Recommended)

| Experiment | Samples | Time | Cost |
|------------|---------|------|------|
| Quick test (per pod) | 10 | ~30 sec | $0.02 |
| Single full experiment | 386 | ~20 min | $0.97 |
| Both experiments (per pod) | 772 | ~40 min | $1.93 |
| **Total (both pods)** | **1544** | **~1.5 hours** | **~$4.00** |

### A40 GPU (Budget)

| Experiment | Samples | Time | Cost |
|------------|---------|------|------|
| Quick test (per pod) | 10 | ~1 min | $0.01 |
| Single full experiment | 386 | ~1 hour | $0.79 |
| Both experiments (per pod) | 772 | ~2 hours | $1.58 |
| **Total (both pods)** | **1544** | **~4 hours** | **~$3.20** |

**Note**: H100 is recommended despite higher hourly cost - completes in 1/3 the time.

---

## Energy Metrics

With this workflow, CodeCarbon will accurately measure:

- ✅ **GPU power consumption** (H100 actual usage)
- ✅ **CPU overhead** (pod CPU)
- ✅ **RAM usage** (pod RAM)
- ✅ **Total emissions** (kg CO2 equivalent)

Energy data saved to: `*_energy_tracking.json`

Example:
```json
{
  "total_emissions": 0.001234,
  "sessions": 2,
  "session_history": [
    {
      "session": 1,
      "start_time": "2025-10-11T16:30:00",
      "end_time": "2025-10-11T16:50:00",
      "samples_processed": 386,
      "session_emissions": 0.000617
    }
  ]
}
```

---

## Troubleshooting

### Issue: vLLM not responding

```bash
# Check vLLM is running
curl http://localhost:8000/v1/models

# Restart if needed (depends on your RunPod template)
```

### Issue: Out of memory

vLLM automatically manages GPU memory. If you get OOM:
- Reduce `--max-model-len` in vLLM start command
- Reduce `--gpu-memory-utilization` (default: 0.9)

### Issue: CodeCarbon password prompt

CodeCarbon needs sudo for PowerMetrics on some systems. This is normal for the first run.

### Issue: Upload/download fails

```bash
# Verify SSH connection
ssh root@<POD_IP> -p <PORT> -i ~/.ssh/runpod_ed25519 "ls /workspace"

# Check SSH key permissions
chmod 600 ~/.ssh/runpod_ed25519
```

---

## Cleanup

### Stop Pods (Important!)

After downloading results:

1. Go to https://www.runpod.io/console/pods
2. Click **"Stop"** on both pods
3. Verify billing stopped

### Delete Pods (Optional)

If you won't reuse:
1. Click **"Delete"** on both pods
2. Verify storage is cleared

**Cost savings**: Billing stops immediately when pods are stopped.

---

## Summary Checklist

### Setup Phase
- [ ] Deploy Pod 1 with Qwen3-4B-Thinking-2507
- [ ] Deploy Pod 2 with Qwen3-4B-Instruct-2507
- [ ] Note IP addresses and ports for both pods (from RunPod console -> TCP Port Mappings)
- [ ] Upload files to Pod 1: `bash scripts/upload_to_runpod.sh <IP1> <PORT1> thinking`
- [ ] Upload files to Pod 2: `bash scripts/upload_to_runpod.sh <IP2> <PORT2> instruct`
- [ ] Setup Pod 1: SSH + `bash scripts/setup_runpod_env.sh`
- [ ] Setup Pod 2: SSH + `bash scripts/setup_runpod_env.sh`

### Testing Phase
- [ ] Test Pod 1: `bash scripts/run_rq1_vuln_runpod.sh reasoning zero test`
- [ ] Test Pod 2: `bash scripts/run_rq1_vuln_runpod.sh baseline zero test`
- [ ] Verify results generated

### Experiment Phase
- [ ] Run Pod 1 experiments: `bash scripts/run_rq1_vuln_runpod.sh reasoning all full`
- [ ] Run Pod 2 experiments: `bash scripts/run_rq1_vuln_runpod.sh baseline all full`
- [ ] Monitor progress with `tail -f`

### Results Phase
- [ ] Download Pod 1 results: `bash scripts/download_from_runpod.sh <IP1> <PORT1> thinking`
- [ ] Download Pod 2 results: `bash scripts/download_from_runpod.sh <IP2> <PORT2> instruct`
- [ ] Verify 4 experiment result sets downloaded
- [ ] Stop both pods
- [ ] Verify billing stopped

---

## Next Steps After Downloading

1. **Combine results** from both pods
2. **Analyze with Python**:
   ```bash
   python src/analyze_results.py results_runpod_*/
   ```
3. **Compare reasoning vs baseline**:
   - Accuracy differences
   - Energy consumption comparison
   - Analyze reasoning quality from detailed_results.jsonl
4. **Document findings** for your research

---

## File Checklist

Files uploaded to RunPod (minimal set):

```
/workspace/agent-green/
├── .env                                    # RunPod configuration
├── src/
│   ├── single_agent_vuln.py              # Main experiment script
│   ├── config.py                          # Configuration
│   └── vuln_evaluation.py                # Evaluation functions
├── scripts/
│   ├── run_rq1_vuln_runpod.sh           # Execution script
│   └── setup_runpod_env.sh              # Setup script
├── vuln_database/
│   ├── VulTrial_386_samples_balanced.jsonl  # Full dataset
│   └── VulTrial_10_samples_test.jsonl      # Test dataset
└── results/                               # Generated during experiments
```

---

**Total setup time**: ~15 minutes
**Total experiment time**: ~1.5 hours (H100) or ~4 hours (A40)
**Total cost**: ~$4-5 for complete RQ1 experiments

For questions, see: [RunPod_Setup_Guide.md](RunPod_Setup_Guide.md)
