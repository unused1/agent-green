# RQ3 Phase A: Rater Instructions (Concise)

## Task

Score the quality of AI-generated vulnerability analyses. All models predicted correctly (TP or TN) — we are evaluating **explanation quality**, not prediction accuracy. The rater sheet is **blinded**: model identity is not visible.

## Spreadsheet Columns

| Column | Action |
|--------|--------|
| `source_code` | Read the C/C++ function under review |
| `ground_truth_label` | "vulnerable" or "safe" — use as reference |
| `cwe` / `cve_desc` | CWE and CVE info (vulnerable samples only) — use as reference |
| `response_text` | **Score this** using the rubric below |
| `completeness_score` | **Fill in** (1–5) |
| `clarity_score` | **Fill in** (1–5) |
| `actionability_score` | **Fill in** (1–5) |
| `informativeness_score` | **Fill in** (1–5) |
| `rater_notes` | **Fill in** (optional but encouraged for non-obvious scores) |

Consecutive rows sharing the same `source_code` are different models analysing the same function. Score each row independently.

## Procedure

1. **Read the source code** — understand the function's purpose, inputs, and control flow (once per code sample).
2. **Check ground truth** — read `ground_truth_label`, `cwe`, and `cve_desc` for context.
3. **Score each response independently** — do not anchor one model's score to another's. Use the full 1–5 range. Do not reward or penalise based on length or format alone.
4. **Add notes** — especially for borderline scores or when a response covers something others missed.

## Scoring Rubric

All metrics use a 1–5 Likert scale. Score based on the descriptions below.

### Completeness

*Does the response cover the vulnerability mechanism or justify why the code is safe, addressing relevant factors including edge cases, attack vectors, and underlying assumptions?*

| Score | Description |
|-------|-------------|
| **1 — Severely incomplete** | States only a conclusion (e.g., "No vulnerability") with no supporting analysis, or addresses only a trivial aspect while ignoring the core security concern. |
| **2 — Major gaps** | Covers one aspect of the security analysis but misses significant factors. For vulnerable code: identifies the general area (e.g., "memory issue") but not the specific mechanism. For safe code: checks one category but overlooks others. |
| **3 — Adequate** | Addresses the key vulnerability mechanism or safety rationale with minor gaps. The main reasoning is present but lacks depth on edge cases, preconditions, or secondary concerns. A reader would understand the core issue but might need to investigate further. |
| **4 — Thorough** | Covers the vulnerability mechanism or safety justification comprehensively, including relevant edge cases and contributing factors. Minor aspects may be unaddressed, but the analysis leaves few open questions about the primary security concern. |
| **5 — Exhaustive** | Fully covers the security analysis with no meaningful gaps. Addresses the mechanism, scope, preconditions, edge cases, and any secondary concerns. A developer could act on this analysis without further investigation. |

### Clarity

*Is the response logically structured, free of ambiguities, and using precise technical terms?*

| Score | Description |
|-------|-------------|
| **1 — Incoherent** | Disorganized, contradictory, or incomprehensible. The reader cannot follow the argument. May contain internally inconsistent claims (e.g., simultaneously stating the code is safe and describing a vulnerability). |
| **2 — Confusing** | Has a discernible argument but is poorly organized, uses vague language, or contains misleading statements. The reader must re-read multiple times to extract the key points. Technical terms may be used incorrectly. |
| **3 — Adequate** | Reasonably structured and understandable on a single read. Some sections may be verbose or slightly ambiguous, but the overall argument is clear. Technical terminology is mostly correct. |
| **4 — Clear** | Well-organized with logical flow from analysis to conclusion. Uses precise technical language. Minor imprecisions may exist but do not impede understanding. Easy to follow. |
| **5 — Exemplary** | Exceptionally well-structured with clear progression. Every claim is precise and unambiguous. Technical terminology is used correctly and consistently. Could serve as a reference for how to communicate a vulnerability analysis. |

### Actionability

*Does the response provide actionable insights such as highlighting vulnerable lines, suggesting patches, or describing specific risks and mitigations?*

| Score | Description |
|-------|-------------|
| **1 — Not actionable** | Provides no guidance on what to do with the finding. States only a generic conclusion with no reference to specific code locations, risks, or remediation. |
| **2 — Minimally actionable** | References the general area of concern but lacks specifics. A developer would know *something* might be wrong but not *where* or *how* to address it. |
| **3 — Moderately actionable** | Identifies specific code constructs or lines involved, and gives a general direction for remediation (e.g., "add bounds checking"). A developer could begin investigating but would need additional research. |
| **4 — Actionable** | Points to specific code locations, explains the risk concretely, and suggests a plausible fix or mitigation strategy. A developer with domain knowledge could act on this with minimal additional research. |
| **5 — Immediately actionable** | Provides precise code references, a concrete fix or mitigation, and explains why the fix resolves the issue. A developer could implement the remediation directly from this analysis. |

**Note on safe code**: For samples labeled "safe," low actionability scores (1–2) are expected when the response does not suggest specific remediation or highlight vulnerable lines — since there is no vulnerability to remediate. If scoring actionability ≤ 2 for safe code, briefly note the rationale in `rater_notes` (e.g., "safe code — no remediation applicable").

### Informativeness

*Does the response offer meaningful, non-redundant, and technically insightful information beyond superficial observations?*

| Score | Description |
|-------|-------------|
| **1 — Uninformative** | Contains only trivial observations restating the code's surface behavior (e.g., "This function takes two parameters"), or is largely filler text with no security-relevant content. |
| **2 — Superficial** | Makes security-relevant observations but at a surface level only. States obvious facts about the code without deeper analysis. May contain filler or repetitive content that dilutes the useful information. |
| **3 — Adequate** | Provides some genuine technical insight about the code's security properties. The analysis goes beyond surface observations but may not reveal anything a competent developer wouldn't notice on their own. |
| **4 — Insightful** | Offers meaningful technical depth — identifies non-obvious interactions, explains *why* a pattern is dangerous (or safe), and demonstrates understanding of the underlying security principles. Contains minimal filler or redundancy. |
| **5 — Highly insightful** | Provides expert-level analysis with novel or non-obvious observations. Demonstrates deep understanding of the vulnerability class, the specific codebase patterns, and their security implications. Every sentence adds value. |

## Quick-Reference Indicators

When scoring, look for these patterns:

| Metric | Positive signals | Negative signals |
|--------|-----------------|-----------------|
| **Completeness** | Discusses specific mechanism, edge cases, multiple relevant vuln classes; for safe code explains *why* classes don't apply | Generic assertions; only one aspect covered; "no vulnerability" without justification |
| **Clarity** | Logical flow, specific code references, correct terminology, no redundancy | Disorganized, vague references, incorrect terms, boilerplate filler |
| **Actionability** | Specific code locations, concrete fix/mitigation, explains what's missing | Generic advice, restates conclusion as recommendation, no remediation direction |
| **Informativeness** | Explains *why* not just *what*, counterfactual reasoning, non-obvious insights | Restates surface behaviour, filler/repetition, obvious observations only |

## Key Reminders

- **Score each metric independently** — a response can be clear but incomplete.
- **Score against the rubric, not against other responses** — review relative ordering after if desired.
- **Ground truth is a reference, not an answer key** — correct conclusion via flawed reasoning still scores lower.
- **Borderline scores** — pick the best rubric match; note uncertainty in `rater_notes`.
- **After scoring** — save the spreadsheet; do not discuss scores with other raters until independent scoring is complete.
