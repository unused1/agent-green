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

**Available pool composition**: The "Correct Available" counts in Section 4.2 represent all correct predictions with valid explanations (≥100 chars), including both **True Positives** (vulnerable code correctly identified) and **True Negatives** (safe code correctly identified). The pool spans SA thinking-model results from both RQ1 Qwen experiments and cross-architecture Nemotron experiments — it is not limited to RQ1 alone.

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

| Model | Mode | Prompting | Correct Available | Sampled |
|-------|------|-----------|-------------------|---------|
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

**Phase A (current)**:

| File | Description |
|------|-------------|
| `results/rq3_baseline/rq3_baseline_samples.csv` | 48 sampled entries with explanation/response text and metadata |
| `results/rq3_baseline/rq3_baseline_samples_vulnerability_detection.csv` | Same 48 samples (vuln-only, identical content) |
| `results/rq3_baseline/rq3_sampling_summary.txt` | Per-stratum statistics (counts, lengths, flags) |
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
| SA | vuln | **0/386 (0%)** | **0/386 (0%)** |
| DA | vuln | 62/387 (16%) | 1/387 (0%) |
| MA | vuln | 333/384 (87%) | 242/384 (63%) |
| SA | code | 163/164 (99%) | 163/164 (99%) |
| DA | code | 153/164 (93%) | 160/164 (98%) |
| MA | code | 160/164 (98%) | 160/164 (98%) |

**Nemotron-Super-49B (Thinking Mode)**

| Agent | Task | Zero-shot | Few-shot |
|-------|------|-----------|----------|
| SA | vuln | 381/386 (99%) | 380/384 (99%) |
| DA | vuln | 382/387 (99%) | 383/387 (99%) |
| MA | vuln | 380/386 (98%) | 383/384 (>99%) |
| SA | code | 96/164 (59%) | 152/164 (93%) |
| DA | code | 148/164 (90%) | 152/164 (93%) |
| MA | code | 146/164 (89%) | 150/164 (91%) |

**Nemotron-Nano-8B (Instruct Mode — Think Tag Leakage)**

| Agent | Task | Zero-shot | Few-shot |
|-------|------|-----------|----------|
| SA | vuln | 0/386 (0%) | 0/386 (0%) |
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

Nemotron-Nano-8B produces **zero** `<think>` or `</think>` tags across all 772 SA vulnerability detection entries (386 zero-shot + 386 few-shot), despite the "detailed thinking on" system prompt being applied via `prepend_thinking_toggle()` in `config_nemotron.py`. This behavior is unique to this model-task-agent combination:

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

## 10. Next Steps

1. **Develop annotation guidelines**: Define scoring rubrics for the four metrics (completeness, clarity, actionability, informativeness) on a 1–5 Likert scale, with concrete examples and boundary cases for vulnerability detection. The rubrics should specify what constitutes each score level and include calibration examples for rater training.

2. **Phase A — Human rater pilot (48 samples)**: Distribute the 48 Phase A samples to human raters for scoring on the four metrics. Model identity, mode, and prompting style are anonymized from raters. At least two raters should independently score the full pilot set to measure inter-rater agreement via Cohen's kappa (for categorical bins) or intraclass correlation coefficient (for ordinal scores), with disagreements resolved through discussion.

3. **Research team decision on Nemotron-Nano-8B anomaly**: The Nemotron-Nano-8B SA vuln thinking strata show 0% `<think>` tag presence despite the "detailed thinking on" system prompt (Section 7.4). The research team should decide whether to: (a) keep these samples as-is, since the model still produces evaluable step-by-step reasoning; (b) flag them with a covariate in the analysis; or (c) exclude them and accept a reduced factorial design. This decision does not block Qwen sample evaluation — raters can begin with the 12 Qwen samples (4 thinking + 4 instruct × 2 prompting, 3 each) while the team deliberates.

4. **Phase B — LLM-based evaluation (~385 samples)**: Using human ratings from Phase A as calibration ground truth, develop and validate an LLM-based evaluator. Apply it to ~385 vulnerability detection samples (covering the ~1,624 available pool at 95% confidence / 5% margin of error). Validate LLM–human agreement on the pilot set before scaling.

5. **Baseline comparison**: Use baseline scores to calibrate expectations for the RQ3 prompting style experiments (no-explanation, explain-after, explain-before, evidence-bound).
