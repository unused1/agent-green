# Qwen3-4B Setup on Mars Server (SMU SCIS) for RQ1 Experiments

## Server Specifications
- **Server**: Mars (10.193.104.137)
- **GPUs**: 4 x NVIDIA RTX A5000 (24GB VRAM each, 96GB total)
- **OS**: Ubuntu 24.04.1 LTS
- **CUDA**: 12.4 (driver 550.90.07)
- **Python**: 3.12.3
- **Docker**: Available (v27.3.1)
- **Workspace**: `/mnt/hdd2/huabengtan` (6.8TB available)

## Overview

This guide sets up **two separate Qwen models** running in parallel on Mars server for RQ1 vulnerability detection experiments:
- **Pod 1 (GPU 0)**: Qwen3-4B-Thinking-2507 (reasoning-enabled)
- **Pod 2 (GPU 1)**: Qwen3-4B-Instruct-2507 (baseline)

Each model requires ~8GB VRAM, easily fitting on one A5000 GPU.

## Prerequisites

Before starting, ensure you have:
- Access to Mars server via SMU VPN
- SSH access: `huabengtan@10.193.104.137`
- Hugging Face account (models are public, no token required)

## Setup Instructions

### 1. Connect to Mars Server

```bash
# From your local machine (with SMU VPN connected)
ssh huabengtan@10.193.104.137
```

### 2. Set Up Working Directory

```bash
# Create project directory in your allocated space
mkdir -p /mnt/hdd2/huabengtan/agent-green/{models,logs,results}
cd /mnt/hdd2/huabengtan/agent-green
```

### 3. Pull vLLM Docker Image

```bash
# Pull the latest vLLM image (if not already available)
docker pull vllm/vllm-openai:latest
```

### 4. Check GPU Availability

**IMPORTANT**: Always check which GPUs are free before starting containers.

```bash
# Check GPU availability and memory usage
nvidia-smi

# Look for GPUs with low memory usage (ideally < 500MiB)
# Note the GPU IDs that are available (0, 1, 2, or 3)
# Avoid GPUs being used by other processes
```

Example output:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 550.90.07              Driver Version: 550.90.07    CUDA: 12.4 |
|-------------------------------+----------------------+----------------------+
|   0  NVIDIA RTX A5000        | 00000000:01:00.0 Off |                  Off |
| GPU 0: 45°C    Fan: 30%      | MIG M.   |  380MiB / 24564MiB |      0%     |
|   1  NVIDIA RTX A5000        | 00000000:25:00.0 Off |                  Off |
| GPU 1: 42°C    Fan: 30%      | MIG M.   |  256MiB / 24564MiB |      0%     |
|   2  NVIDIA RTX A5000        | 00000000:41:00.0 Off |                  Off |
| GPU 2: 50°C    Fan: 35%      | MIG M.   | 8456MiB / 24564MiB |     45%     | ← In use
|   3  NVIDIA RTX A5000        | 00000000:61:00.0 Off |                  Off |
| GPU 3: 44°C    Fan: 30%      | MIG M.   |  298MiB / 24564MiB |      0%     |
+-----------------------------------------------------------------------------+
```
In this example, GPUs 0, 1, and 3 are available. GPU 2 is in use.

### 5. Start vLLM Containers for Both Models

#### Container 1: Qwen3-4B-Thinking-2507 (Reasoning Model)

**Update `--gpus '"device=X"'` based on available GPUs from nvidia-smi.**

```bash
# Start thinking model on GPU 0 (or first available GPU)
docker run -d \
    --name qwen-thinking \
    --gpus '"device=1"' \
    --shm-size=16g \
    -v /mnt/hdd2/huabengtan/agent-green/models:/models \
    -p 8000:8000 \
    --restart unless-stopped \
    vllm/vllm-openai:latest \
    --model Qwen/Qwen3-4B-Thinking-2507 \
    --download-dir /models \
    --gpu-memory-utilization 0.80 \
    --max-model-len 65536 \
    --dtype auto

# Monitor startup progress
docker logs qwen-thinking -f
```

#### Container 2: Qwen3-4B-Instruct-2507 (Baseline Model)

```bash
# Start baseline model on GPU 1 (or second available GPU)
docker run -d \
    --name qwen-baseline \
    --gpus '"device=3"' \
    --shm-size=16g \
    -v /mnt/hdd2/huabengtan/agent-green/models:/models \
    -p 8001:8000 \
    --restart unless-stopped \
    vllm/vllm-openai:latest \
    --model Qwen/Qwen3-4B-Instruct-2507 \
    --download-dir /models \
    --gpu-memory-utilization 0.80 \
    --max-model-len 65536 \
    --dtype auto

# Monitor startup progress
docker logs qwen-baseline -f
```

**⚠️ Configuration Notes:**

**Context Length (--max-model-len 65536)**:
- 64K tokens provides adequate headroom for reasoning models
- Thinking models generate verbose step-by-step reasoning (5-10K+ tokens)
- System prompt + code + reasoning + answer can exceed 32K
- Prevents truncation of model outputs

**GPU Memory (--gpu-memory-utilization 0.80)**:
- 80% utilization leaves room for 64K context window
- Prevents OOM errors during inference
- Can be adjusted to 0.75 if needed

**⚠️ IMPORTANT - Initial Setup Time:**
- **Model Download**: ~8GB per model, takes 2-4 minutes on Mars network
- **Model Loading**: Takes 2-3 minutes to load into GPU memory
- **Total First Run**: Expect 4-7 minutes per model before server is ready
- **Subsequent Runs**: Only 2-3 minutes (models already downloaded)
- **Both models can download in parallel** if sufficient bandwidth

**Progress Indicators to Watch For:**
1. `Downloading shards...` - Download starting
2. `Loading model weights...` - Loading into GPU
3. `Warmup finished` - Server warming up
4. `Application startup complete` - Server ready!
5. API responds at `http://localhost:8000/v1/models` (or port 8001)

### 6. Verify Both Servers are Running

Wait for "Application startup complete" in logs, then test:

```bash
# Test thinking model (port 8000)
curl http://localhost:8000/v1/models

# Test baseline model (port 8001)
curl http://localhost:8001/v1/models

# Test thinking model inference
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-4B-Thinking-2507",
    "prompt": "Hello, how are you?",
    "max_tokens": 50,
    "temperature": 0
  }'

# Test baseline model inference
curl http://localhost:8001/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-4B-Instruct-2507",
    "prompt": "Hello, how are you?",
    "max_tokens": 50,
    "temperature": 0
  }'
```

### 7. Upload Experiment Files from Local Machine

From your **local machine**:

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Upload necessary files
scp -r src scripts vuln_database huabengtan@10.193.104.137:/mnt/hdd2/huabengtan/agent-green/

# Upload .env file (create Mars-specific version first)
scp .env.mars huabengtan@10.193.104.137:/mnt/hdd2/huabengtan/agent-green/.env
```

### 8. Create Mars-Specific .env File (on Local Machine First)

Create `.env.mars` on your local machine:

```bash
# Project configuration
PROJECT_ROOT=/mnt/hdd2/huabengtan/agent-green

# ============================================================================
# BACKEND SELECTION
# ============================================================================
USE_RUNPOD=true  # Keep true - vLLM uses OpenAI-compatible API

# ============================================================================
# REASONING MODE TOGGLE
# ============================================================================
ENABLE_REASONING=false  # Will be toggled by experiment script

# ============================================================================
# MODEL CONFIGURATION (Mars Server - Local vLLM)
# ============================================================================

# Reasoning model (localhost:8000)
REASONING_MODEL=Qwen/Qwen3-4B-Thinking-2507
REASONING_ENDPOINT=http://localhost:8000/v1
REASONING_API_KEY=

# Baseline model (localhost:8001)
BASELINE_MODEL=Qwen/Qwen3-4B-Instruct-2507
BASELINE_ENDPOINT=http://localhost:8001/v1
BASELINE_API_KEY=
```

### 9. Setup Python Environment on Mars

```bash
# SSH into Mars
ssh huabengtan@10.193.104.137
cd /mnt/hdd2/huabengtan/agent-green

# Install Python dependencies
pip3 install --user autogen-agentchat python-dotenv codecarbon pandas numpy scikit-learn

# Or create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install autogen-agentchat python-dotenv codecarbon pandas numpy scikit-learn
```

### 10. Run Quick Test (10 samples)

```bash
# Still on Mars server
cd /mnt/hdd2/huabengtan/agent-green

# Test thinking model (10 samples, ~1 minute)
export VULN_DATASET="$PWD/vuln_database/VulTrial_10_samples_test.jsonl"
export ENABLE_REASONING=true
python3 src/single_agent_vuln.py SA-zero

# Test baseline model (10 samples, ~1 minute)
export ENABLE_REASONING=false
python3 src/single_agent_vuln.py SA-zero
```

### 11. Run Full Experiments (386 samples each)

You can run both experiments **in parallel** since they use different GPUs:

```bash
# Run thinking model experiments in background
nohup bash -c "
  export ENABLE_REASONING=true
  python3 src/single_agent_vuln.py SA-zero
  python3 src/single_agent_vuln.py SA-few
" > logs/thinking_experiments.log 2>&1 &

# Run baseline model experiments in background
nohup bash -c "
  export ENABLE_REASONING=false
  python3 src/single_agent_vuln.py SA-zero
  python3 src/single_agent_vuln.py SA-few
" > logs/baseline_experiments.log 2>&1 &

# Monitor progress
tail -f logs/thinking_experiments.log
tail -f logs/baseline_experiments.log

# Check results as they're generated
ls -lh results/
tail -f results/*_detailed_results.jsonl
```

**Expected Runtime** (on A5000):
- Single experiment: ~45-60 minutes (386 samples)
- Both zero+few per model: ~90-120 minutes
- **Total for all 4 experiments**: ~90-120 minutes (parallel execution)

### 12. Monitor Experiments

```bash
# Check GPU usage
watch -n 2 nvidia-smi

# Check Docker containers
docker ps

# Check experiment logs
tail -f logs/thinking_experiments.log
tail -f logs/baseline_experiments.log

# Count completed samples
wc -l results/*_detailed_results.jsonl

# Check energy consumption
cat results/*_energy_tracking.json | python3 -m json.tool
```

### 13. Download Results to Local Machine

From your **local machine**:

```bash
# Download all results
scp -r huabengtan@10.193.104.137:/mnt/hdd2/huabengtan/agent-green/results ./results_mars

# Download specific experiment
scp huabengtan@10.193.104.137:/mnt/hdd2/huabengtan/agent-green/results/Sa-zero_Qwen-Qwen3-4B-Thinking-2507_*.csv ./results_mars/
```

## Docker Container Management

### Check Container Status

```bash
# Check both containers
docker ps | grep qwen

# Check specific container
docker ps -a | grep qwen-thinking
docker ps -a | grep qwen-baseline
```

### View Logs

```bash
# View thinking model logs
docker logs qwen-thinking
docker logs -f qwen-thinking  # Follow in real-time
docker logs --tail 100 qwen-thinking  # Last 100 lines

# View baseline model logs
docker logs qwen-baseline
docker logs -f qwen-baseline
```

### Stop/Start/Restart Containers

```bash
# Stop containers
docker stop qwen-thinking
docker stop qwen-baseline

# Start containers
docker start qwen-thinking
docker start qwen-baseline

# Restart containers
docker restart qwen-thinking
docker restart qwen-baseline

# Remove containers (keeps downloaded models)
docker rm qwen-thinking
docker rm qwen-baseline
```

## Resource Management on Shared Server

Since Mars is a shared server, follow these guidelines:

### 1. GPU Selection
```bash
# Always check before starting
nvidia-smi

# Use GPUs with low memory usage
# Avoid GPUs with high utilization (>10%)
```

### 2. Memory Management
```bash
# Monitor your GPU processes
nvidia-smi | grep huabengtan

# If needed, reduce memory utilization
# Edit container start command:
# --gpu-memory-utilization 0.80  # Instead of 0.90
```

### 3. Storage Management
```bash
# Check your disk usage
du -sh /mnt/hdd2/huabengtan/agent-green

# Clean up old results if needed
rm -rf /mnt/hdd2/huabengtan/agent-green/results/old_*

# Check downloaded models
du -sh /mnt/hdd2/huabengtan/agent-green/models/*
```

### 4. Process Management
```bash
# Check your processes
ps aux | grep huabengtan

# Kill stuck Python processes if needed
pkill -u huabengtan -f single_agent_vuln.py

# Stop Docker containers
docker stop qwen-thinking qwen-baseline
```

## Monitoring and Troubleshooting

### Essential Monitoring Commands

```bash
# 1. Check both containers status
docker ps | grep qwen

# 2. View recent logs with timestamps
docker logs -t --tail 50 qwen-thinking
docker logs -t --tail 50 qwen-baseline

# 3. Check GPU memory usage
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv

# 4. Verify models downloaded
ls -lh /mnt/hdd2/huabengtan/agent-green/models/

# 5. Test if APIs are responding
curl -s http://localhost:8000/v1/models | python3 -m json.tool
curl -s http://localhost:8001/v1/models | python3 -m json.tool

# 6. Monitor experiment progress
tail -f results/*_detailed_results.jsonl

# 7. Check for errors in logs
docker logs qwen-thinking 2>&1 | grep -E "ERROR|Failed|Exception"
docker logs qwen-baseline 2>&1 | grep -E "ERROR|Failed|Exception"
```

### Startup Timeline (Per Container)

- **0-2 min**: Container initialization, detecting CUDA
- **2-5 min**: Downloading model weights (first run only)
- **5-7 min**: Loading model into GPU memory
- **7-8 min**: Model warmup and API startup
- **Ready**: Look for "Application startup complete" in logs

### Common Issues and Solutions

#### 1. Container Won't Start

```bash
# Check if port is already in use
lsof -i :8000
lsof -i :8001

# Use different ports if needed
# -p 8002:8000 instead of -p 8000:8000
```

#### 2. CUDA Out of Memory

```bash
# Check GPU usage
nvidia-smi

# Reduce memory utilization or use different GPU
# --gpu-memory-utilization 0.75
# --gpus '"device=2"'
```

#### 3. Model Download Fails

```bash
# Check internet connectivity
curl -I https://huggingface.co

# Check disk space
df -h /mnt/hdd2

# Manual download if needed
cd /mnt/hdd2/huabengtan/agent-green/models
git clone https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507
```

#### 4. Experiment Script Fails

```bash
# Check Python environment
which python3
python3 --version

# Verify .env file
cat .env | grep ENDPOINT

# Test model endpoints
curl http://localhost:8000/v1/models
curl http://localhost:8001/v1/models

# Check Python dependencies
pip3 list | grep -E "autogen|codecarbon|dotenv"
```

#### 5. SSH Connection Drops

```bash
# Use screen or tmux for long-running tasks
screen -S experiments
# or
tmux new -s experiments

# Detach: Ctrl+A, D (screen) or Ctrl+B, D (tmux)
# Reattach: screen -r experiments or tmux attach -t experiments
```

#### 6. Results Not Saving

```bash
# Check results directory permissions
ls -la results/

# Create if missing
mkdir -p results

# Check disk space
df -h /mnt/hdd2
```

## Performance Expectations

### GPU Performance (NVIDIA RTX A5000)

**Per Experiment (386 samples)**:
- **Throughput**: ~6-8 samples/minute
- **Duration**: 45-60 minutes
- **GPU Utilization**: 40-60%
- **Memory Usage**: ~8-10GB VRAM
- **Power Draw**: ~150-180W

**Total Experiments**:
- 4 experiments in parallel on 2 GPUs: ~90-120 minutes
- Energy consumption: ~0.3-0.5 kWh total
- CO2 emissions: Will be captured by CodeCarbon

### Comparison to Other Hardware

| Hardware | Time (4 experiments) | Cost | Energy |
|----------|---------------------|------|--------|
| **Mars A5000 (2 GPUs)** | **~2 hours** | **Free** | ~0.4 kWh |
| RunPod H100 | ~1.5 hours | $4.00 | ~0.5 kWh |
| RunPod A40 | ~4 hours | $3.20 | ~0.6 kWh |
| Local M3 Max | ~26 hours | Free | ~2.0 kWh |

**Mars is the best option**: Free, fast enough, and accurate energy tracking!

## Best Practices

### 1. Use Screen/Tmux for Long-Running Tasks

```bash
# Start screen session
screen -S qwen-experiments

# Run experiments
bash scripts/run_experiments.sh

# Detach: Ctrl+A, D
# Reattach: screen -r qwen-experiments
```

### 2. Monitor Resource Usage

```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    date
    echo "=== Docker Containers ==="
    docker ps | grep qwen
    echo -e "\n=== GPU Usage ==="
    nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader
    echo -e "\n=== Experiment Progress ==="
    wc -l results/*_detailed_results.jsonl 2>/dev/null
    sleep 5
done
EOF

chmod +x monitor.sh
./monitor.sh
```

### 3. Backup Results Regularly

```bash
# Create backup script
cat > backup_results.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
tar -czf results_backup_${TIMESTAMP}.tar.gz results/
echo "Backup created: results_backup_${TIMESTAMP}.tar.gz"
EOF

chmod +x backup_results.sh
```

### 4. Clean Up After Experiments

```bash
# Stop containers
docker stop qwen-thinking qwen-baseline

# Optional: Remove containers (keeps models)
docker rm qwen-thinking qwen-baseline

# Optional: Remove models to free space (after downloading results)
# rm -rf /mnt/hdd2/huabengtan/agent-green/models/*
```

## Integration with Experiment Scripts

Your existing `src/single_agent_vuln.py` script will work directly with this setup when:
1. `.env` is configured with localhost endpoints (8000 and 8001)
2. `USE_RUNPOD=true` (for OpenAI-compatible API)
3. `ENABLE_REASONING` is toggled for each experiment
4. Docker containers are running

The script automatically:
- Selects the correct endpoint based on `ENABLE_REASONING`
- Uses OpenAI-compatible API format
- Tracks energy consumption with CodeCarbon
- Saves results incrementally

## Quick Reference Commands

```bash
# Start both models
docker start qwen-thinking qwen-baseline

# Check status
docker ps | grep qwen

# View logs
docker logs -f qwen-thinking
docker logs -f qwen-baseline

# Test APIs
curl http://localhost:8000/v1/models
curl http://localhost:8001/v1/models

# Run experiments
python3 src/single_agent_vuln.py SA-zero
python3 src/single_agent_vuln.py SA-few

# Monitor progress
tail -f results/*_detailed_results.jsonl
watch -n 2 nvidia-smi

# Stop containers
docker stop qwen-thinking qwen-baseline

# Download results to local
scp -r huabengtan@10.193.104.137:/mnt/hdd2/huabengtan/agent-green/results ./results_mars
```

---

**Ready to run your RQ1 experiments on Mars!** 🚀

For questions or issues, refer to the troubleshooting section or check the similar setup at `docs/gemma_mars_setup.md`.
