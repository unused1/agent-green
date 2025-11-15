# RQ2 Monitoring and Troubleshooting Guide

Quick reference for monitoring parallel pod execution and resolving common issues.

---

## Table of Contents
1. [Quick Status Checks](#quick-status-checks)
2. [Detailed Monitoring](#detailed-monitoring)
3. [Common Issues & Fixes](#common-issues--fixes)
4. [Emergency Procedures](#emergency-procedures)
5. [Cost Tracking](#cost-tracking)

---

## Quick Status Checks

### Check All Pods at Once (Local Machine)

```bash
#!/bin/bash
# Quick check of all pods
# Replace POD_INFO with your actual IP:PORT values

PODS=(
    "POD1_IP:POD1_PORT"
    "POD2_IP:POD2_PORT"
    "POD3_IP:POD3_PORT"
    "POD4_IP:POD4_PORT"
    "POD5_IP:POD5_PORT"
    "POD6_IP:POD6_PORT"
    "POD7_IP:POD7_PORT"
    "POD8_IP:POD8_PORT"
)

for i in "${!PODS[@]}"; do
    IFS=':' read -r ip port <<< "${PODS[$i]}"
    pod_num=$((i+1))

    echo "=== Pod $pod_num ($ip:$port) ==="

    # Check if pod is reachable
    ssh -o ConnectTimeout=5 root@$ip -p $port -i ~/.ssh/runpod_ed25519 \
        "echo 'Connected'" 2>/dev/null || echo "  ⚠️ Connection failed"

    # Check running processes
    ssh -o ConnectTimeout=5 root@$ip -p $port -i ~/.ssh/runpod_ed25519 \
        "ps aux | grep -c 'python src/' || echo '0'" 2>/dev/null | \
        xargs -I {} echo "  Python processes running: {}"

    # Check last log line
    ssh -o ConnectTimeout=5 root@$ip -p $port -i ~/.ssh/runpod_ed25519 \
        "tail -1 /workspace/agent-green/pod${pod_num}_full_run.log 2>/dev/null" 2>/dev/null || \
        echo "  No log file yet"

    echo ""
done
```

**Save as**: `scripts/quick_check_all_pods.sh`

**Run**: `bash scripts/quick_check_all_pods.sh`

---

## Detailed Monitoring

### 1. Monitor Sample Progress on Single Pod

**SSH into pod**, then run:

```bash
cd /workspace/agent-green

# Show current experiment progress
tail -20 pod*_full_run.log

# Count completed samples per experiment
echo "=== Sample Counts ==="
for file in results/*_detailed_results.jsonl; do
    if [ -f "$file" ]; then
        count=$(wc -l < "$file")
        echo "$(basename $file): $count samples"
    fi
done

# Show most recent sample timestamp
echo ""
echo "=== Most Recent Activity ==="
find results -name "*_detailed_results.jsonl" -exec tail -1 {} \; | \
    grep -o '"timestamp":"[^"]*"' | tail -5

# Estimate time remaining
echo ""
echo "=== Time Estimates ==="
echo "Dual-agent: ~60-90 min per experiment"
echo "Multi-agent: ~120-180 min per experiment"
echo "Check timestamps to estimate completion"
```

### 2. Monitor GPU and Memory Usage

```bash
# GPU utilization
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv

# Watch GPU in real-time
watch -n 10 nvidia-smi

# System memory
free -h

# Disk usage
df -h | grep workspace
```

### 3. Monitor Energy Consumption

```bash
# View current energy tracking
cat results/*_energy_tracking.json | python -m json.tool

# Summary of energy across experiments
grep -h "total_emissions" results/*_energy_tracking.json | sort
```

### 4. Real-Time Log Monitoring

```bash
# Watch experiment log in real-time
tail -f pod*_full_run.log

# Filter for important events
tail -f pod*_full_run.log | grep -E "(Starting|Completed|ERROR|WARNING)"

# Multi-file log monitoring
tail -f results/*.log pod*_full_run.log
```

---

## Common Issues & Fixes

### Issue 1: Experiment Not Starting

**Symptoms**:
- No log output
- No Python process running
- `ps aux | grep python` returns nothing

**Diagnosis**:
```bash
# Check if script exists
ls -lh src/dual_agent_vuln.py

# Check for syntax errors
python -m py_compile src/dual_agent_vuln.py

# Check environment variables
echo $ENABLE_REASONING

# Check dataset exists
ls -lh vuln_database/*.jsonl
```

**Fix**:
```bash
# Re-run setup
cd /workspace/agent-green
bash scripts/setup_runpod_env.sh

# Manually start experiment with verbose output
python src/dual_agent_vuln.py --prompt_type zero_shot 2>&1 | tee manual_run.log
```

---

### Issue 2: Out of Memory (OOM)

**Symptoms**:
- Process killed suddenly
- `nvidia-smi` shows 100% memory
- Log shows "CUDA out of memory"

**Diagnosis**:
```bash
# Check GPU memory
nvidia-smi

# Check system memory
free -h

# Check for memory leaks
ps aux --sort=-%mem | head -10
```

**Fix**:
```bash
# Kill stuck processes
pkill -9 -f "python src/"

# Restart vLLM with lower context window (if using custom deployment)
# Or switch to smaller batch size in config

# Resume experiment (will skip completed samples)
python src/dual_agent_vuln.py --prompt_type zero_shot
```

---

### Issue 3: Experiment Stuck/Hanging

**Symptoms**:
- No new samples processed for > 30 minutes
- Log shows same timestamp repeatedly
- Process running but no progress

**Diagnosis**:
```bash
# Check last processed sample
tail -20 results/*_detailed_results.jsonl

# Check if process is actually running
ps aux | grep python

# Check system load
top

# Check network connectivity to API
curl -I http://localhost:8000/v1/models
```

**Fix**:
```bash
# Get process ID
ps aux | grep "python src/" | grep -v grep

# Kill gracefully
pkill -f "python src/dual_agent_vuln.py"

# Wait 10 seconds, then force kill if needed
pkill -9 -f "python src/dual_agent_vuln.py"

# Resume experiment (will use resume functionality)
python src/dual_agent_vuln.py --prompt_type zero_shot
```

---

### Issue 4: Resume Not Working

**Symptoms**:
- Experiment restarts from sample 0
- Existing results not detected
- Resume prompt not shown

**Diagnosis**:
```bash
# Check if result files exist
ls -lh results/*_detailed_results.jsonl

# Check file permissions
ls -la results/

# Check if results are valid JSON
tail -1 results/*_detailed_results.jsonl | python -m json.tool
```

**Fix**:
```bash
# Verify result file format
head -5 results/*_detailed_results.jsonl

# If corrupted, remove last line and retry
# Backup first!
cp results/DA-vuln-*_detailed_results.jsonl results/backup.jsonl
head -n -1 results/backup.jsonl > results/DA-vuln-*_detailed_results.jsonl

# Resume
python src/dual_agent_vuln.py --prompt_type zero_shot
```

---

### Issue 5: SSH Connection Lost

**Symptoms**:
- Can't SSH into pod
- "Connection refused" or "Connection timeout"
- Pod appears offline

**Diagnosis**:
```bash
# Check pod status in RunPod console
# Visit: https://runpod.io/console/pods

# Test connection
ping <POD_IP>
nc -zv <POD_IP> <POD_PORT>
```

**Fix**:
1. Check RunPod console - pod may be terminated or suspended
2. If pod is running but SSH fails, try restarting pod
3. If critical: download partial results using RunPod web terminal
4. Redeploy pod if necessary

**Recover Partial Results**:
```bash
# If SSH down but pod running, use RunPod web terminal
cd /workspace/agent-green
tar -czf results_backup.tar.gz results/

# Then download via RunPod console File Manager
```

---

### Issue 6: vLLM API Not Responding

**Symptoms**:
- Experiments hang waiting for API response
- Long timeouts
- No output from model

**Diagnosis**:
```bash
# Check vLLM service status
curl http://localhost:8000/v1/models

# Check vLLM logs
docker logs <vllm_container_name> --tail 50

# Check if port 8000 is listening
netstat -tuln | grep 8000
```

**Fix**:
```bash
# Restart vLLM container (if using Docker)
docker restart <vllm_container_name>

# Or restart vLLM service
sudo systemctl restart vllm  # if using systemd

# Wait 30 seconds for model to reload
sleep 30

# Test API again
curl http://localhost:8000/v1/models

# Resume experiment
python src/dual_agent_vuln.py --prompt_type zero_shot
```

---

## Emergency Procedures

### Emergency Stop All Experiments

**On each pod via SSH**:
```bash
# Graceful stop
pkill -f "python src/"

# Force stop (if graceful fails after 30 seconds)
pkill -9 -f "python src/"

# Verify stopped
ps aux | grep python
```

### Emergency Download Partial Results

**On local machine** (even if experiments not complete):
```bash
# Download whatever results exist
bash scripts/download_from_runpod.sh <POD_IP> <POD_PORT> emergency_backup

# Or manual download
scp -r -P <POD_PORT> -i ~/.ssh/runpod_ed25519 \
    root@<POD_IP>:/workspace/agent-green/results \
    ./emergency_backup/
```

### Resume After Emergency Stop

**After resolving issue**, resume on each pod:
```bash
cd /workspace/agent-green

# The scripts will automatically detect existing results and resume
# Choose option 1 (Resume) when prompted

python src/dual_agent_vuln.py --prompt_type zero_shot
# ... continue with remaining experiments
```

---

## Cost Tracking

### Monitor RunPod Spending

**Check current spend**:
1. Go to https://runpod.io/console/user/billing
2. View "Current Cycle Usage"
3. Check cost per pod

**Estimate total cost**:
```
Per Pod Cost = Hours Running × $2.49/hr (spot) or $2.89/hr (on-demand)

8 Pods × 5 Hours × $2.49/hr = ~$100
```

**Set Budget Alert**:
1. Go to RunPod Billing settings
2. Set budget alert at $120 (gives 20% buffer)
3. Get email notification when approaching limit

### Track Experiment Time

**On each pod**, check elapsed time:
```bash
# Check when experiment started
head -5 pod*_full_run.log | grep "STARTING"

# Check current time
date

# Calculate elapsed time
# Manual calculation or use script
```

**Estimate completion**:
```bash
# Count completed samples
completed=$(wc -l results/*_detailed_results.jsonl | tail -1 | awk '{print $1}')

# Calculate percentage
total=386  # or 164 for code generation
percent=$(echo "scale=2; $completed / $total * 100" | bc)

echo "Progress: $percent% ($completed/$total samples)"

# Estimate time remaining (rough)
if [ $completed -gt 0 ]; then
    # Assuming constant sample rate
    echo "Check timestamp of first and last sample to calculate rate"
fi
```

---

## Useful One-Liners

### Count All Completed Samples Across Pods

```bash
for i in {1..8}; do
    ssh root@<POD${i}_IP> -p <POD${i}_PORT> -i ~/.ssh/runpod_ed25519 \
        "cd /workspace/agent-green && wc -l results/*_detailed_results.jsonl 2>/dev/null" | \
        awk '{sum+=$1} END {print "Pod '$i': " sum " samples"}'
done
```

### Check If All Experiments Complete

```bash
# On each pod
cd /workspace/agent-green
grep -c "COMPLETE" pod*_full_run.log
# Should be 1 if finished
```

### Get Summary Statistics

```bash
# On each pod
cd /workspace/agent-green

echo "=== Experiment Summary ==="
echo "Dual-agent experiments:"
ls results/DA-* 2>/dev/null | wc -l

echo "Multi-agent experiments:"
ls results/MA-* 2>/dev/null | wc -l

echo "Total samples processed:"
cat results/*_detailed_results.jsonl 2>/dev/null | wc -l

echo "Total energy consumed:"
grep "total_emissions" results/*_energy_tracking.json 2>/dev/null
```

---

## Debugging Checklist

Before asking for help or restarting, verify:

- [ ] Pod is running (check RunPod console)
- [ ] SSH connection works
- [ ] Python environment is setup (`python --version`)
- [ ] Datasets exist (`ls vuln_database/*.jsonl`)
- [ ] Config file is correct (`cat src/config.py | grep DATASET`)
- [ ] vLLM API is responding (`curl http://localhost:8000/v1/models`)
- [ ] Sufficient disk space (`df -h`)
- [ ] Sufficient GPU memory (`nvidia-smi`)
- [ ] No zombie processes (`ps aux | grep defunct`)
- [ ] Correct ENABLE_REASONING value (`echo $ENABLE_REASONING`)

---

## Support Resources

**Documentation**:
- Test Run: `RQ2_Test_Run_Commands.md`
- Full Run: `RQ2_Full_Run_Commands.md`
- RunPod Setup: `RunPod_Setup_Guide.md`
- Mars Workflow: `mars_docker_workflow.md`

**RunPod Support**:
- Discord: https://discord.gg/runpod
- Docs: https://docs.runpod.io/

**AutoGen Issues**:
- GitHub: https://github.com/microsoft/autogen/issues
- Docs: https://microsoft.github.io/autogen/
