# Mars Docker Workflow - Running Experiments Inside Containers

> **⚠️ Note**: This guide uses `huabengtan` as the username, which is the author's assigned SMU account.
> **Replace all instances of `huabengtan` with your own SMU username** throughout this document.

## Problem

When vLLM runs in Docker and experiments run on host:
- ❌ CodeCarbon can't measure GPU energy (only host CPU/RAM)
- ❌ Need admin rights for pip install on host
- ❌ Energy metrics will be inaccurate

## Solution

Run experiments **inside the Docker container** alongside vLLM, so CodeCarbon can access the GPU.

---

## Setup Workflow

### Step 1: Start vLLM Containers (Keep Running)

On Mars server:

```bash
# Container 1: Thinking Model (GPU 1, port 8000)
docker run -d \
    --name qwen-thinking \
    --gpus '"device=1"' \
    --shm-size=16g \
    -v /mnt/hdd2/huabengtan/agent-green:/workspace/agent-green \
    -p 8000:8000 \
    --entrypoint /bin/bash \
    vllm/vllm-openai:latest \
    -c "python3 -m vllm.entrypoints.openai.api_server \
        --model Qwen/Qwen3-4B-Thinking-2507 \
        --download-dir /workspace/agent-green/models \
        --gpu-memory-utilization 0.80 \
        --max-model-len 65536 \
        --dtype auto \
        --host 0.0.0.0 \
        --port 8000 & tail -f /dev/null"

# Container 2: Baseline Model (GPU 3, port 8001)
docker run -d \
    --name qwen-baseline \
    --gpus '"device=3"' \
    --shm-size=16g \
    -v /mnt/hdd2/huabengtan/agent-green:/workspace/agent-green \
    -p 8001:8000 \
    --entrypoint /bin/bash \
    vllm/vllm-openai:latest \
    -c "python3 -m vllm.entrypoints.openai.api_server \
        --model Qwen/Qwen3-4B-Instruct-2507 \
        --download-dir /workspace/agent-green/models \
        --gpu-memory-utilization 0.80 \
        --max-model-len 65536 \
        --dtype auto \
        --host 0.0.0.0 \
        --port 8000 & tail -f /dev/null"
```

**Key Configuration:**
- `-v /mnt/hdd2/huabengtan/agent-green:/workspace/agent-green` - Mounts your code
- `--entrypoint /bin/bash` - Allows running commands inside container
- `& tail -f /dev/null` - Keeps container running after vLLM starts
- `--max-model-len 65536` - **64K context window** (prevents truncation of reasoning outputs)
- `--gpu-memory-utilization 0.80` - 80% GPU memory (leaves room for 64K context)

**Why 64K Context?**
- Reasoning models produce verbose step-by-step reasoning (5-10K+ tokens)
- System prompt + code sample + reasoning + answer can exceed 32K
- 64K provides adequate headroom to avoid truncation

### Step 2: Wait for vLLM to Load

```bash
# Watch thinking model startup
docker logs -f qwen-thinking

# Watch baseline model startup
docker logs -f qwen-baseline

# Wait for "Application startup complete" (~5 minutes)
```

### Step 3: Install Dependencies Inside Containers

```bash
# Install in thinking container
docker exec qwen-thinking pip install autogen python-dotenv codecarbon pandas numpy scikit-learn

# Install in baseline container
docker exec qwen-baseline pip install autogen python-dotenv codecarbon pandas numpy scikit-learn
```

**No admin rights needed!** Dependencies install inside the container.

### Step 4: Verify vLLM is Running

```bash
# Test thinking model (inside container)
docker exec qwen-thinking curl http://localhost:8000/v1/models

# Test baseline model (inside container)
docker exec qwen-baseline curl http://localhost:8000/v1/models
```

### Step 5: Update .env for Container Environment

The `.env.mars` file should use `localhost:8000` because experiments run inside the container:

```bash
# Already correct in .env.mars:
# REASONING_ENDPOINT=http://localhost:8000/v1
# BASELINE_ENDPOINT=http://localhost:8000/v1
# ENABLE_CODECARBON=true  # Enable GPU energy tracking inside container
```

Note: Both use port 8000 because each runs inside its own container. The host port mapping (8000 vs 8001) doesn't matter inside.

**Important:** `ENABLE_CODECARBON=true` enables GPU energy tracking because experiments run inside the Docker container with direct GPU access.

### Step 6: Run Experiments Inside Containers

#### Option A: Interactive Mode (Recommended for Testing)

**For Thinking Model (Reasoning Enabled):**
```bash
# Enter thinking container
docker exec -it qwen-thinking bash

# Inside container, navigate to project directory:
cd /workspace/agent-green

# Copy .env configuration for container
cp .env.mars .env

# Set environment variables (override .env settings)
export ENABLE_REASONING=true
export VULN_DATASET=/workspace/agent-green/vuln_database/VulTrial_10_samples_test.jsonl

# Quick test (10 samples)
python3 src/single_agent_vuln.py SA-zero

# Full experiments
unset VULN_DATASET
python3 src/single_agent_vuln.py SA-zero
python3 src/single_agent_vuln.py SA-few

# Exit container
exit
```

**For Baseline Model (Reasoning Disabled):**
```bash
# Enter baseline container
docker exec -it qwen-baseline bash

# Inside container, navigate to project directory:
cd /workspace/agent-green

# Copy .env configuration for container
cp .env.mars .env

# Set environment variables (override .env settings)
export ENABLE_REASONING=false
export VULN_DATASET=/workspace/agent-green/vuln_database/VulTrial_10_samples_test.jsonl

# Quick test (10 samples)
python3 src/single_agent_vuln.py SA-zero

# Full experiments
unset VULN_DATASET
python3 src/single_agent_vuln.py SA-zero
python3 src/single_agent_vuln.py SA-few

# Exit container
exit
```

#### Option B: Non-Interactive Mode (Run in Background)

```bash
# Run thinking experiments
docker exec -d qwen-thinking bash -c "
  cd /workspace/agent-green && \
  cp .env.mars .env && \
  export ENABLE_REASONING=true && \
  python3 src/single_agent_vuln.py SA-zero && \
  python3 src/single_agent_vuln.py SA-few
"

# Run baseline experiments
docker exec -d qwen-baseline bash -c "
  cd /workspace/agent-green && \
  cp .env.mars .env && \
  export ENABLE_REASONING=false && \
  python3 src/single_agent_vuln.py SA-zero && \
  python3 src/single_agent_vuln.py SA-few
"
```

### Step 7: Monitor Progress

```bash
# Watch experiment logs
docker exec qwen-thinking tail -f /workspace/agent-green/results/*_detailed_results.jsonl

# Check GPU usage
nvidia-smi

# Check results
ls -lh /mnt/hdd2/huabengtan/agent-green/results/
```

### Step 8: Download Results

```bash
# From your local machine
scp -r huabengtan@10.193.104.137:/mnt/hdd2/huabengtan/agent-green/results ./results_mars
```

---

## Why This Works

✅ **CodeCarbon can measure GPU** - Running inside container with GPU access (when `ENABLE_CODECARBON=true`)
✅ **No admin rights needed** - pip install inside container
✅ **Accurate energy metrics** - Direct GPU access via Docker GPU passthrough
✅ **Shared filesystem** - Results save to mounted volume
✅ **Both models in parallel** - Independent containers
✅ **Flexible energy tracking** - Can enable/disable CodeCarbon via environment variable

---

## Alternative: Skip CodeCarbon, Use nvidia-smi

If CodeCarbon still doesn't work in Docker, can manually track GPU power:

### Create Monitoring Script

```bash
# On Mars host
cat > /mnt/hdd2/huabengtan/agent-green/monitor_gpu.sh << 'EOF'
#!/bin/bash
LOG_FILE="/mnt/hdd2/huabengtan/agent-green/gpu_power_log.csv"
echo "timestamp,gpu_id,power_draw_w,memory_used_mb,utilization_pct" > $LOG_FILE

while true; do
  TIMESTAMP=$(date +%s)
  nvidia-smi --query-gpu=index,power.draw,memory.used,utilization.gpu --format=csv,noheader,nounits | while read line; do
    echo "$TIMESTAMP,$line" >> $LOG_FILE
  done
  sleep 5
done
EOF

chmod +x /mnt/hdd2/huabengtan/agent-green/monitor_gpu.sh

# Run in background
nohup /mnt/hdd2/huabengtan/agent-green/monitor_gpu.sh &
```

### Calculate Energy Manually

```python
import pandas as pd

# Read GPU power log
df = pd.read_csv('gpu_power_log.csv')
df = df[df['gpu_id'].isin([1, 3])]  # Only GPUs 1 and 3

# Calculate energy (Power * Time)
df['time_diff'] = df['timestamp'].diff().fillna(5)  # seconds
df['energy_wh'] = (df['power_draw_w'] * df['time_diff']) / 3600

total_energy_kwh = df['energy_wh'].sum() / 1000
print(f"Total energy: {total_energy_kwh:.4f} kWh")
```

---

## Troubleshooting

### Issue: API Timeout Errors

**Error**: `TimeoutError: OpenAI API call timed out`

**Cause**: Reasoning models (like Qwen3-4B-Thinking-2507) take longer to generate responses because they perform explicit reasoning steps.

**Solution**: The timeout has been increased to 300 seconds (5 minutes) in `config.py`:
```python
"timeout": 300,  # 5 minutes timeout (reasoning models can be slow)
```

If you still experience timeouts:
1. **Check vLLM server logs**: `docker logs qwen-thinking`
2. **Verify GPU is not overloaded**: `nvidia-smi`
3. **Check for OOM errors**: If seeing "CUDA out of memory", reduce `--gpu-memory-utilization` from 0.80 to 0.75 or reduce `--max-model-len` from 65536 to 49152 (48K)
4. **Consider increasing timeout**: Modify `config.py` line 84 to use a higher timeout value (e.g., 600 seconds)
5. **Check for context truncation**: Look for warnings in vLLM logs about exceeding max model length

### Issue: Context Length / Truncated Reasoning

**Error**: Reasoning outputs appear incomplete or cut off

**Symptoms**:
- Reasoning stops mid-sentence
- Model doesn't provide final answer
- vLLM logs show: "Input length exceeds maximum model length"

**Solution**:
1. **Check current max-model-len**: `docker logs qwen-thinking | grep "max-model-len"`
2. **If using 32K, increase to 64K**: Stop and restart containers with `--max-model-len 65536` (see Step 1 commands above)
3. **Monitor GPU memory**: `nvidia-smi` - ensure no OOM errors after increasing context
4. **If OOM occurs with 64K**:
   - Try 48K: `--max-model-len 49152`
   - Reduce GPU utilization: `--gpu-memory-utilization 0.75`

### Issue: CodeCarbon Fails with "No GPU found"

**Solution**: CodeCarbon might not detect GPUs in Docker. Use nvidia-smi monitoring instead (see above).

### Issue: Permission Denied Inside Container

**Solution**: Run as root (default in vLLM container):
```bash
docker exec -u 0 -it qwen-thinking bash
```

### Issue: Results Not Saving

**Solution**: Check mount and permissions:
```bash
# On host
ls -la /mnt/hdd2/huabengtan/agent-green/results/

# Inside container
ls -la /workspace/agent-green/results/
```

### Issue: Container Exits

**Solution**: The `tail -f /dev/null` keeps it running. If it exits, check logs:
```bash
docker logs qwen-thinking
```

---

## Quick Reference

```bash
# Start both containers
# (Use commands from Step 1)

# Install dependencies
docker exec qwen-thinking pip install autogen python-dotenv codecarbon pandas numpy scikit-learn
docker exec qwen-baseline pip install autogen python-dotenv codecarbon pandas numpy scikit-learn

# Run experiments (interactive) - Thinking model
docker exec -it qwen-thinking bash
cd /workspace/agent-green
cp .env.mars .env
export ENABLE_REASONING=true
python3 src/single_agent_vuln.py SA-zero

# Run experiments (interactive) - Baseline model
docker exec -it qwen-baseline bash
cd /workspace/agent-green
cp .env.mars .env
export ENABLE_REASONING=false
python3 src/single_agent_vuln.py SA-zero

# Run experiments (background) - Thinking model
docker exec -d qwen-thinking bash -c "cd /workspace/agent-green && cp .env.mars .env && export ENABLE_REASONING=true && python3 src/single_agent_vuln.py SA-zero"

# Run experiments (background) - Baseline model
docker exec -d qwen-baseline bash -c "cd /workspace/agent-green && cp .env.mars .env && export ENABLE_REASONING=false && python3 src/single_agent_vuln.py SA-zero"

# Monitor thinking model
docker exec qwen-thinking tail -f /workspace/agent-green/results/*_detailed_results.jsonl

# Monitor baseline model
docker exec qwen-baseline tail -f /workspace/agent-green/results/*_detailed_results.jsonl

# Check GPU usage
nvidia-smi

# Download results
scp -r huabengtan@10.193.104.137:/mnt/hdd2/huabengtan/agent-green/results ./results_mars
```

---

## Summary

**This approach solves both problems:**
1. ✅ No pip admin rights needed - install inside container
2. ✅ CodeCarbon can measure GPU - running in same container as vLLM

**Expected Timeline:**
- Setup: 10 minutes
- Model download/load: 5 minutes per model
- Experiments: ~2 hours (both in parallel)
- Total: ~2.5 hours from start to results

**Cost:** $0 (free!)
