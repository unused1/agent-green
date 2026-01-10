# RunPod Pods Information

## Pod 1: Thinking Model (Reasoning)

**Model**: `Qwen/Qwen3-4B-Thinking-2507`

**API Endpoint**: `https://6ytsnx3b0q5ovg-8000.proxy.runpod.net/v1`

**SSH Access**:
- **IP**: `213.181.122.135`
- **Port**: `19442`
- **SSH Command**: `ssh root@213.181.122.135 -p 19442 -i ~/.ssh/runpod_ed25519`

**Upload Files**:
```bash
bash scripts/upload_to_runpod.sh 213.181.122.135 19442 thinking
```

**Download Results**:
```bash
bash scripts/download_from_runpod.sh 213.181.122.135 19442 thinking
```

---

## Pod 2: Instruct Model (Baseline)

**Model**: `Qwen/Qwen3-4B-Instruct-2507`

**API Endpoint**: `https://obkrbyez1dj50o-8000.proxy.runpod.net/v1`

**SSH Access**:
- **IP**: `63.141.33.80`
- **Port**: `22096`
- **SSH Command**: `ssh root@63.141.33.80 -p 22096 -i ~/.ssh/runpod_ed25519`

**Upload Files**:
```bash
bash scripts/upload_to_runpod.sh 63.141.33.80 22096 instruct
```

**Download Results**:
```bash
bash scripts/download_from_runpod.sh 63.141.33.80 22096 instruct
```

---

## Quick Commands

### Upload to Both Pods
```bash
# Upload to thinking pod
bash scripts/upload_to_runpod.sh 213.181.122.135 19442 thinking

# Upload to instruct pod
bash scripts/upload_to_runpod.sh 63.141.33.80 22096 instruct
```

### Setup Both Pods
```bash
# SSH into thinking pod
ssh root@213.181.122.135 -p 19442 -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh
exit

# SSH into instruct pod
ssh root@63.141.33.80 -p 22096 -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh
exit
```

### Run Experiments
```bash
# On thinking pod
bash scripts/run_rq1_vuln_runpod.sh reasoning all full

# On instruct pod
bash scripts/run_rq1_vuln_runpod.sh baseline all full
```

### Download Results
```bash
# From thinking pod
bash scripts/download_from_runpod.sh 213.181.122.135 19442 thinking

# From instruct pod
bash scripts/download_from_runpod.sh 63.141.33.80 22096 instruct
```

---

## API Keys

Both pods use the same API key: `sk-IrR7Bwxtin0haWagUnPrBgq5PurnUz86`

---

## Notes

- **API calls from local machine**: Use endpoint URLs above
- **Experiments on pods**: Use `http://localhost:8000/v1` (local vLLM)
- **SSH key**: `~/.ssh/runpod_ed25519`
- **Remember to stop pods** after experiments to avoid charges!
