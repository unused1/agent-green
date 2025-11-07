# RunPod Setup for Phase 3b: Qwen3-30B Code Generation

**Date**: 2025-11-07
**Models**: Qwen3-30B-A3B-Instruct-2507 & Qwen3-30B-A3B-Thinking-2507
**Task**: HumanEval Code Generation (164 samples)
**GPU**: H100 80GB (RunPod)

## Step 1: Deploy RunPod Pods

Deploy 2 separate pods for the two models:

### Pod 1: Qwen3-30B-A3B-Thinking (Reasoning)
- **Template**: RunPod PyTorch 2.4.0
- **GPU**: 1× H100 80GB
- **Container Disk**: 50GB
- **Volume**: 200GB (persistent storage)
- **Expose Ports**: 8000, 22

### Pod 2: Qwen3-30B-A3B-Instruct (Baseline)
- **Template**: RunPod PyTorch 2.4.0
- **GPU**: 1× H100 80GB
- **Container Disk**: 50GB
- **Volume**: 200GB (persistent storage)
- **Expose Ports**: 8000, 22

## Step 2: SSH into Pods

```bash
# Pod 1 (Thinking) - 157.66.254.40:10736
ssh root@157.66.254.40 -p 10736 -i ~/.ssh/runpod_ed25519

# Pod 2 (Instruct) - 154.57.34.102:43716
ssh root@154.57.34.102 -p 43716 -i ~/.ssh/runpod_ed25519
```

## Step 3: Install Dependencies (on both pods)

```bash
# Install hf_transfer for fast model downloads
pip install hf_transfer --break-system-packages

# Install vLLM
pip install vllm --break-system-packages

# Install experiment dependencies
pip install autogen python-dotenv codecarbon pandas numpy evaluate --break-system-packages

# Create project directory structure
cd /workspace
mkdir -p agent-green/src agent-green/vuln_database agent-green/results
```

## Step 4: Upload Files to Both Pods

From your local machine:

```bash
# Upload .env config
scp -P <port> .env.runpod.codegen root@<pod-ssh-address>:/workspace/agent-green/.env

# Upload code generation script (if updated)
scp -P <port> src/single_agent_code_generation.py root@<pod-ssh-address>:/workspace/agent-green/src/

# Upload HumanEval dataset
scp -P <port> vuln_database/HumanEval.jsonl root@<pod-ssh-address>:/workspace/agent-green/vuln_database/
```

## Step 5: Start vLLM Servers

### On Pod 1 (Thinking Model)

```bash
cd /workspace/agent-green

# Start vLLM server for Thinking model
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

# Verify model is running
curl http://localhost:8000/v1/models
```

### On Pod 2 (Instruct Model)

```bash
cd /workspace/agent-green

# Update .env to use port 8000 (not 8001) since it's a separate pod
sed -i 's|BASELINE_ENDPOINT=http://localhost:8001/v1|BASELINE_ENDPOINT=http://localhost:8000/v1|g' .env

# Start vLLM server for Instruct model
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

# Verify model is running
curl http://localhost:8000/v1/models
```

## Step 6: Run Experiments

### On Pod 1 (Thinking): Run Zero-shot and Few-shot

```bash
# Thinking Zero-shot
cd /workspace/agent-green
export ENABLE_REASONING=true
python3 src/single_agent_code_generation.py SA-zero

# Thinking Few-shot
python3 src/single_agent_code_generation.py SA-few
```

### On Pod 2 (Instruct): Run Zero-shot and Few-shot

```bash
# Instruct Zero-shot
cd /workspace/agent-green
export ENABLE_REASONING=false
python3 src/single_agent_code_generation.py SA-zero

# Instruct Few-shot
python3 src/single_agent_code_generation.py SA-few
```

## Step 7: Download Results

```bash
# Download from Pod 1 (Thinking)
scp -P <port> -r root@<pod1-ssh-address>:/workspace/agent-green/results/Sa-*Qwen3-30B-A3B-Thinking* results/runpod_codegen/
scp -P <port> -r root@<pod1-ssh-address>:/workspace/agent-green/results/codecarbon_thinking_* results/runpod_codegen/

# Download from Pod 2 (Instruct)
scp -P <port> -r root@<pod2-ssh-address>:/workspace/agent-green/results/Sa-*Qwen3-30B-A3B-Instruct* results/runpod_codegen/
scp -P <port> -r root@<pod2-ssh-address>:/workspace/agent-green/results/codecarbon_baseline_* results/runpod_codegen/
```

## Expected Results Structure

```
results/runpod_codegen/
├── Sa-zero_Qwen3-30B-A3B-Instruct-2507_*_detailed_results.jsonl
├── Sa-zero_Qwen3-30B-A3B-Instruct-2507_*_evaluation.json
├── Sa-few_Qwen3-30B-A3B-Instruct-2507_*_detailed_results.jsonl
├── Sa-few_Qwen3-30B-A3B-Instruct-2507_*_evaluation.json
├── Sa-zero_Qwen3-30B-A3B-Thinking-2507_*_detailed_results.jsonl
├── Sa-zero_Qwen3-30B-A3B-Thinking-2507_*_evaluation.json
├── Sa-few_Qwen3-30B-A3B-Thinking-2507_*_detailed_results.jsonl
├── Sa-few_Qwen3-30B-A3B-Thinking-2507_*_evaluation.json
├── codecarbon_baseline_sa-zero/emissions.csv
├── codecarbon_baseline_sa-few/emissions.csv
├── codecarbon_thinking_sa-zero/emissions.csv
└── codecarbon_thinking_sa-few/emissions.csv
```

## Notes

- Each experiment takes ~40-60 minutes on H100 80GB
- Total cost: ~4 hours × 2 pods × $2.49/hr = ~$20
- CodeCarbon will track GPU energy consumption
- Resume capability enabled if experiments are interrupted
- Port 8000 is used internally in both pods (no conflict)
