# RQ3 Phase A: Rater Instructions for Vulnerability Analysis Explanation Quality Evaluation

## 1. Task Overview

We are evaluating the quality of AI-generated vulnerability analyses. The goal is to assess how well the AI's response explains its vulnerability assessment.

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

## 3. Evaluation Procedure

For each sample, follow these steps in order:

### Step 1: Read the source code

Read the function in `source_code`. Form an initial understanding of what the code does, its inputs, control flow, and any potential security concerns.

### Step 2: Check the ground truth

Read `ground_truth_label` to see if the code is vulnerable or safe. For vulnerable samples, read the `cwe` and `cve_desc` columns to understand what the known vulnerability is. This provides context for assessing the response — it does not mean the AI had access to this information.

### Step 3: Read the AI's response

Read `response_text` carefully. This is the AI's full analysis of the code. Some responses may be short and direct; others may be long and detailed. Both are valid — the scoring rubric accounts for this.

### Step 4: Score each metric independently

Score all four metrics using the rubrics in Section 4. Important:

- Score each metric on its own merits. E.g. A response can be highly clear (high clarity) but miss important issues (low completeness).
- Use the full 1–5 range.
- Do not adjust scores based on response length alone. A short response that precisely identifies the core issue can score well; a long response that repeats itself without substance should not.

### Step 5: Add notes

Optional but encouraged for any other scores where the reasoning may not be obvious. Notes are valuable for resolving disagreements between raters.

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

## 5. General Guidelines

### Scoring independence
Score each metric independently. Do not let one score influence another. It is entirely valid for a response to score high on one metric and low on another (e.g., highly clear but incomplete).

### Ground truth as reference, not answer key
The `ground_truth_label` tells whether the code is actually vulnerable. Use this to assess whether the response correctly identifies (or justifies) the security status. However, a response that reaches the correct conclusion via flawed reasoning should still receive lower scores for completeness and informativeness.

### Handling uncertain cases
If unsure between two adjacent scores (e.g., 3 vs. 4), lean toward the score that best matches the rubric description. Use `rater_notes` to record the uncertainty (e.g., "borderline 3/4 — solid analysis but missing X").

### Response format variation
Responses vary in format — some use numbered steps, others use bullet points, and others use prose. Do not penalize or reward any particular format. Focus on the substance of the analysis, not its formatting.

### Response length
Longer responses are not inherently better. A concise response that precisely identifies the core issue can outscore a verbose response that buries the key insight in repetition. Conversely, brevity is not inherently better — a response that is too brief to be useful should score accordingly.

## 6. After Scoring

- Save the completed spreadsheet
- Do not discuss individual scores with other raters until the independent scoring phase is complete
- After all raters have submitted independent scores, a disagreement resolution session will be scheduled for items with divergent ratings
