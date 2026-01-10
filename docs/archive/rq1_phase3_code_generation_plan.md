# RQ1 Phase 3: Code Generation Experiment Plan

**Date Created**: 2025-11-06
**Status**: Planning Stage
**Previous Phases**: Phase 1 (4B Vuln Detection ✅), Phase 2a (30B Vuln Detection ✅), Prompt Comparison ✅

---

## 1. Objective

Test if reasoning advantage and prompt quality patterns observed in vulnerability detection (classification task) generalize to code generation (generative task).

**Key Questions**:
1. Do reasoning models (Thinking) outperform baseline models (Instruct) on code generation?
2. Does prompt quality matter for code generation as it did for vulnerability detection?
3. How do energy-performance tradeoffs compare between classification and generation tasks?

---

## 2. Experimental Design

### 2.1 Models

**Same models as Phase 2a** (for consistency):
- Qwen3-30B-A3B-Instruct-2507 (Baseline)
- Qwen3-30B-A3B-Thinking-2507 (Reasoning)

**Rationale**:
- 30B MoE models showed best performance in vulnerability detection
- Enables direct comparison between task types
- Already deployed and tested infrastructure

### 2.2 Prompt Configurations

**Zero-shot**: Basic instruction without examples
**Few-shot**: With canonical programming examples

**Key Insight from Prompt Comparison**: Canonical examples matter! Need high-quality, domain-validated examples (not LLM-generated).

### 2.3 Dataset

**HumanEval** (164 Python programming problems)
- **Source**: https://github.com/openai/human-eval
- **Format**: JSONL with task_id, prompt, canonical_solution, test cases, entry_point
- **Status**: ⚠️ NEEDS TO BE DOWNLOADED

**Dataset Location**: `vuln_database/HumanEval.jsonl`

---

## 3. Current Implementation Status

### 3.1 Existing Code ✅

**Code Generation Script**: `src/single_agent_code_generation.py`
- Single agent implementation
- Supports SA-zero and SA-few designs
- CodeCarbon emissions tracking integrated
- Incremental saving (JSONL format)
- Automatic evaluation after completion

**Evaluation Script**: `src/evaluate_code_generation.py`
- Uses HuggingFace `code_eval` metric
- Computes Pass@1 score
- Code extraction from model responses (handles markdown, code blocks, function definitions)
- Test execution using provided test cases
- Outputs: JSON, TXT, CSV with detailed results

**Output Files**:
- `{exp_name}_detailed_results.jsonl` - Generated code per sample
- `{exp_name}_evaluation.json` - Pass@1 and per-sample results
- `{exp_name}_evaluation.txt` - Human-readable results
- `{exp_name}_evaluated.csv` - Detailed CSV with test outcomes
- `emissions.csv` - CodeCarbon energy tracking

### 3.2 Missing Components ⚠️

**1. Prompts Not Defined in Config**

Currently missing from `src/config.py`:
```python
CODE_GENERATION_TASK_PROMPT = ???
SYS_MSG_CODE_GENERATOR_ZERO_SHOT = ???
SYS_MSG_CODE_GENERATOR_FEW_SHOT = ???
```

**2. HumanEval Dataset Not Downloaded**

Need to download from: https://github.com/openai/human-eval/blob/master/data/HumanEval.jsonl.gz

**3. Canonical Few-Shot Examples Not Designed**

Following vulnerability detection learning: Need canonical programming examples (not LLM-generated)

**Candidates**:
- Classic algorithms (sorting, searching, dynamic programming)
- Standard library usage patterns
- Edge case handling examples

---

## 4. Performance Metrics

### 4.1 Primary Metric

**Pass@1**: Percentage of problems where the first generated solution passes all test cases
- Computed using HuggingFace `code_eval` metric
- Test cases execute in sandboxed environment
- Binary outcome: passed or failed

### 4.2 Secondary Metrics

**From Evaluation Script**:
- Total samples: 164
- Passed samples: Count of successful solutions
- Failed samples: Count of failed solutions
- Pass rate: (Passed / Total) × 100%

**Code Quality** (can be added):
- Syntax correctness rate (valid Python)
- Compilation success rate (no syntax errors before test execution)

### 4.3 Energy Metrics

**From CodeCarbon**:
- Total energy (kWh)
- CO2 emissions (kg)
- Duration (hours)
- Component breakdown (CPU/GPU/RAM)

**Efficiency Metrics** (computed):
- Energy per problem (kWh / 164)
- Energy per successful solution (kWh / passed_samples)
- CO2 per successful solution

### 4.4 Token Metrics

**To be added** (following Phase 2a analysis):
- Average output tokens per sample
- Total tokens generated
- Tokens per kWh
- Energy per 1K tokens
- Token length vs Pass@1 correlation

---

## 5. Experimental Phases

### Phase 3a: Validation Run (Small Scale) ⬜

**Purpose**: Validate setup and prompts before full experiment

**Configuration**:
- Models: Both (Instruct + Thinking)
- Prompts: Both (Zero-shot + Few-shot)
- Dataset: First 10 problems from HumanEval
- Total: 4 experiments (2 models × 2 prompts)

**Success Criteria**:
- Code generation completes without errors
- Evaluation script runs successfully
- Pass@1 scores are reasonable (>0%)
- Energy tracking works correctly
- Prompts produce valid code

**Estimated Time**: 1-2 hours (using H100)

**Outputs**:
- Validation results to verify metrics
- Prompt quality assessment
- Identification of any issues before full run

### Phase 3b: Full Experiment ⬜

**Purpose**: Complete code generation experiment for RQ1

**Configuration**:
- Models: Both (Instruct + Thinking)
- Prompts: Both (Zero-shot + Few-shot with canonical examples)
- Dataset: All 164 HumanEval problems
- Total: 4 experiments

**Estimated Time**: 8-12 hours total (2-3 hours per experiment on H100)

**Expected Outputs**:
1. Performance metrics (Pass@1 for 4 configurations)
2. Energy consumption data
3. Token usage analysis
4. Energy-performance tradeoffs
5. Comparison with vulnerability detection findings

---

## 6. Prompt Design Strategy

### 6.1 Zero-Shot Prompt (Basic)

**Structure**:
```
You are an expert Python programmer. Your task is to generate a complete,
working Python function based on the provided problem description.

Requirements:
- Generate only the function implementation
- Ensure the function signature matches the problem description
- Include all necessary imports
- Handle edge cases appropriately
- Write clean, efficient code

Problem:
{prompt}

Generate the complete Python function:
```

### 6.2 Few-Shot Prompt (Canonical Examples)

**Strategy**: Use canonical programming examples following the CWE-based approach from vulnerability detection

**Example Categories**:
1. **List manipulation**: Classic example (e.g., removing duplicates)
2. **String processing**: Standard pattern (e.g., palindrome check)
3. **Mathematical computation**: Clean implementation (e.g., factorial)

**Structure**:
```
You are an expert Python programmer. Here are examples of well-written Python functions:

Example 1: [Canonical list manipulation example]
Example 2: [Canonical string processing example]
Example 3: [Canonical mathematical example]

Now, generate a complete Python function for the following problem:

{prompt}

Generate the complete Python function:
```

**Important**: Examples should be:
- From standard computer science curriculum (canonical)
- Well-documented and clean
- Cover different programming patterns
- NOT LLM-generated

---

## 7. Comparison Framework

### 7.1 Cross-Task Comparison

Compare Phase 3 (Code Generation) with Phase 1 & 2a (Vulnerability Detection):

| Dimension | Vulnerability Detection | Code Generation |
|-----------|------------------------|-----------------|
| Task Type | Classification (binary) | Generation (open-ended) |
| Evaluation | F1 score, accuracy | Pass@1, pass rate |
| Output Length | Reasoning + label | Function code |
| Correctness | Against ground truth labels | Against test cases (executable) |

### 7.2 Expected Patterns

**Based on vulnerability detection findings**:

1. **Reasoning Advantage**: Thinking models likely to outperform Instruct
   - Vuln detection: +15-20pp F1
   - Code gen: Expected positive impact on Pass@1

2. **Prompt Quality Effect**: Few-shot quality should matter
   - Vuln detection: +6.9% to +31.7% with CWE prompts
   - Code gen: Canonical examples expected to help

3. **Energy Tradeoff**: Thinking uses more energy but better performance
   - Vuln detection: 3.9x energy for Thinking
   - Code gen: Similar ratio expected

4. **Model Scale**: 30B MoE efficiency
   - Vuln detection: 69% less CO2/sample than 4B
   - Code gen: Should maintain efficiency advantage

---

## 8. Infrastructure Requirements

### 8.1 Platform

**RunPod H100 80GB SXM** (same as Phase 2a)
- Dedicated pod per experiment
- Clean emissions.csv (no filtering needed)
- vLLM deployment

### 8.2 Model Deployment

```bash
# Terminal 1: Qwen3-30B-A3B-Instruct
vllm serve Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --host 0.0.0.0 --port 8000 \
  --dtype auto --gpu-memory-utilization 0.95 \
  --max-model-len 65536 --trust-remote-code

# Terminal 2: Qwen3-30B-A3B-Thinking
vllm serve Qwen/Qwen3-30B-A3B-Thinking-2507 \
  --host 0.0.0.0 --port 8000 \
  --dtype auto --gpu-memory-utilization 0.95 \
  --max-model-len 65536 --trust-remote-code
```

### 8.3 Execution Commands

```bash
# Zero-shot with Instruct model
python src/single_agent_code_generation.py SA-zero

# Few-shot with Instruct model
python src/single_agent_code_generation.py SA-few

# Zero-shot with Thinking model (update config for reasoning mode)
python src/single_agent_code_generation.py SA-zero

# Few-shot with Thinking model
python src/single_agent_code_generation.py SA-few
```

---

## 9. Data Collection Plan

### 9.1 File Structure

```
results/
├── phase3_code_gen/
│   ├── instruct_zero/
│   │   ├── Sa-zero_Qwen3-30B-A3B-Instruct_*_detailed_results.jsonl
│   │   ├── Sa-zero_Qwen3-30B-A3B-Instruct_*_evaluation.json
│   │   ├── Sa-zero_Qwen3-30B-A3B-Instruct_*_evaluation.txt
│   │   ├── Sa-zero_Qwen3-30B-A3B-Instruct_*_evaluated.csv
│   │   └── emissions.csv
│   ├── instruct_few/
│   │   └── [same structure]
│   ├── thinking_zero/
│   │   └── [same structure]
│   └── thinking_few/
│       └── [same structure]
```

### 9.2 Analysis Notebooks

**Create new notebooks** (following Phase 2a pattern):
1. `notebooks/rq1_phase3_code_generation_analysis.ipynb`
   - Pass@1 comparison across configurations
   - Per-problem difficulty analysis
   - Code quality metrics

2. `notebooks/rq1_phase3_codecarbon_analysis.ipynb`
   - Energy consumption breakdown
   - Token usage analysis
   - Energy-performance tradeoffs

3. `notebooks/rq1_cross_task_comparison.ipynb`
   - Vulnerability detection vs Code generation
   - Task-dependent reasoning advantage
   - Energy efficiency across tasks

---

## 10. Success Criteria

### 10.1 Minimum Viable Results

- ✅ All 4 experiments complete (2 models × 2 prompts)
- ✅ Pass@1 scores computed for all configurations
- ✅ Energy data collected via CodeCarbon
- ✅ Clear comparison: Thinking vs Instruct
- ✅ Clear comparison: Zero-shot vs Few-shot

### 10.2 Ideal Results

- ✅ All 164 problems evaluated successfully
- ✅ Token usage analysis complete
- ✅ Cross-task comparison (vuln detection vs code gen)
- ✅ Energy-performance tradeoff analysis
- ✅ Canonical few-shot examples validated

### 10.3 Key Research Questions Answered

1. **Does reasoning help code generation?**
   - Compare Thinking vs Instruct Pass@1
   - Expected: Thinking outperforms (based on vuln detection pattern)

2. **Does prompt quality matter for generation?**
   - Compare canonical few-shot vs zero-shot
   - Expected: Canonical examples improve performance

3. **Are energy tradeoffs similar across tasks?**
   - Compare energy/performance ratio
   - Expected: Thinking uses more energy but justifies with better Pass@1

4. **Does task type affect reasoning advantage?**
   - Compare vuln detection F1 gains vs code gen Pass@1 gains
   - Expected: Reasoning helps both, but magnitude may differ

---

## 11. Timeline

### Week 1: Preparation
- Day 1-2: Download HumanEval dataset
- Day 2-3: Design canonical few-shot examples
- Day 3: Update `config.py` with prompts
- Day 4: Review code generation script
- Day 5: Run Phase 3a validation (10 samples)

### Week 2: Execution
- Day 1-2: Run full Phase 3b experiments (4 configs)
- Day 3-4: Analysis notebooks and visualizations
- Day 5: Cross-task comparison

### Week 3: Documentation
- Day 1-2: Update ANALYSIS_SUMMARY.md
- Day 3: Write findings
- Day 4-5: Prepare visualizations for publication

**Total**: 3 weeks

---

## 12. Cost Estimation

**RunPod H100 80GB @ $3.50/hour**

**Phase 3a (Validation)**:
- 10 samples × 4 configs = 40 inferences
- Estimated: 0.5-1 hour total
- Cost: ~$3.50

**Phase 3b (Full Experiment)**:
- 164 samples × 4 configs = 656 inferences
- Estimated: 8-12 hours total (2-3 hours per config)
- Cost: ~$28-42

**Total Budget**: $35-50

**Cost Optimization**:
- Use spot instances: ~$15-25 total
- Run overnight for better availability

---

## 13. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Dataset download issues | High | Download and verify before experiments |
| Poor prompt quality | High | Run Phase 3a validation first |
| Test execution failures | Medium | Code extraction logic already tested |
| Pod interruptions | Medium | Incremental saving in JSONL format |
| Energy tracking issues | Low | Same infrastructure as Phase 2a (validated) |

---

## 14. Next Immediate Actions

### Priority 1: Dataset Preparation
1. ⬜ Download HumanEval dataset
2. ⬜ Verify dataset format matches expected schema
3. ⬜ Place in `vuln_database/HumanEval.jsonl`

### Priority 2: Prompt Design
1. ⬜ Design zero-shot prompt (basic instruction)
2. ⬜ Design canonical few-shot examples (3-5 examples)
3. ⬜ Validate examples are high-quality and domain-standard
4. ⬜ Add prompts to `config.py`

### Priority 3: Code Review
1. ⬜ Review `single_agent_code_generation.py` for reasoning mode support
2. ⬜ Verify it uses correct config variables
3. ⬜ Test prompt templating works correctly

### Priority 4: Validation
1. ⬜ Set up RunPod pod with Instruct model
2. ⬜ Run Phase 3a with 10 samples
3. ⬜ Verify evaluation completes successfully
4. ⬜ Assess prompt quality from outputs

---

## 15. Expected Outcomes

### 15.1 Performance Outcomes

**Hypothesis 1**: Thinking > Instruct
- Expected Pass@1 difference: +10-20%
- Rationale: Reasoning helped vuln detection (+15-20pp F1)

**Hypothesis 2**: Canonical Few-shot > Zero-shot
- Expected Pass@1 improvement: +5-15%
- Rationale: CWE prompts gave +6.9% to +31.7% F1 in vuln detection

**Hypothesis 3**: Scale patterns hold
- 30B MoE maintains energy efficiency
- Energy per token similar to vuln detection

### 15.2 Energy Outcomes

**Expected Energy Ratios**:
- Thinking / Instruct: ~3-4x energy (consistent with Phase 2a)
- Few-shot / Zero-shot: Slightly higher energy (more detailed outputs)

**Expected Efficiency**:
- 30B MoE: 1.2M-1.7M tokens/kWh (consistent with vuln detection)
- Energy per successful solution: Higher than per-sample (not all pass)

### 15.3 Research Contributions

1. ✅ First comparison of reasoning models on code generation with energy tracking
2. ✅ Cross-task validation (classification vs generation)
3. ✅ Canonical prompting strategy validated across tasks
4. ✅ Energy-performance tradeoffs quantified for both task types
5. ✅ Complete RQ1: Reasoning advantage demonstrated across 2 SE tasks

---

## 16. References

### HumanEval
- Paper: Evaluating Large Language Models Trained on Code (Chen et al., 2021)
- Dataset: https://github.com/openai/human-eval
- Evaluation: HuggingFace `code_eval` metric

### Evaluation Metric
- Code evaluation: https://huggingface.co/spaces/evaluate-metric/code_eval
- Pass@k definition: Chen et al. (2021)

### Related Work
- Phase 1: Qwen3-4B Vulnerability Detection
- Phase 2a: Qwen3-30B-A3B Vulnerability Detection
- Prompt Comparison: CWE-based canonical examples (+6.9% to +31.7% F1)

---

**Document Status**: Draft
**Last Updated**: 2025-11-06
**Next Review**: After Phase 3a validation
