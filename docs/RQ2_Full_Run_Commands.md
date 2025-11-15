# RQ2 Full Run: Copy-Paste Commands (8 Pods, 32 Experiments)

**Objective**: Complete all RQ2 experiments (32 total) in maximum parallel configuration
**Duration**: ~5 hours wall-clock time (8 pods running in parallel)
**Cost**: ~$100 (8 pods × 5 hours × $2.49/hr spot pricing)
**Samples**: Full dataset (386 samples for vuln, 164 samples for code)

---

## 8-Pod Configuration Matrix

| Pod | Model | Size | Reasoning | Prompt Style | Experiments (Sequential) | Est. Time |
|-----|-------|------|-----------|--------------|-------------------------|-----------|
| 1 | Instruct | 4B | No | Zero-shot | DA-vuln-zero, DA-code-zero, MA-vuln-zero, MA-code-zero | 5h |
| 2 | Thinking | 4B | Yes | Zero-shot | DA-vuln-zero, DA-code-zero, MA-vuln-zero, MA-code-zero | 5h |
| 3 | Instruct | 4B | No | Few-shot | DA-vuln-few, DA-code-few, MA-vuln-few, MA-code-few | 5h |
| 4 | Thinking | 4B | Yes | Few-shot | DA-vuln-few, DA-code-few, MA-vuln-few, MA-code-few | 5h |
| 5 | Instruct | 30B | No | Zero-shot | DA-vuln-zero, DA-code-zero, MA-vuln-zero, MA-code-zero | 5h |
| 6 | Thinking | 30B | Yes | Zero-shot | DA-vuln-zero, DA-code-zero, MA-vuln-zero, MA-code-zero | 5h |
| 7 | Instruct | 30B | No | Few-shot | DA-vuln-few, DA-code-few, MA-vuln-few, MA-code-few | 5h |
| 8 | Thinking | 30B | Yes | Few-shot | DA-vuln-few, DA-code-few, MA-vuln-few, MA-code-few | 5h |

**Total**: 32 experiments (8 pods × 4 experiments each)

---

## Alternative: 4-Pod Configuration (~10 hours)

If you prefer to use fewer pods (lower concurrent cost, longer duration):

| Pod | Model | Size | Reasoning | Experiments (8 per pod) | Est. Time |
|-----|-------|------|-----------|------------------------|-----------|
| 1 | Instruct | 4B | No | All 8 zero+few experiments | 10h |
| 2 | Thinking | 4B | Yes | All 8 zero+few experiments | 10h |
| 3 | Instruct | 30B | No | All 8 zero+few experiments | 10h |
| 4 | Thinking | 30B | Yes | All 8 zero+few experiments | 10h |

**Choose which configuration below** (commands provided for both)

---

## Prerequisites

- ✅ Test run completed successfully (see `RQ2_Test_Run_Commands.md`)
- ✅ All scripts validated
- ✅ Resume functionality confirmed working
- ✅ Full datasets available in `vuln_database/`

---

## Step 1: Deploy Pods

### For 8-Pod Configuration:

**Deploy via RunPod Web Console** (https://runpod.io/console/pods):

**Configuration for ALL 8 Pods:**
- GPU: **H100 80GB SXM** (~$2.49/hr spot pricing)
- Template: **Jupyter Notebook + PyTorch** (provides direct SSH + Jupyter UI)
- **Volume Disk: 100GB** (persistent storage mounted to /workspace)
  - Ensures model files and results persist
  - vLLM will download models here (~5GB for 4B, ~20GB for 30B)
- Container Disk: Leave at default (temporary storage)

**Deploy 8 pods for these model types:**

1. **Pod 1-4: Qwen3-4B Models** (will install vLLM manually after deployment)
   - Pod 1 (Zero-Shot): Will run `Qwen/Qwen3-4B-Instruct-2507` experiments
   - Pod 2 (Zero-Shot): Will run `Qwen/Qwen3-4B-Thinking-2507` experiments
   - Pod 3 (Few-Shot): Will run `Qwen/Qwen3-4B-Instruct-2507` experiments
   - Pod 4 (Few-Shot): Will run `Qwen/Qwen3-4B-Thinking-2507` experiments

2. **Pod 5-8: Qwen3-30B Models** (will install vLLM manually after deployment)
   - Pod 5 (Zero-Shot): Will run `Qwen/Qwen3-30B-A3B-Instruct-2507` experiments
   - Pod 6 (Zero-Shot): Will run `Qwen/Qwen3-30B-A3B-Thinking-2507` experiments
   - Pod 7 (Few-Shot): Will run `Qwen/Qwen3-30B-A3B-Instruct-2507` experiments
   - Pod 8 (Few-Shot): Will run `Qwen/Qwen3-30B-A3B-Thinking-2507` experiments

**Fill in Pod Information:**
```
Pod 1 (4B-Instruct):  IP=__________ Port=______ Jupyter=__________
Pod 2 (4B-Thinking):  IP=__________ Port=______ Jupyter=__________
Pod 3 (4B-Instruct):  IP=__________ Port=______ Jupyter=__________
Pod 4 (4B-Thinking):  IP=__________ Port=______ Jupyter=__________
Pod 5 (30B-Instruct): IP=__________ Port=______ Jupyter=__________
Pod 6 (30B-Thinking): IP=__________ Port=______ Jupyter=__________
Pod 7 (30B-Instruct): IP=__________ Port=______ Jupyter=__________
Pod 8 (30B-Thinking): IP=__________ Port=______ Jupyter=__________
```

**Note**: We'll install vLLM and start model servers manually after deployment (Step 3b)

---

## Step 2: Upload Code to All Pods

**Run on your LOCAL machine**:

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Upload to all 8 pods
bash scripts/upload_to_runpod.sh <POD1_IP> <POD1_PORT> pod1
bash scripts/upload_to_runpod.sh <POD2_IP> <POD2_PORT> pod2
bash scripts/upload_to_runpod.sh <POD3_IP> <POD3_PORT> pod3
bash scripts/upload_to_runpod.sh <POD4_IP> <POD4_PORT> pod4
bash scripts/upload_to_runpod.sh <POD5_IP> <POD5_PORT> pod5
bash scripts/upload_to_runpod.sh <POD6_IP> <POD6_PORT> pod6
bash scripts/upload_to_runpod.sh <POD7_IP> <POD7_PORT> pod7
bash scripts/upload_to_runpod.sh <POD8_IP> <POD8_PORT> pod8
```

---

## Step 3: Setup Environment on All Pods

**Open 8 terminal tabs/windows** (or use tmux), one for each pod.

**Run on each pod** (replace IP/PORT):

```bash
# SSH into pod
ssh root@<POD_IP> -p <POD_PORT> -i ~/.ssh/runpod_ed25519

# Setup Python environment
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh

# Verify
python -c "import autogen; import codecarbon; print('Setup OK')"
```

---

## Step 3b: Install vLLM and Start Model Servers

**On EACH pod**, install vLLM and start the appropriate model server.

**Installation Notes:**
- vLLM installation: ~5-10 minutes
- Model download (first time): ~2-5 min for 4B models, ~5-15 min for 30B models
- Use port 8000 (OpenAI-compatible API endpoint)

### 🚀 Pod 1: 4B-Instruct, Zero-Shot

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

# Wait for model to load (~2-5 min first time)
tail -f /workspace/vllm_4b_instruct.log
# Press Ctrl+C when you see "Uvicorn running on http://0.0.0.0:8000"

# Verify API is running
curl http://localhost:8000/v1/models
# Should return JSON with "id": "Qwen/Qwen3-4B-Instruct-2507"
```

### 🚀 Pod 2: 4B-Thinking, Zero-Shot

```bash
cd /workspace/agent-green
pip install hf_transfer --break-system-packages
pip install vllm --break-system-packages
mkdir -p /workspace/agent-green/models

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

tail -f /workspace/vllm_4b_thinking.log
curl http://localhost:8000/v1/models
```

### 🚀 Pod 3: 4B-Instruct, Few-Shot

```bash
cd /workspace/agent-green
pip install hf_transfer --break-system-packages
pip install vllm --break-system-packages
mkdir -p /workspace/agent-green/models

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

tail -f /workspace/vllm_4b_instruct.log
curl http://localhost:8000/v1/models
```

### 🚀 Pod 4: 4B-Thinking, Few-Shot

```bash
cd /workspace/agent-green
pip install hf_transfer --break-system-packages
pip install vllm --break-system-packages
mkdir -p /workspace/agent-green/models

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

tail -f /workspace/vllm_4b_thinking.log
curl http://localhost:8000/v1/models
```

### 🚀 Pod 5: 30B-Instruct, Zero-Shot

```bash
cd /workspace/agent-green
pip install hf_transfer --break-system-packages
pip install vllm --break-system-packages
mkdir -p /workspace/agent-green/models

# 30B models take longer to download (~20GB, 5-15 min)
nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --served-model-name "Qwen/Qwen3-30B-A3B-Instruct-2507" \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 \
  > /workspace/vllm_30b_instruct.log 2>&1 &

tail -f /workspace/vllm_30b_instruct.log
curl http://localhost:8000/v1/models
```

### 🚀 Pod 6: 30B-Thinking, Zero-Shot

```bash
cd /workspace/agent-green
pip install hf_transfer --break-system-packages
pip install vllm --break-system-packages
mkdir -p /workspace/agent-green/models

nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --served-model-name "Qwen/Qwen3-30B-A3B-Thinking-2507" \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 \
  > /workspace/vllm_30b_instruct.log 2>&1 &

tail -f /workspace/vllm_30b_instruct.log
curl http://localhost:8000/v1/models
```

### 🚀 Pod 7: 30B-Instruct, Few-Shot

```bash
cd /workspace/agent-green
pip install hf_transfer --break-system-packages
pip install vllm --break-system-packages
mkdir -p /workspace/agent-green/models

nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --served-model-name "Qwen/Qwen3-30B-A3B-Instruct-2507" \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 \
  > /workspace/vllm_30b_instruct.log 2>&1 &

tail -f /workspace/vllm_30b_instruct.log
curl http://localhost:8000/v1/models
```

### 🚀 Pod 8: 30B-Thinking, Few-Shot

```bash
cd /workspace/agent-green
pip install hf_transfer --break-system-packages
pip install vllm --break-system-packages
mkdir -p /workspace/agent-green/models

nohup python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --served-model-name "Qwen/Qwen3-30B-A3B-Thinking-2507" \
  --download-dir /workspace/agent-green/models \
  --max-model-len 65536 \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 \
  --port 8000 \
  > /workspace/vllm_30b_thinking.log 2>&1 &

tail -f /workspace/vllm_30b_thinking.log
curl http://localhost:8000/v1/models
```

**Common Issues During vLLM Setup:**
- **First download slow**: Normal for models (~5GB for 4B, ~20GB for 30B)
- **Port already in use**: Kill existing vLLM: `pkill -f vllm`
- **Out of memory**: Reduce `--gpu-memory-utilization` to 0.85 or 0.80
- **pip install fails**: Add `--break-system-packages` flag (already included above)

**Alternative Download Methods** (if auto-download fails with XET CDN errors):
See `RunPod_Jupyter_Ssh_Transfer_Workflow.md` for Method 2 (HuggingFace CLI) and Method 3 (Git-LFS)

---

## Step 4: Start All Experiments (Copy-Paste Commands Per Pod)

### 🚀 POD 1: 4B-Instruct, Zero-Shot (4 Experiments)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=false

# Log file for all experiments
exec > >(tee -a pod1_full_run.log) 2>&1

echo "=== POD 1 STARTING: 4B-Instruct Zero-Shot ==="
date

# Experiment 1/4: DA-vuln-zero
echo "Starting Experiment 1/4: DA-vuln-zero"
python src/dual_agent_vuln.py --prompt_type zero_shot
echo "✓ Completed: DA-vuln-zero"

# Experiment 2/4: DA-code-zero
echo "Starting Experiment 2/4: DA-code-zero"
python src/dual_agent_code_generation.py --prompt_type zero_shot
echo "✓ Completed: DA-code-zero"

# Experiment 3/4: MA-vuln-zero (4-agent)
echo "Starting Experiment 3/4: MA-vuln-zero"
python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot
echo "✓ Completed: MA-vuln-zero"

# Experiment 4/4: MA-code-zero
echo "Starting Experiment 4/4: MA-code-zero"
python src/multi_agent_code_generation.py --prompt_type zero_shot
echo "✓ Completed: MA-code-zero"

echo "=== POD 1 COMPLETE: All 4 experiments finished ==="
date
```

### 🚀 POD 2: 4B-Thinking, Zero-Shot (4 Experiments)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=true

# Log file for all experiments
exec > >(tee -a pod2_full_run.log) 2>&1

echo "=== POD 2 STARTING: 4B-Thinking Zero-Shot ==="
date

# Experiment 1/4: DA-vuln-zero
echo "Starting Experiment 1/4: DA-vuln-zero (Thinking)"
python src/dual_agent_vuln.py --prompt_type zero_shot
echo "✓ Completed: DA-vuln-zero (Thinking)"

# Experiment 2/4: DA-code-zero
echo "Starting Experiment 2/4: DA-code-zero (Thinking)"
python src/dual_agent_code_generation.py --prompt_type zero_shot
echo "✓ Completed: DA-code-zero (Thinking)"

# Experiment 3/4: MA-vuln-zero
echo "Starting Experiment 3/4: MA-vuln-zero (Thinking)"
python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot
echo "✓ Completed: MA-vuln-zero (Thinking)"

# Experiment 4/4: MA-code-zero
echo "Starting Experiment 4/4: MA-code-zero (Thinking)"
python src/multi_agent_code_generation.py --prompt_type zero_shot
echo "✓ Completed: MA-code-zero (Thinking)"

echo "=== POD 2 COMPLETE: All 4 experiments finished ==="
date
```

### 🚀 POD 3: 4B-Instruct, Few-Shot (4 Experiments)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=false

exec > >(tee -a pod3_full_run.log) 2>&1

echo "=== POD 3 STARTING: 4B-Instruct Few-Shot ==="
date

# Experiment 1/4: DA-vuln-few
echo "Starting Experiment 1/4: DA-vuln-few"
python src/dual_agent_vuln.py --prompt_type few_shot
echo "✓ Completed: DA-vuln-few"

# Experiment 2/4: DA-code-few
echo "Starting Experiment 2/4: DA-code-few"
python src/dual_agent_code_generation.py --prompt_type few_shot
echo "✓ Completed: DA-code-few"

# Experiment 3/4: MA-vuln-few
echo "Starting Experiment 3/4: MA-vuln-few"
python src/multi_agent_vuln_detection_four_agents.py --prompt_type few_shot
echo "✓ Completed: MA-vuln-few"

# Experiment 4/4: MA-code-few
echo "Starting Experiment 4/4: MA-code-few"
python src/multi_agent_code_generation.py --prompt_type few_shot
echo "✓ Completed: MA-code-few"

echo "=== POD 3 COMPLETE: All 4 experiments finished ==="
date
```

### 🚀 POD 4: 4B-Thinking, Few-Shot (4 Experiments)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=true

exec > >(tee -a pod4_full_run.log) 2>&1

echo "=== POD 4 STARTING: 4B-Thinking Few-Shot ==="
date

# Experiment 1/4: DA-vuln-few (Thinking)
echo "Starting Experiment 1/4: DA-vuln-few (Thinking)"
python src/dual_agent_vuln.py --prompt_type few_shot
echo "✓ Completed: DA-vuln-few (Thinking)"

# Experiment 2/4: DA-code-few (Thinking)
echo "Starting Experiment 2/4: DA-code-few (Thinking)"
python src/dual_agent_code_generation.py --prompt_type few_shot
echo "✓ Completed: DA-code-few (Thinking)"

# Experiment 3/4: MA-vuln-few (Thinking)
echo "Starting Experiment 3/4: MA-vuln-few (Thinking)"
python src/multi_agent_vuln_detection_four_agents.py --prompt_type few_shot
echo "✓ Completed: MA-vuln-few (Thinking)"

# Experiment 4/4: MA-code-few (Thinking)
echo "Starting Experiment 4/4: MA-code-few (Thinking)"
python src/multi_agent_code_generation.py --prompt_type few_shot
echo "✓ Completed: MA-code-few (Thinking)"

echo "=== POD 4 COMPLETE: All 4 experiments finished ==="
date
```

### 🚀 POD 5: 30B-Instruct, Zero-Shot (4 Experiments)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=false

exec > >(tee -a pod5_full_run.log) 2>&1

echo "=== POD 5 STARTING: 30B-Instruct Zero-Shot ==="
date

# Experiment 1/4: DA-vuln-zero (30B)
echo "Starting Experiment 1/4: DA-vuln-zero (30B)"
python src/dual_agent_vuln.py --prompt_type zero_shot
echo "✓ Completed: DA-vuln-zero (30B)"

# Experiment 2/4: DA-code-zero (30B)
echo "Starting Experiment 2/4: DA-code-zero (30B)"
python src/dual_agent_code_generation.py --prompt_type zero_shot
echo "✓ Completed: DA-code-zero (30B)"

# Experiment 3/4: MA-vuln-zero (30B)
echo "Starting Experiment 3/4: MA-vuln-zero (30B)"
python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot
echo "✓ Completed: MA-vuln-zero (30B)"

# Experiment 4/4: MA-code-zero (30B)
echo "Starting Experiment 4/4: MA-code-zero (30B)"
python src/multi_agent_code_generation.py --prompt_type zero_shot
echo "✓ Completed: MA-code-zero (30B)"

echo "=== POD 5 COMPLETE: All 4 experiments finished ==="
date
```

### 🚀 POD 6: 30B-Thinking, Zero-Shot (4 Experiments)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=true

exec > >(tee -a pod6_full_run.log) 2>&1

echo "=== POD 6 STARTING: 30B-Thinking Zero-Shot ==="
date

# Experiment 1/4: DA-vuln-zero (30B Thinking)
echo "Starting Experiment 1/4: DA-vuln-zero (30B Thinking)"
python src/dual_agent_vuln.py --prompt_type zero_shot
echo "✓ Completed: DA-vuln-zero (30B Thinking)"

# Experiment 2/4: DA-code-zero (30B Thinking)
echo "Starting Experiment 2/4: DA-code-zero (30B Thinking)"
python src/dual_agent_code_generation.py --prompt_type zero_shot
echo "✓ Completed: DA-code-zero (30B Thinking)"

# Experiment 3/4: MA-vuln-zero (30B Thinking)
echo "Starting Experiment 3/4: MA-vuln-zero (30B Thinking)"
python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot
echo "✓ Completed: MA-vuln-zero (30B Thinking)"

# Experiment 4/4: MA-code-zero (30B Thinking)
echo "Starting Experiment 4/4: MA-code-zero (30B Thinking)"
python src/multi_agent_code_generation.py --prompt_type zero_shot
echo "✓ Completed: MA-code-zero (30B Thinking)"

echo "=== POD 6 COMPLETE: All 4 experiments finished ==="
date
```

### 🚀 POD 7: 30B-Instruct, Few-Shot (4 Experiments)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=false

exec > >(tee -a pod7_full_run.log) 2>&1

echo "=== POD 7 STARTING: 30B-Instruct Few-Shot ==="
date

# Experiment 1/4: DA-vuln-few (30B)
echo "Starting Experiment 1/4: DA-vuln-few (30B)"
python src/dual_agent_vuln.py --prompt_type few_shot
echo "✓ Completed: DA-vuln-few (30B)"

# Experiment 2/4: DA-code-few (30B)
echo "Starting Experiment 2/4: DA-code-few (30B)"
python src/dual_agent_code_generation.py --prompt_type few_shot
echo "✓ Completed: DA-code-few (30B)"

# Experiment 3/4: MA-vuln-few (30B)
echo "Starting Experiment 3/4: MA-vuln-few (30B)"
python src/multi_agent_vuln_detection_four_agents.py --prompt_type few_shot
echo "✓ Completed: MA-vuln-few (30B)"

# Experiment 4/4: MA-code-few (30B)
echo "Starting Experiment 4/4: MA-code-few (30B)"
python src/multi_agent_code_generation.py --prompt_type few_shot
echo "✓ Completed: MA-code-few (30B)"

echo "=== POD 7 COMPLETE: All 4 experiments finished ==="
date
```

### 🚀 POD 8: 30B-Thinking, Few-Shot (4 Experiments)

```bash
cd /workspace/agent-green
export ENABLE_REASONING=true

exec > >(tee -a pod8_full_run.log) 2>&1

echo "=== POD 8 STARTING: 30B-Thinking Few-Shot ==="
date

# Experiment 1/4: DA-vuln-few (30B Thinking)
echo "Starting Experiment 1/4: DA-vuln-few (30B Thinking)"
python src/dual_agent_vuln.py --prompt_type few_shot
echo "✓ Completed: DA-vuln-few (30B Thinking)"

# Experiment 2/4: DA-code-few (30B Thinking)
echo "Starting Experiment 2/4: DA-code-few (30B Thinking)"
python src/dual_agent_code_generation.py --prompt_type few_shot
echo "✓ Completed: DA-code-few (30B Thinking)"

# Experiment 3/4: MA-vuln-few (30B Thinking)
echo "Starting Experiment 3/4: MA-vuln-few (30B Thinking)"
python src/multi_agent_vuln_detection_four_agents.py --prompt_type few_shot
echo "✓ Completed: MA-vuln-few (30B Thinking)"

# Experiment 4/4: MA-code-few (30B Thinking)
echo "Starting Experiment 4/4: MA-code-few (30B Thinking)"
python src/multi_agent_code_generation.py --prompt_type few_shot
echo "✓ Completed: MA-code-few (30B Thinking)"

echo "=== POD 8 COMPLETE: All 4 experiments finished ==="
date
```

---

## Step 5: Monitor Progress Across All Pods

### Quick Status Check (Run Locally)

**Create monitoring script**:

```bash
#!/bin/bash
# Save as: monitor_all_pods.sh

echo "=== RQ2 FULL RUN MONITORING ==="
echo "Time: $(date)"
echo ""

# Pod details (fill in your IPs/ports)
declare -A PODS
PODS[1]="<POD1_IP>:<POD1_PORT>"
PODS[2]="<POD2_IP>:<POD2_PORT>"
PODS[3]="<POD3_IP>:<POD3_PORT>"
PODS[4]="<POD4_IP>:<POD4_PORT>"
PODS[5]="<POD5_IP>:<POD5_PORT>"
PODS[6]="<POD6_IP>:<POD6_PORT>"
PODS[7]="<POD7_IP>:<POD7_PORT>"
PODS[8]="<POD8_IP>:<POD8_PORT>"

for pod_num in {1..8}; do
    IFS=':' read -r ip port <<< "${PODS[$pod_num]}"
    echo "--- Pod $pod_num ($ip:$port) ---"

    ssh -o ConnectTimeout=5 root@$ip -p $port -i ~/.ssh/runpod_ed25519 \
        "cd /workspace/agent-green && tail -3 pod${pod_num}_full_run.log 2>/dev/null" 2>/dev/null || echo "  [Connection failed]"

    echo ""
done

echo "Total experiments expected: 32 (4 per pod)"
```

**Run monitoring every 30 minutes**:
```bash
watch -n 1800 bash monitor_all_pods.sh
```

### Detailed Progress Check

**SSH into any pod** and run:

```bash
# Check active processes
ps aux | grep python

# Count completed samples across all experiments
find results -name "*_detailed_results.jsonl" -exec wc -l {} \;

# Check most recent activity
tail -20 pod*_full_run.log

# Estimate completion time based on current sample count
wc -l results/*_detailed_results.jsonl | grep total
```

---

## Step 6: Download All Results (~5 hours after start)

**After all pods complete**, download results from all 8 pods.

**Run on your LOCAL machine**:

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Download from all pods
for i in {1..8}; do
    echo "Downloading from Pod $i..."
    bash scripts/download_from_runpod.sh <POD${i}_IP> <POD${i}_PORT> pod${i}_full_results
done

echo "All downloads complete!"
```

Results will be in: `results/pod{1-8}_full_results/`

---

## Step 7: Organize and Verify Results

**Organize downloaded results**:

```bash
cd results

# Create organized structure
mkdir -p RQ2_Full_Results/{4B,30B}/{Instruct,Thinking}/{ZeroShot,FewShot}

# Move results to organized folders (example for Pod 1)
# Repeat for all 8 pods with appropriate paths
```

**Verify all 32 experiments completed**:

```bash
# Count result files
find results -name "*_detailed_results.jsonl" | wc -l
# Should be 32

# Check sample counts
find results -name "*_detailed_results.jsonl" -exec wc -l {} \; | grep -E "(386|164)"

# Check for errors
find results -name "*.log" -exec grep -l "ERROR\|FAILED" {} \;
```

---

## Step 8: Cleanup

**Terminate all pods** to stop billing:

1. Go to RunPod console (https://runpod.io/console/pods)
2. Select all 8 pods
3. Click "Terminate"
4. Confirm

**Final Cost**: ~$100 (8 pods × 5 hours × $2.49/hr spot)

---

## Expected Outputs

### Per Experiment (32 total):
- `*_detailed_results.jsonl` (JSONL with all samples)
- `*_detailed_results.csv` (CSV format)
- `*_energy_tracking.json` (Energy consumption)
- `*_summary.json` (Code generation experiments)
- `*_metrics.csv` (Vulnerability detection experiments)

### File Structure:
```
results/
├── pod1_full_results/
│   ├── DA-vuln-two-zero_shot_qwen3-4b-instruct_*.jsonl
│   ├── DA-code-zero_shot_qwen3-4b-instruct_*.jsonl
│   ├── MA-vuln-four-zero_shot_qwen3-4b-instruct_*.jsonl
│   └── MA-code-zero_shot_qwen3-4b-instruct_*.jsonl
├── pod2_full_results/
│   ├── DA-vuln-two-zero_shot_qwen3-4b-thinking_*.jsonl
│   ... (4 experiments)
... (pods 3-8)
```

---

## Next Steps

After full run completion:

1. **Validate Results**: Check all 32 experiments completed successfully
2. **Run Comprehensive Analysis**: Similar to RQ1 prompt comparison
3. **Generate Visualizations**: Accuracy, robustness, efficiency comparisons
4. **Write RQ2 Findings**: Document dual-agent vs multi-agent performance

See `RQ2_Analysis_Guide.md` for analysis procedures.
