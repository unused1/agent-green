# RQ3 Phase A: Rater Instructions for Vulnerability Analysis Explanation Quality Evaluation

## 1. Task Overview

We are evaluating the quality of AI-generated vulnerability analyses across multiple models. For each source code sample, responses from three models are presented for evaluation. All models arrived at the correct prediction (true positive or true negative) for every sample — the goal is to assess how well each model *explains* its vulnerability assessment, not whether the prediction is correct.

The cross-model design enables direct comparison of explanation quality across models for the same code, while the blinded rater sheet ensures scoring is not influenced by model identity.

## 2. Spreadsheet Columns

| Column | Description | Action |
|--------|-------------|--------|
| `sample_id` | Unique identifier for this sample | Reference only |
| `source_code` | The C/C++ function under review | Read and understand |
| `ground_truth_label` | "vulnerable" or "safe" — the actual security status of the code | Use as reference when evaluating |
| `cwe` | CWE identifier (e.g., CWE-119) — only present for vulnerable samples | Use as reference when evaluating |
| `cve_desc` | Brief CVE description — only present for vulnerable samples | Use as reference when evaluating |
| `response_text` | The AI's vulnerability analysis — **this is what to score** | Evaluate and score |
| `completeness_score` | Score 1–5 (see rubric below) | **Fill in** |
| `clarity_score` | Score 1–5 (see rubric below) | **Fill in** |
| `actionability_score` | Score 1–5 (see rubric below) | **Fill in** |
| `informativeness_score` | Score 1–5 (see rubric below) | **Fill in** |
| `rater_notes` | Free-text notes | **Fill in** (optional) |

**Note on cross-model grouping**: Multiple consecutive rows may share the same `source_code` — these are responses from different models analyzing the same function. The rater sheet is **blinded**: model identity is not visible. Each row should be scored independently on the merits of its `response_text`.

## 3. Evaluation Procedure

For each group of samples sharing the same source code, follow these steps:

### Step 1: Read the source code

Read the function in `source_code`. Form an initial understanding of what the code does, its inputs, control flow, and any potential security concerns. This step is performed **once per code sample** — the same code appears across multiple rows (one per model response).

### Step 2: Check the ground truth

Read `ground_truth_label` to see if the code is vulnerable or safe. For vulnerable samples, read the `cwe` and `cve_desc` columns to understand what the known vulnerability is. This provides context for assessing the response — it does not mean the AI had access to this information.

### Step 3: Read and score each model's response independently

For each row in the group, read `response_text` carefully and score it on its own merits using the rubrics in Section 4. Important:

- **Score each response independently** before comparing across models. Do not anchor one model's score to another's — each response should stand on its own against the rubric.
- Score each metric on its own merits. E.g. A response can be highly clear (high clarity) but miss important issues (low completeness).
- Use the full 1–5 range.
- Do not adjust scores based on response length alone. A short response that precisely identifies the core issue can score well; a long response that repeats itself without substance should not.

### Step 4: Add notes

Optional but encouraged for any scores where the reasoning may not be obvious. Notes are valuable for resolving disagreements between raters. When multiple responses cover the same code, comparative notes (e.g., "covers edge case X that the other responses missed") are useful but not required.

## 4. Scoring Rubric

All metrics use a 1–5 Likert scale. Score based on the descriptions below.

### 4.1 Completeness

*Does the response cover the vulnerability mechanism or justify why the code is safe, addressing relevant factors including edge cases, attack vectors, and underlying assumptions?*

| Score | Description |
|-------|-------------|
| **1 — Severely incomplete** | States only a conclusion (e.g., "No vulnerability") with no supporting analysis, or addresses only a trivial aspect while ignoring the core security concern. |
| **2 — Major gaps** | Covers one aspect of the security analysis but misses significant factors. For vulnerable code: identifies the general area (e.g., "memory issue") but not the specific mechanism. For safe code: checks one category but overlooks others. |
| **3 — Adequate** | Addresses the key vulnerability mechanism or safety rationale with minor gaps. The main reasoning is present but lacks depth on edge cases, preconditions, or secondary concerns. A reader would understand the core issue but might need to investigate further. |
| **4 — Thorough** | Covers the vulnerability mechanism or safety justification comprehensively, including relevant edge cases and contributing factors. Minor aspects may be unaddressed, but the analysis leaves few open questions about the primary security concern. |
| **5 — Exhaustive** | Fully covers the security analysis with no meaningful gaps. Addresses the mechanism, scope, preconditions, edge cases, and any secondary concerns. A developer could act on this analysis without further investigation. |

### 4.2 Clarity

*Is the response logically structured, free of ambiguities, and using precise technical terms?*

| Score | Description |
|-------|-------------|
| **1 — Incoherent** | Disorganized, contradictory, or incomprehensible. The reader cannot follow the argument. May contain internally inconsistent claims (e.g., simultaneously stating the code is safe and describing a vulnerability). |
| **2 — Confusing** | Has a discernible argument but is poorly organized, uses vague language, or contains misleading statements. The reader must re-read multiple times to extract the key points. Technical terms may be used incorrectly. |
| **3 — Adequate** | Reasonably structured and understandable on a single read. Some sections may be verbose or slightly ambiguous, but the overall argument is clear. Technical terminology is mostly correct. |
| **4 — Clear** | Well-organized with logical flow from analysis to conclusion. Uses precise technical language. Minor imprecisions may exist but do not impede understanding. Easy to follow. |
| **5 — Exemplary** | Exceptionally well-structured with clear progression. Every claim is precise and unambiguous. Technical terminology is used correctly and consistently. Could serve as a reference for how to communicate a vulnerability analysis. |

### 4.3 Actionability

*Does the response provide actionable insights such as highlighting vulnerable lines, suggesting patches, or describing specific risks and mitigations?*

| Score | Description |
|-------|-------------|
| **1 — Not actionable** | Provides no guidance on what to do with the finding. States only a generic conclusion with no reference to specific code locations, risks, or remediation. |
| **2 — Minimally actionable** | References the general area of concern but lacks specifics. A developer would know *something* might be wrong but not *where* or *how* to address it. |
| **3 — Moderately actionable** | Identifies specific code constructs or lines involved, and gives a general direction for remediation (e.g., "add bounds checking"). A developer could begin investigating but would need additional research. |
| **4 — Actionable** | Points to specific code locations, explains the risk concretely, and suggests a plausible fix or mitigation strategy. A developer with domain knowledge could act on this with minimal additional research. |
| **5 — Immediately actionable** | Provides precise code references, a concrete fix or mitigation, and explains why the fix resolves the issue. A developer could implement the remediation directly from this analysis. |

**Note on safe code**: For samples labeled "safe," low actionability scores (1–2) are expected when the response does not suggest specific remediation or highlight vulnerable lines — since there is no vulnerability to remediate. If scoring actionability ≤ 2 for safe code, briefly note the rationale in `rater_notes` (e.g., "safe code — no remediation applicable").

### 4.4 Informativeness

*Does the response offer meaningful, non-redundant, and technically insightful information beyond superficial observations?*

| Score | Description |
|-------|-------------|
| **1 — Uninformative** | Contains only trivial observations restating the code's surface behavior (e.g., "This function takes two parameters"), or is largely filler text with no security-relevant content. |
| **2 — Superficial** | Makes security-relevant observations but at a surface level only. States obvious facts about the code without deeper analysis. May contain filler or repetitive content that dilutes the useful information. |
| **3 — Adequate** | Provides some genuine technical insight about the code's security properties. The analysis goes beyond surface observations but may not reveal anything a competent developer wouldn't notice on their own. |
| **4 — Insightful** | Offers meaningful technical depth — identifies non-obvious interactions, explains *why* a pattern is dangerous (or safe), and demonstrates understanding of the underlying security principles. Contains minimal filler or redundancy. |
| **5 — Highly insightful** | Provides expert-level analysis with novel or non-obvious observations. Demonstrates deep understanding of the vulnerability class, the specific codebase patterns, and their security implications. Every sentence adds value. |

## 5. Evaluation Indicators

The following indicators complement the scoring rubric in Section 4. They describe concrete aspects to look for (and watch out for) when evaluating each metric. These are **descriptive guides, not checklists** — a response does not need to exhibit every positive indicator to score well, nor does the presence of one negative indicator automatically lower a score. Use these alongside the Likert descriptions to anchor scoring decisions.

### 5.1 Completeness

| Look for (positive) | Watch for (negative) |
|----------------------|----------------------|
| Discusses the code's purpose, inputs, outputs, and key variables | Generic assertions without grounding in the actual code |
| Examines multiple vulnerability classes relevant to the code (e.g., buffer overflow, use-after-free, integer overflow) | Focuses on only one aspect when multiple security concerns exist |
| Provides depth on the specific vulnerability mechanism or safety rationale, not just surface-level categorization | Lists vulnerability categories as a checklist without analyzing each |
| For vulnerable code: identifies the specific mechanism, not just the general area | Misses obvious attack surfaces or secondary vulnerabilities noted in the CVE |
| For safe code: explains *why* relevant vulnerability classes do not apply | States "no vulnerability" without justifying the safety of specific constructs |

### 5.2 Clarity

| Look for (positive) | Watch for (negative) |
|----------------------|----------------------|
| Organized logical flow from analysis to conclusion | Disorganized structure that requires re-reading to follow |
| References specific functions, variables, or code lines | Vague references (e.g., "the code checks..." without specifying what or where) |
| Technical terms used correctly and precisely | Incorrect factual claims or misuse of technical terminology |
| Each section advances the argument without redundancy | Boilerplate disclaimers or repeated conclusions that add no analytical value |

### 5.3 Actionability

| Look for (positive) | Watch for (negative) |
|----------------------|----------------------|
| Points to specific code locations or constructs involved | Generic advice (e.g., "add bounds checking") without specifying where or how |
| Suggests a concrete fix, patch, or mitigation strategy | Identifies a problem without any direction for remediation |
| Explains what is missing and how to address it | Restates the conclusion as a recommendation (e.g., "fix the vulnerability") |
| For safe code: scores of 1–2 are expected — note this in `rater_notes` | N/A — low actionability for safe code is not a negative indicator |

### 5.4 Informativeness

| Look for (positive) | Watch for (negative) |
|----------------------|----------------------|
| Explains *why* a pattern is dangerous or safe, not just *that* it is | Restates the code's surface behavior without security analysis |
| Provides counterfactual reasoning (e.g., what could go wrong without a specific control) | Filler, repetition, or generic security platitudes that dilute useful content |
| Identifies non-obvious interactions, edge cases, or domain-specific context | Observations that any competent developer would make on first reading |
| Demonstrates understanding of the vulnerability class and its broader implications | Mechanically listing vulnerability categories without genuine insight |

## 6. General Guidelines

> **Note**: Section 5 (Evaluation Indicators) was added during Phase A calibration to codify recurring patterns observed across initial samples. These indicators are derived from inter-rater discussion and are intended to improve scoring consistency.

### Scoring independence
Score each metric independently. Do not let one score influence another. It is entirely valid for a response to score high on one metric and low on another (e.g., highly clear but incomplete).

### Cross-model scoring
When multiple responses analyse the same source code, score each response against the **rubric**, not against each other. Two responses for the same code may legitimately receive the same scores, or very different scores — let the rubric guide the decision.

After scoring all responses for a code sample independently, it is acceptable to review whether the relative ordering feels correct (e.g., if response A covers more vulnerability classes than response B, A should not score lower on completeness). If a review leads to an adjustment, note the reason in `rater_notes`.

### Sampling constraint
All samples in this evaluation were selected under a **cross-model correctness constraint**: for each source code sample, all evaluated models arrived at the correct prediction (true positive or true negative). This ensures that explanation quality is assessed for cases where models agree on the correct answer, isolating explanation quality from prediction accuracy.

### Ground truth as reference, not answer key
The `ground_truth_label` tells whether the code is actually vulnerable. Use this to assess whether the response correctly identifies (or justifies) the security status. However, a response that reaches the correct conclusion via flawed reasoning should still receive lower scores for completeness and informativeness.

### Handling uncertain cases
If unsure between two adjacent scores (e.g., 3 vs. 4), lean toward the score that best matches the rubric description. Use `rater_notes` to record the uncertainty (e.g., "borderline 3/4 — solid analysis but missing X").

### Response format variation
Responses vary in format — some use numbered steps, others use bullet points, and others use prose. Do not penalize or reward any particular format. Focus on the substance of the analysis, not its formatting.

### Response length
Longer responses are not inherently better. A concise response that precisely identifies the core issue can outscore a verbose response that buries the key insight in repetition. Conversely, brevity is not inherently better — a response that is too brief to be useful should score accordingly.

## 7. After Scoring

- Save the completed spreadsheet
- Do not discuss individual scores with other raters until the independent scoring phase is complete
- After all raters have submitted independent scores, a disagreement resolution session will be scheduled for items with divergent ratings
