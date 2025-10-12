# RQ1 Setup Summary

## Overview
You can now run RQ1 vulnerability detection experiments with Qwen3 model in **reasoning mode (thinking enabled)** vs **baseline mode (thinking disabled)** using the **same base model** for fair comparison.

## What Was Done

### 1. ✅ Configuration Files Updated

**`.env`** - Environment configuration with reasoning toggle:
- `ENABLE_REASONING=true/false` - Toggle reasoning mode
- `REASONING_MODEL=qwen3:4b-thinking` - Model with thinking
- `BASELINE_MODEL=qwen3:4b` - Model without thinking
- Both use same endpoint (localhost Ollama)

**`src/config.py`** - Dynamic model selection logic:
- Reads `ENABLE_REASONING` from environment
- Automatically selects reasoning or baseline model
- Prints configuration on startup for verification
- Supports both local Ollama and RunPod endpoints

### 2. ✅ Documentation Created

**`docs/rq1_experiment_plan.md`** - Complete experimental protocol:
- 324 total experiments across 5 tasks
- Model selection strategy
- Dataset descriptions
- Metrics and evaluation procedures
- Cost estimates and timeline

**`docs/RQ1_QuickStart_Vulnerability.md`** - Step-by-step guide:
- Environment setup instructions
- How to run individual experiments
- How to compare results
- Troubleshooting tips

**`docs/RQ1_Setup_Summary.md`** - This file!

### 3. ✅ Scripts Created

**`scripts/run_rq1_vuln.sh`** - Batch execution:
- Runs all 4 vulnerability detection experiments
- Reasoning + Zero-shot
- Baseline + Zero-shot
- Reasoning + Few-shot
- Baseline + Few-shot

### 4. ✅ Code Ready

**`src/single_agent_vuln.py`** - Already supports:
- VulTrial dataset (386 samples)
- Zero-shot and few-shot prompting
- Incremental result saving
- Energy tracking with CodeCarbon
- Multiple evaluation strategies

## Key Innovation: Same Model, Different Modes

Unlike comparing different models entirely, you can use:
- **qwen3:4b-thinking** - Reasoning enabled (generates internal thoughts)
- **qwen3:4b** - Reasoning disabled (direct answers)

This isolates the **reasoning capability** as the only variable!

## Quick Start

### Option 1: Single Experiment (Manual)

```bash
# 1. Pull models
ollama pull qwen3:4b-thinking
ollama pull qwen3:4b

# 2. Start Ollama
ollama serve

# 3. Run with reasoning enabled
export ENABLE_REASONING=true
python src/single_agent_vuln.py SA-zero

# 4. Run with reasoning disabled
export ENABLE_REASONING=false
python src/single_agent_vuln.py SA-zero
```

### Option 2: Batch Execution (All 4 experiments)

```bash
# Run all experiments automatically
./scripts/run_rq1_vuln.sh
```

### Option 3: Direct Model Override

```bash
# Bypass ENABLE_REASONING and specify model directly
LLM_MODEL=qwen3:4b-thinking python src/single_agent_vuln.py SA-zero
LLM_MODEL=qwen3:4b python src/single_agent_vuln.py SA-zero
```

## Expected Workflow

1. **Setup** (5 minutes):
   - Pull both qwen3 models
   - Verify `.env` configuration
   - Start Ollama server

2. **Run Experiments** (~2-4 hours for all 4):
   - Each experiment processes 386 code samples
   - Results saved incrementally
   - Energy consumption tracked

3. **Compare Results**:
   - Check accuracy differences
   - Analyze energy consumption
   - Statistical significance testing

## Output Structure

```
results/
├── SA-zero_qwen3-4b-thinking_YYYYMMDD-HHMMSS_detailed_results.jsonl
├── SA-zero_qwen3-4b-thinking_YYYYMMDD-HHMMSS_detailed_results.csv
├── SA-zero_qwen3-4b-thinking_YYYYMMDD-HHMMSS_energy_tracking.json
├── SA-zero_qwen3-4b-thinking_YYYYMMDD-HHMMSS_eval_basic.json
├── SA-zero_qwen3-4b-thinking_YYYYMMDD-HHMMSS_eval_conservative.json
├── SA-zero_qwen3-4b-thinking_YYYYMMDD-HHMMSS_eval_strict.json
├── SA-zero_qwen3-4b_YYYYMMDD-HHMMSS_detailed_results.jsonl
├── SA-zero_qwen3-4b_YYYYMMDD-HHMMSS_detailed_results.csv
├── SA-zero_qwen3-4b_YYYYMMDD-HHMMSS_energy_tracking.json
├── SA-zero_qwen3-4b_YYYYMMDD-HHMMSS_eval_basic.json
├── ...
└── emissions.csv
```

## Metrics Collected

For each experiment:
- **Accuracy**: Percentage of correct vulnerability detections
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **F1 Score**: Harmonic mean of precision and recall
- **Energy**: kWh and kg CO2 emissions
- **Time**: Inference time per sample
- **Confusion Matrix**: Detailed classification breakdown

## Verification Steps

Before starting experiments, verify:

```bash
# 1. Models available
ollama list | grep qwen3
# Should show: qwen3:4b and qwen3:4b-thinking

# 2. Config loads correctly
python -c "import src.config as config; print(f'Model: {config.LLM_MODEL}'); print(f'Reasoning: {config.ENABLE_REASONING}')"
# Should print current configuration

# 3. Dataset accessible
python -c "import src.config as config; import os; print(f'Dataset exists: {os.path.exists(config.VULN_DATASET)}')"
# Should print: Dataset exists: True

# 4. Ollama responsive
curl http://localhost:11434/api/version
# Should return version info
```

## Next Steps

1. **Test Setup**:
   ```bash
   # Quick test with first 10 samples (modify script to limit dataset)
   ENABLE_REASONING=true python src/single_agent_vuln.py SA-zero
   ```

2. **Run Full Experiments**:
   ```bash
   ./scripts/run_rq1_vuln.sh
   ```

3. **Analyze Results**:
   - Compare accuracy between reasoning/baseline
   - Check if reasoning improves vulnerability detection
   - Measure energy cost of reasoning

4. **Extend to Other Tasks**:
   - Log parsing
   - Code generation
   - (Implement log analysis and technical debt)

## Troubleshooting

### "Model not found"
```bash
ollama pull qwen3:4b-thinking
ollama pull qwen3:4b
```

### "Connection refused"
```bash
# Start Ollama server in separate terminal
ollama serve
```

### "No module named 'autogen'"
```bash
pip install -r requirements_flexible.txt
```

### "Config not loading"
```bash
# Check .env file
cat .env | grep ENABLE_REASONING

# Verify dotenv loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('ENABLE_REASONING'))"
```

## Comparison with Original Plan

| Original Plan | Current Implementation | Status |
|--------------|----------------------|--------|
| QwQ-32B (reasoning) | qwen3:4b-thinking | ✅ Adapted |
| Qwen2.5-32B (baseline) | qwen3:4b | ✅ Adapted |
| RunPod/vLLM | Local Ollama | ⚠️ Later |
| 5 tasks | 1 task (vuln) | 🔄 In Progress |
| 324 experiments | 4 experiments | 🔄 Starting |

**Advantages of current approach:**
1. **Faster iteration**: Local Ollama, no RunPod setup delays
2. **Same base model**: qwen3 with/without thinking is perfect comparison
3. **Lower cost**: Free local testing before cloud deployment
4. **Easier debugging**: Direct model access

**When to move to RunPod:**
1. After validating approach locally
2. When running full 324 experiments
3. For larger models (32B, 70B)
4. For parallel execution (multiple pods)

## Research Questions Addressed

✅ **RQ1**: Do reasoning-enabled LLMs outperform non-reasoning baselines?
- **Current experiment**: qwen3:4b-thinking vs qwen3:4b on vulnerability detection
- **Metrics**: Accuracy, precision, recall, F1, energy consumption
- **Expected insight**: Quantify reasoning benefit vs. cost

## Summary

You're now set up to:
1. ✅ Run vulnerability detection with reasoning ON/OFF
2. ✅ Use same base model (qwen3) for fair comparison
3. ✅ Track energy consumption with CodeCarbon
4. ✅ Collect comprehensive accuracy metrics
5. ✅ Scale to full RQ1 study when ready

**Next action**: Run `./scripts/run_rq1_vuln.sh` to start experiments!
