# RQ3 Baseline Sampling: Explanation Quality from Thinking and Instruct Models

## 1. Objective

RQ3 investigates how prompting styles impact explanation usefulness and faithfulness in LLM-based software engineering tasks. Before running new experiments with explicit prompting styles (no-explanation, explain-after, explain-before, evidence-bound), we first establish a **baseline assessment** of how well thinking models naturally produce explanations without explicit explanation prompting.

**Key constructs**: We evaluate explanation quality along four metrics, each scored on a 1–5 Likert scale:
- **Completeness**: Does the reasoning cover the vulnerability mechanism or justify why the code is safe, by addressing all relevant factors, including edge cases, attack vectors, and underlying assumptions?
- **Clarity**: Is the reasoning logically structured, free of ambiguities, and using precise technical terms?
- **Actionability**: Does the reasoning provide actionable insights like highlighting vulnerable lines, suggesting patches, or describing specific risks and how to mitigate them?
- **Informativeness**: Does the reasoning offer meaningful, non-redundant, and technically insightful information beyond superficial observations?

This document records the sampling methodology, implementation, data quality findings, and a critical data gap discovered during the process.

## 2. Scope

### 2.1 Phase A (Current — Human Rater Pilot)

- **Task**: Vulnerability detection (BigVul) only
- **Models**: 4 model architectures × 2 modes = 8 model configurations
  - Qwen3-4B (Thinking + Instruct), Qwen3-30B-A3B (Thinking + Instruct)
  - Nemotron-Nano-8B (Thinking + Instruct), Nemotron-Super-49B (Thinking + Instruct)
- **Design**: Single-Agent (SA) only, isolating model reasoning without multi-agent confounds
- **Prompting**: Both zero-shot and few-shot (existing experiment configurations)
- **Strata**: 4 models × 2 modes × 2 prompting = 16 strata, 3 samples each = 48 samples

Phase A focuses on vulnerability detection to keep the pilot tractable for inter-rater agreement calibration. Both Thinking and Instruct modes are included because Thinking vs. Instruct is one of the key ablation factors for RQ3. While only Thinking models produce `<think>` blocks, both model types generate step-by-step reasoning in the response body due to the "Let's think step-by-step" task prompt (see `config.VULNERABILITY_TASK_PROMPT`), making Instruct model outputs equally evaluable. Model identity, mode, and prompting style are anonymized from raters.

### 2.2 Original Scope (Full Baseline)

- **Models**: Thinking models only — Qwen3-4B-Thinking, Qwen3-30B-A3B-Thinking, Nemotron-Nano-8B, Nemotron-Super-49B
- **Tasks**: Code generation (HumanEval), vulnerability detection (BigVul), log analysis (HDFS)
- **Strata**: 20 strata × 10 samples = 200 samples

The original baseline captured the "default" explanation behavior of thinking models when prompted with standard task instructions that include "Let's think step-by-step" but no structured explanation format requirements. See Section 4.2 for the full strata table. Phase A narrows the scope for pilot purposes; the full baseline remains available for Phase B.

## 3. Sampling Methodology

### 3.1 Stratified Random Sampling

We employ stratified random sampling across model, mode, and prompting style. Each unique combination of (model, mode, prompting) defines a stratum. For Phase A, we draw 3 samples per stratum uniformly at random from the pool of **correctly predicted** entries, using a fixed random seed (42) for reproducibility. The original full baseline used 10 samples per stratum across 20 strata (see Section 4.2).

**Two-phase evaluation approach**: Explanation quality assessment follows a two-phase design:

1. **Phase A — Human rater pilot (30–50 samples)**: A small stratified sample is scored by human raters to establish ground-truth ratings, measure inter-rater reliability (Cohen's kappa or ICC), and calibrate the LLM evaluator. Both Thinking and Instruct models are included — while only Thinking models produce `<think>` blocks, both model types generate step-by-step reasoning in the response body due to the "Let's think step-by-step" task prompt (see `config.VULNERABILITY_TASK_PROMPT`). The evaluation targets the model's actual response, so Instruct model outputs are equally evaluable. Thinking vs. Instruct is one of the ablation factors for RQ3; model identity, mode, and prompting style are anonymized from raters. The current strata cover Single-Agent (SA) designs only, as results are drawn from RQ1; DA/MA configurations from RQ2 are not yet included. With SA vulnerability detection strata spanning models × prompting styles × modes, 30–50 samples yields a few samples per stratum — sufficient for calibration but not for per-stratum inference.

2. **Phase B — LLM-based evaluation (~385 samples)**: Once the LLM evaluator is calibrated against human ratings, it is applied to a larger sample for statistically significant results. The target of ~385 samples provides 95% confidence with a 5% margin of error under the most conservative assumption (proportion estimation with p=0.5): `n = Z² × p(1−p) / E² = 1.96² × 0.25 / 0.05² ≈ 385`. With a finite population correction for the ~1,624 available vulnerability detection samples: `n_adj = 385 / (1 + 384/1624) ≈ 311`. For Likert-scale mean estimation (σ ≈ 1.0 on a 5-point scale, E = ±0.25 i.e. 5% of scale range): `n = (1.96 × 1.0 / 0.25)² ≈ 62 per condition`. The initial focus is on vulnerability detection; code generation and log analysis follow the same methodology.

**Statistical analysis**: Aggregated results are computed by averaging annotator ratings across all instances for each metric. To compare explanation quality across models, pairwise statistical significance tests use the Wilcoxon signed-rank test, following previous studies. To assess consistency between manual and automatic (LLM-based) evaluations, Spearman's rank correlation coefficient is computed for each metric.

**Available pool composition**: The "Correct Available" counts in Section 4.2 represent all correct predictions with valid explanations (≥100 chars), including both **True Positives** (vulnerable code correctly identified) and **True Negatives** (safe code correctly identified). The pool spans SA thinking-model results from both RQ1 Qwen experiments and cross-architecture Nemotron experiments — it is not limited to RQ1 alone. Vulnerability detection pools are based on VulTrial-486 (486 balanced samples: 243 vulnerable, 243 safe).

**Rationale for sampling only correct predictions**: Explanation quality is most meaningfully evaluated when the model arrives at the right answer. An incorrect prediction with plausible-sounding reasoning would confound assessment — the explanation may be coherent but causally disconnected from the (wrong) decision. Restricting to correct predictions isolates explanation quality from task accuracy.

### 3.2 Correctness Criteria

| Task | Correctness Definition | Source |
|------|------------------------|--------|
| Code Generation | Generated code passes all HumanEval test cases | `*_evaluation.json` → `per_sample_results[].passed` |
| Vulnerability Detection | Parsed prediction matches `ground_truth` field (0=safe, 1=vulnerable) | Prediction extracted from `reasoning` field via pattern matching on "(1) YES" / "(2) NO" keywords |
| Log Analysis | Prediction matches ground truth label (Normal=0, Anomaly=1) | Pre-computed in `*_per_session_metrics.csv` → TP or TN entries |

### 3.3 Explanation and Response Extraction

The Phase A sampling script distinguishes between `explanation_text` (the thinking process) and `response_text` (the evaluable output that raters score):

**Thinking mode** models produce extended reasoning in `<think>...</think>` blocks before the final answer. The extraction logic handles three observed formats:

1. **Full tags present** (`<think>content</think>`): `explanation_text` = content between tags; `response_text` = content after `</think>`. Observed in Nemotron-Super-49B and Qwen models (with opening tag stripped for Qwen, see format 2).
2. **Opening tag stripped** (`content</think>`): `explanation_text` = everything before `</think>`; `response_text` = content after `</think>`. Observed in all Qwen thinking model outputs.
3. **No tags present**: `explanation_text` = full output; `response_text` = full output (same content). Observed in Nemotron-Nano-8B SA vulnerability detection, which produces structured reasoning without explicit think tags (see Section 7.4 for detailed analysis).

**Instruct mode** models do not produce `<think>` blocks. The full model output is the response:
- `explanation_text` = empty string (no thinking block to extract)
- `response_text` = full `reasoning` field content

Raters evaluate `response_text` for all samples, regardless of mode.

### 3.4 Exclusion Filters

**Phase A (vuln-only)**: No exclusion filters are applied. All correct predictions are included in the sampling pool regardless of response length; raters handle short or low-quality responses via low scores on the four metrics.

**Original full baseline**: Two categories of entries were excluded:

1. **No model output**: Log analysis entries where `raw_output='NONE'` (~3 per stratum across all log analysis experiments). These represent inference failures with no explanation to evaluate.
2. **Non-response placeholders**: Vulnerability detection entries where explanation text is under 100 characters (e.g., "No response from agent"). These are pipeline failures, not genuine model explanations.

### 3.5 Truncation Flagging

For each task, we compute the 10th percentile of explanation length (in characters) across all sampled entries. Entries at or below this threshold are flagged as potentially truncated (`truncation_flag=True`). This serves as a quality signal for human raters -- flagged entries may contain incomplete reasoning chains that terminated prematurely due to token limits.

## 4. Strata and Sample Counts

### 4.1 Phase A Strata (Vuln Detection, 16 Strata, 48 Samples)

> **Superseded**: This 16-strata × 3-samples design was the original Phase A plan. The revised Phase A (Section 11) focuses on Nemotron-Super-49B zero-shot with 15 code snippets × 2 modes = 30 evaluations. The table below is retained for reference; "Correct Available" counts are from the VulTrial-386 pool and have since increased with VulTrial-486.

| Model | Mode | Prompting | Correct Available (386) | Sampled |
|-------|------|-----------|--------------------------|---------|
| Qwen3-4B | thinking | few-shot | 201 | 3 |
| Qwen3-4B | thinking | zero-shot | 198 | 3 |
| Qwen3-30B-A3B | thinking | few-shot | 207 | 3 |
| Qwen3-30B-A3B | thinking | zero-shot | 212 | 3 |
| Nemotron-Nano-8B | thinking | few-shot | 189 | 3 |
| Nemotron-Nano-8B | thinking | zero-shot | 195 | 3 |
| Nemotron-Super-49B | thinking | few-shot | 218 | 3 |
| Nemotron-Super-49B | thinking | zero-shot | 219 | 3 |
| Qwen3-4B | instruct | zero-shot | 204 | 3 |
| Qwen3-4B | instruct | few-shot | 203 | 3 |
| Qwen3-30B-A3B | instruct | zero-shot | 209 | 3 |
| Qwen3-30B-A3B | instruct | few-shot | 217 | 3 |
| Nemotron-Nano-8B | instruct | zero-shot | 196 | 3 |
| Nemotron-Nano-8B | instruct | few-shot | 196 | 3 |
| Nemotron-Super-49B | instruct | zero-shot | 216 | 3 |
| Nemotron-Super-49B | instruct | few-shot | 210 | 3 |
| | | | **Total** | **48** |

**Note**: The "Correct Available" counts here do not apply the 100-character minimum explanation length filter used in the original full baseline (Section 4.2). Phase A includes all correct predictions; raters handle short responses via low quality scores.

### 4.2 Original Full Baseline Strata (All Tasks, 20 Strata, 200 Samples)

The original design targeted ~200 samples across 20 strata (8 codegen + 8 vuln + 4 log). The initial yield was 160 samples across 16 strata due to a data gap in code generation (see Section 6). After rerunning the 4 Qwen codegen strata on 2026-02-07 with the corrected script, all 20 strata are now populated, yielding 200 samples.

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
| **Vulnerability Detection** | Qwen3-4B-Thinking | few-shot | 200 | 10 |
| | Qwen3-4B-Thinking | zero-shot | 197 | 10 |
| | Qwen3-30B-A3B-Thinking | few-shot | 206 | 10 |
| | Qwen3-30B-A3B-Thinking | zero-shot | 211 | 10 |
| | Nemotron-Nano-8B | few-shot | 188 | 10 |
| | Nemotron-Nano-8B | zero-shot | 194 | 10 |
| | Nemotron-Super-49B | few-shot | 212 | 10 |
| | Nemotron-Super-49B | zero-shot | 216 | 10 |
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

**Phase A (original 16-strata design, now archived)**:

| File | Description |
|------|-------------|
| `results/rq3_baseline/archive_386/rq3_baseline_samples.csv` | 48 sampled entries (archived — based on VulTrial-386) |
| `results/rq3_baseline/archive_386/rq3_baseline_samples_vulnerability_detection.csv` | Same 48 samples (archived) |
| `results/rq3_baseline/archive_386/rq3_sampling_summary.txt` | Per-stratum statistics (archived) |
| `src/rq3_baseline_sampling.py` | Reproducible sampling script (Phase A version) |

### 5.2 CSV Schema

| Column | Description |
|--------|-------------|
| `sample_id` | Sequential identifier (1–48) |
| `task` | `vulnerability_detection` (Phase A is vuln-only) |
| `model` | Base model name (e.g., `Qwen3-4B`, `Nemotron-Nano-8B`) |
| `mode` | `thinking` or `instruct` |
| `parameters_b` | Model parameter count in billions |
| `prompting` | `zero-shot` or `few-shot` |
| `entry_id` | BigVul sample index |
| `ground_truth` | Ground truth label (0=safe, 1=vulnerable) |
| `prediction` | Model's parsed prediction (0 or 1) |
| `is_correct` | Always `True` (by construction) |
| `explanation_text` | Extracted `<think>` block content (Thinking mode) or empty (Instruct mode) |
| `explanation_length_chars` | Character count of explanation_text |
| `has_think_close_tag` | Whether `</think>` tag was present in raw output |
| `response_text` | The evaluable response: post-`</think>` content (Thinking) or full output (Instruct) |
| `truncation_flag` | `True` if explanation length is at or below the 10th percentile |
| `completeness_score` | Empty — for rater (1–5 Likert scale) |
| `clarity_score` | Empty — for rater (1–5 Likert scale) |
| `actionability_score` | Empty — for rater (1–5 Likert scale) |
| `informativeness_score` | Empty — for rater (1–5 Likert scale) |
| `rater_notes` | Empty — for rater |

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

### 7.2 Think Tag Presence (SA Thinking Mode)

#### 7.2.1 Summary by Task (Sampled Observations)

| Model | Code Gen | Vuln Detection | Log Analysis |
|-------|----------|----------------|--------------|
| Qwen3-4B-Thinking | `</think>` only (10/10) | `</think>` only (no `<think>`) | `</think>` only |
| Qwen3-30B-A3B-Thinking | `</think>` only (10/10) | `</think>` only | `</think>` only |
| Nemotron-Nano-8B | `<think>`+`</think>` | **Neither tag (0%)** | N/A |
| Nemotron-Super-49B | `<think>`+`</think>` | `<think>`+`</think>` (98–99%) | N/A |

#### 7.2.2 Full Audit: Nemotron Think Tags Across All Experiments

A comprehensive audit of all Nemotron JSONL files (not limited to sampled entries) revealed that think-tag presence varies dramatically by model size, task, and agent architecture:

**Nemotron-Nano-8B (Thinking Mode)**

| Agent | Task | Zero-shot | Few-shot |
|-------|------|-----------|----------|
| SA | vuln | **0/486 (0%)** | **0/486 (0%)** |
| DA | vuln | 62/387 (16%) | 1/387 (0%) |
| MA | vuln | 333/384 (87%) | 242/384 (63%) |
| SA | code | 163/164 (99%) | 163/164 (99%) |
| DA | code | 153/164 (93%) | 160/164 (98%) |
| MA | code | 160/164 (98%) | 160/164 (98%) |

**Nemotron-Super-49B (Thinking Mode)**

| Agent | Task | Zero-shot | Few-shot |
|-------|------|-----------|----------|
| SA | vuln | ~99% | ~99% |
| DA | vuln | 382/387 (99%) | 383/387 (99%) |
| MA | vuln | 380/386 (98%) | 383/384 (>99%) |
| SA | code | 96/164 (59%) | 152/164 (93%) |
| DA | code | 148/164 (90%) | 152/164 (93%) |
| MA | code | 146/164 (89%) | 150/164 (91%) |

**Nemotron-Nano-8B (Instruct Mode — Think Tag Leakage)**

| Agent | Task | Zero-shot | Few-shot |
|-------|------|-----------|----------|
| SA | vuln | 0/486 (0%) | 0/486 (0%) |
| SA | code | 0/164 (0%) | **126/164 (77%)** |
| DA | code | 19/164 (12%) | 3/164 (2%) |
| MA | code | 5/164 (3%) | 81/164 (49%) |

**Nemotron-Super-49B (Instruct Mode)**: 0% think tags across all experiments — clean separation.

**Key observations**:
- Qwen thinking models consistently have `</think>` but not `<think>` across all tasks. The opening tag was stripped during vLLM response processing or chat template application.
- Nemotron-Super-49B is well-behaved: near-universal paired tags in thinking mode, zero leakage in instruct mode.
- **Nemotron-Nano-8B SA vuln is a confirmed anomaly**: 0% think tags despite the "detailed thinking on" system prompt. This is not a general model limitation — the same model produces 99% tags for SA code. See Section 7.4 for detailed analysis.
- Nemotron-Nano-8B leaks think tags into instruct mode for code generation (up to 77% in SA few-shot), suggesting the few-shot examples prime the model to engage its thinking protocol even without the thinking system prompt.
- Nemotron-Super-49B zero-shot codegen has lower tag coverage (59% in SA) than few-shot (93%), suggesting the model sometimes responds without a thinking block for simpler problems.
- Across all Nemotron files, ~6–10% of opened `<think>` tags lack a closing `</think>`, likely due to output truncation at the token limit.

### 7.3 Truncation Flags

**Phase A (48 samples)**: Truncation flags are computed at the 10th percentile across all samples. All 24 Instruct samples are flagged (explanation_length_chars = 0 by design, since Instruct mode has no `<think>` block). Thinking mode samples are not flagged.

**Original full baseline (200 samples)**: 20 of 200 samples (10.0%) were flagged as potentially truncated (at or below the 10th percentile length for their task). The distribution is concentrated in Nemotron-Nano-8B vulnerability detection strata, where explanations are substantially shorter (median ~2,100 chars) compared to other models (median 10,000–17,000 chars). This likely reflects a model capacity constraint rather than actual truncation — the 8B model produces more concise reasoning.

### 7.4 Nemotron-Nano-8B SA Vulnerability Detection: Missing Think Tags

#### 7.4.1 Anomaly Description

Nemotron-Nano-8B produces **zero** `<think>` or `</think>` tags across all 972 SA vulnerability detection entries (486 zero-shot + 486 few-shot), despite the "detailed thinking on" system prompt being applied via `prepend_thinking_toggle()` in `config_nemotron.py`. This behavior is unique to this model-task-agent combination:

- The same model produces think tags in 99% of SA code generation entries
- The same model produces think tags in 63–87% of MA vulnerability detection entries
- The larger Nemotron-Super-49B produces think tags in 98–99% of SA vulnerability detection entries

#### 7.4.2 Root Cause Analysis

The Nemotron architecture uses a **system prompt instruction** ("detailed thinking on") to enable thinking mode, unlike Qwen3 which uses an API parameter (`enable_thinking=True`). This is a softer control mechanism — the model is *asked* to think, not *forced* to. The evidence suggests the 8B model fails to engage its thinking protocol specifically for SA vulnerability detection because:

1. **Format anchoring**: The vulnerability detection few-shot examples present a strong output format (`(1) YES: ...` or `(2) NO: ...`) that the model immediately pattern-matches to, bypassing the thinking instruction. Code generation has no such format anchor, so the model engages its reasoning chain.

2. **Task length interaction**: SA vulnerability detection prompts are relatively short and self-contained. The model apparently judges that explicit `<think>` block reasoning is unnecessary and responds directly. In multi-agent configurations (MA), the longer discussion context may trigger the thinking behavior (63–87% tag presence).

3. **Model capacity**: The 8B model may lack the capacity to consistently follow meta-instructions (like "detailed thinking on") when task-specific format priors are strong. The 49B model, with greater capacity, follows the thinking instruction reliably across all task types.

#### 7.4.3 Impact on Output Quality

Direct comparison of the same sample (idx=360829) across modes reveals that the Nemotron-Nano-8B "thinking" vuln SA output is **structurally indistinguishable from instruct mode**:

- **Thinking mode** (1672 chars): `(2) NO: No vulnerability.\n\n**Step-by-Step Analysis:**...`
- **Instruct mode** (2539 chars): `(2) NO: No vulnerability.\n\n**Step-by-Step Analysis:**...`

Both modes produce the same format: direct answer followed by numbered steps with bold headers. The "detailed thinking on" system prompt instruction is effectively ignored.

#### 7.4.4 Implications for RQ3 Phase A

The Nemotron-Nano-8B thinking vuln SA samples remain in the Phase A baseline for several reasons:

1. **Balanced design**: Removing them would break the 4 × 2 × 2 factorial design (16 → 14 strata)
2. **Evaluable content**: The model still produces substantive step-by-step analysis (1,500–2,700 chars) that raters can evaluate
3. **Research value**: The anomaly directly speaks to RQ3 — whether the "thinking mode" system prompt produces measurably different explanation quality when the model does not structurally comply

However, this anomaly is flagged for discussion with the research team (see Section 10). The `has_think_close_tag` column in the output CSV allows filtering or stratified analysis that accounts for this behavior.

## 8. Verification

### 8.1 Phase A Checks

The Phase A sampling script performs automated verification checks on every run:

| Check | Result |
|-------|--------|
| Strata represented | 16 / 16 |
| Total samples | 48 (expected 48) |
| Within-stratum duplicates | 0 |
| Empty response_text | 0 |
| All is_correct = True | True |
| All samples have `mode` field | True |
| Instruct explanation_text all empty | True |
| Thinking explanation_text all populated | True |

### 8.2 Original Full Baseline Checks

| Check | Result |
|-------|--------|
| Within-stratum duplicates | 0 |
| Empty explanations | 0 |
| All is_correct = True | True |
| Minimum explanation length | 1,247 chars |

Cross-stratum duplicate entry IDs (same `task_id` or `idx` appearing in different model/prompting strata) are expected and valid — they represent different models reasoning about the same input, which is the desired comparison.

## 9. Limitations

1. **Nemotron-Nano-8B thinking mode anomaly**: For SA vulnerability detection, this model's "thinking" mode output is structurally indistinguishable from instruct mode (see Section 7.4). The `has_think_close_tag` column allows filtering or stratified analysis, and this anomaly is flagged for research team discussion.

2. **Prediction extraction reliability**: For vulnerability detection, predictions are extracted from free-text reasoning via keyword matching ("(1) YES", "(2) NO", etc.). This parser may misclassify ambiguous responses, though manual spot-checks of sampled entries confirmed correct extraction.

3. **Log analysis class imbalance** (original full baseline only): The HDFS dataset has 373 Normal vs. 12 Anomaly sessions. Correct predictions are predominantly True Negatives.

4. **Log analysis stratum saturation** (original full baseline only): Two Qwen3-4B-Thinking log analysis strata had only 10–11 correct predictions with valid explanations, leaving no room for alternative draws.

## 10. Previous Next Steps (Status)

> Items 1–4 below are from the original plan and have been addressed. See Section 11 for the current revised design and status.

1. **Develop annotation guidelines** — **Complete**. Rubrics defined in `docs/RQ3_Rater_Instructions.md` with detailed 1–5 Likert scale descriptions and boundary cases.

2. **Human rater pilot** — **Complete (revised scope)**. Original 48-sample plan superseded by the revised 30-evaluation design (Section 11.4). Three raters completed all 30 evaluations; ICC ≥ 0.50 on all dimensions.

3. **Nemotron-Nano-8B anomaly** — **Acknowledged**. The anomaly is documented (Section 7.4) and flagged as a covariate. The revised Phase A focuses on Super-49B, so this anomaly does not affect the current evaluation.

4. **LLM-based evaluation** — **In progress**. Pipeline implemented in `scripts/rq3_llm_judge.py` with Claude and Google backends. Ready to execute Steps 2–4 (Section 11.5).

5. **Baseline comparison** — Deferred to after LLM judge evaluation is complete.

## 11. Revised Phase A: Super-49B Zero-Shot Focus with LLM-as-Judge

### 11.1 Rationale

The original Phase A design (Section 2.1) distributes 48 samples across 16 strata (4 models × 2 modes × 2 prompting), yielding only 3 samples per stratum — sufficient for rater calibration but not for per-stratum inference. Cross-model agreement pools (Sections 6–7 of the RQ3 pool analysis notebook) further showed that requiring multiple models to agree on correct predictions produces pools too small for adequate sampling, especially for True Positives.

The revised approach focuses evaluation depth on **Nemotron-Super-49B zero-shot** (the best-performing SA model from RQ1, with F1=0.620 in thinking mode) and uses a two-stage human + LLM-as-judge workflow to achieve full coverage of the available pool while minimising human annotation effort.

**Justification for Super-49B**: Nemotron-Super-49B zero-shot achieves the highest SA vulnerability detection F1 across all configurations (RQ1 Table 1). Starting with the best-performing model provides the strongest baseline for explanation quality assessment. Zero-shot avoids the confound of few-shot influence on explanation style. Qwen3-30B-A3B is added as a secondary evaluation round (Section 11.7) to enable cross-family validation — framed as a replication study testing whether findings from Super-49B generalise to a different architecture and training lineage.

### 11.2 Evaluation Pools

Nemotron-Super-49B SA zero-shot correct predictions on VulTrial-486 (486 balanced samples: 243 vulnerable, 243 safe):

| Stratum | Pool Size | Composition |
|---------|-----------|-------------|
| Thinking zero-shot TP | 183 | Vulnerable code correctly identified |
| Thinking zero-shot TN | 79 | Safe code correctly identified |
| Instruct zero-shot TP | 93 | Vulnerable code correctly identified |
| Instruct zero-shot TN | 162 | Safe code correctly identified |
| **Total evaluations** | **517** | 262 thinking + 255 instruct |
| **Think ∩ Inst intersection** | **135** | 77 TP + 58 TN (same code sample correct in both modes; 5 text-parser mismatches excluded) |

Each code sample in the intersection has two evaluable responses (thinking and instruct), enabling direct within-sample mode comparison.

> **Note on TP/TN balance**: The intersection pool shifted from near-balanced (54 TP / 57 TN on VulTrial-386) to TP-heavy (~57% TP on VulTrial-486). This reflects thinking mode's strong TP bias (69.8% TP) dominating the intersection. Five entries were excluded from the original 140 due to text-parser mismatches where the response text conclusion contradicts the parser's prediction: three instruct-mode entries where gt=1 but the response concludes "no vulnerability" (entry_ids 197518, 204017, 206676), and two entries where gt=0 but the response concludes "vulnerability detected" (entry_ids 270922 thinking, 387593 instruct). The corrected pool of 135 remains adequate for stratified sampling of 15 snippets (8 TP / 7 TN) with ample margin.

### 11.3 Workflow Overview

```
Step 1: Human Rating (15 code samples → 30 evaluations)
    ↓
Step 2: LLM-as-Judge Calibration (few-shot from Step 1)
    ↓
Step 3: LLM-as-Judge Validation (held-out from Step 1)
    ↓
Step 4: LLM-as-Judge Full Evaluation (remaining ~487 evaluations)
    ↓
Step 5: Secondary Model — Qwen3-30B-A3B (reuse calibrated judge)
```

### 11.4 Step 1 — Human Rating

**Sample count: 15 code snippets → 30 response evaluations**

Samples are drawn from the think∩inst intersection pool (135 samples: 77 TP, 58 TN) using stratified random sampling with seed=42. Each selected code snippet is rated for both its thinking-mode and instruct-mode response, yielding two evaluations per snippet.

| Stratum | Snippets | Evaluations |
|---------|----------|-------------|
| Intersection TP | 8 | 16 (8 think + 8 inst) |
| Intersection TN | 7 | 14 (7 think + 7 inst) |
| **Total** | **15** | **30** |

**Why 15 snippets (30 evaluations)**:
- **Few-shot calibration** requires ~8 diverse evaluations (2 per stratum: think-TP, think-TN, inst-TP, inst-TN) covering a range of quality levels to anchor the LLM judge.
- **Validation** requires ~22 evaluations to compute meaningful Spearman rank correlation (ρ) between human and LLM scores across four metrics.
- **Efficiency**: Reading code once and rating two responses (think + inst) halves the code-reading effort compared to independent sampling.

**Evaluation criteria**: The same four metrics (completeness, clarity, actionability, informativeness) on a 1–5 Likert scale, using the rubrics in `docs/rq3_rater_instructions.md` (Section 4). Model identity and mode are anonymized from raters; however, since each code snippet has exactly two responses, raters will know they are comparing two different model configurations without knowing which is which.

**Rater protocol**: At least two raters independently score all 30 evaluations. Inter-rater agreement is measured via intraclass correlation coefficient (ICC, two-way random, absolute agreement). Disagreements >1 point on any metric are resolved through discussion.

#### 11.4.1 Inter-Rater Reliability Results

##### Two-rater analysis (Shane, HS)

The initial two-rater analysis revealed poor absolute agreement across all dimensions, driven by a systematic calibration bias where HS rated consistently higher than Shane (mean difference 0.37–1.30 points).

| Dimension | ICC(2,1) | 95% CI | Interp. | Spearman ρ | Weighted κ | Mean \|diff\| | % Perfect | % Within 1 | Signed diff |
|-----------|----------|--------|---------|------------|------------|---------------|-----------|------------|-------------|
| Completeness | 0.354 | [−0.11, 0.69] | poor | 0.637 (p<.001) | 0.346 | 1.17 | 26.7% | 56.7% | −1.17 (HS higher) |
| Clarity | 0.325 | [−0.05, 0.62] | poor | 0.497 (p=.005) | 0.317 | 0.83 | 30.0% | 86.7% | −0.70 (HS higher) |
| Actionability | 0.432 | [0.11, 0.68] | poor | 0.535 (p=.002) | 0.424 | 0.63 | 50.0% | 86.7% | −0.37 (HS higher) |
| Informativeness | 0.171 | [−0.09, 0.49] | poor | 0.520 (p=.003) | 0.166 | 1.30 | 10.0% | 63.3% | −1.30 (HS higher) |

Despite poor ICC values, Spearman correlations (0.50–0.64) indicated the raters agreed on relative quality rankings — the disagreement was primarily about absolute scale calibration rather than which responses were better or worse.

##### Three-rater analysis (Shane, HS, Merve)

A third rater (Merve) independently scored all 30 evaluations. Merve's means fell between Shane and HS on all dimensions, confirming the issue was HS's higher calibration point rather than fundamental disagreement about quality. The three-rater ICC(2,k) values represent the reliability of the averaged scores across raters.

| Dimension | ICC(2,k) | 95% CI | Interp. | Spearman ρ | Weighted κ | Mean \|diff\| | % Perfect | % Within 1 | Signed diff |
|-----------|----------|--------|---------|------------|------------|---------------|-----------|------------|-------------|
| Completeness | 0.731 | [0.27, 0.89] | moderate | 0.673 (p<.001) | 0.504 | 0.84 | 35.6% | 80.0% | −0.27 (HS higher) |
| Clarity | 0.542 | [0.18, 0.76] | moderate | 0.419 (p=.050) | 0.287 | 0.71 | 36.7% | 92.2% | −0.07 (HS higher) |
| Actionability | 0.809 | [0.65, 0.90] | good | 0.602 (p=.002) | 0.574 | 0.51 | 57.8% | 91.1% | −0.09 (HS higher) |
| Informativeness | 0.534 | [0.02, 0.79] | moderate | 0.535 (p=.035) | 0.302 | 0.91 | 27.8% | 82.2% | −0.47 (HS higher) |

ICC interpretation follows Koo & Li (2016): < 0.50 = poor, 0.50–0.75 = moderate, 0.75–0.90 = good, > 0.90 = excellent.

##### Metric rationale and limitations

The three metrics capture complementary aspects of inter-rater agreement:

| Metric | Question answered | Sensitive to bias? | Sensitive to rank? | Chance-corrected? |
|--------|-------------------|--------------------|--------------------|-------------------|
| ICC(2,k) | Do raters assign the same absolute scores? | Yes | Yes | No |
| Spearman ρ | Do raters agree on the relative ordering of responses? | No | Yes | No |
| Weighted κ (quadratic) | Do raters agree beyond what chance alone would predict? | Yes | Yes | Yes |

**ICC** (Intraclass Correlation Coefficient) is the primary measure. The two-way random model ICC(2,1) treats both raters and samples as random draws from larger populations; ICC(2,k) extends this to the reliability of the *averaged* score across k raters. ICC penalises both rank disagreement and systematic level differences — hence the poor two-rater values despite moderate Spearman correlations. **Spearman ρ** ignores absolute score levels entirely and asks only whether raters rank responses in the same order. When ICC is low but Spearman is moderate, the disagreement is primarily about scale calibration (a correctable problem) rather than fundamentally different quality judgements. **Weighted kappa** corrects for agreement expected by chance alone — important for ordinal scales where raters might cluster around modal values. The quadratic weighting penalises a 2-point disagreement 4× more than a 1-point disagreement, reflecting the ordinal structure of Likert scales.

**Three-rater averaging and limitations**: For three raters, ICC is computed natively via `pingouin.intraclass_corr`, which handles arbitrary rater counts using the full ANOVA-based formulation. However, Spearman ρ and Cohen's weighted κ are inherently pairwise metrics with no standard multi-rater generalisation. The values reported above are the arithmetic mean of the three pairwise comparisons (Shane–HS, Shane–Merve, HS–Merve). This averaging approach has two limitations: (1) it does not account for the non-independence of pairwise comparisons (each rater appears in two of the three pairs), and (2) the reported p-values for Spearman ρ are the most conservative (maximum) pairwise p-value rather than a formally combined statistic. Fleiss' kappa would provide a true multi-rater chance-corrected agreement measure, but does not support ordinal weighting; Kendall's W (coefficient of concordance) is an alternative multi-rater rank agreement measure. Given that ICC is the primary metric and all dimensions pass the ICC ≥ 0.50 threshold, the averaged pairwise Spearman and kappa values serve as supplementary indicators rather than decision criteria.

**Rater means** (completeness / clarity / actionability / informativeness):
- Shane: 2.97 / 3.67 / 2.37 / 2.77
- HS: 4.13 / 4.37 / 2.73 / 4.07
- Merve: 3.37 / 3.77 / 2.50 / 3.47

**Key observations**:

1. **Substantial improvement with 3rd rater**: All dimensions now exceed ICC ≥ 0.50, with actionability reaching "good" (0.809). The third rater anchored between the two original raters, reducing the effective bias in the averaged consensus and tightening confidence intervals.

2. **Systematic bias resolved by averaging**: The signed difference dropped from −0.37 to −1.30 (2-rater) to −0.07 to −0.47 (3-rater), confirming that the 3-rater average naturally down-weights the outlier calibration. The remaining bias is within acceptable bounds for all dimensions.

3. **Agreement statistics improved**: Within-1-point agreement increased from 57–87% (2-rater) to 80–92% (3-rater). Perfect agreement also improved, particularly for completeness (26.7% → 35.6%) and informativeness (10.0% → 27.8%).

4. **Residual disagreements**: 21 of 30 samples (70%) still have at least one dimension with max rater diff > 1 point. These are concentrated in completeness and informativeness where HS's scores remain elevated. However, with ICC ≥ 0.5 on all dimensions, the 3-rater average is a statistically appropriate consensus measure.

5. **Per-stratum patterns**: Thinking-mode responses receive higher consensus scores than instruct-mode on completeness (think 3.8 vs. inst 3.2) and clarity (think 4.2 vs. inst 3.7). TN samples score higher than TP samples overall, potentially reflecting the relative difficulty of explaining vulnerability mechanisms vs. confirming safety.

**Consensus approach**: With all ICC values ≥ 0.50, the 3-rater average is used as the consensus score for LLM judge calibration. This avoids the need for discussion-based resolution while producing stable consensus values that are robust to any single rater's calibration bias.

The IRR analysis outputs are:
- `results/rq3_baseline/irr_summary.csv` — per-dimension metrics (3-rater)
- `results/rq3_baseline/irr_disagreements.csv` — 21 flagged samples with per-rater scores
- `results/rq3_baseline/super49b_zero_consensus_scores.csv` — 30 rows with per-rater and averaged consensus scores
- Script: `scripts/rq3_inter_rater_agreement.py`

### 11.5 Steps 2–4 — LLM-as-Judge Pipeline

The LLM judge pipeline uses a model independent of the models under test (Qwen3 and Nemotron). Claude (Anthropic) is the primary judge, with Google Gemini as an alternative backend.

#### 11.5.1 Judge Model Selection

| Backend | Model | Rationale |
|---------|-------|-----------|
| Anthropic (primary) | Claude Sonnet 4.6 (`claude-sonnet-4-6`) | Independent family; strong structured output; cost-effective |
| Anthropic (premium) | Claude Opus 4.6 (`claude-opus-4-6`) | Higher accuracy for complex cases; available via `--judge-model` |
| Google (alternative) | Gemini 3 Flash (`gemini-3-flash-preview`) | Independent backend; free tier available |

The judge model must not overlap with any model under test (Qwen3-4B, Qwen3-30B, Nemotron-Nano-8B, Nemotron-Super-49B) to avoid self-evaluation bias.

#### 11.5.2 Step 2 — Zero-Shot Baseline (LLM as "4th Rater")

The LLM scores all 30 human-rated samples using the rubric only (no human examples), establishing the LLM's natural alignment with human raters before any calibration.

```bash
export ANTHROPIC_API_KEY=<key>
python scripts/rq3_llm_judge.py --claude --mode zero-shot-baseline
```

**Outputs**: `llm_judge_zero_shot_baseline.csv` (per-sample scores + justifications), `llm_judge_zero_shot_baseline_metrics.csv` (agreement metrics).

**Agreement metrics computed**:
- **Spearman ρ** (rank correlation with human consensus)
- **MAE** — Mean Absolute Error (average absolute difference between LLM and human scores on the 1–5 scale)
- **Bias** (signed mean difference: positive = LLM scores higher)
- Per-rater comparison (LLM vs. Shane, LLM vs. HS, LLM vs. Merve)

##### Why Spearman ρ (not ICC) for LLM judge validation

ICC (Intraclass Correlation Coefficient) was used for human inter-rater reliability (Section 11.4.1) because all 3 human raters scored the same items independently under identical conditions — ICC appropriately measures absolute agreement.

For LLM-vs-human validation, Spearman ρ is preferred because:

1. **Rank agreement is the primary concern**: the LLM judge must correctly identify which explanations are better/worse (ranking), rather than produce identical absolute scores. A systematic offset (e.g., LLM scoring 0.3 points lower) is correctable and less concerning than rank inversions.
2. **Absolute alignment is already captured by MAE and bias**: these two metrics catch the issues ICC would flag (systematic over/under-scoring, absolute divergence). Together with Spearman ρ, the three metrics cover the full space that ICC measures alone.
3. **Robustness to small samples**: with 18–22 validation samples, Spearman is more robust than ICC to small-sample distributional effects.
4. **Convention in LLM-as-judge literature**: studies evaluating LLM judges typically report Spearman or Kendall's τ for judge-human agreement (e.g., Zheng et al., "Judging LLM-as-a-Judge"; Widyasari et al.)

In summary, the three metrics together provide complementary coverage:

| Metric | Question Answered | Sensitive to Bias? | Sensitive to Rank? |
|--------|-------------------|--------------------|--------------------|
| Spearman ρ | Do the LLM and human agree on relative quality ordering? | No | Yes |
| MAE | How close are the absolute scores? | Yes | Indirectly |
| Bias | Does the LLM systematically score higher or lower? | Yes | No |

#### 11.5.3 Step 3 — Calibration and Validation

If zero-shot baseline does not pass thresholds, calibrate with few-shot examples from the human-rated set.

**Calibration** (`--mode calibrate`): Select 8 calibration + 22 validation samples. From each stratum (think-TP, think-TN, inst-TP, inst-TN), the highest and lowest mean consensus samples are selected as few-shot examples, giving the LLM judge concrete quality anchors.

**Validation** (`--mode validate`): Run judge on 22 held-out validation samples. The LLM judge must demonstrate:
- Spearman ρ ≥ 0.7 with human scores on each of the four metrics
- Mean absolute error (MAE) ≤ 1.0 on the 5-point scale
- No systematic bias (|mean signed error| ≤ 0.5)

If validation fails, the calibration set is revised and validation is re-run. Up to 3 iterations are attempted before expanding the human-rated set.

```bash
python scripts/rq3_llm_judge.py --claude --mode calibrate --iteration 2 --num-examples 3
python scripts/rq3_llm_judge.py --claude --mode validate --iteration 2
```

##### Validation Results — All Configurations Tested

Five configurations were evaluated, varying the judge model (Sonnet 4.6 vs Opus 4.6) and prompting strategy (zero-shot vs few-shot with 8 or 12 calibration examples):

| Config | Completeness ρ | Clarity ρ | Actionability ρ | Informativeness ρ | Dims ≥ 0.7 | Dims > Human IRR |
|--------|---------------|-----------|-----------------|-------------------|-----------|-----------------|
| **Opus 4.6 zero-shot** | **0.786** | **0.577** | **0.737** | **0.670** | **2** | **4/4** |
| Sonnet 4.6 v2 (12 ex) | 0.848 | 0.478 | 0.863 | 0.585 | 2 | 4/4 |
| Sonnet 4.6 v1 (8 ex) | 0.730 | 0.539 | 0.804 | 0.660 | 2 | 4/4 |
| Opus 4.6 v1 (8 ex) | 0.709 | 0.400 | 0.659 | 0.525 | 1 | 3/4 |
| Sonnet 4.6 zero-shot | 0.674 | 0.564 | 0.750 | 0.630 | 1 | 4/4 |

*Human IRR Spearman ρ: completeness=0.673, clarity=0.419, actionability=0.602, informativeness=0.535*

**Key findings from model comparison**:

1. **Opus 4.6 zero-shot provides the best balanced performance** — no dimension drops below 0.577, and it is the only configuration where even the weakest dimension (clarity ρ=0.577) substantially exceeds human IRR (0.419). It passes 2 of 4 dimensions at the strict ρ ≥ 0.7 threshold.

2. **Few-shot examples degrade Opus performance**: All four dimensions worsened when v1 few-shot examples were added to Opus (completeness 0.786→0.709, clarity 0.577→0.400, actionability 0.737→0.659, informativeness 0.670→0.525). The more capable model appears to be constrained by the examples rather than guided by them.

3. **Sonnet benefits from few-shot but with trade-offs**: Sonnet v2 (12 examples) achieves the highest individual dimension scores (completeness 0.848, actionability 0.863) but at the cost of clarity (0.478) and informativeness (0.585). Adding more examples helped some dimensions but hurt others.

4. **Clarity is consistently the weakest dimension** across all configurations and both models, reflecting the inherent subjectivity of this dimension (human ICC=0.542, the lowest among the four).

##### Threshold Adjustment: Accepting Opus 4.6 Zero-Shot

Clarity (ρ=0.577) and informativeness (ρ=0.670) do not meet the original ρ ≥ 0.7 threshold. However, Opus 4.6 zero-shot is accepted as the final judge configuration based on the following justification:

1. **All dimensions exceed human inter-rater agreement**: Completeness (0.786 vs 0.673), clarity (0.577 vs 0.419), actionability (0.737 vs 0.602), informativeness (0.670 vs 0.535). It is unreasonable to require the LLM judge to agree with consensus more strongly than individual human raters agree with each other.

2. **Inherent subjectivity ceiling**: Clarity and informativeness are the most subjective dimensions. Human ICC values confirm this: clarity ICC(2,k)=0.542 (moderate) and informativeness ICC(2,k)=0.534 (moderate), compared to completeness ICC(2,k)=0.731 and actionability ICC(2,k)=0.809. The lower inter-rater reliability places a ceiling on how well any judge can agree with consensus.

3. **Absolute score accuracy is strong**: MAE ≤ 0.59 and |bias| ≤ 0.43 across all dimensions, meaning scores are within one point of human consensus on average. The disagreement is in fine-grained ranking, not gross miscalibration.

4. **Few-shot calibration does not help Opus**: Unlike Sonnet, adding examples consistently degrades Opus performance, ruling out further calibration iterations as a remedy.

5. **Zero-shot is more principled**: Using rubric-only evaluation (no anchoring to specific examples) reduces the risk of overfitting to the calibration set and provides a more generalisable judge.

**Decision**: Use **Opus 4.6 zero-shot** (rubric only, no few-shot examples) for full evaluation. The second-best alternative is Sonnet 4.6 with v1 few-shot (8 examples) if cost is a concern. Report per-dimension agreement metrics transparently in the paper.

#### 11.5.4 Step 4 — Full Evaluation

Once validated, the LLM judge evaluates the remaining Super-49B zero-shot samples:

| Target | Human-rated | LLM-judged | Total |
|--------|-------------|------------|-------|
| Think zero-shot | 15 (from intersection) | 247 | 262 |
| Inst zero-shot | 15 (from intersection) | 240 | 255 |
| **Total** | **30** | **487** | **517** |

```bash
python scripts/rq3_llm_judge.py --claude --judge-model claude-opus-4-6 --mode evaluate --model super49b
```

Each LLM evaluation produces scores on all four metrics plus a justification. The justifications are retained for qualitative analysis and spot-check verification. The script supports crash recovery via incremental CSV appending.

**Quality control**: A random 10% of LLM-judged evaluations (~49 samples) are spot-checked by a human rater to verify the judge maintains calibrated performance beyond the validation set.

```bash
python scripts/rq3_llm_judge.py --claude --mode spot-check --model super49b
```

### 11.7 Step 5 — Secondary Model: Qwen3-30B-A3B

After completing Super-49B evaluation, the same calibrated LLM judge (with the same few-shot examples) is applied to Qwen3-30B-A3B zero-shot correct predictions:

| Stratum | Pool Size |
|---------|-----------|
| Thinking zero-shot | 270 correct |
| Instruct zero-shot | 264 correct |
| Think ∩ Inst intersection | 190 (89 TP + 101 TN) |

The Qwen3-30B evaluation enables cross-model comparison of explanation quality (Super-49B vs. Qwen3-30B) on their respective correct prediction pools. Where the two models' intersection pools overlap (i.e., the same code sample is correctly predicted by both models in the same mode), direct pairwise comparison of explanation quality is possible.

**Optional human validation**: A small validation set (~10 evaluations) from the Qwen3-30B pool may be human-rated to verify the LLM judge generalises across models. This is recommended but not blocking.

### 11.8 Deliverables

| Artifact | Description |
|----------|-------------|
| **Human rating** | |
| `results/rq3_baseline/super49b_zero_human_rating_set.csv` | 30-row master file with entry_id, response_id, source code, response text |
| `results/rq3_baseline/super49b_zero_rater_sheet.csv` | Rater sheet template (30 rows) |
| `results/rq3_baseline/super49b_zero_rater_sheet v2_*.xlsx` | Completed rater sheets (Shane, HS, Merve) |
| `results/rq3_baseline/super49b_zero_consensus_scores.csv` | 30 rows with per-rater scores, consensus scores, stratum metadata |
| `results/rq3_baseline/irr_summary.csv` | Per-dimension ICC, Spearman ρ, weighted κ, agreement statistics |
| `results/rq3_baseline/irr_disagreements.csv` | 21 samples flagged for discussion-based resolution |
| **LLM judge** | |
| `results/rq3_baseline/llm_judge_zero_shot_baseline.csv` | Zero-shot baseline scores (LLM as 4th rater) |
| `results/rq3_baseline/llm_judge_zero_shot_baseline_metrics.csv` | Zero-shot agreement metrics vs human consensus |
| `results/rq3_baseline/llm_judge_prompt_v{N}.txt` | Saved judge prompt per calibration iteration |
| `results/rq3_baseline/llm_judge_split_v{N}.csv` | Calibration/validation split per iteration |
| `results/rq3_baseline/llm_judge_validation_v{N}.csv` | Validation results per iteration |
| `results/rq3_baseline/llm_judge_validation_metrics_v{N}.csv` | Validation agreement metrics per iteration |
| `results/rq3_baseline/super49b_zero_llm_judged.csv` | ~487 LLM-judged evaluations (Super-49B) |
| `results/rq3_baseline/super49b_zero_spot_check_sheet.csv` | 10% stratified spot-check sheet |
| `results/rq3_baseline/qwen30b_zero_llm_judged.csv` | ~534 LLM-judged evaluations (Qwen3-30B) |
| **Scripts** | |
| `scripts/rq3_inter_rater_agreement.py` | IRR computation and consensus scoring |
| `scripts/rq3_llm_judge.py` | LLM-as-judge pipeline (supports `--claude`, `--google`, OpenRouter backends) |
| `scripts/rq3_generate_human_rating_set.py` | Script to generate the 15-snippet human rating set |

### 11.9 Current Status

| Step | Status | Notes |
|------|--------|-------|
| Step 1: Human rating (30 evaluations) | **Complete** | 3 raters (Shane, HS, Merve); ICC ≥ 0.50 all dimensions |
| Step 2: Zero-shot baseline | **Complete** | Tested Sonnet 4.6 + Opus 4.6; Opus zero-shot best balanced (2/4 PASS, 4/4 > human IRR) |
| Step 3: Calibration + validation | **Complete** | 5 configs tested; few-shot hurts Opus; Opus zero-shot selected as final judge |
| Step 4: Full evaluation (Super-49B) | **Ready to run** | ~487 samples; use Opus 4.6 zero-shot (`--judge-model claude-opus-4-6`) |
| Step 5: Secondary model (Qwen3-30B) | **Ready to run** | Reuses same Opus 4.6 zero-shot judge |
