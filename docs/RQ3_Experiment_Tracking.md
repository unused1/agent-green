# RQ3 Experiment Tracking - Explanation Prompting

**Session Date**: November 22, 2025
**Objective**: Evaluate explain-before prompting strategy for vulnerability detection and code generation tasks
**Research Question**: How does explain-before prompting impact explanation usefulness and faithfulness, and do effects differ between reasoning and non-reasoning models?

---

## 📋 Pre-Execution Checklist

### ✅ Prompt Validation (Literature Review)

**Status**: ⏳ **PENDING - MUST COMPLETE BEFORE EXPERIMENTS**

**Task**: Find and review existing research on explain-before (chain-of-thought) prompt design to validate our RQ3 prompts

**Search Strategy**:
- [ ] Search for "chain-of-thought prompting" design patterns
- [ ] Search for "explain-before" or "reasoning-before-answer" prompting
- [ ] Search for "structured explanation prompting" in LLMs
- [ ] Review prompt engineering best practices papers
- [ ] Check if our prompt structure aligns with established patterns

**Key Questions to Answer**:
1. Does our "REASONING: ... DECISION/CODE: ..." structure align with established CoT patterns?
2. Are there recommended phrase patterns (e.g., "Let's think step-by-step") we should incorporate?
3. What are common pitfalls in explain-before prompt design?
4. How do state-of-the-art papers structure explanation prompts?

**Recommended Papers to Search**:
- Wei et al. (2022) - "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
- Kojima et al. (2023) - "Large Language Models are Zero-Shot Reasoners"
- Zhou et al. (2023) - "Large Language Models are Human-Level Prompt Engineers"
- Any recent surveys on prompt engineering for code/security tasks

**Deliverable**: Document findings in `docs/RQ3_Prompt_Validation.md` with:
- Summary of best practices from literature
- Comparison of our prompts vs. recommended patterns
- Any modifications needed before running experiments
- Citation list for methodology section

**Deadline**: Complete before starting experiments

---

## 🧪 Experiment Configuration

### Model Configuration

| Model ID | Size | Type | ENABLE_REASONING | Experiments |
|----------|------|------|------------------|-------------|
| Qwen/Qwen3-4B-Instruct-2507 | 4B | Baseline | `false` | SA-zero-explain, SA-few-explain (2×) |
| Qwen/Qwen3-4B-Thinking-2507 | 4B | Reasoning | `true` | SA-zero-explain, SA-few-explain (2×) |
| Qwen/Qwen3-30B-A3B-Instruct | 30B | Baseline | `false` | SA-zero-explain, SA-few-explain (2×) |
| Qwen/Qwen3-30B-A3B-Thinking | 30B | Reasoning | `true` | SA-zero-explain, SA-few-explain (2×) |

**Total Experiments**: 8 (4 models × 2 designs each)
- Each model runs: SA-zero-explain, SA-few-explain
- Each design runs on: 2 tasks (vuln detection + code generation)

### Baseline Comparison

RQ3 experiments will be compared against RQ1 baseline (no-explanation):
- **RQ1 Baselines**: SA-zero, SA-few (answer-only mode)
- **RQ3 Explain-Before**: SA-zero-explain, SA-few-explain (structured reasoning mode)

### Dataset Information

| Task | Dataset | Samples | Source File |
|------|---------|---------|-------------|
| Vulnerability Detection | Custom Dataset | 386 | `datasets/vulnerability_detection/vulnerability_dataset.jsonl` |
| Code Generation | HumanEval | 164 | `datasets/code_generation/HumanEval.jsonl` |

---

## 📊 Experiment Status

### Phase 1: Infrastructure & Validation ✅

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create explain-before prompts | ✅ Complete | 6 prompts in config.py |
| 2 | Modify single_agent_vuln.py | ✅ Complete | Supports SA-zero-explain, SA-few-explain |
| 3 | Modify single_agent_code_generation.py | ✅ Complete | Supports SA-zero-explain, SA-few-explain |
| 4 | Implement faithfulness metrics | ✅ Complete | faithfulness_metrics.py module |
| 5 | Create test scripts | ✅ Complete | test_rq3_sample.py |
| 6 | **Literature review for prompt validation** | ⏳ **PENDING** | **BLOCKER - Must complete first** |
| 7 | Run validation tests (2 samples each) | ⏳ Pending | After prompt validation |

### Phase 2: Vulnerability Detection Experiments (4 experiments)

| # | Design | Model | Size | Type | Samples | Status | Duration | Results File | Faithfulness Metrics |
|---|--------|-------|------|------|---------|--------|----------|--------------|---------------------|
| 1 | SA-zero-explain | 4B-Instruct | 4B | Baseline | 386 | ⏳ Pending | - | - | - |
| 2 | SA-few-explain | 4B-Instruct | 4B | Baseline | 386 | ⏳ Pending | - | - | - |
| 3 | SA-zero-explain | 4B-Thinking | 4B | Reasoning | 386 | ⏳ Pending | - | - | - |
| 4 | SA-few-explain | 4B-Thinking | 4B | Reasoning | 386 | ⏳ Pending | - | - | - |
| 5 | SA-zero-explain | 30B-Instruct | 30B | Baseline | 386 | ⏳ Pending | - | - | - |
| 6 | SA-few-explain | 30B-Instruct | 30B | Baseline | 386 | ⏳ Pending | - | - | - |
| 7 | SA-zero-explain | 30B-Thinking | 30B | Reasoning | 386 | ⏳ Pending | - | - | - |
| 8 | SA-few-explain | 30B-Thinking | 30B | Reasoning | 386 | ⏳ Pending | - | - | - |

**Progress**: 0/8 Complete (0.0%)

### Phase 3: Code Generation Experiments (4 experiments)

| # | Design | Model | Size | Type | Samples | Status | Duration | Results File | Faithfulness Metrics |
|---|--------|-------|------|------|---------|--------|----------|--------------|---------------------|
| 1 | SA-zero-explain | 4B-Instruct | 4B | Baseline | 164 | ⏳ Pending | - | - | - |
| 2 | SA-few-explain | 4B-Instruct | 4B | Baseline | 164 | ⏳ Pending | - | - | - |
| 3 | SA-zero-explain | 4B-Thinking | 4B | Reasoning | 164 | ⏳ Pending | - | - | - |
| 4 | SA-few-explain | 4B-Thinking | 4B | Reasoning | 164 | ⏳ Pending | - | - | - |
| 5 | SA-zero-explain | 30B-Instruct | 30B | Baseline | 164 | ⏳ Pending | - | - | - |
| 6 | SA-few-explain | 30B-Instruct | 30B | Baseline | 164 | ⏳ Pending | - | - | - |
| 7 | SA-zero-explain | 30B-Thinking | 30B | Reasoning | 164 | ⏳ Pending | - | - | - |
| 8 | SA-few-explain | 30B-Thinking | 30B | Reasoning | 164 | ⏳ Pending | - | - | - |

**Progress**: 0/8 Complete (0.0%)

### Phase 4: Faithfulness Metrics Computation

| # | Task Type | Design | Model | Status | Metrics File | Notes |
|---|-----------|--------|-------|--------|--------------|-------|
| 1 | Vuln | SA-zero-explain | 4B-Instruct | ⏳ Pending | - | - |
| 2 | Vuln | SA-few-explain | 4B-Instruct | ⏳ Pending | - | - |
| 3 | Vuln | SA-zero-explain | 4B-Thinking | ⏳ Pending | - | - |
| 4 | Vuln | SA-few-explain | 4B-Thinking | ⏳ Pending | - | - |
| 5 | Vuln | SA-zero-explain | 30B-Instruct | ⏳ Pending | - | - |
| 6 | Vuln | SA-few-explain | 30B-Instruct | ⏳ Pending | - | - |
| 7 | Vuln | SA-zero-explain | 30B-Thinking | ⏳ Pending | - | - |
| 8 | Vuln | SA-few-explain | 30B-Thinking | ⏳ Pending | - | - |
| 9 | CodeGen | SA-zero-explain | 4B-Instruct | ⏳ Pending | - | - |
| 10 | CodeGen | SA-few-explain | 4B-Instruct | ⏳ Pending | - | - |
| 11 | CodeGen | SA-zero-explain | 4B-Thinking | ⏳ Pending | - | - |
| 12 | CodeGen | SA-few-explain | 4B-Thinking | ⏳ Pending | - | - |
| 13 | CodeGen | SA-zero-explain | 30B-Instruct | ⏳ Pending | - | - |
| 14 | CodeGen | SA-few-explain | 30B-Instruct | ⏳ Pending | - | - |
| 15 | CodeGen | SA-zero-explain | 30B-Thinking | ⏳ Pending | - | - |
| 16 | CodeGen | SA-few-explain | 30B-Thinking | ⏳ Pending | - | - |

**Progress**: 0/16 Complete (0.0%)

### Phase 5: Usefulness Rating (Self-Rating)

**Target**: Sample 60 explanations across conditions for usefulness rating

| Condition | Task Type | Target Samples | Status | Rated | Notes |
|-----------|-----------|----------------|--------|-------|-------|
| 4B-Instruct | Vuln | 8 | ⏳ Pending | 0/8 | 4 from zero-shot, 4 from few-shot |
| 4B-Instruct | CodeGen | 7 | ⏳ Pending | 0/7 | 4 from zero-shot, 3 from few-shot |
| 4B-Thinking | Vuln | 8 | ⏳ Pending | 0/8 | 4 from zero-shot, 4 from few-shot |
| 4B-Thinking | CodeGen | 7 | ⏳ Pending | 0/7 | 4 from zero-shot, 3 from few-shot |
| 30B-Instruct | Vuln | 8 | ⏳ Pending | 0/8 | 4 from zero-shot, 4 from few-shot |
| 30B-Instruct | CodeGen | 7 | ⏳ Pending | 0/7 | 4 from zero-shot, 3 from few-shot |
| 30B-Thinking | Vuln | 8 | ⏳ Pending | 0/8 | 4 from zero-shot, 4 from few-shot |
| 30B-Thinking | CodeGen | 7 | ⏳ Pending | 0/7 | 4 from zero-shot, 3 from few-shot |

**Progress**: 0/60 Rated (0.0%)

**Usefulness Rubric** (to be applied during rating):
- **Clarity**: Is the explanation easy to understand?
- **Localization**: Does it reference specific code artifacts?
- **Actionability**: Does it provide concrete next steps?
- **Testability**: Are claims verifiable/reproducible?
- **Context Fit**: Is the explanation appropriate for the task?

**Rating Scale**: 1 (Poor) to 5 (Excellent) for each dimension

---

## 🚀 Experiment Commands

### Validation Test Commands

```bash
# Test explain-before mode on 2 samples
python3 scripts/test_rq3_sample.py vuln 2
python3 scripts/test_rq3_sample.py codegen 2
```

### Vulnerability Detection Commands

```bash
# 4B-Instruct (ENABLE_REASONING=false)
python3 src/single_agent_vuln.py SA-zero-explain
python3 src/single_agent_vuln.py SA-few-explain

# 4B-Thinking (ENABLE_REASONING=true)
# Update config.py: ENABLE_REASONING=true, switch to 4B-Thinking model
python3 src/single_agent_vuln.py SA-zero-explain
python3 src/single_agent_vuln.py SA-few-explain

# 30B-Instruct (ENABLE_REASONING=false)
# Update config.py: ENABLE_REASONING=false, switch to 30B-Instruct model
python3 src/single_agent_vuln.py SA-zero-explain
python3 src/single_agent_vuln.py SA-few-explain

# 30B-Thinking (ENABLE_REASONING=true)
# Update config.py: ENABLE_REASONING=true, switch to 30B-Thinking model
python3 src/single_agent_vuln.py SA-zero-explain
python3 src/single_agent_vuln.py SA-few-explain
```

### Code Generation Commands

```bash
# 4B-Instruct (ENABLE_REASONING=false)
python3 src/single_agent_code_generation.py SA-zero-explain
python3 src/single_agent_code_generation.py SA-few-explain

# 4B-Thinking (ENABLE_REASONING=true)
# Update config.py: ENABLE_REASONING=true, switch to 4B-Thinking model
python3 src/single_agent_code_generation.py SA-zero-explain
python3 src/single_agent_code_generation.py SA-few-explain

# 30B-Instruct (ENABLE_REASONING=false)
# Update config.py: ENABLE_REASONING=false, switch to 30B-Instruct model
python3 src/single_agent_code_generation.py SA-zero-explain
python3 src/single_agent_code_generation.py SA-few-explain

# 30B-Thinking (ENABLE_REASONING=true)
# Update config.py: ENABLE_REASONING=true, switch to 30B-Thinking model
python3 src/single_agent_code_generation.py SA-zero-explain
python3 src/single_agent_code_generation.py SA-few-explain
```

### Faithfulness Metrics Commands

After each experiment completes:

```bash
# Vulnerability Detection
python3 src/compute_faithfulness.py results/<vuln_results_file>.csv vuln

# Code Generation
python3 src/compute_faithfulness.py results/<codegen_results_file>.jsonl codegen
```

---

## 📈 Monitoring

### Check Experiment Progress

```bash
# Vulnerability detection (CSV files)
tail -f results/vuln_SA-*-explain_*_detailed_results.csv

# Code generation (JSONL files)
tail -f results/code_SA-*-explain_*_detailed_results.jsonl

# Count completed samples
wc -l results/*_detailed_results.*
```

### Check for Errors

```bash
# Search for error messages in results
grep -i "error" results/*_detailed_results.*

# Check for context overflows
grep -i "context" results/*_detailed_results.*
```

### Monitor vLLM Server (if using local vLLM)

```bash
# Check vLLM status
curl http://localhost:8000/v1/models | python -m json.tool

# Monitor GPU
nvidia-smi
watch -n 1 nvidia-smi
```

---

## 📊 Analysis Tasks

### Statistical Analysis

- [ ] Compare task performance: explain-before vs. no-explanation (RQ1 baselines)
- [ ] Analyze faithfulness metrics across models and prompting strategies
- [ ] Test for statistically significant differences (t-tests, effect sizes)
- [ ] Create comparison visualizations (bar charts, box plots)
- [ ] Perform correlation analysis (explanation length vs. task performance)

### Visualization Tasks

- [ ] Faithfulness metrics comparison (by model, by task, by prompting)
- [ ] Usefulness ratings distribution
- [ ] Task performance comparison (explain-before vs. baseline)
- [ ] Citation density analysis
- [ ] Structure compliance rates

### Documentation

- [ ] Document findings in `docs/RQ3_Analysis_Summary.md`
- [ ] Create tables for final report
- [ ] Write RQ3 methodology section
- [ ] Write RQ3 results section
- [ ] Write RQ3 discussion section

---

## ⚠️ Known Issues & Risks

### Potential Risks

1. **Context Overflow Risk**
   - Explain-before prompting increases token usage
   - May hit context limits on long samples
   - Mitigation: Resume functionality already implemented
   - Monitor: Track context overflow rate vs. RQ1 baseline

2. **Prompt Compliance Risk**
   - Models may not follow "REASONING: ... DECISION/CODE: ..." format
   - Mitigation: Validation tests before full experiments
   - Fallback: Extraction functions handle partial compliance

3. **Time Estimation**
   - Explain-before increases latency per sample
   - Estimated time per experiment:
     - Vuln (386 samples): ~2-3h for 4B, ~4-6h for 30B
     - CodeGen (164 samples): ~1-2h for 4B, ~2-3h for 30B
   - Total estimated time: ~40-60 hours across all 16 experiments

4. **Model Availability**
   - vLLM server must remain stable throughout experiments
   - Mitigation: Resume functionality preserves progress

### Troubleshooting

**Issue**: Model doesn't follow structured format
- **Solution**: Check prompt in config.py, verify EXPLANATION_MODE flag is set
- **Diagnostic**: Run validation test to see actual output

**Issue**: Context overflow on explain-before mode
- **Solution**: Use resume option 2 to skip problematic sample
- **Note**: Track overflow rate for comparison with baselines

**Issue**: Extraction function fails to parse reasoning
- **Solution**: Check extraction logic in single_agent_*.py
- **Fallback**: Treat entire response as reasoning

---

## 📝 Notes

### Session Notes

- RQ3 focuses on **explain-before prompting only** (not all 4 strategies from research design)
- Strategic subset approach: 8 new experiments + reuse RQ1 baselines
- All infrastructure committed to `rq3-explainability` branch
- Backup tag: `pre-rq3-backup`

### Experiment Design Notes

- **Explain-Before Strategy**: Model must provide step-by-step reasoning BEFORE final answer
- **Format**: "REASONING: [analysis] DECISION/CODE: [answer]"
- **Comparison**: Against RQ1 no-explanation baselines (SA-zero, SA-few)
- **Metrics**:
  - **Faithfulness** (automated): Citation validity, decision consistency, implementation alignment
  - **Usefulness** (self-rated): Clarity, actionability, specificity
  - **Task Performance**: Maintain or improve on baseline accuracy

### Literature Review Findings

**Status**: ⏳ **TO BE COMPLETED**

(This section will be populated after literature review is complete)

---

## 📅 Timeline

| Date | Event |
|------|-------|
| Nov 22, 2025 | RQ3 infrastructure created (prompts, scripts, metrics) ✅ |
| TBD | **Literature review for prompt validation** ⏳ **NEXT TASK** |
| TBD | Run validation tests (2 samples each) |
| TBD | Execute 8 vulnerability detection experiments |
| TBD | Execute 8 code generation experiments |
| TBD | Compute faithfulness metrics for all 16 experiments |
| TBD | Self-rate 60 sampled explanations |
| TBD | Perform statistical analysis |
| TBD | Write RQ3 section for final report |

---

**Last Updated**: 2025-11-22 (Created)
**Overall Progress**: Infrastructure Complete (Phase 1: 6/7 tasks) - **Awaiting Prompt Validation**
