# RunPod Setup Guide for Nemotron 8B Multi-Agent Experiments

**Date**: December 16, 2025
**Purpose**: Step-by-step guide for running Nemotron-Nano-8B DA/MA experiments on RunPod
**Hardware Required**: 1× H100 80GB

---

## Prerequisites

- RunPod account with sufficient credits
- SSH key configured (e.g., `~/.ssh/runpod_ed25519`)
- Local copy of agent-green repository

---

## Step 1: Create RunPod Pod

### 1.1 Pod Configuration
1. Go to https://www.runpod.io/console/pods
2. Click **"Deploy"** → **"GPU Cloud"**
3. Select: **1× NVIDIA H100 80GB** (~$2.66/hour)
4. Select template: **"RunPod Pytorch"** or **"vLLM OpenAI Compatible"**
5. Configure:
   - **Container Disk**: 100 GB (8B model ~16GB, plus dependencies)
   - **Expose HTTP Ports**: 8000
   - **Expose TCP Ports**: 22 (for SSH)
6. Deploy and note down SSH details

### 1.2 SSH Connection
```bash
# Example SSH command (replace with your pod details)
ssh root@<POD_IP> -p <PORT> -i ~/.ssh/runpod_ed25519
```

---

## Step 2: Setup Pod Environment

### 2.1 Create Folder Structure (on RunPod)
```bash
cd /workspace
mkdir -p agent-green/src agent-green/scripts agent-green/vuln_database agent-green/results
```

### 2.2 Transfer Files (from local machine)

Open a **new terminal** on your local machine:

```bash
# Set your pod SSH details
POD_IP="<YOUR_POD_IP>"
POD_PORT="<YOUR_PORT>"
SSH_KEY="~/.ssh/runpod_ed25519"

# Transfer src folder
scp -P $POD_PORT -i $SSH_KEY -r /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/src root@$POD_IP:/workspace/agent-green/

# Transfer scripts folder
scp -P $POD_PORT -i $SSH_KEY -r /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/scripts root@$POD_IP:/workspace/agent-green/

# Transfer vuln_database folder
scp -P $POD_PORT -i $SSH_KEY -r /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/vuln_database root@$POD_IP:/workspace/agent-green/

# Transfer env file (8B config)
scp -P $POD_PORT -i $SSH_KEY /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/.env.nemotron root@$POD_IP:/workspace/agent-green/

# Transfer requirements file
scp -P $POD_PORT -i $SSH_KEY /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/requirements-runpod.txt root@$POD_IP:/workspace/agent-green/
```

### 2.3 Install Dependencies (on RunPod)
```bash
cd /workspace/agent-green

# Install hf_transfer for fast model downloads
pip install hf_transfer

# Install experiment dependencies
pip install autogen python-dotenv codecarbon pandas numpy evaluate scikit-learn python-Levenshtein

pip install vllm

# Note: 'autogen' is an alias for 'ag2'. Do NOT use 'pyautogen'.
```

### 2.4 Setup Environment File
```bash
cd /workspace/agent-green

# Copy 8B env file
cp .env.nemotron .env

# Verify env settings
cat .env | grep -E "(MODEL|ENABLE_REASONING|ENDPOINT)"
```

### 2.5 Source Environment Variables
**IMPORTANT**: Use `set -a` to auto-export all variables when sourcing `.env`:
```bash
# This ensures all variables are exported to child processes (Python scripts)
set -a && source .env && set +a

# Set MODEL_FAMILY for script config selection
export MODEL_FAMILY=nemotron

# Override ENABLE_REASONING as needed for each experiment
export ENABLE_REASONING=true   # for thinking mode
# or
export ENABLE_REASONING=false  # for instruct mode
```

---

## Step 3: Deploy vLLM Server

### 3.1 Start vLLM for Nemotron-Nano-8B
```bash
cd /workspace/agent-green

# IMPORTANT: Unset HF_HUB_ENABLE_HF_TRANSFER to avoid vLLM startup errors
unset HF_HUB_ENABLE_HF_TRANSFER

# Start vLLM server for Nemotron-Nano-8B (single H100)
# Using 64K context to match Qwen3/49B experiments for fair comparison
nohup python3 -m vllm.entrypoints.openai.api_server \
    --model nvidia/Llama-3.1-Nemotron-Nano-8B-v1 \
    --served-model-name "nvidia/Llama-3.1-Nemotron-Nano-8B-v1" \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype auto \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.9 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    --trust-remote-code \
    > /workspace/vllm.log 2>&1 &

# Monitor loading progress (~2-3 minutes)
tail -f /workspace/vllm.log
```

**Context Length Note (Updated Dec 23, 2025)**:
- Using 64K (`--max-model-len 65536`) to match Qwen3 and Nemotron-49B experiments
- This ensures fair energy consumption comparison across architectures
- Some samples may hit context overflow or timeout - use skip/resume to handle (see Troubleshooting)

### 3.2 Verify Server is Ready
Look for this message in the logs:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Test the server:
```bash
curl http://localhost:8000/v1/models
```

### 3.3 Validate Thinking Toggle
```bash
python scripts/validate_nemotron_modes.py --endpoint http://localhost:8000/v1
```

---

## Step 4: Run Multi-Agent Experiments

### 4.1 Experiment Matrix (RQ2 DA/MA - 16 experiments)

| ID | Agent | Task | Mode | Prompting | ENABLE_REASONING | Status |
|----|-------|------|------|-----------|------------------|--------|
| NM-25 | DA | Vuln | Instruct | Zero-shot | false | ⏳ |
| NM-26 | DA | Vuln | Instruct | Few-shot | false | ⏳ |
| NM-27 | DA | Vuln | Thinking | Zero-shot | true | ⏳ |
| NM-28 | DA | Vuln | Thinking | Few-shot | true | ⏳ |
| NM-29 | DA | Code | Instruct | Zero-shot | false | ⏳ |
| NM-30 | DA | Code | Instruct | Few-shot | false | ⏳ |
| NM-31 | DA | Code | Thinking | Zero-shot | true | ⏳ |
| NM-32 | DA | Code | Thinking | Few-shot | true | ⏳ |
| NM-33 | MA | Vuln | Instruct | Zero-shot | false | ⏳ |
| NM-34 | MA | Vuln | Instruct | Few-shot | false | ⏳ |
| NM-35 | MA | Vuln | Thinking | Zero-shot | true | ⏳ |
| NM-36 | MA | Vuln | Thinking | Few-shot | true | ⏳ |
| NM-37 | MA | Code | Instruct | Zero-shot | false | ⏳ |
| NM-38 | MA | Code | Instruct | Few-shot | false | ⏳ |
| NM-39 | MA | Code | Thinking | Zero-shot | true | ⏳ |
| NM-40 | MA | Code | Thinking | Few-shot | true | ⏳ |

### 4.2 Run Dual-Agent Vulnerability Detection

Open a **second SSH terminal** for running experiments:

```bash
cd /workspace/agent-green

# Source environment (IMPORTANT: use set -a to export variables)
set -a && source .env && set +a
export MODEL_FAMILY=nemotron

# === NM-25: DA Vuln Zero-shot Instruct ===
export ENABLE_REASONING=false
nohup python src/dual_agent_vuln.py --prompt_type zero_shot > nm25.log 2>&1 &
tail -f nm25.log

# === NM-26: DA Vuln Few-shot Instruct ===
export ENABLE_REASONING=false
nohup python src/dual_agent_vuln.py --prompt_type few_shot > nm26.log 2>&1 &
tail -f nm26.log

# === NM-27: DA Vuln Zero-shot Thinking ===
export ENABLE_REASONING=true
nohup python src/dual_agent_vuln.py --prompt_type zero_shot > nm27.log 2>&1 &
tail -f nm27.log

# === NM-28: DA Vuln Few-shot Thinking ===
export ENABLE_REASONING=true
nohup python src/dual_agent_vuln.py --prompt_type few_shot > nm28.log 2>&1 &
tail -f nm28.log
```

### 4.3 Run Dual-Agent Code Generation

```bash
cd /workspace/agent-green
set -a && source .env && set +a
export MODEL_FAMILY=nemotron

# === NM-29: DA Code Zero-shot Instruct ===
export ENABLE_REASONING=false
nohup python src/dual_agent_code_generation.py --prompt_type zero_shot > nm29.log 2>&1 &
tail -f nm29.log

# === NM-30: DA Code Few-shot Instruct ===
export ENABLE_REASONING=false
nohup python src/dual_agent_code_generation.py --prompt_type few_shot > nm30.log 2>&1 &
tail -f nm30.log

# === NM-31: DA Code Zero-shot Thinking ===
export ENABLE_REASONING=true
nohup python src/dual_agent_code_generation.py --prompt_type zero_shot > nm31.log 2>&1 &
tail -f nm31.log

# === NM-32: DA Code Few-shot Thinking ===
export ENABLE_REASONING=true
nohup python src/dual_agent_code_generation.py --prompt_type few_shot > nm32.log 2>&1 &
tail -f nm32.log
```

### 4.4 Run Multi-Agent Vulnerability Detection (4 agents)

```bash
cd /workspace/agent-green
set -a && source .env && set +a
export MODEL_FAMILY=nemotron

# === NM-33: MA Vuln Zero-shot Instruct ===
export ENABLE_REASONING=false
nohup python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot > nm33.log 2>&1 &
tail -f nm33.log

# === NM-34: MA Vuln Few-shot Instruct ===
export ENABLE_REASONING=false
nohup python src/multi_agent_vuln_detection_four_agents.py --prompt_type few_shot > nm34.log 2>&1 &
tail -f nm34.log

# === NM-35: MA Vuln Zero-shot Thinking ===
export ENABLE_REASONING=true
nohup python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot > nm35.log 2>&1 &
tail -f nm35.log

# === NM-36: MA Vuln Few-shot Thinking ===
export ENABLE_REASONING=true
nohup python src/multi_agent_vuln_detection_four_agents.py --prompt_type few_shot > nm36.log 2>&1 &
tail -f nm36.log
```

### 4.5 Run Multi-Agent Code Generation

```bash
cd /workspace/agent-green
set -a && source .env && set +a
export MODEL_FAMILY=nemotron

# === NM-37: MA Code Zero-shot Instruct ===
export ENABLE_REASONING=false
nohup python src/multi_agent_code_generation.py --prompt_type zero_shot > nm37.log 2>&1 &
tail -f nm37.log

# === NM-38: MA Code Few-shot Instruct ===
export ENABLE_REASONING=false
nohup python src/multi_agent_code_generation.py --prompt_type few_shot > nm38.log 2>&1 &
tail -f nm38.log

# === NM-39: MA Code Zero-shot Thinking ===
export ENABLE_REASONING=true
nohup python src/multi_agent_code_generation.py --prompt_type zero_shot > nm39.log 2>&1 &
tail -f nm39.log

# === NM-40: MA Code Few-shot Thinking ===
export ENABLE_REASONING=true
nohup python src/multi_agent_code_generation.py --prompt_type few_shot > nm40.log 2>&1 &
tail -f nm40.log
```

### 4.6 Monitor Progress
```bash
# Check running processes
ps aux | grep python

# Check experiment logs
tail -50 nm*.log

# Check GPU utilization
nvidia-smi
```

---

## Step 5: Download Results & Cleanup

### 5.1 Download Results (from local machine)
```bash
POD_IP="<YOUR_POD_IP>"
POD_PORT="<YOUR_PORT>"
SSH_KEY="~/.ssh/runpod_ed25519"

# Download all results
scp -P $POD_PORT -i $SSH_KEY -r root@$POD_IP:/workspace/agent-green/results \
  /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results_nemotron_8b_ma/
```

### 5.2 Verify Downloads
```bash
ls -la results_nemotron_8b_ma/
```

### 5.3 Stop/Delete Pod
1. Go to RunPod console
2. Click **"Stop"** or **"Delete"** on your pod
3. Verify billing stops

---

## Nemotron 8B Toggle Reference

Nemotron-Nano-8B uses explicit system prompt toggle:

| Mode | System Prompt Prefix |
|------|---------------------|
| Thinking ON | `detailed thinking on` |
| Thinking OFF | `detailed thinking off` |

The `config_nemotron.py` handles this automatically based on `ENABLE_REASONING` environment variable.

---

## Troubleshooting

### vLLM Server Not Responding
```bash
# Check if vLLM is running
ps aux | grep vllm

# Check logs for errors
tail -100 vllm.log

# Restart if needed
pkill -f vllm
# Then re-run the vLLM start command
```

### Experiment Hangs or Timeout
- Thinking mode can generate very long traces
- Use `Ctrl+C` to interrupt, then resume
- Check `config_nemotron.py` for `max_tokens` limit

### GPU Memory Not Released
```bash
# Kill orphaned processes
nvidia-smi --query-compute-apps=pid --format=csv,noheader | xargs -r kill -9

# Verify GPU is free
nvidia-smi
```

---

## Cost Estimate

| Resource | Rate | Estimated Time | Cost |
|----------|------|----------------|------|
| 1× H100 | ~$2.66/hr | 8-12 hours (16 experiments) | ~$21-32 |

**Note**: MA experiments take longer than SA due to multi-turn conversations.

---

## Quick Reference Commands

```bash
# SSH into pod
ssh root@<IP> -p <PORT> -i ~/.ssh/runpod_ed25519

# IMPORTANT: Unset HF_HUB_ENABLE_HF_TRANSFER to avoid vLLM startup errors
unset HF_HUB_ENABLE_HF_TRANSFER

# Start vLLM 8B (64K context - matches Qwen3/49B for fair comparison)
nohup python3 -m vllm.entrypoints.openai.api_server \
    --model nvidia/Llama-3.1-Nemotron-Nano-8B-v1 \
    --trust-remote-code --max-model-len 65536 \
    --gpu-memory-utilization 0.90 --enforce-eager > vllm.log 2>&1 &

# Check vLLM status
curl http://localhost:8000/v1/models

# Setup environment
set -a && source .env && set +a
export MODEL_FAMILY=nemotron

# Run DA vuln (instruct)
export ENABLE_REASONING=false
python src/dual_agent_vuln.py --prompt_type zero_shot

# Run MA code (thinking)
export ENABLE_REASONING=true
python src/multi_agent_code_generation.py --prompt_type few_shot
```
