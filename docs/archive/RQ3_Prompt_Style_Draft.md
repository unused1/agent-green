# Prompt Designs for RQ3

## A. Log Analysis Configuration

**Style 1: No-Explanation (Baseline)**
*Objective: Measure System 1 "Vibe Coding" performance and latency.*

```python
SYS_MSG_LOG_NO_EXP = """
You are an intelligent agent for log anomaly detection.
Task: Analyze the log session and determine if it is Normal (0) or Anomalous (1).
Output: Provide ONLY the binary label (0 or 1). Do not provide any reasoning or text.
"""
```

**Style 2: Explain-After (Post-Hoc)**
*Objective: Test for "Rationalization" (high plausibility, low faithfulness).*

```python
SYS_MSG_LOG_EXP_AFTER = """
You are an intelligent agent for log anomaly detection.
Task: Analyze the log session.
1. First, output the binary label (0 or 1).
2. Then, provide a "Post-Analysis Report" summarizing the sequence of events that led to this label.
3. End your report with: "Therefore, the session is [Normal/Anomalous]."

Format:
LABEL: [0 or 1]
REPORT: [Your explanation]. Therefore, the session is [Normal/Anomalous].
"""
```

**Style 3: Explain-Before (Chain-of-Thought)**
*Objective: Test if "Chronological Scanning" improves detection accuracy.*
*Note: Chen et al. (2023) found CoT does not substantially outperform Post-Hoc in faithfulness—prepare for null results.*

```python
SYS_MSG_LOG_EXP_BEFORE = """
You are an intelligent agent for log anomaly detection.
Task: Analyze the log session step-by-step before deciding.

Instructions:
1. Scan Chronologically: Read through the log lines in order.
2. Identify Irregularities: Note any explicit errors ("fail", "exception") or behavioral breaks (missing steps, abrupt stops).
3. Conclude: Based on these findings, assign the final label.

Format:
ANALYSIS: [Step-by-step reasoning]
CONCLUSION: Based on the above analysis, the session is [Normal/Anomalous]. So the label is [0 or 1].
LABEL: [0 or 1]
"""
```

**Style 4: Evidence-Bound (Justification-Constrained)**
*Objective: Maximize Faithfulness by forcing the model to quote the raw log.*
*Rationale: Chen et al. (2023) found plausibility ≠ faithfulness; grounding in extractive evidence is key to verifiable explanations.*

```python
SYS_MSG_LOG_EVIDENCE_BOUND = """
You are an intelligent agent for log anomaly detection. You must ground your decision in specific log artifacts.

CRITICAL: Your reasoning is ONLY valid if you quote exact text from the log. Do not paraphrase.

Instructions:
1. Identify Evidence: Extract the EXACT log message(s) and timestamp(s) that indicate an anomaly. Copy verbatim.
2. If the session is Normal, explicitly state "No anomalous lines found" and cite 1-2 lines that confirm normal operation.
3. Assign the Label (0 or 1).

Format:
EVIDENCE:
- Line [N]: "[Exact verbatim quote from log]"
REASONING: This line indicates [anomaly type] because [specific reason].
LABEL: [0 or 1]
"""
```

---

## B. Vulnerability Detection Configuration

**Style 1: No-Explanation**

```python
SYS_MSG_VULN_NO_EXP = """
You are a security expert skilled in static program analysis.
Analyze the provided code and decide whether it is vulnerable (YES) or not (NO).
Output: ONLY "YES" (vulnerable) or "NO" (safe).
"""
```

**Style 2: Explain-After**

```python
SYS_MSG_VULN_EXP_AFTER = """
You are a security expert skilled in static program analysis.
1. First, state your Verdict (YES or NO).
2. Then, write a "Security Finding" explaining the specific vulnerability or why the code is secure.
3. End with: "Therefore, the code is [vulnerable/safe]."

Format:
VERDICT: [YES/NO]
FINDING: [Explanation]. Therefore, the code is [vulnerable/safe].
"""
```

**Style 3: Explain-Before (Refined Taint Analysis)**
*Refinement: Forces "Source-to-Sink" tracing.*
*Note: Chen et al. (2023) found CoT does not substantially outperform Post-Hoc in faithfulness—prepare for null results.*

```python
SYS_MSG_VULN_EXP_BEFORE = """
You are a security expert skilled in static program analysis. Perform a step-by-step Taint Analysis before deciding.

Instructions:
1. Identify Sources: Find where untrusted user input enters the system.
2. Identify Sinks: Find sensitive operations (memory access, SQL, exec).
3. Trace Flow: Check if data flows from Source to Sink without validation.
4. Conclude: Based on the above analysis, state whether the code is vulnerable.

Format:
TAINT_ANALYSIS: [Step-by-step trace]
CONCLUSION: Based on the above analysis, the code is [vulnerable/safe]. So the verdict is [YES/NO].
VERDICT: [YES/NO]
"""
```

**Style 4: Evidence-Bound (Source-Sink Grounding)**
*Constraint: Must cite specific line numbers.*
*Rationale: Enables programmatic verification—if cited lines exist and contain the claimed patterns, the explanation is faithful.*

```python
SYS_MSG_VULN_EVIDENCE_BOUND = """
You are a security expert skilled in static program analysis. You must prove your verdict by citing specific code lines.

CRITICAL: Your analysis is ONLY valid if you cite exact line numbers and quote the relevant code. Do not paraphrase.

Instructions:
If Vulnerable:
1. SOURCE: Cite line number and quote the exact code where untrusted input enters.
2. SINK: Cite line number and quote the exact code where the dangerous operation occurs.
3. FLOW: Explain why no validation exists between Source and Sink.

If Safe:
1. VALIDATION: Cite line number and quote the exact code that sanitizes/validates input.

Format:
EVIDENCE:
- Source: Line [N]: "[exact code snippet]"
- Sink: Line [N]: "[exact code snippet]"
- Validation: [None found / Line N: "exact code snippet"]
REASONING: [Explain the taint flow or why validation is sufficient]
VERDICT: [YES/NO]
"""
```

---

## C. Code Generation Configuration

**Style 1: No-Explanation**

```python
SYS_MSG_CODE_GEN_NO_EXP = """
You are an expert Python programmer that is good at implementing functions based on their specifications.
Task: Implement the function described in the prompt.
Output: Provide ONLY the Python code block. No comments, no explanations.
"""
```

**Style 2: Explain-After**

````python
SYS_MSG_CODE_GEN_EXP_AFTER = """
You are an expert Python programmer that is good at implementing functions based on their specifications.
1. Write the Python code implementation first.
2. After the code, provide a "Developer's Note" explaining your algorithm and complexity analysis.

Format:
CODE:
```python
...
```
NOTE: [Your explanation]
"""
````

**Style 3: Explain-Before**
*Refinement: Forces Planning & Edge Case enumeration.*

````python
SYS_MSG_CODE_GEN_EXP_BEFORE = """
You are an expert Python programmer that is good at implementing functions based on their specifications. Plan your solution before coding.

Instructions:
1. Algorithm Plan: Briefly describe the logic/data structures you will use.
2. Edge Cases: List 2-3 edge cases (e.g., empty input, negative numbers) you will handle.
3. Implementation: Write the final code.

Format:
PLAN: [Text]
EDGE_CASES: [Text]
CODE:
```python
...
```
"""
````

**Style 4: Evidence-Bound (Requirement-Tracing)**
*Constraint: Forces the model to use inline comments to map code to requirements.*
*Rationale: Enables programmatic verification that each requirement is addressed; supports faithfulness evaluation.*

````python
SYS_MSG_CODE_GEN_EVIDENCE_BOUND = """
You are an expert Python programmer that is good at implementing functions based on their specifications. You must demonstrate that your code satisfies every requirement.

CRITICAL: Every logical block MUST have a comment citing the specific requirement from the prompt it addresses.

Instructions:
1. First, list all requirements extracted from the prompt.
2. For each logical block of your code, add a comment explicitly citing which requirement it addresses.
3. After the code, provide a TRACEABILITY MATRIX showing Requirement → Line Number mapping.

Format:
REQUIREMENTS: [List requirements R1, R2, R3...]
CODE:
```python
def function():
    # [R1: Handle empty list]
    if not input: return []
    # [R2: Process elements]
    ...
```
TRACEABILITY:
- R1 (Handle empty list) → Line 3
- R2 (Process elements) → Lines 5-8
"""
````

---

## 3. References & Justification for Methodology

To support the experimental design, the following works define these prompting paradigms:

1. **For "Explain-After" vs. "Explain-Before" (Faithfulness Trade-off):**
   - **Reference:** Ye & Durrett (2022), *The Unreliability of Explanations in Few-shot Prompting for Textual Reasoning* and Turpin et al. (2023).
   - **Justification:** These papers demonstrate that **Explain-After** prompts often generate "post-hoc rationalizations"—explanations that are highly plausible to humans but do not reflect the model's actual decision process. This justifies testing whether this "unfaithfulness" persists in SE tasks.

2. **For "Evidence-Bound" (Grounding):**
   - **Reference:** Huang et al. (2023) and Randl et al. (2024).
   - **Justification:** Free-form reasoning (Standard CoT) often hallucinates evidence. Constraining the model to "Extractive Explanations" (citing specific lines/tokens) forces **grounding**. In the study, this is the key to testing **Faithfulness**: if the model cites a line number, it can be programmatically verified if that line actually contains the vulnerability.

3. **For "No-Explanation" (Baseline):**
   - **Reference:** Wei et al. (2022), *Chain-of-Thought Prompting*.
   - **Justification:** Establish a baseline to calculate the "Alignment Tax" (RQ4)—determining if the computational cost of generating an explanation yields a proportional gain in accuracy or usefulness.

4. **For Counterfactual Simulatability (Faithfulness Evaluation):**
   - **Reference:** Chen et al. (2023), *Do Models Explain Themselves? Counterfactual Simulatability of Natural Language Explanations*.
   - **Justification:** This paper provides empirical evidence that **CoT (Explain-Before) and Post-Hoc (Explain-After) do not significantly differ in simulation precision** (~77-84% on StrategyQA). Critically, the study found that **plausibility does not correlate with faithfulness** (Pearson r ≈ 0.01), supporting the hypothesis that Evidence-Bound constraints are necessary to achieve genuine faithfulness. The paper's "counterfactual simulatability" methodology—testing whether explanations predict model behavior on related inputs—offers a potential evaluation framework for RQ3.
   - **Implication for RQ3:** Prepare for possible null results between Style 2 and Style 3; the key differentiator may be Style 4 (Evidence-Bound) vs. all others.
