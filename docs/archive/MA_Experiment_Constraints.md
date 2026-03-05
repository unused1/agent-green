# Multi-Agent Experiment Constraints and Limitations

**Date**: January 4, 2026
**Context**: Nemotron-8B Multi-Agent Vulnerability Detection Experiments

---

## Overview

During the Multi-Agent (MA) vulnerability detection experiments with Nemotron-8B, certain samples failed to complete execution. This document analyzes the root causes, quantifies the impact, and documents findings from targeted reruns with extended context.

---

## Constraint 1: Context Window Overflow (64K Limit)

### Description
The MA 4-agent pipeline involves multi-turn conversations between:
1. **Security Researcher** - Analyzes code for vulnerabilities
2. **Code Author** - Responds to security findings
3. **Moderator** - Summarizes the discussion
4. **Review Board** - Makes final vulnerability decision

Each agent's response accumulates in the context window. For samples with long source code functions, the cumulative context can exceed the 64K token limit configured for vLLM.

### Context Accumulation Mechanism

**Important**: Function length in characters does not directly determine if context will overflow. Context accumulates across all 4 phases:

```
Phase 1 (Security Researcher):
  Input:  System prompt + Task prompt + Code
  Output: Security analysis (~2-5K tokens)

Phase 2 (Code Author):
  Input:  System prompt + Task prompt + Code + Researcher findings
  Output: Author response (~2-5K tokens)

Phase 3 (Moderator):
  Input:  System prompt + Task prompt + Researcher + Author responses
  Output: Moderator summary (~1-3K tokens)

Phase 4 (Review Board):
  Input:  System prompt + Task prompt + Code + Researcher + Author + Moderator
  Output: Final decision (~1-2K tokens)
```

**Example calculation for a 32K-char function:**
- Original code: ~10K tokens (1 token ≈ 3-4 chars)
- Security Researcher response: ~5K tokens
- Code Author response: ~5K tokens
- Moderator summary: ~3K tokens
- System/task prompts: ~2K tokens
- **Total by Phase 4: ~25-40K tokens**

In Thinking mode, each agent produces longer reasoning traces (can be 2-3x longer), easily pushing total context beyond 64K tokens even for moderately-sized functions.

### Impact
When context overflow occurs:
1. The vLLM server returns an error or crashes
2. The experiment script terminates
3. On resume, the `auto_resume_ma_vuln.sh` script automatically skips the problematic sample
4. A placeholder record is written with `skipped=true`, `error=USER_SKIP`, `vuln=-1`

### Observed Failure Rates (64K Context)

| Experiment | Skipped Samples | Skip Rate | Mode |
|------------|-----------------|-----------|------|
| MA-few Instruct | 17/384 | 4.4% | Instruct |
| MA-zero Instruct | 25/384 | 6.5% | Instruct |
| MA-few Think | 34/384 | 8.9% | Thinking |
| MA-zero Think | 39/384 | 10.2% | Thinking |

**Key Observation**: Thinking mode has ~2x higher skip rate than Instruct mode due to longer reasoning traces in agent responses.

---

## Constraint 2: API Timeout

### Description
Even when context is sufficient, some samples with very long functions take extended time to process through all 4 agents. The OpenAI-compatible API has a default timeout that can be exceeded.

### Error Message
```
OpenAI API call timed out. This could be due to congestion or too small
a timeout value. The timeout can be specified by setting the 'timeout'
value (in seconds) in the llm_config.
```

### Impact
- Sample fails with `vuln=-1` and error recorded
- Different from context overflow (no crash, just timeout)

---

## Experiment: Extended Context (128K) Rerun

### Objective
Test whether increasing context window from 64K to 128K allows previously-skipped samples to complete.

### Configuration
- **Model**: Nemotron-Nano-8B
- **vLLM max-model-len**: 131072 (128K tokens)
- **Experiment**: MA-few Instruct (17 skipped samples)
- **Test subset**: 3 samples (limit for initial validation)

### Results

| Sample ID | Project | Function Length | 64K Result | 128K Result |
|-----------|---------|-----------------|------------|-------------|
| 299319 | ImageMagick | 6,690 chars | SKIPPED | ✅ SUCCESS (vuln=1) |
| 411926 | heimdal | 31,969 chars | SKIPPED | ✅ SUCCESS (vuln=1) |
| 292609 | puma | 19,424 chars | SKIPPED | ❌ TIMEOUT |

### Summary
- **Success Rate**: 2/3 (66.7%)
- **Emissions**: 0.221 kg CO2
- **Duration**: ~1.5 hours for 3 samples

### Key Findings

1. **128K context resolves most overflow issues**: Even the longest function (31,969 chars ≈ 10K tokens) completed successfully. With 4-agent context accumulation, this sample likely required ~40-50K tokens total, which fits within 128K but exceeded 64K.

2. **Timeout is a separate constraint**: Sample 292609 failed due to API timeout, not context overflow. This requires adjusting timeout settings rather than context length.

3. **Function length is not the only factor**: The 31,969-char sample succeeded while the 19,424-char sample timed out, suggesting that code complexity and agent response lengths also matter.

---

## Skipped Sample Characteristics

### Function Length Distribution (MA-few Instruct, 17 skipped samples)
```
Sample 411926: 31,969 chars (heimdal)     - Longest
Sample 292609: 19,424 chars (puma)
Sample 299319:  6,690 chars (ImageMagick)
Sample 389760:  4,234 chars (jasper)
Sample 289293:  2,969 chars (linux)
... (12 more samples)
```

### Common Projects with Skipped Samples
- ImageMagick (complex image processing code)
- heimdal (Kerberos implementation)
- linux kernel (system-level code)
- puma (Ruby web server)

---

## Implications for Research

### 1. Sample Coverage
- With 64K context: ~4-10% of samples are skipped (depending on mode)
- With 128K context: Estimated <2% would be skipped (based on preliminary test)
- Skipped samples are marked with `vuln=-1` and excluded from accuracy calculations

### 2. Reproducibility
- Skipped samples are deterministic: the same samples fail every run
- Rerun verification (Jan 3, 2026) confirmed 100% reproducibility

### 3. Bias Considerations
- Skipped samples tend to have longer/more complex functions
- These may represent a specific subset of vulnerabilities (e.g., complex parsing code)
- This could introduce selection bias in vulnerability detection results

### 4. Energy Consumption
- Context overflow causes crashes and restarts, increasing energy consumption
- MA experiments required 18-40 sessions due to these crashes
- Extended context (128K) would reduce crashes but increase per-sample energy

---

## Files and Artifacts

### Original Experiment Results
```
results/rq2_cross_architecture/nemotron_8b_vuln_MA-few_instruct/
results/rq2_cross_architecture/nemotron_8b_vuln_MA-zero_instruct/
results/rq2_cross_architecture/nemotron_8b_vuln_MA-few_think/
results/rq2_cross_architecture/nemotron_8b_vuln_MA-zero_think/
```

### Extended Context Test Results
```
results/context_overflow_test/
├── rerun_few_instruct_20260104-042043.jsonl      # Detailed results
├── rerun_few_instruct_20260104-042043_summary.json
└── emissions.csv
```

### Rerun Script
```
scripts/rerun_skipped_samples.py
```

---

## Cross-Model Comparison: Skip Rates

### Skip Rates by Model and Architecture

| Model | Architecture | Experiment Type | Skip Rate | Notes |
|-------|--------------|-----------------|-----------|-------|
| **Nemotron 8B** | MA | Vuln Detection | 4.4-10.2% | Highest skip rates |
| **Nemotron 49B** | MA | Vuln Detection | 0.3-1.6% | Much lower |
| **Nemotron 8B/49B** | DA/SA | Vuln Detection | 0.8-3.6% | Lower than MA |
| **Qwen3 4B/30B** | All | All | 0% | No skipped samples |

### Key Observations
1. Context overflow is primarily a **Nemotron 8B MA** issue
2. Larger models (49B) have lower skip rates, possibly due to more efficient tokenization or shorter responses
3. Qwen3 experiments completed without context overflow issues
4. Multi-Agent has higher skip rates than Dual-Agent/Single-Agent due to more conversation turns

---

## Proposed Approach for Research Validity

> **Status**: Pending discussion with research supervisors

### Challenge
How to handle skipped samples without introducing bias or threatening research validity?

### Options Considered

| Option | Approach | Description |
|--------|----------|-------------|
| **Option 1** | Document as Limitation | Keep 64K results as-is, document skip rates as known limitation |
| **Option 2** | Merge Reruns | Re-run failed samples with 128K, merge into primary results |
| **Option 3** | Two-Part Presentation | Primary (64K) + Supplementary (128K) reported separately |
| **Option 4** | Full Re-run | Re-run ALL experiments with 128K context |

---

### Option 1: Document as Limitation (Conservative)

**Approach**: Keep all results from 64K experiments as-is. Document skip rates as a known limitation.

**Pros**:
- Simple, no additional experiments needed
- Consistent experimental conditions across all samples
- Common practice in ML research

**Cons**:
- 4-10% of samples excluded from analysis
- Potential selection bias unexplored (are skipped samples different?)
- Reviewers may question missing data

**When to choose**: If skip rates are deemed acceptable and bias analysis shows no systematic differences.

---

### Option 2: Merge Reruns into Primary Results

**Approach**: Re-run failed samples with 128K context, then replace placeholder records (`vuln=-1`) with successful results in the primary dataset.

**Pros**:
- Higher sample coverage (potentially 100%)
- Single unified result set

**Cons**:
- **Threat to validity**: Different samples run under different conditions
- Mixed experimental setup (some 64K, some 128K)
- Energy consumption not comparable across samples
- Reviewers may criticize inconsistent methodology

**When to choose**: Generally not recommended due to validity concerns.

---

### Option 3: Two-Part Results Presentation (Recommended)

**Approach**: Keep primary results (64K) separate from supplementary recovery results (128K). Present both transparently.

**Pros**:
- **Maintains internal validity**: Primary results have consistent conditions
- **Transparent**: Limitations clearly documented, not hidden
- **Enables analysis**: Can compare skipped vs completed samples
- **Sensitivity check**: Shows whether conclusions change with recovered samples
- Reviewers can see full picture

**Cons**:
- More complex presentation in thesis/paper
- Requires additional experiments for recovery
- Two sets of results to explain

**When to choose**: When transparency and research rigor are priorities.

---

### Option 4: Full Re-run with 128K Context

**Approach**: Re-run ALL Nemotron experiments (not just failed samples) with 128K context from scratch.

**Pros**:
- Consistent conditions across all samples
- Maximum sample coverage
- Clean, unified dataset

**Cons**:
- **Expensive**: ~$50-100 in compute costs
- **Time-consuming**: Days of GPU time
- Changes energy consumption baseline (128K uses more memory/energy)
- May not be necessary if skip rate is acceptable

**When to choose**: If budget allows and consistent 128K conditions are preferred over 64K.

---

### Recommended: Option 3 (Two-Part Presentation)

#### Part 1: Primary Results (64K Context - Consistent Conditions)
- All experiments evaluated under identical 64K context limit
- Skip rates clearly reported per experiment (Table in Section "Observed Failure Rates")
- Accuracy calculated on completed samples only
- This maintains internal validity with consistent experimental conditions

#### Part 2: Supplementary Analysis (128K Context - Recovery)
- Re-run **only** the skipped samples with extended context (128K) and timeout
- Keep results in separate folder: `results/context_overflow_recovery/`
- Report:
  - Recovery rate (how many previously-skipped samples now complete)
  - Predictions for recovered samples
  - Comparison with primary results

#### Part 3: Combined Sensitivity Analysis
- Compare characteristics of skipped vs completed samples:
  - Function length distribution
  - Vulnerability rate (are skipped samples more/less likely to be vulnerable?)
  - Project types and CWE categories
- Answer: "Does including recovered samples change the conclusions?"
- Statistical comparison of patterns (e.g., Thinking vs Instruct mode)

### Proposed File Structure

```
results/
├── rq2_cross_architecture/              # Primary Results (64K)
│   └── nemotron_8b_vuln_MA-*/
│       └── *_detailed_results.jsonl      # Original, vuln=-1 for skipped
│
├── context_overflow_recovery/            # Supplementary (128K)
│   ├── nemotron_8b_vuln_MA-few_instruct/
│   │   └── recovered_samples.jsonl       # Only recovered samples
│   ├── nemotron_8b_vuln_MA-zero_instruct/
│   ├── nemotron_8b_vuln_MA-few_think/
│   └── nemotron_8b_vuln_MA-zero_think/
│
└── analysis/
    └── sensitivity_analysis/
        ├── skipped_vs_completed_comparison.csv
        └── combined_accuracy_analysis.csv
```

### Advantages of This Approach
1. **Transparency**: Clear separation of primary and supplementary results
2. **No hidden limitations**: Skip rates documented, not masked
3. **Research questions addressed**:
   - Do skipped samples have different characteristics?
   - Does recovery change conclusions?
4. **Maintains validity**: Primary results have consistent conditions
5. **Enables sensitivity analysis**: Can quantify impact of missing samples

### Estimated Effort for Full Recovery
- **Samples to recover**: 17 + 25 + 34 + 39 = 115 samples (some overlap)
- **Unique samples**: ~80-100 (estimated after deduplication)
- **Time**: ~1-2 hours per experiment (based on preliminary test)
- **Cost**: ~$10-15 RunPod compute

---

## Discussion Points for Supervisors

### Questions to Resolve

1. **Is the proposed two-part presentation acceptable for the thesis/paper?**
   - Primary results (64K) as main findings
   - Supplementary analysis (128K) as sensitivity check

2. **Should we re-run ALL Nemotron experiments with 128K for consistency?**
   - Pro: Consistent conditions across all samples
   - Con: Higher cost, changes energy consumption baseline

3. **How to handle the timeout issue?**
   - Some samples fail due to timeout, not context
   - Should we increase timeout or document as separate limitation?

4. **Is the skip rate (4-10%) acceptable for publication?**
   - Common practice: Document and exclude from accuracy calculation
   - Alternative: Report accuracy with and without skipped samples

5. **Should we analyze bias in skipped samples before proceeding?**
   - Check if skipped samples have different vulnerability rates
   - This would inform whether recovery is necessary

---

## Next Steps (Pending Approval)

1. [ ] Discuss approach with supervisors
2. [ ] If approved: Extend `rerun_skipped_samples.py` for all 4 MA experiments
3. [ ] Run recovery experiments with 128K context
4. [ ] Create analysis script for comparing primary vs recovered samples
5. [ ] Update thesis/paper with two-part results presentation

---

## References

- Commit c8793c6: Extraction bug fix for markdown-wrapped JSON
- Results README: `results/README.md` (Context Overflow Skips section)
- RunPod Setup Guide: `docs/RunPod_Nemotron_8B_MA_Setup_Guide.md`
