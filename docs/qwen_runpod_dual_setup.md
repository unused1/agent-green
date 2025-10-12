# Qwen3-4B Dual-Pod Setup on RunPod (Parallel Experiments)

## Overview
This guide provides instructions for deploying TWO Qwen3-4B models on RunPod using vLLM for parallel experiment execution. One pod runs the reasoning model (thinking mode) while the other runs the baseline model (standard instruction-following).

**Key Advantage**: Run all 4 experiments in parallel instead of sequentially, cutting total time in half.

## Model Specifications

### Pod 1: Reasoning Model
- **Model**: Qwen/Qwen3-4B-Thinking-2507
- **Size**: ~8GB (4B parameters in bfloat16)
- **VRAM Required**: ~12GB (with overhead and reasoning)
- **Context Length**: 32K tokens (configurable)
- **Special Features**: Reasoning mode enabled with DeepSeek-R1 parser

### Pod 2: Baseline Model
- **Model**: Qwen/Qwen3-4B-Instruct-2507
- **Size**: ~8GB (4B parameters in bfloat16)
- **VRAM Required**: ~10GB (with overhead)
- **Context Length**: 32K tokens (configurable)
- **Mode**: Standard instruction-following

## Why Two Pods?

### Parallel Execution Benefits
- ✅ Run reasoning and baseline experiments simultaneously
- ✅ Cut total experiment time by 50% (4 hours → 2 hours on A40, or 1.5 hours → 45 min on H100)
- ✅ No need to restart/reconfigure between experiments
- ✅ Both models always available for ad-hoc testing

### Cost Consideration
- **Two H100s**: $5.78/hour × 0.7-1.5 hours = **$4-9 total**
- **Two A40s**: $1.58/hour × 2-4 hours = **$3-6 total**
- **Savings**: Time is more valuable than $2-4 extra cost for research

## RunPod Setup

### Step 1: Create RunPod Account
1. Sign up at [runpod.io](https://runpod.io)
2. Add credits to your account (recommend $20+ for both pods)
3. Navigate to "Pods" section

### Step 2: Deploy Pod 1 - Reasoning Model

#### 2.1 Select GPU Configuration
- **⭐ RECOMMENDED**: H100 80GB (~$2.89/hour, fastest)
- **Budget**: A40 48GB (~$0.79/hour)
- **Budget**: RTX A6000 48GB (~$0.69/hour)

#### 2.2 Configure Pod Settings
1. Click "Deploy" → Select "GPU Cloud"
2. Choose your GPU (H100 recommended)
3. Select Template: **"vLLM OpenAI"** (vllm/vllm-openai:latest)

**Container Settings:**
```yaml
Container Disk: 50 GB (sufficient for Qwen3-4B)
Volume Disk: Optional (50 GB if you want persistence)
Volume Mount Path: /workspace (if using volume)
```

**Environment Variables (Optional):**
```bash
HF_HOME=/workspace/huggingface
```

#### 2.3 Container Start Command - Reasoning Pod

```bash
--host 0.0.0.0 --port 8000 --model Qwen/Qwen3-4B-Thinking-2507 --dtype bfloat16 --gpu-memory-utilization 0.9 --max-model-len 32768 --api-key sk-IrR7Bwxtin0haWagUnPrBgq5PurnUz86
```

**Breakdown:**
- `--model Qwen/Qwen3-4B-Thinking-2507` - Reasoning-capable model (has built-in thinking mode)
- `--dtype bfloat16` - Efficient precision for H100/A40
- `--gpu-memory-utilization 0.9` - Use 90% VRAM (safe for single model)
- `--max-model-len 32768` - 32K context (sufficient for code analysis)
- `--api-key sk-...` - Secure API key (change this!)

**Note**: The Qwen3-4B-Thinking model has **native reasoning capabilities**. No `--enable-reasoning` flag is needed - the model automatically generates thinking chains when appropriate. The `--enable-reasoning` and `--reasoning-parser` flags are only for vLLM >= 0.8.5 with specific model configurations, which this template doesn't support yet.

#### 2.4 Launch Reasoning Pod
1. Click "Deploy On-Demand" (or "Spot" for 50% savings)
2. Wait 3-5 minutes for model download and initialization
3. **Note the Pod ID and Endpoint**: e.g., `https://abc123xyz-8000.proxy.runpod.net`

### Step 3: Deploy Pod 2 - Baseline Model

#### 3.1 Repeat GPU Selection
- Use the **SAME GPU TYPE** as Pod 1 for fair comparison
- If H100 was used for Pod 1, use H100 for Pod 2

#### 3.2 Configure Pod Settings (Same as Pod 1)
```yaml
Container Disk: 50 GB
Volume Disk: Optional (50 GB)
Template: vLLM OpenAI (vllm/vllm-openai:latest)
```

#### 3.3 Container Start Command - Baseline Pod

```bash
--host 0.0.0.0 --port 8000 --model Qwen/Qwen3-4B-Instruct-2507 --dtype bfloat16 --gpu-memory-utilization 0.9 --max-model-len 32768 --api-key sk-IrR7Bwxtin0haWagUnPrBgq5PurnUz86
```

**Breakdown:**
- `--model Qwen/Qwen3-4B-Instruct-2507` - Standard instruction model
- **NO** `--enable-reasoning` flag (this is the key difference)
- Same context length and memory settings for fair comparison
- Different API key for easier tracking

#### 3.4 Launch Baseline Pod
1. Click "Deploy"
2. Wait 3-5 minutes for initialization
3. **Note the Pod ID and Endpoint**: e.g., `https://def456uvw-8000.proxy.runpod.net`

### Step 4: Verify Both Pods

Once both pods show "Running" status:

#### Test Reasoning Pod
```bash
# Replace with your actual Pod 1 URL
curl https://6ytsnx3b0q5ovg-8000.proxy.runpod.net/v1/models \
  -H "Authorization: Bearer sk-IrR7Bwxtin0haWagUnPrBgq5PurnUz86"

# Should return: Qwen/Qwen3-4B-Thinking-2507
```

#### Test Baseline Pod
```bash
# Replace with your actual Pod 2 URL
curl https://uk1hxoq950qqfb-8000.proxy.runpod.net/v1/models \
  -H "Authorization: Bearer sk-IrR7Bwxtin0haWagUnPrBgq5PurnUz86"

# Should return: Qwen/Qwen3-4B-Instruct-2507
```

## Local Environment Configuration

### Update .env File

Edit `/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/.env`:

```bash
# ========================================================================================
# RUNPOD DUAL-POD CONFIGURATION
# ========================================================================================

# Enable RunPod
USE_RUNPOD=true

# Pod 1: Reasoning Model (Thinking Mode)
REASONING_ENDPOINT=https://abc123xyz-8000.proxy.runpod.net/v1
REASONING_MODEL=Qwen/Qwen3-4B-Thinking-2507
REASONING_API_KEY=sk-reasoning-qwen-secure-key-2025

# Pod 2: Baseline Model (Standard Mode)
BASELINE_ENDPOINT=https://def456uvw-8000.proxy.runpod.net/v1
BASELINE_MODEL=Qwen/Qwen3-4B-Instruct-2507
BASELINE_API_KEY=sk-baseline-qwen-secure-key-2025

# Experiment toggle (script will change this automatically)
ENABLE_REASONING=false

# Use full dataset (not test subset)
# VULN_DATASET=/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/vuln_database/VulTrial_386_samples_balanced.jsonl
```

**Important**: Replace:
- `abc123xyz` with your actual Pod 1 ID
- `def456uvw` with your actual Pod 2 ID
- API keys with your generated secure keys

### Generate Secure API Keys (Optional)

```bash
# Generate random API keys
echo "sk-reasoning-$(openssl rand -hex 16)"
echo "sk-baseline-$(openssl rand -hex 16)"
```

Or use the same key for both:
```bash
echo "sk-qwen-$(openssl rand -hex 16)"
```

## Testing the Deployment

### Test Script (Automated)

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Test connection to both pods
bash scripts/test_runpod_connection.sh
```

Expected output:
```
✅ Models endpoint accessible
✅ Completion endpoint accessible
✅ AutoGen client connection successful!
✅ ALL TESTS PASSED
```

### Manual Testing

#### Test Reasoning Model
```bash
curl https://abc123xyz-8000.proxy.runpod.net/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-reasoning-qwen-secure-key-2025" \
  -d '{
    "model": "Qwen/Qwen3-4B-Thinking-2507",
    "messages": [{"role": "user", "content": "Is this code vulnerable? void func() { char buf[10]; gets(buf); }"}],
    "max_tokens": 200,
    "temperature": 0
  }'
```

Should return reasoning chain (thinking process) followed by answer.

#### Test Baseline Model
```bash
curl https://def456uvw-8000.proxy.runpod.net/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-baseline-qwen-secure-key-2025" \
  -d '{
    "model": "Qwen/Qwen3-4B-Instruct-2507",
    "messages": [{"role": "user", "content": "Is this code vulnerable? void func() { char buf[10]; gets(buf); }"}],
    "max_tokens": 200,
    "temperature": 0
  }'
```

Should return direct answer without reasoning chain.

## Running Parallel Experiments

### Method 1: Using Run Script (Sequential but Fast)

The existing script will automatically use the correct pod based on `ENABLE_REASONING`:

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Run all 4 experiments
bash scripts/run_rq1_vuln.sh
```

**Execution order:**
1. Reasoning + Zero-shot → Uses Pod 1 (thinking)
2. Baseline + Zero-shot → Uses Pod 2 (standard)
3. Reasoning + Few-shot → Uses Pod 1 (thinking)
4. Baseline + Few-shot → Uses Pod 2 (standard)

**Time**: 0.7-1.5 hours on H100, 2-4 hours on A40

### Method 2: True Parallel Execution (Advanced)

Run experiments in separate terminals simultaneously:

**Terminal 1 - Reasoning Experiments:**
```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Experiment 1: Reasoning + Zero-shot
export ENABLE_REASONING=true
python src/single_agent_vuln.py SA-zero &

# Experiment 3: Reasoning + Few-shot (run after Exp 1 completes)
# python src/single_agent_vuln.py SA-few
```

**Terminal 2 - Baseline Experiments:**
```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Experiment 2: Baseline + Zero-shot
export ENABLE_REASONING=false
python src/single_agent_vuln.py SA-zero &

# Experiment 4: Baseline + Few-shot (run after Exp 2 completes)
# python src/single_agent_vuln.py SA-few
```

**Time savings**: Cut experiment time in half (~30-45 min on H100)

### Monitor Progress

```bash
# Watch results in real-time
tail -f results/*_detailed_results.jsonl

# Check energy consumption
cat results/*_energy_tracking.json | jq '.total_emissions'

# Count completed samples
wc -l results/*_detailed_results.jsonl
```

## Cost Analysis

### H100 Dual-Pod (Recommended)
| Item | Rate | Quantity | Cost |
|------|------|----------|------|
| H100 Pod 1 (Reasoning) | $2.89/hour | 0.7-1.5 hours | $2.02-4.34 |
| H100 Pod 2 (Baseline) | $2.89/hour | 0.7-1.5 hours | $2.02-4.34 |
| Storage (both) | $0.10/GB/month | 100 GB × 1 day | $0.33 |
| **Total** | | | **$4.37-9.01** |

### A40 Dual-Pod (Budget)
| Item | Rate | Quantity | Cost |
|------|------|----------|------|
| A40 Pod 1 (Reasoning) | $0.79/hour | 2-4 hours | $1.58-3.16 |
| A40 Pod 2 (Baseline) | $0.79/hour | 2-4 hours | $1.58-3.16 |
| Storage (both) | $0.10/GB/month | 100 GB × 1 day | $0.33 |
| **Total** | | | **$3.49-6.65** |

### Value Proposition
- **Time savings vs single pod**: 50% faster (experiments run in parallel)
- **Cost increase vs single pod**: ~$2-4 extra
- **Trade-off**: Pay $2-4 to save 1-2 hours of your research time

## Context Length Optimization

### Recommended Settings by GPU

#### For H100 (80GB VRAM)
```bash
--max-model-len 65536   # 64K context (plenty of headroom)
--gpu-memory-utilization 0.9
```

#### For A40/A6000 (48GB VRAM)
```bash
--max-model-len 32768   # 32K context (balanced)
--gpu-memory-utilization 0.9
```

#### If Memory Issues Occur
```bash
--max-model-len 16384   # 16K context
--gpu-memory-utilization 0.85
```

### Context Requirements by Task
- **Vulnerability Detection**: 8K-16K (most code samples < 2K tokens)
- **Log Analysis**: 16K-32K (multiple log entries)
- **Code Generation**: 32K-64K (with context and examples)

Our experiments use **32K** as a safe default for all tasks.

## Troubleshooting

### Issue 1: Pod Fails to Start
**Error**: Model download timeout or disk quota exceeded

**Solution**:
```bash
# Increase container disk to 100 GB
# Or use volume disk for model persistence
```

### Issue 2: API Key Authentication Error
**Error**: `401 Unauthorized`

**Solution**:
```bash
# Verify API key matches in .env and RunPod start command
# Check Authorization header format: "Bearer sk-..."
```

### Issue 3: Reasoning Not Working
**Error**: Model returns direct answer without thinking

**Solution**:
```bash
# Qwen3-4B-Thinking has native reasoning - it activates automatically
# The model decides when to show thinking based on task complexity
# For explicit thinking, use prompts like: "Let's think step-by-step"
# Confirm using Qwen3-4B-Thinking-2507, not the Instruct variant

# If you still don't see reasoning, the model might determine it's not needed
# Test with a complex query to trigger thinking mode
```

### Issue 4: One Pod Works, Other Doesn't
**Solution**:
```bash
# Check both pods are running in RunPod console
# Verify different endpoints in .env
# Test each pod independently with curl
```

### Issue 5: Slow Inference
**Symptoms**: > 30 seconds per sample

**Solution**:
```bash
# Reduce context length: --max-model-len 16384
# Lower memory utilization: --gpu-memory-utilization 0.85
# Check GPU utilization with: nvidia-smi (via SSH)
```

### Issue 6: Out of Memory (OOM)
**Error**: CUDA out of memory

**Solution**:
```bash
# Reduce max-model-len:
--max-model-len 16384  # from 32768

# Or reduce memory utilization:
--gpu-memory-utilization 0.8  # from 0.9

# For extreme cases:
--max-model-len 8192
--gpu-memory-utilization 0.75
```

## Performance Expectations

### H100 Performance
- **Inference Speed**: 40-80 tokens/second
- **Time per Sample**: 5-15 seconds (avg ~10s)
- **Total Time (386 samples)**: 35-65 minutes per experiment
- **All 4 Experiments**: 0.7-1.5 hours

### A40 Performance
- **Inference Speed**: 15-30 tokens/second
- **Time per Sample**: 15-40 seconds (avg ~25s)
- **Total Time (386 samples)**: 90-160 minutes per experiment
- **All 4 Experiments**: 2-4 hours

### Reasoning Model vs Baseline
- **Reasoning**: Slightly slower (generates thinking chain)
- **Baseline**: Faster (direct answer)
- **Difference**: ~20-30% longer for reasoning

## Cleanup and Cost Management

### Stop Pods After Experiments

**Option 1: Stop (Pause)**
```bash
# In RunPod console:
1. Click "Stop" on each pod
2. Storage persists, billing paused
3. Can restart later without re-downloading models
```

**Option 2: Terminate (Delete)**
```bash
# In RunPod console:
1. Click "Terminate" on each pod
2. Complete removal, no further charges
3. Models must be re-downloaded if restarted
```

### Download Results First

```bash
# From local machine
scp -r /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results \
  ./results_backup_$(date +%Y%m%d)
```

### Verify Final Billing

1. Go to RunPod → Usage tab
2. Confirm GPU hours for each pod
3. Expected charges:
   - H100: $2-4 per pod = $4-9 total
   - A40: $1.50-3 per pod = $3-6 total

## Security Best Practices

### API Key Management
1. **Never commit API keys** to git
2. **Use different keys** for each pod (easier tracking)
3. **Rotate keys** after experiments
4. **Use strong random strings**: `openssl rand -hex 32`

### Network Security
- RunPod provides HTTPS by default ✅
- API endpoints are publicly accessible (but require API key)
- No sensitive data is stored on pods (models are public)

### Data Privacy
- Code samples sent to RunPod for inference
- **Recommendation**: Don't use proprietary/sensitive code
- Use VulTrial dataset (public CVEs) as designed

## Next Steps

1. ✅ Deploy both pods on RunPod
2. ✅ Update `.env` with both endpoints
3. ✅ Test connection with `test_runpod_connection.sh`
4. ✅ Run experiments with `run_rq1_vuln.sh`
5. ✅ Monitor progress in `results/` directory
6. ✅ Download results and stop/terminate pods
7. ✅ Analyze results (accuracy, energy, reasoning quality)

## Support Resources

- **RunPod Discord**: [discord.gg/runpod](https://discord.gg/runpod)
- **RunPod Docs**: [docs.runpod.io](https://docs.runpod.io)
- **vLLM GitHub**: [github.com/vllm-project/vllm](https://github.com/vllm-project/vllm)
- **Qwen Documentation**: [qwenlm.github.io](https://qwenlm.github.io)

## Summary Checklist

- [ ] Create RunPod account and add credits ($20+)
- [ ] Deploy Pod 1 (Reasoning) with H100/A40
- [ ] Set start command with Qwen3-4B-Thinking-2507 (native reasoning, no flags needed)
- [ ] Note Pod 1 endpoint URL
- [ ] Deploy Pod 2 (Baseline) with same GPU type
- [ ] Set start command without reasoning flags
- [ ] Note Pod 2 endpoint URL
- [ ] Update `.env` with both endpoints and API keys
- [ ] Test both pods with `test_runpod_connection.sh`
- [ ] Run experiments with `run_rq1_vuln.sh`
- [ ] Monitor progress and download results
- [ ] Stop/terminate pods to avoid extra charges
- [ ] Analyze results and prepare findings

**Total Time**: 10 min setup + 0.7-4 hours experiments = **1-4.5 hours**
**Total Cost**: **$4-9 (H100)** or **$3-6 (A40)**

---

*Last Updated: January 2025*
