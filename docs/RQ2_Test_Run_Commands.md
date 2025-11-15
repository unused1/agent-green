# RQ2 Test Run: Copy-Paste Commands (4 Pods, 4 Experiments)

**Objective**: Validate all scripts work correctly before full RQ2 run
**Duration**: ~1 hour wall-clock time (all pods running in parallel)
**Cost**: ~$10 (4 pods × 1 hour × $2.49/hr)
**Samples**: 10 samples per experiment (for quick validation)

---

## Pod Configuration Matrix

| Pod # | Model | Reasoning | Experiment | Script | Prompt Type |
|-------|-------|-----------|------------|--------|-------------|
| 1 | Qwen3-4B-Instruct | No | DA-vuln | dual_agent_vuln.py | zero_shot |
| 2 | Qwen3-4B-Thinking | Yes | DA-vuln | dual_agent_vuln.py | few_shot |
| 3 | Qwen3-4B-Instruct | No | MA-code | multi_agent_code_generation.py | zero_shot |
| 4 | Qwen3-4B-Thinking | Yes | MA-code | multi_agent_code_generation.py | few_shot |

---

## Step 1: Deploy 4 RunPod H100 Pods

**Deploy via RunPod Web Console:**

1. Go to https://runpod.io/console/pods
2. Click "Deploy" → Select "Community Cloud" (for spot pricing)
3. GPU: **H100 80GB SXM** (~$2.49/hr spot pricing)
4. Template: **Jupyter Notebook + PyTorch** (provides direct SSH + Jupyter UI)
5. **Volume Disk: 100GB** (persistent storage mounted to /workspace)
   - Ensures model files and results persist
   - vLLM will download models here (~20GB per model)
6. Container Disk: Leave at default (temporary storage)
7. Deploy **4 separate pods** for these model types:
   - Pod 1: Will run `Qwen/Qwen3-4B-Instruct-2507` experiments
   - Pod 2: Will run `Qwen/Qwen3-4B-Thinking-2507` experiments
   - Pod 3: Will run `Qwen/Qwen3-4B-Instruct-2507` experiments (few-shot)
   - Pod 4: Will run `Qwen/Qwen3-4B-Thinking-2507` experiments (few-shot)

8. **Note down for each pod:**
   - Public IP
   - SSH Port
   - Jupyter URL (for backup file management)

**Example Pod Info Table (fill this in):**
```
Pod 1: IP=__________ Port=______ Jupyter=__________
Pod 2: IP=__________ Port=______ Jupyter=__________
Pod 3: IP=__________ Port=______ Jupyter=__________
Pod 4: IP=__________ Port=______ Jupyter=__________
```

**Note**: We'll install vLLM manually after deployment (Step 3b)

---

## Step 2: Upload Code to All Pods

**Run these commands on your LOCAL machine** (replace IP/PORT with actual values):

```bash
# Navigate to project directory
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Upload to Pod 1
bash scripts/upload_to_runpod.sh <POD1_IP> <POD1_PORT> test_pod1

# Upload to Pod 2
bash scripts/upload_to_runpod.sh <POD2_IP> <POD2_PORT> test_pod2

# Upload to Pod 3
bash scripts/upload_to_runpod.sh <POD3_IP> <POD3_PORT> test_pod3

# Upload to Pod 4
bash scripts/upload_to_runpod.sh <POD4_IP> <POD4_PORT> test_pod4
```

**Wait for all uploads to complete** (~1-2 minutes each)

---

## Step 3: Setup Environment on Each Pod

**Open 4 terminal tabs/windows**, one for each pod.

### Terminal 1 - Pod 1 (4B-Instruct):
```bash
# SSH into Pod 1
ssh root@<POD1_IP> -p <POD1_PORT> -i ~/.ssh/runpod_ed25519

# Setup Python environment
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh

# Verify installation
python -c "import autogen; import codecarbon; print('Setup OK')"
```

### Terminal 2 - Pod 2 (4B-Thinking):
```bash
# SSH into Pod 2
ssh root@<POD2_IP> -p <POD2_PORT> -i ~/.ssh/runpod_ed25519

# Setup Python environment
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh

# Verify installation
python -c "import autogen; import codecarbon; print('Setup OK')"
```

### Terminal 3 - Pod 3 (4B-Instruct):
```bash
# SSH into Pod 3
ssh root@<POD3_IP> -p <POD3_PORT> -i ~/.ssh/runpod_ed25519

# Setup Python environment
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh

# Verify installation
python -c "import autogen; import codecarbon; print('Setup OK')"
```

### Terminal 4 - Pod 4 (4B-Thinking):
```bash
# SSH into Pod 4
ssh root@<POD4_IP> -p <POD4_PORT> -i ~/.ssh/runpod_ed25519

# Setup Python environment
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh

# Verify installation
python -c "import autogen; import codecarbon; print('Setup OK')"
```

---

## Step 3b: Install vLLM and Start Model Server

**On EACH pod**, install vLLM and start the model server.

**Note**: Installation takes ~5-10 minutes. Model download (first time) takes ~2-5 minutes for 4B models.

### Pod 1 (4B-Instruct, Zero-Shot):
```bash
cd /workspace/agent-green

# Install dependencies
pip install hf_transfer --break-system-packages  # For fast model downloads
pip install vllm --break-system-packages

# Create models directory
mkdir -p /workspace/agent-green/models

# Start vLLM with 4B-Instruct model (auto-downloads on first run)
nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-4B-Instruct-2507 \
  --served-model-name "Qwen/Qwen3-4B-Instruct-2507" \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 \
  > /workspace/vllm_4b_instruct.log 2>&1 &

# Wait for model to load (~2-5 min first time, ~30 sec subsequent)
echo "Waiting for vLLM to start (check log)..."
tail -f /workspace/vllm_4b_instruct.log
# Press Ctrl+C when you see "Uvicorn running on http://0.0.0.0:8000"

# Verify API is running
curl http://localhost:8000/v1/models
# Should return JSON with "id": "Qwen/Qwen3-4B-Instruct-2507"
```

### Pod 2 (4B-Thinking, Zero-Shot):
```bash
cd /workspace/agent-green

# Install dependencies
pip install hf_transfer --break-system-packages
pip install vllm --break-system-packages

# Create models directory
mkdir -p /workspace/agent-green/models

# Start vLLM with 4B-Thinking model
nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --served-model-name "Qwen/Qwen3-4B-Thinking-2507" \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 \
  > /workspace/vllm_4b_thinking.log 2>&1 &

# Wait for model to load
tail -f /workspace/vllm_4b_thinking.log
# Press Ctrl+C when you see "Uvicorn running on http://0.0.0.0:8000"

# Verify API is running
curl http://localhost:8000/v1/models
```

### Pod 3 (4B-Instruct, Few-Shot):
```bash
cd /workspace/agent-green

# Install dependencies
pip install hf_transfer --break-system-packages
pip install vllm --break-system-packages

# Create models directory
mkdir -p /workspace/agent-green/models

# Start vLLM with 4B-Instruct model
nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-4B-Instruct-2507 \
  --served-model-name "Qwen/Qwen3-4B-Instruct-2507" \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 \
  > /workspace/vllm_4b_instruct.log 2>&1 &

# Wait for model to load
tail -f /workspace/vllm_4b_instruct.log

# Verify API is running
curl http://localhost:8000/v1/models
```

### Pod 4 (4B-Thinking, Few-Shot):
```bash
cd /workspace/agent-green

# Install dependencies
pip install hf_transfer --break-system-packages
pip install vllm --break-system-packages

# Create models directory
mkdir -p /workspace/agent-green/models

# Start vLLM with 4B-Thinking model
nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --served-model-name "Qwen/Qwen3-4B-Thinking-2507" \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 \
  > /workspace/vllm_4b_thinking.log 2>&1 &

# Wait for model to load
tail -f /workspace/vllm_4b_thinking.log

# Verify API is running
curl http://localhost:8000/v1/models
```

**Common Issues During vLLM Setup:**
- **First download slow**: Normal for 4B models (~5GB), wait 2-5 minutes
- **Port already in use**: Kill existing vLLM: `pkill -f vllm`
- **Out of memory**: Reduce `--gpu-memory-utilization` to 0.85
- **pip install fails**: Add `--break-system-packages` flag (already included above)

---

## Step 4: Configure Test Dataset (10 Samples)

**IMPORTANT**: Before running experiments, modify dataset to use only 10 samples for testing.

**Option A: Temporary Override (Recommended for Test)**

Add this to each pod **before running experiments**:

```bash
# Create test dataset with 10 samples
cd /workspace/agent-green/vuln_database
head -n 10 VulTrial_386_samples_balanced.jsonl > VulTrial_10_samples_test.jsonl
head -n 10 HumanEval.jsonl > HumanEval_10_samples_test.jsonl

# Update config to use test dataset
cd /workspace/agent-green/src
cp config.py config.py.backup

# Edit config.py to point to test datasets
sed -i 's/VulTrial_386_samples_balanced.jsonl/VulTrial_10_samples_test.jsonl/g' config.py
sed -i 's/HumanEval.jsonl/HumanEval_10_samples_test.jsonl/g' config.py
```

**Option B: Manual Edit**

Or SSH into each pod and edit `src/config.py`:
```python
# Change these lines:
VULN_DATASET = f"{PROJECT_ROOT}/vuln_database/VulTrial_10_samples_test.jsonl"
HUMANEVAL_DATASET = f"{PROJECT_ROOT}/vuln_database/HumanEval_10_samples_test.jsonl"
```

---

## Step 5: Start Test Experiments (Copy-Paste Per Pod)

### 🚀 Pod 1: DA-vuln-zero (4B-Instruct)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=false

# Start experiment in background
nohup python src/dual_agent_vuln.py --prompt_type zero_shot > test_da_vuln_zero.log 2>&1 &

# Get process ID
echo $! > test_da_vuln_zero.pid
echo "✓ Started DA-vuln-zero (PID: $(cat test_da_vuln_zero.pid))"
echo "Monitor: tail -f test_da_vuln_zero.log"
```

### 🚀 Pod 2: DA-vuln-few (4B-Thinking)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=true

# Start experiment in background
nohup python src/dual_agent_vuln.py --prompt_type few_shot > test_da_vuln_few.log 2>&1 &

# Get process ID
echo $! > test_da_vuln_few.pid
echo "✓ Started DA-vuln-few (PID: $(cat test_da_vuln_few.pid))"
echo "Monitor: tail -f test_da_vuln_few.log"
```

### 🚀 Pod 3: MA-code-zero (4B-Instruct)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=false

# Start experiment in background
nohup python src/multi_agent_code_generation.py --prompt_type zero_shot > test_ma_code_zero.log 2>&1 &

# Get process ID
echo $! > test_ma_code_zero.pid
echo "✓ Started MA-code-zero (PID: $(cat test_ma_code_zero.pid))"
echo "Monitor: tail -f test_ma_code_zero.log"
```

### 🚀 Pod 4: MA-code-few (4B-Thinking)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=true

# Start experiment in background
nohup python src/multi_agent_code_generation.py --prompt_type few_shot > test_ma_code_few.log 2>&1 &

# Get process ID
echo $! > test_ma_code_few.pid
echo "✓ Started MA-code-few (PID: $(cat test_ma_code_few.pid))"
echo "Monitor: tail -f test_ma_code_few.log"
```

---

## Step 6: Monitor Progress

### Check if Experiments are Running

**On each pod**, run:
```bash
# Check process
ps aux | grep python | grep -E "(dual_agent|multi_agent)"

# Check log output
tail -f test_*.log

# Quick status check
ls -lh results/*_detailed_results.jsonl 2>/dev/null | tail -5
```

### Monitor Sample Progress

```bash
# Count completed samples (should reach 10)
wc -l results/*_detailed_results.jsonl

# Watch live progress
watch -n 30 'wc -l results/*_detailed_results.jsonl'
```

### Monitor from Local Machine

**Create a monitoring script** (run locally):

```bash
#!/bin/bash
# Save as: monitor_test_pods.sh

echo "=== RQ2 TEST RUN MONITORING ==="
echo ""

for i in 1 2 3 4; do
    echo "--- Pod $i ---"
    ssh root@<POD${i}_IP> -p <POD${i}_PORT> -i ~/.ssh/runpod_ed25519 \
        "cd /workspace/agent-green && wc -l results/*_detailed_results.jsonl 2>/dev/null | tail -1" 2>/dev/null
    echo ""
done
```

Run every few minutes:
```bash
bash monitor_test_pods.sh
```

---

## Step 7: Download Results

**After all experiments complete** (~1 hour), download results from all pods.

**Run on your LOCAL machine:**

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Download from Pod 1
bash scripts/download_from_runpod.sh <POD1_IP> <POD1_PORT> test_pod1_results

# Download from Pod 2
bash scripts/download_from_runpod.sh <POD2_IP> <POD2_PORT> test_pod2_results

# Download from Pod 3
bash scripts/download_from_runpod.sh <POD3_IP> <POD3_PORT> test_pod3_results

# Download from Pod 4
bash scripts/download_from_runpod.sh <POD4_IP> <POD4_PORT> test_pod4_results
```

Results will be in `results/test_pod{1-4}_results/`

---

## Step 8: Validate Results

**Check each experiment output:**

```bash
cd results

# Check file counts (should have 4 experiments)
ls -lh test_pod*_results/*.jsonl

# Verify sample counts (should be 10 lines each)
wc -l test_pod*_results/*_detailed_results.jsonl

# Check for errors
grep -i "error\|failed" test_pod*_results/*.log
```

**Expected Files Per Pod:**
- `*_detailed_results.jsonl` (10 lines)
- `*_detailed_results.csv`
- `*_energy_tracking.json`
- `*_summary.json` (for code generation)

---

## Step 9: Decision Point

### ✅ If Test Successful:
- All 4 experiments completed
- 10 samples each processed
- No major errors
- Resume functionality works
- **→ Proceed to Full RQ2 Run** (see `RQ2_Full_Run_Commands.md`)

### ❌ If Issues Found:
- Debug specific script
- Fix and re-run failed experiments
- Validate resume functionality
- **→ Re-run test before full run**

---

## Quick Troubleshooting

### Experiment Not Starting
```bash
# Check Python errors
cat test_*.log | grep -i "error\|traceback"

# Check if process died
ps aux | grep python

# Restart if needed
python src/dual_agent_vuln.py --prompt_type zero_shot
```

### Out of Memory
```bash
# Check GPU memory
nvidia-smi

# Check system memory
free -h

# If OOM, may need to reduce batch size or restart pod
```

### Experiment Stuck
```bash
# Kill process
pkill -f "python src/dual_agent"

# Check for resume files
ls results/*_detailed_results.jsonl

# Resume from where it stopped
python src/dual_agent_vuln.py --prompt_type zero_shot
```

---

## Cleanup (After Download)

**Terminate all test pods** to stop billing:

1. Go to RunPod console
2. Select each pod
3. Click "Terminate"
4. Confirm termination

**Cost for test run**: ~$10 (4 pods × 1 hour × $2.49/hr)

---

## Next Steps

After successful test validation:

1. Review `RQ2_Full_Run_Commands.md` for full experiment execution
2. Decide on 4-pod or 8-pod configuration
3. Deploy production pods with full datasets
4. Execute complete RQ2 experiment suite
