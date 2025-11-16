# RQ2 Experiment Tracking - Live Session

**Session Date**: November 16, 2025
**Objective**: Run RQ2 experiments across multiple RunPod H100 pods

---

## Pod Configuration

| Pod | IP | SSH Port | Model | Size | vLLM Status | Experiments to Run |
|-----|-----|----------|-------|------|-------------|-------------------|
| **1** | 157.66.254.40 | 14555 | Qwen3-4B-Instruct | 4B | ✅ Running | DA-vuln-zero, DA-code-zero, MA-vuln-zero, MA-code-zero |
| **2** | 205.196.17.138 | 12500 | Qwen3-4B-Thinking | 4B | ✅ Running | DA-vuln-zero, DA-code-zero, MA-vuln-zero, MA-code-zero |
| **3** | 205.196.17.99 | 9700 | Qwen3-4B-Instruct | 4B | ✅ Running | DA-vuln-few, DA-code-few, MA-vuln-few, MA-code-few |
| **4** | 205.196.17.123 | 11670 | Qwen3-4B-Thinking | 4B | ✅ Running | DA-vuln-few, DA-code-few, MA-vuln-few, MA-code-few |
| **5** | 205.196.17.139 | 9294 | Qwen3-30B-A3B-Instruct | 30B | ✅ Running | DA-vuln-zero, DA-code-zero, MA-vuln-zero, MA-code-zero |
| **6** | 63.141.33.85 | 22145 | Qwen3-30B-A3B-Thinking | 30B | ✅ Running | DA-vuln-zero, DA-code-zero, MA-vuln-zero, MA-code-zero |
| **7** | 205.196.17.131 | 10944 | Qwen3-30B-A3B-Instruct | 30B | ✅ Running | DA-vuln-few, DA-code-few, MA-vuln-few, MA-code-few |
| **8** | 213.181.122.251 | 15454 | Qwen3-30B-A3B-Thinking | 30B | ✅ Running | DA-vuln-few, DA-code-few, MA-vuln-few, MA-code-few |

---

## Experiment Status

### Pod 1 (4B-Instruct, Zero-Shot) - 157.66.254.40:14555

| # | Experiment | Type | Samples | Status | Start Time | Duration | Notes |
|---|------------|------|---------|--------|------------|----------|-------|
| 1 | DA-vuln-zero | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~1.5h | ENABLE_REASONING=false |
| 2 | DA-code-zero | Code Gen | 164 | ✅ Complete | Nov 16 | ~30min | 163/164 successful (99.4%) |
| 3 | MA-vuln-zero | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~1.5h | 3 samples skipped (context overflow) |
| 4 | MA-code-zero | Code Gen | 164 | ✅ Complete | Nov 16 | ~30min | 4B Instruct, Zero-Shot ✨ |

**Status**: 🎉 **ALL 4/4 EXPERIMENTS COMPLETE** - Results downloaded, pod stopped (ready to terminate)

**Results**: ✅ Downloaded to `results/runpod_rq2_pod1_results.zip` (3.7MB, 25 files)

### Pod 2 (4B-Thinking, Zero-Shot) - 205.196.17.138:12500

| # | Experiment | Type | Samples | Status | Start Time | Duration | Notes |
|---|------------|------|---------|--------|------------|----------|-------|
| 1 | DA-vuln-zero | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~1.5h | ENABLE_REASONING=true, 4B Thinking |
| 2 | DA-code-zero | Code Gen | 164 | ✅ Complete | Nov 16 | ~30min | ENABLE_REASONING=true, 4B Thinking |
| 3 | MA-vuln-zero | Vuln Detection | 386 | 🏃 Running | Nov 16 | ~1.5h est | ENABLE_REASONING=true, 4B Thinking |
| 4 | MA-code-zero | Code Gen | 164 | ⏳ Pending | - | ~30min est | After exp 3 |

**Commands for Pod 2:**
```bash
ssh root@205.196.17.138 -p 12500 -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green
export ENABLE_REASONING=true
export OPENAI_API_KEY='dummy-key-for-vllm'

# Currently running experiment 3/4:
python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot

# Next command (run after previous completes):
python src/multi_agent_code_generation.py --prompt_type zero_shot
```

### Pod 3 (4B-Instruct, Few-Shot) - 205.196.17.99:9700

| # | Experiment | Type | Samples | Status | Start Time | Duration | Notes |
|---|------------|------|---------|--------|------------|----------|-------|
| 1 | DA-vuln-few | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~1.5h | ENABLE_REASONING=false |
| 2 | DA-code-few | Code Gen | 164 | ✅ Complete | Nov 16 | ~30min | 163/164 successful (99.4%), Pass@1: 1.0000 |
| 3 | MA-vuln-few | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~1.5h | Completed successfully |
| 4 | MA-code-few | Code Gen | 164 | ✅ Complete | Nov 16 | ~30min | 163/164 successful (99.4%), Pass@1: 1.0000 ✨ |

**Commands for Pod 3:**
```bash
ssh root@205.196.17.99 -p 9700 -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green
export ENABLE_REASONING=false
export OPENAI_API_KEY='dummy-key-for-vllm'

# Currently running:
python src/multi_agent_code_generation.py --prompt_type few_shot
```

### Pod 4 (4B-Thinking, Few-Shot) - 205.196.17.123:11670

| # | Experiment | Type | Samples | Status | Start Time | Duration | Notes |
|---|------------|------|---------|--------|------------|----------|-------|
| 1 | DA-vuln-few | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~1.5h | ENABLE_REASONING=true |
| 2 | DA-code-few | Code Gen | 164 | ✅ Complete | Nov 16 | ~30min | ENABLE_REASONING=true, 4B Thinking |
| 3 | MA-vuln-few | Vuln Detection | 386 | 🏃 Running | Nov 16 | ~1.5h est | Context overflow on sample 8 (idx: 344242) - skipping |
| 4 | MA-code-few | Code Gen | 164 | ⏳ Pending | - | ~30min est | After exp 3 |

**Commands for Pod 4:**
```bash
ssh root@205.196.17.123 -p 11670 -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green
export ENABLE_REASONING=true
export OPENAI_API_KEY='dummy-key-for-vllm'

# Currently running experiment 3/4:
python src/multi_agent_vuln_detection_four_agents.py --prompt_type few_shot

# Next command (run after previous completes):
python src/multi_agent_code_generation.py --prompt_type few_shot
```

### Pod 5 (30B-A3B-Instruct, Zero-Shot) - 205.196.17.139:9294

| # | Experiment | Type | Samples | Status | Start Time | Duration | Notes |
|---|------------|------|---------|--------|------------|----------|-------|
| 1 | DA-vuln-zero | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~2-3h | ENABLE_REASONING=false, 30B model |
| 2 | DA-code-zero | Code Gen | 164 | ✅ Complete | Nov 16 | ~45min | 30B Instruct model |
| 3 | MA-vuln-zero | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~2-3h | ENABLE_REASONING=false, 30B Instruct |
| 4 | MA-code-zero | Code Gen | 164 | ✅ Complete | Nov 16 | ~45min | 30B Instruct, Zero-Shot ✨ |

**Status**: 🎉 **ALL 4/4 EXPERIMENTS COMPLETE** - Results downloaded, pod stopped (ready to terminate)

**Results**: ✅ Downloaded to `results/runpod_rq2_pod5/` (21MB, 28 files)
- DA-vuln-zero: 387 samples
- DA-code-zero: 164 samples
- MA-vuln-zero: 386 samples
- MA-code-zero: 164 samples

### Pod 6 (30B-A3B-Thinking, Zero-Shot) - 63.141.33.85:22145

| # | Experiment | Type | Samples | Status | Start Time | Duration | Notes |
|---|------------|------|---------|--------|------------|----------|-------|
| 1 | DA-vuln-zero | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~2-3h | ENABLE_REASONING=true, 30B Thinking, 32768 context |
| 2 | DA-code-zero | Code Gen | 164 | ✅ Complete | Nov 16 | ~45min | 1 context overflow (65594 tokens), evaluation completed |
| 3 | MA-vuln-zero | Vuln Detection | 386 | 🏃 Running | Nov 16 | ~2-3h est | ENABLE_REASONING=true, 30B Thinking |
| 4 | MA-code-zero | Code Gen | 164 | ⏳ Pending | - | ~45min est | After exp 3 |

**Commands for Pod 6:**
```bash
ssh root@63.141.33.85 -p 22145 -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green
export ENABLE_REASONING=true
export OPENAI_API_KEY='dummy-key-for-vllm'

# Currently running experiment 3/4:
python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot

# Next command (run after previous completes):
python src/multi_agent_code_generation.py --prompt_type zero_shot
```

### Pod 7 (30B-A3B-Instruct, Few-Shot) - 205.196.17.131:10944

| # | Experiment | Type | Samples | Status | Start Time | Duration | Notes |
|---|------------|------|---------|--------|------------|----------|-------|
| 1 | DA-vuln-few | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~2-3h | ENABLE_REASONING=false, 30B Instruct |
| 2 | DA-code-few | Code Gen | 164 | ✅ Complete | Nov 16 | ~45min | ENABLE_REASONING=false, 30B Instruct |
| 3 | MA-vuln-few | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~2-3h | ENABLE_REASONING=false, 30B Instruct |
| 4 | MA-code-few | Code Gen | 164 | ✅ Complete | Nov 16 | ~45min | 30B Instruct, Few-Shot ✨ |

**Status**: 🎉 **ALL 4/4 EXPERIMENTS COMPLETE** - Results downloaded, pod stopped (ready to terminate)

**Results**: ✅ Downloaded to `results/runpod_rq2_pod7/` (28 files)

### Pod 8 (30B-A3B-Thinking, Few-Shot) - 213.181.122.251:15454

| # | Experiment | Type | Samples | Status | Start Time | Duration | Notes |
|---|------------|------|---------|--------|------------|----------|-------|
| 1 | DA-vuln-few | Vuln Detection | 386 | ✅ Complete | Nov 16 | ~2-3h | ENABLE_REASONING=true, 30B Thinking, 32768 context |
| 2 | DA-code-few | Code Gen | 164 | ✅ Complete | Nov 16 | ~45min | Pass@1: 0.6890 |
| 3 | MA-vuln-few | Vuln Detection | 386 | 🏃 Running | Nov 16 | ~2-3h est | ENABLE_REASONING=true, 30B Thinking |
| 4 | MA-code-few | Code Gen | 164 | ⏳ Pending | - | ~45min est | After exp 3 |

**Commands for Pod 8:**
```bash
ssh root@213.181.122.251 -p 15454 -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green
export ENABLE_REASONING=true
export OPENAI_API_KEY='dummy-key-for-vllm'

# ✅ vLLM reconfigured: --max-model-len 65536, --gpu-memory-utilization 0.9

# Currently running experiment 3/4:
python src/multi_agent_vuln_detection_four_agents.py --prompt_type few_shot

# Next command (run after previous completes):
python src/multi_agent_code_generation.py --prompt_type few_shot
```

---

## Quick SSH Access

```bash
# Pod 1 (4B-Instruct, Zero-Shot)
ssh root@157.66.254.40 -p 14555 -i ~/.ssh/runpod_ed25519

# Pod 2 (4B-Thinking, Zero-Shot)
ssh root@205.196.17.138 -p 12500 -i ~/.ssh/runpod_ed25519

# Pod 3 (4B-Instruct, Few-Shot)
ssh root@205.196.17.99 -p 9700 -i ~/.ssh/runpod_ed25519

# Pod 4 (4B-Thinking, Few-Shot)
ssh root@205.196.17.123 -p 11670 -i ~/.ssh/runpod_ed25519

# Pod 5 (30B-A3B-Instruct, Zero-Shot)
ssh root@205.196.17.139 -p 9294 -i ~/.ssh/runpod_ed25519

# Pod 6 (30B-A3B-Thinking, Zero-Shot)
ssh root@63.141.33.85 -p 22145 -i ~/.ssh/runpod_ed25519

# Pod 7 (30B-A3B-Instruct, Few-Shot)
ssh root@205.196.17.131 -p 10944 -i ~/.ssh/runpod_ed25519

# Pod 8 (30B-A3B-Thinking, Few-Shot)
ssh root@213.181.122.251 -p 15454 -i ~/.ssh/runpod_ed25519
```

---

## Troubleshooting

### Context Overflow Recovery (Multi-Agent Experiments)

If an experiment crashes with context length error (65,536 token limit):

**Step 1**: Re-run the experiment script
```bash
# Example for Pod 1
ssh root@157.66.254.40 -p 14555 -i ~/.ssh/runpod_ed25519
cd /workspace/agent-green
export ENABLE_REASONING=false
export OPENAI_API_KEY='dummy-key-for-vllm'

python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot
```

**Step 2**: When prompted with resume options, select **option 2**:
```
[FOUND] Existing experiment: MA-vuln-zero_shot_Qwen-Qwen3-4B-Instruct-2507_20251116-XXXXXX
Options:
  1. Resume from last completed sample (continue normally)
  2. Skip the next sample and mark as failed (if it's problematic)  ← SELECT THIS
  3. Start a fresh new experiment

Enter choice (1/2/3): 2
```

**Step 3**: Script will:
- Mark the problematic sample as FAILED
- Add reasoning: "SKIPPED - Sample marked as problematic by user"
- Continue from the next sample

**Affected Samples**:
- Pod 1: Sample 68/383 (idx: 389760) - Integer overflow with endless "999..." output
- Pod 1: Sample 85/312 (idx: 413623) - Integer overflow with endless "000..." output
- Pod 1: Sample 161/227 (idx: 197973) - Integer overflow with endless "999..." output (LISTEN_FDS parsing)
- Pod 2: Sample 59/386 (idx: 252437) - Endless "000..." in attack example (vector size overflow, 65,544 tokens)
- Pod 2: Sample 33/325 (idx: 427707) - Repetitive arithmetic overflow calculation (SIZE_MAX wrapping)
- Pod 2: Sample 36/292 (idx: 391628) - Repetitive vulnerability enumeration (BMP file handling)
- Pod 2: Sample 8/234 (idx: 351182) - Endless "000..." in index overflow demonstration (int64_t bounds)
- Pod 2: Sample 6/225 (idx: 440872) - Repetitive "no obvious vulnerabilities" loop (ccline.cmdbuff analysis)
- Pod 4: Sample 8/386 (idx: 344242) - Endless "luaC_checkGC(L);" output (Lua memory management)
- Pod 4: Sample 7/378 (idx: 450812) - Overly verbose analysis of glob function (brace expansion vulnerability)
- Pod 4: Sample 1/370 (idx: 259619) - Repetitive STRCAT buffer overflow analysis (66,426 tokens)
- Pod 4: Sample 131/365 (idx: 439266) - Repetitive vulnerability searching (BMP file size validation)
- Pod 4: Sample 3/234 (idx: 328807) - Repetitive "no vulnerabilities" loop (y_array null pointer analysis)
- Pod 8: Sample 40/386 (idx: 447053) - Repetitive overflow calculation (TIFF count * size arithmetic)

---

## Monitoring Commands

### Check experiment progress:
```bash
# See latest results
tail -f /workspace/agent-green/results/*_detailed_results.jsonl

# Count completed samples
grep "Completed:" /workspace/agent-green/results/*_detailed_results.jsonl | wc -l

# Check for errors
grep -i "error" /workspace/vllm_*.log
```

### Check vLLM server:
```bash
curl http://localhost:8000/v1/models | python -m json.tool
```

### Monitor GPU usage:
```bash
nvidia-smi
watch -n 1 nvidia-smi
```

---

## Results Download Commands

After experiments complete, download results from local machine:

```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green

# Pod 1 (Zero-Shot Instruct)
scp -P 14555 -i ~/.ssh/runpod_ed25519 -r root@157.66.254.40:/workspace/agent-green/results ./results_pod1

# Pod 2 (Zero-Shot Thinking)
scp -P 12500 -i ~/.ssh/runpod_ed25519 -r root@205.196.17.138:/workspace/agent-green/results ./results_pod2

# Pod 3 (Few-Shot Instruct)
scp -P 9700 -i ~/.ssh/runpod_ed25519 -r root@205.196.17.99:/workspace/agent-green/results ./results_pod3

# Pod 4 (Few-Shot Thinking)
scp -P 11670 -i ~/.ssh/runpod_ed25519 -r root@205.196.17.123:/workspace/agent-green/results ./results_pod4

# Pod 5 (Zero-Shot 30B Instruct)
scp -P 9294 -i ~/.ssh/runpod_ed25519 -r root@205.196.17.139:/workspace/agent-green/results ./results_pod5

# Pod 6 (Zero-Shot 30B Thinking)
scp -P 22145 -i ~/.ssh/runpod_ed25519 -r root@63.141.33.85:/workspace/agent-green/results ./results_pod6

# Pod 7 (Few-Shot 30B Instruct)
scp -P 10944 -i ~/.ssh/runpod_ed25519 -r root@205.196.17.131:/workspace/agent-green/results ./results_pod7

# Pod 8 (Few-Shot 30B Thinking)
scp -P 15454 -i ~/.ssh/runpod_ed25519 -r root@213.181.122.251:/workspace/agent-green/results ./results_pod8
```

---

## Notes & Issues

### Session Notes:
- All 4 pods deployed and running experiments in parallel
- **Pod 1**: Running MA-vuln-zero (resumed from sample 3/386)
- **Pod 2**: Running DA-vuln-zero
- **Pod 3**: Running MA-vuln-few (just started)
- **Pod 4**: Running DA-vuln-few
- All vLLM compatibility fixes applied (api_base→base_url, model name sanitization with "/" handling)
- Using max-model-len 65536 for all models
- **Progress**: 6/16 experiments complete (37.5%) on 4B models
- **Pod 5**: 30B-A3B-Instruct model downloading/starting

### Known Issues:

#### 1. Setup Script Model Configuration
- ⚠️ Setup script sets Instruct model by default - need to manually switch to Thinking model for Thinking pods
- **Fix**: Update config.py to uncomment/comment the correct LLM_MODEL line for each pod

#### 2. vLLM Context Length Misconfiguration (Critical - Experimental Validity)
- ⚠️ **Issue**: 30B models (Pods 5-8) were configured with `--max-model-len 32768` instead of 65536
- **Impact**:
  - **Pod 5** (30B-Instruct, Zero-Shot): 0 failures (zero-shot requires fewer tokens)
  - **Pod 7** (30B-Instruct, Few-Shot): **6 failures** in DA-vuln-few due to 32,768 token limit
  - **Pod 6** (30B-Thinking, Zero-Shot): Still running with 32,768 (DA-vuln-zero)
  - **Pod 8** (30B-Thinking, Few-Shot): Still running with 32,768 (DA-vuln-few) - **high risk**
- **Inconsistency**: 4B models (Pods 1-4) had 65,536 tokens vs 30B models had 32,768 tokens
- **Root Cause**: Configuration error during setup; should have been consistent across all pods
- **Resolution Plan**:
  - Accept limitations for completed experiments (Pods 5, 7)
  - **For Pods 6 & 8**: After current experiment completes, restart vLLM with `--max-model-len 65536` before next experiment
  - Document as experimental limitation in research paper
- **Experimental Impact**: Few-shot experiments on 30B models are compromised due to insufficient context for examples

#### 3. Multi-Agent Context Overflow (Critical)
- ⚠️ **Issue**: Multi-agent experiments can hit context length limits on certain samples
- **Observed on**: Pod 1, MA-vuln-zero, Sample 68/383 (idx: 389760)
- **Symptoms**:
  - Security researcher agent generates pathological output (e.g., endless repetition of "9999999...")
  - Conversation grows until exceeding vLLM's 65,536 token limit
  - Error: `BadRequestError: This model's maximum context length is 65536 tokens. However, your request has 65544 input tokens`
- **Root Cause**:
  - Agent detects integer overflow vulnerability
  - Generates attack example with extremely long string
  - No conversation length safeguards in multi-agent setup
  - Model gets stuck in repetitive generation pattern
- **Impact**: Experiment crashes and resume attempts retry the same problematic sample
- **Solution**:
  1. Run the script again
  2. When prompted, select option **2**: "Skip the next sample and mark as failed"
  3. Script will mark the sample as FAILED and continue from next sample
- **Prevention**: Consider adding:
  - Max output length limits per agent response
  - Conversation truncation for multi-agent chats
  - Timeout mechanisms for individual samples
- **Frequency**: Occurs on ~3.6% of samples (14/386 observed across pods)
- **Pattern**: Agents generate overly verbose output, either through repetition or exhaustive analysis
  - Pod 1, Sample 68 (idx: 389760): Endless "999..." (integer overflow in `r_num_math`)
  - Pod 1, Sample 85 (idx: 413623): Endless "000..." (integer overflow attack example)
  - Pod 1, Sample 161 (idx: 197973): Endless "999..." (LISTEN_FDS parsing via `strtoll()`)
  - Pod 2, Sample 59 (idx: 252437): Endless "000..." (vector size overflow, 65,544 tokens)
  - Pod 2, Sample 33 (idx: 427707): Repetitive arithmetic overflow calculation (SIZE_MAX wrapping)
  - Pod 2, Sample 36 (idx: 391628): Repetitive vulnerability enumeration (BMP file handling)
  - Pod 2, Sample 8 (idx: 351182): Endless "000..." in index overflow demonstration (int64_t bounds)
  - Pod 2, Sample 6 (idx: 440872): Repetitive "no obvious vulnerabilities" loop (ccline.cmdbuff analysis)
  - Pod 4, Sample 8 (idx: 344242): Endless "luaC_checkGC(L);" (Lua memory management)
  - Pod 4, Sample 7 (idx: 450812): Overly verbose analysis (66,177 tokens for glob function analysis)
  - Pod 4, Sample 1 (idx: 259619): Repetitive STRCAT buffer overflow analysis (66,426 tokens)
  - Pod 4, Sample 131 (idx: 439266): Repetitive vulnerability searching (BMP file size validation)
  - Pod 4, Sample 3 (idx: 328807): Repetitive "no vulnerabilities" loop (y_array null pointer analysis)
  - Pod 8, Sample 40 (idx: 447053): Repetitive overflow calculation (TIFF count * size modulo arithmetic)
- **Impact on Results**: 14 unique samples identified that need to be skipped across different pods (~3.6% failure rate)
- **Common Pattern**: Either repetitive string generation (attack examples) or excessively verbose multi-agent analysis that exceeds context window
- **Pod-specific**: Pod 4 (4B-Thinking, Few-Shot) showing highest failure rate with 6 context overflows, followed by Pod 2 (5), Pod 1 (3), and Pod 8 (1)
- **Logging Improvement**: ✅ Completed - Scripts uploaded to all 4 active pods, verified present on all systems

### Completed Tasks:
- ✅ Upload script fixed to include all 22 Python files
- ✅ Setup script auto-configures for vLLM
- ✅ vLLM compatibility issues resolved (api_base→base_url, model sanitization)
- ✅ Model name sanitization fixed to handle "/" character
- ✅ 10-sample validation test passed
- ✅ All 4 pods deployed and operational
- ✅ `evaluate` library installed on all pods
- ✅ Pod 1: DA-vuln-zero and DA-code-zero completed
- ✅ Pod 3: DA-vuln-few and DA-code-few completed

---

## Timeline

| Time | Event |
|------|-------|
| Nov 16 00:00 | Pod 1 created and setup complete (157.66.254.40:14555) |
| Nov 16 00:00 | Pod 2 created and setup complete (205.196.17.138:12500) |
| Nov 16 00:00 | Pod 1 DA-vuln-zero started (4B-Instruct) |
| Nov 16 00:00 | Pod 2 config fixed (Instruct → Thinking model) |
| Nov 16 00:00 | Pod 2 DA-vuln-zero started (4B-Thinking) |
| Nov 16 00:00 | Pods 3 & 4 created and setup complete |
| Nov 16 00:00 | Pod 3 DA-vuln-few started, Pod 4 DA-vuln-few started |
| Nov 16 00:00 | Pod 1 DA-vuln-zero completed ✅ |
| Nov 16 00:00 | Pod 1 DA-code-zero started |
| Nov 16 00:00 | Model sanitization fix applied to all pods (handle "/" character) |
| Nov 16 00:00 | Pod 1 DA-code-zero completed ✅ (99.4% success) |
| Nov 16 00:00 | `evaluate` library installed on all pods |
| Nov 16 00:00 | Pod 1 MA-vuln-zero started |
| Nov 16 00:00 | Pod 1 MA-vuln-zero paused then resumed (from sample 3/386) |
| Nov 16 00:00 | Pod 3 DA-vuln-few completed ✅ |
| Nov 16 00:00 | Pod 3 DA-code-few completed ✅ (99.4% success, Pass@1: 1.0000) |
| Nov 16 00:59 | Pod 3 MA-vuln-few started 🏃 |
| Nov 16 01:15 | ⚠️ Pod 1 MA-vuln-zero hit context overflow on sample 68/383 (idx: 389760) |
| Nov 16 01:15 | Issue: Security researcher generated endless "999..." string, exceeded 65,536 token limit |
| Nov 16 01:20 | Resolution: Use resume option 2 to skip sample 68 and continue from sample 69 |
| Nov 16 02:10 | Pod 3 MA-vuln-few completed ✅ |
| Nov 16 02:10 | Pod 5 created (205.196.17.139:9294) for Qwen3-30B-A3B-Instruct experiments |
| Nov 16 02:10 | Pod 5 vLLM downloading 30B model (~60GB) |
| Nov 16 02:20 | Pod 3 MA-code-few started (fixed prompt selection bug) |
| Nov 16 02:25 | Pod 5 vLLM startup complete - Ready for experiments ✅ |
| Nov 16 02:30 | Pod 5 DA-vuln-zero started (30B model) 🏃 |
| Nov 16 02:35 | ⚠️ Pod 1 MA-vuln-zero hit context overflow AGAIN on sample 85/312 (idx: 413623) |
| Nov 16 02:35 | Pattern: Security researcher generates endless "000..." for integer overflow vulns |
| Nov 16 02:40 | Pod 3 MA-code-few completed ✅ (99.4% success, Pass@1: 1.0000) |
| Nov 16 02:40 | 🎉 Pod 3 is FIRST to complete all 4 experiments (100% done!) |
| Nov 16 02:45 | Pod 6 created (63.141.33.85:22145) for Qwen3-30B-A3B-Thinking experiments |
| Nov 16 02:45 | Pod 7 created (205.196.17.131:10944) for Qwen3-30B-A3B-Instruct Few-Shot |
| Nov 16 02:50 | Pod 6 DA-vuln-zero started (30B Thinking model) 🏃 |
| Nov 16 02:50 | Pod 7 vLLM startup complete - Ready for experiments ✅ |
| Nov 16 02:55 | Pod 5 DA-vuln-zero completed ✅ (30B model) |
| Nov 16 02:55 | Pod 5 DA-code-zero started 🏃 |
| Nov 16 03:00 | Pod 8 created (213.181.122.251:15454) for Qwen3-30B-A3B-Thinking Few-Shot |
| Nov 16 03:05 | ⚠️ Pod 1 MA-vuln-zero hit context overflow THIRD TIME on sample 161/227 (idx: 197973) |
| Nov 16 03:05 | Pattern confirmed: All 3 overflows involve string-to-number parsing (strtoll/strtoull) |
| Nov 16 03:05 | Pod 3 results verified and downloaded (20MB, 30 files) - Safe to terminate ✅ |
| Nov 16 03:10 | Pod 3 stopped (not yet terminated) |
| Nov 16 03:10 | Pod 8 vLLM startup complete - Ready for experiments ✅ |
| Nov 16 03:10 | Pod 1 MA-vuln-zero resumed (skipped sample 161, continuing from 162) |
| Nov 16 03:10 | 🚀 All 8 pods deployed - 7 active (Pod 3 stopped) |
| Nov 16 03:15 | Pod 8 DA-vuln-few started (30B Thinking model) 🏃 |
| Nov 16 03:20 | Pod 5 DA-code-zero completed ✅ (30B Instruct model) |
| Nov 16 04:00 | Pod 5 MA-vuln-zero started 🏃 |
| Nov 16 04:00 | Pod 7 DA-vuln-few started 🏃 |
| Nov 16 06:00 | Pod 5 MA-vuln-zero completed ✅ |
| Nov 16 06:05 | Pod 5 MA-code-zero started 🏃 |
| Nov 16 06:30 | Pod 7 DA-vuln-few completed ✅ |
| Nov 16 06:35 | Pod 7 DA-code-few started 🏃 |
| Nov 16 06:50 | Pod 5 MA-code-zero completed ✅ - Pod 5 ALL 4/4 DONE 🎉 |
| Nov 16 06:55 | Pod 5 results downloaded (21MB, 28 files) and verified ✅ |
| Nov 16 07:00 | Pod 5 stopped - Ready to terminate |
| Nov 16 07:10 | ⚠️ Pod 4 hit context overflow on sample 8/386 (idx: 344242) - Endless "luaC_checkGC(L);" |
| Nov 16 07:15 | Pod 4 resumed with skip option 2 |
| Nov 16 07:30 | Pod 7 DA-code-few completed ✅ |
| Nov 16 07:35 | Pod 7 MA-vuln-few started 🏃 |
| Nov 16 08:00 | ⚠️ Pod 4 hit context overflow on sample 7/378 (idx: 450812) - Verbose glob analysis |
| Nov 16 08:05 | Pod 4 resumed with skip option 2 |
| Nov 16 09:30 | Pod 7 MA-vuln-few completed ✅ |
| Nov 16 09:35 | Pod 7 MA-code-few started 🏃 |
| Nov 16 10:00 | Pod 7 MA-code-few completed ✅ - Pod 7 ALL 4/4 DONE 🎉 |
| Nov 16 10:05 | 🔍 **CRITICAL DISCOVERY**: Checked vLLM processes - 30B models running with 32,768 context instead of 65,536! |
| Nov 16 10:10 | Analysis: Pod 7 had 6 failures in DA-vuln-few due to context limit; Pod 5 had 0 (zero-shot uses fewer tokens) |
| Nov 16 10:15 | Decision: Accept limitations for Pods 5 & 7, reconfigure Pods 6 & 8 before next experiments |
| Nov 16 10:20 | Pod 7 results downloaded (28 files) and verified ✅ |
| Nov 16 10:25 | Pod 7 stopped - Ready to terminate |
| Nov 16 10:30 | ⚠️ Pod 4 hit context overflow on sample 1/370 (idx: 259619) - STRCAT buffer overflow (66,426 tokens) |
| Nov 16 10:35 | Pod 4 resumed with skip option 2 |
| Nov 16 11:00 | ⚠️ Pod 2 hit context overflow on sample 59/386 (idx: 252437) - Endless "000..." (65,544 tokens) |
| Nov 16 11:05 | Pod 2 resumed with skip option 2 |
| Nov 16 12:00 | Pod 8 DA-vuln-few completed ✅ |
| Nov 16 12:05 | 🔧 Pod 8 vLLM reconfiguration started: --max-model-len 65536 --gpu-memory-utilization 0.85 |
| Nov 16 12:10 | ❌ Pod 8 vLLM failed to start: KV cache needs 6.00 GiB, only 4.68 GiB available |
| Nov 16 12:15 | 🔧 Pod 8 vLLM reconfigured with --gpu-memory-utilization 0.9 - SUCCESS ✅ |
| Nov 16 12:20 | Pod 8 DA-code-few started 🏃 |
| Nov 16 13:00 | Pod 6 DA-vuln-zero completed ✅ |
| Nov 16 13:05 | 🔧 Pod 6 vLLM reconfigured: --max-model-len 65536 --gpu-memory-utilization 0.9 ✅ |
| Nov 16 13:10 | Pod 6 DA-code-zero started 🏃 |
| Nov 16 14:00 | ⚠️ Pod 2 hit context overflow on sample 33/325 (idx: 427707) - SIZE_MAX arithmetic wrapping |
| Nov 16 14:05 | Pod 2 resumed with skip option 2 |
| Nov 16 14:30 | Pod 2 MA-vuln-zero completed ✅ |
| Nov 16 14:35 | Pod 2 MA-code-zero started 🏃 |
| Nov 16 14:40 | Git commit: Pod 5 & 7 results, vLLM misconfiguration documentation (57 files, 236K+ insertions) |
| Nov 16 15:00 | Pod 8 DA-code-few completed ✅ (Pass@1: 0.6890) |
| Nov 16 15:05 | Pod 6 DA-code-zero completed with 1 context overflow error (65,594 tokens) |
| Nov 16 15:10 | Pod 6 evaluation failed: "cannot access local variable 'results_file'" |
| Nov 16 15:30 | 🐛 Fixed dual_agent_code_generation.py evaluation error (initialize results_file = None) |
| Nov 16 15:35 | 📝 Added logging improvements to multi-agent scripts (print sample/idx at each phase) |
| Nov 16 15:40 | Git commit: Logging improvements and evaluation fix |
| Nov 16 15:45 | 📤 Uploaded improved scripts to all 4 active pods (2, 4, 6, 8) |
| Nov 16 15:50 | Pod 6 manual evaluation completed ✅ |
| Nov 16 15:55 | Pod 8 MA-vuln-few started 🏃 (with new logging!) |
| Nov 16 16:00 | Pod 6 MA-vuln-zero started 🏃 (with new logging!) |
| Nov 16 16:10 | ⚠️ Pod 2 hit context overflow on sample 36/292 (idx: 391628) - Repetitive vulnerability enumeration |
| Nov 16 16:15 | Pod 2 resumed with skip option 2 |
| Nov 16 16:20 | ⚠️ Pod 4 hit context overflow on sample 131/365 (idx: 439266) - Repetitive vulnerability searching |
| Nov 16 16:25 | Pod 4 resumed with skip option 2 |
| Nov 16 16:30 | ⚠️ Pod 2 hit context overflow on sample 8/234 (idx: 351182) - Endless "000..." in int64_t demo |
| Nov 16 16:35 | Pod 2 resumed with skip option 2 |
| Nov 16 16:40 | ⚠️ Pod 4 hit context overflow on sample 3/234 (idx: 328807) - Repetitive "no vulnerabilities" loop |
| Nov 16 16:45 | Pod 4 resumed with skip option 2 |
| Nov 16 16:50 | Git commit: 2 new context overflow samples, updated tracking |
| Nov 16 16:55 | **Current Status**: 23/32 experiments complete (71.875%) - 4 pods actively running |

---

**Last Updated**: 2025-11-16 16:55
