# RQ3 Baseline Sampling: Explanation Quality from Thinking Models

## 1. Objective

RQ3 investigates how prompting styles impact explanation usefulness and faithfulness in LLM-based software engineering tasks. Before running new experiments with explicit prompting styles (no-explanation, explain-after, explain-before, evidence-bound), we first establish a **baseline assessment** of how well thinking models naturally produce explanations without explicit explanation prompting.

**Key constructs**: We evaluate two dimensions of explanation quality:
- **Usefulness**: Whether the explanation helps a human developer understand the model's decision well enough to verify, debug, or build upon it. A useful explanation identifies the relevant aspects of the input, articulates the reasoning chain, and provides actionable insight.
- **Faithfulness**: Whether the explanation accurately reflects the model's actual decision process, rather than being a plausible but post-hoc rationalization. A faithful explanation cites evidence that causally influenced the prediction, not merely evidence that is consistent with it.

This document records the sampling methodology, implementation, data quality findings, and a critical data gap discovered during the process.

## 2. Scope

- **Models**: Thinking models only -- Qwen3-4B-Thinking, Qwen3-30B-A3B-Thinking, Nemotron-Nano-8B, Nemotron-Super-49B
- **Design**: Single-Agent (SA) only, isolating model reasoning without multi-agent confounds
- **Prompting**: Both zero-shot and few-shot (existing experiment configurations)
- **Tasks**: Code generation (HumanEval), vulnerability detection (BigVul), log analysis (HDFS)

The baseline captures the "default" explanation behavior of thinking models when prompted with standard task instructions that include "Let's think step-by-step" but no structured explanation format requirements.

## 3. Sampling Methodology

### 3.1 Stratified Random Sampling

We employ stratified random sampling across model, prompting style, and SE task. Each unique combination of (task, model, prompting) defines a stratum. From each stratum, we draw 10 samples uniformly at random from the pool of **correctly predicted** entries, using a fixed random seed (42) for reproducibility.

**Sample size justification**: We select 10 samples per stratum as a pragmatic minimum that balances coverage across 16 strata with the manual evaluation burden of human annotation. With 160 total samples, each requiring careful reading and scoring of explanation text (median ~9,000 characters), the annotation effort is already substantial. The per-stratum count of 10 is sufficient for descriptive characterization of explanation quality within each stratum, though not for inferential statistical testing between individual strata. Cross-stratum comparisons (e.g., by model family or task) aggregate 40-80 samples, providing more statistical power.

**Rationale for sampling only correct predictions**: Explanation usefulness and faithfulness are most meaningfully evaluated when the model arrives at the right answer. An incorrect prediction with plausible-sounding reasoning would confound faithfulness assessment -- the explanation may be coherent but causally disconnected from the (wrong) decision. Restricting to correct predictions isolates explanation quality from task accuracy.

### 3.2 Correctness Criteria

| Task | Correctness Definition | Source |
|------|------------------------|--------|
| Code Generation | Generated code passes all HumanEval test cases | `*_evaluation.json` → `per_sample_results[].passed` |
| Vulnerability Detection | Parsed prediction matches `ground_truth` field (0=safe, 1=vulnerable) | Prediction extracted from `reasoning` field via pattern matching on "(1) YES" / "(2) NO" keywords |
| Log Analysis | Prediction matches ground truth label (Normal=0, Anomaly=1) | Pre-computed in `*_per_session_metrics.csv` → TP or TN entries |

### 3.3 Explanation Extraction

Thinking models produce extended reasoning in `<think>...</think>` blocks before the final answer. The extraction logic handles three observed formats:

1. **Full tags present** (`<think>content</think>`): Extract content between tags. Observed in Nemotron codegen and Nemotron-Super-49B vuln detection.
2. **Opening tag stripped** (`content</think>`): Extract everything before `</think>`. Observed in all Qwen thinking model outputs for vulnerability detection and log analysis.
3. **No tags present**: Use the full response text as the explanation. Observed in Nemotron-Nano-8B vulnerability detection (which produces structured reasoning without explicit think tags).

### 3.4 Exclusion Filters

Two categories of entries are excluded from the sampling pool:

1. **No model output**: Log analysis entries where `raw_output='NONE'` (~3 per stratum across all log analysis experiments). These represent inference failures with no explanation to evaluate.
2. **Non-response placeholders**: Vulnerability detection entries where explanation text is under 100 characters (e.g., "No response from agent"). These are pipeline failures, not genuine model explanations.

### 3.5 Truncation Flagging

For each task, we compute the 10th percentile of explanation length (in characters) across all sampled entries. Entries at or below this threshold are flagged as potentially truncated (`truncation_flag=True`). This serves as a quality signal for human raters -- flagged entries may contain incomplete reasoning chains that terminated prematurely due to token limits.

## 4. Strata and Sample Counts

### 4.1 Planned vs. Actual Design

The original design targeted ~200 samples across 20 strata (8 codegen + 8 vuln + 4 log). The initial yield was 160 samples across 16 strata due to a data gap in code generation (see Section 6). After rerunning the 4 Qwen codegen strata on 2026-02-07 with the corrected script, all 20 strata are now populated, yielding 200 samples.

### 4.2 Final Strata

| Task | Model | Prompting | Correct Available | Sampled |
|------|-------|-----------|-------------------|---------|
| **Code Generation** | Qwen3-4B-Thinking | few-shot | 160 | 10 |
| | Qwen3-4B-Thinking | zero-shot | 162 | 10 |
| | Qwen3-30B-A3B-Thinking | few-shot | 159 | 10 |
| | Qwen3-30B-A3B-Thinking | zero-shot | 161 | 10 |
| | Nemotron-Nano-8B | few-shot | 151 | 10 |
| | Nemotron-Nano-8B | zero-shot | 150 | 10 |
| | Nemotron-Super-49B | few-shot | 152 | 10 |
| | Nemotron-Super-49B | zero-shot | 123 | 10 |
| **Vulnerability Detection** | Qwen3-4B-Thinking | few-shot | 201 | 10 |
| | Qwen3-4B-Thinking | zero-shot | 193 | 10 |
| | Qwen3-30B-A3B-Thinking | few-shot | 194 | 10 |
| | Qwen3-30B-A3B-Thinking | zero-shot | 202 | 10 |
| | Nemotron-Nano-8B | few-shot | 188 | 10 |
| | Nemotron-Nano-8B | zero-shot | 194 | 10 |
| | Nemotron-Super-49B | few-shot | 210 | 10 |
| | Nemotron-Super-49B | zero-shot | 207 | 10 |
| **Log Analysis** | Qwen3-4B-Thinking | zero-shot | 11 | 10 |
| | Qwen3-4B-Thinking | few-shot | 10 | 10 |
| | Qwen3-30B-A3B-Thinking | zero-shot | 12 | 10 |
| | Qwen3-30B-A3B-Thinking | few-shot | 213 | 10 |
| | | | **Total** | **200** |

**Note on log analysis strata**: The Qwen3-4B-Thinking strata have very few correct predictions available (10-11 after filtering). In these cases, we sample all available entries. This exhaustive sampling within tight strata does not introduce bias but limits any future re-sampling.

### 4.3 Task Coverage by Model Family

|  | Qwen3-4B | Qwen3-30B | Nemotron-8B | Nemotron-49B |
|--|----------|-----------|-------------|--------------|
| Code Generation | zero + few | zero + few | zero + few | zero + few |
| Vulnerability Detection | zero + few | zero + few | zero + few | zero + few |
| Log Analysis | zero + few | zero + few | not conducted* | not conducted* |

\* **Not conducted**: No log analysis experiments were run with Nemotron models. The RQ2 cross-architecture study focused Nemotron on code generation and vulnerability detection, while log analysis used only Qwen models. This is a design boundary, not a data loss.

**Note on Qwen codegen strata**: The original Qwen codegen experiments (November 2025) did not save thinking content due to a script versioning issue (see Section 6). These 4 strata were rerun on 2026-02-07 with the corrected script, successfully recovering thinking content for all entries.

## 5. Output Artifacts

### 5.1 Files Produced

| File | Description |
|------|-------------|
| `results/rq3_baseline/rq3_baseline_samples.csv` | 200 sampled entries with explanation text and metadata |
| `results/rq3_baseline/rq3_sampling_summary.txt` | Per-stratum statistics (counts, lengths, flags) |
| `src/rq3_baseline_sampling.py` | Reproducible sampling script |

### 5.2 CSV Schema

| Column | Description |
|--------|-------------|
| `sample_id` | Sequential identifier (1-200) |
| `task` | `code_generation`, `vulnerability_detection`, or `log_analysis` |
| `model` | Model name |
| `parameters_b` | Model parameter count in billions |
| `prompting` | `zero-shot` or `few-shot` |
| `entry_id` | Task-specific identifier (HumanEval task ID, BigVul idx, HDFS block ID) |
| `ground_truth` | Ground truth label |
| `prediction` | Model's prediction |
| `is_correct` | Always `True` (by construction) |
| `explanation_text` | Extracted thinking/reasoning content |
| `explanation_length_chars` | Character count of explanation |
| `has_think_close_tag` | Whether `</think>` tag was present in raw output |
| `truncation_flag` | `True` if length is at or below the 10th percentile for the task |
| `usefulness_score` | Empty -- for human rater |
| `faithfulness_score` | Empty -- for human rater |
| `rater_notes` | Empty -- for human rater |

## 6. Data Gap: Qwen Code Generation Thinking Content

### 6.1 Discovery

During sampling, we discovered that all four Qwen thinking-model code generation result files (4B zero/few, 30B zero/few) contain **no reasoning or thinking content**. The JSONL fields are limited to `[task_id, prompt, entry_point, canonical_solution, test, generated_solution]`, with no `reasoning` field and no `<think>` tags embedded in `generated_solution`.

### 6.2 Root Cause Analysis

The root cause is a **script versioning issue** in the inference pipeline, not an API or model configuration problem.

**Timeline of events:**

1. The `single_agent_code_generation.py` script was inherited from the upstream repository (`merveast/agent-green`). The upstream version saves only `generated_solution` (extracted executable code) and discards the full model response.

2. The Qwen codegen experiments were run on **November 7, 2025** using commit `12d979a`, which had this result schema:
   ```python
   result = {
       'task_id': ..., 'prompt': ..., 'entry_point': ...,
       'canonical_solution': ..., 'test': ...
   }
   # Only result['generated_solution'] = extracted_code was added
   ```

3. The `reasoning` field was added on **November 22, 2025** in commit `bb54a9e` ("RQ3: Add explain-before support"), along with the `extract_code_and_explanation()` function.

4. The Nemotron codegen experiments were run on **December 9+, 2025**, using the post-fix version that saves `result['reasoning'] = response_text`. These results correctly contain the full thinking content.

**Why vulnerability detection was unaffected**: The `single_agent_vuln_detection.py` script was designed from the outset to save the full model response as `result['reasoning']`, because the reasoning text is the primary output for classification tasks (the prediction is parsed from it). This script was not inherited from the same upstream code path.

**Upstream status**: As of the latest upstream commit (`09e1ccb`, December 20, 2025), `merveast/agent-green` still does not save thinking content in any code generation script. The `dual_agent_code_generation.py` and `multi_agent_code_generation.py` scripts in the upstream repository actively strip `<think>` blocks via `re.sub(r'<think>.*?</think>', '', ...)`. No raw response is persisted anywhere upstream.

### 6.3 Irrecoverability

The thinking content is **unrecoverable** from existing result files. The `extract_code_from_response()` function discards everything before the first `def`/`import` statement or code block delimiter. The full `response_text` existed only as a local variable during inference and was never written to disk.

### 6.4 Remediation (Completed 2026-02-07)

The four affected strata were rerun on 2026-02-07 using the corrected script (post-commit `bb54a9e`) on RunPod H100 instances. The rerun results are stored alongside original results in `results/runpod_codegen/`:

| Rerun Result File | Model | Prompting | Pass@1 |
|-------------------|-------|-----------|--------|
| `SA-zero_Qwen-Qwen3-4B-Thinking-2507_20260207-090420_*` | 4B | zero-shot | 98.78% (162/164) |
| `SA-few_Qwen-Qwen3-4B-Thinking-2507_20260207-100729_*` | 4B | few-shot | 97.56% (160/164) |
| `SA-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20260207-095305_*` | 30B | zero-shot | 98.17% (161/164) |
| `SA-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20260207-105006_*` | 30B | few-shot | 96.95% (159/164) |

All rerun results contain the `reasoning` field with full thinking content. Pass@1 scores show minor variation from the original runs (within vLLM non-determinism), confirming functional equivalence. The original results remain the "official" performance records for RQ1/RQ2; the reruns serve exclusively for RQ3 thinking content recovery.

## 7. Explanation Characteristics

### 7.1 Length Distribution by Task

| Task | Min | Median | Mean | Max |
|------|-----|--------|------|-----|
| Code Generation | 1,247 | 6,763 | 8,572 | 31,367 |
| Vulnerability Detection | 1,314 | 10,411 | 10,840 | 31,846 |
| Log Analysis | 3,300 | 13,184 | 13,605 | 38,687 |

Log analysis explanations are longest on average, likely because the models narrate parsing of multi-line log sessions. Code generation explanations are shortest, as the thinking primarily covers algorithm planning rather than extended analysis.

### 7.2 Think Tag Presence

| Model | Code Gen | Vuln Detection | Log Analysis |
|-------|----------|----------------|--------------|
| Qwen3-4B-Thinking | `</think>` only (10/10) | `</think>` only (no `<think>`) | `</think>` only |
| Qwen3-30B-A3B-Thinking | `</think>` only (10/10) | `</think>` only | `</think>` only |
| Nemotron-Nano-8B | `<think>`+`</think>` | Neither tag | N/A |
| Nemotron-Super-49B | `<think>`+`</think>` | `<think>`+`</think>` | N/A |

**Observations**:
- Qwen thinking models consistently have `</think>` but not `<think>` across all tasks (codegen, vuln detection, log analysis). The opening tag was stripped during vLLM response processing or chat template application.
- Nemotron-Nano-8B produces structured reasoning for vulnerability detection without any think tags -- the model outputs step-by-step analysis in plain text.
- Nemotron-Super-49B zero-shot codegen has `</think>` in only 6 of 10 sampled entries, suggesting some responses may have been truncated before the thinking block completed or the model did not engage its thinking mode for simpler problems. The few-shot condition has `</think>` in all 10 sampled entries.

### 7.3 Truncation Flags

Overall, 20 of 200 samples (10.0%) were flagged as potentially truncated (at or below the 10th percentile length for their task). The distribution is concentrated in Nemotron-Nano-8B vulnerability detection strata, where explanations are substantially shorter (median ~2,100 chars) compared to other models (median 10,000-17,000 chars). This likely reflects a model capacity constraint rather than actual truncation -- the 8B model produces more concise reasoning.

## 8. Verification

The sampling script performs automated verification checks on every run:

| Check | Result |
|-------|--------|
| Within-stratum duplicates | 0 |
| Empty explanations | 0 |
| All is_correct = True | True |
| Minimum explanation length | 1,247 chars |

Cross-stratum duplicate entry IDs (same `task_id` or `idx` appearing in different model/prompting strata) are expected and valid -- they represent different models reasoning about the same input, which is the desired comparison.

## 9. Limitations

1. **Log analysis class imbalance**: The HDFS dataset has 373 Normal vs. 12 Anomaly sessions. Correct predictions are predominantly True Negatives (Normal predicted as Normal). The small anomaly set limits the diversity of correctly detected anomalies in the sample.

2. **Log analysis stratum saturation**: Two Qwen3-4B-Thinking log analysis strata had only 10-11 correct predictions with valid explanations. All available entries were sampled, leaving no room for alternative draws. Findings from these strata should be interpreted cautiously given the near-census nature of the sample.

3. **Prediction extraction reliability**: For vulnerability detection, predictions are extracted from free-text reasoning via keyword matching ("(1) YES", "(2) NO", etc.). This parser may misclassify ambiguous responses, though manual spot-checks of sampled entries confirmed correct extraction.

## 10. Next Steps

1. **Develop annotation guidelines**: Define scoring rubrics for usefulness and faithfulness with concrete examples and boundary cases for each task. The rubrics should specify what constitutes each score level and include calibration examples for rater training.

2. **Human rater review**: Distribute the 200 samples to human raters for usefulness and faithfulness scoring using the empty columns in the output CSV. To assess annotation reliability, a subset of samples (minimum 20%, i.e., 40+ samples) should be independently scored by at least two raters. Inter-rater agreement should be measured using Cohen's kappa (for categorical bins) or intraclass correlation coefficient (for ordinal/continuous scores), with disagreements resolved through discussion.

3. **Baseline comparison**: Use baseline scores to calibrate expectations for the RQ3 prompting style experiments (no-explanation, explain-after, explain-before, evidence-bound).
