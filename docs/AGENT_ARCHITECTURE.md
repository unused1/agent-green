# Agent Architecture Overview

## 📋 Summary

This document describes the multi-agent architectures used in RQ2 experiments, comparing **Dual-Agent** and **Multi-Agent** designs for both vulnerability detection and code generation tasks.

---

## 🏗️ Architecture Comparison

| Aspect | Dual-Agent | Multi-Agent |
|--------|-----------|-------------|
| **Agents** | 2 specialized agents | 4 specialized agents |
| **Pattern** | Adversarial debate | Structured deliberation |
| **Turns** | 2 sequential turns | 4 sequential turns |
| **Complexity** | Lower token usage | Higher token usage |
| **Use Case** | Fast, focused analysis | Comprehensive, deliberative analysis |

---

## 🔍 Dual-Agent Architecture

### Vulnerability Detection (2 Agents)

**Pattern**: Adversarial Debate

```
Code Input
    ↓
┌─────────────────────────────────────────┐
│  Turn 1: Code Author                    │
│  - Defends/explains the code            │
│  - Highlights intended functionality    │
│  - Provides context for design choices  │
└─────────────────────────────────────────┘
    ↓ (Author's defense)
┌─────────────────────────────────────────┐
│  Turn 2: Security Analyst               │
│  - Analyzes code + author's defense     │
│  - Identifies vulnerabilities           │
│  - Makes FINAL DECISION (JSON format)   │
└─────────────────────────────────────────┘
    ↓
Final Decision (1=vulnerable, 0=safe)
```

**Agent Roles**:

1. **Code Author** (`code_author_agent`)
   - **System Prompt**: `SYS_MSG_CODE_AUTHOR_DUAL_[FEW/ZERO]_SHOT`
   - **Task Prompt**: `DUAL_AGENT_TASK_CODE_SUBMISSION`
   - **Role**: Defends the code snippet
   - **Task**: _"Explain or justify [code] behavior as if you implemented it. Describe its intent and design choices. Be honest about potential risky parts."_
   - **Output**: Explanation/defense of implementation choices

2. **Security Analyst** (`security_analyst_agent`)
   - **System Prompt**: `SYS_MSG_SECURITY_ANALYST_[FEW/ZERO]_SHOT`
   - **Task Prompt**: `DUAL_AGENT_TASK_FINAL_DECISION` + `DUAL_AGENT_ANALYST_EMPHASIS_WRAPPER`
   - **Role**: Produces final vulnerability decision
   - **Task**: _"Review the Code Author's explanation. Decide whether code contains vulnerability. **When in doubt, err on the side of caution.**"_
   - **Output**: JSON with `vulnerability_detected` (boolean), `vulnerabilities` array, and `analysis` (reasoning)
   - **Special Note**: Includes emphasis wrapper that instructs: _"When in doubt, err on the side of caution. Even minor issues should be flagged. Absence of security measures is often itself a vulnerability."_

**Implementation**: `src/dual_agent_vuln.py:143-166, 216-243`

**Key Features**:
- Adversarial perspective balances false positives
- Code Author provides context that may explain suspicious patterns
- Security Analyst has final authority with full context
- **Emphasis wrapper** (line 231-234) increases sensitivity to vulnerabilities

---

### Code Generation (2 Agents)

**Pattern**: Programmer → Reviewer

```
Problem Specification
    ↓
┌─────────────────────────────────────────┐
│  Turn 1: Programmer                     │
│  - Implements initial solution          │
│  - Writes complete Python code          │
└─────────────────────────────────────────┘
    ↓ (Initial code)
┌─────────────────────────────────────────┐
│  Turn 2: Refiner/Reviewer               │
│  - Reviews initial implementation       │
│  - Refines and improves code            │
│  - Produces FINAL CODE                  │
└─────────────────────────────────────────┘
    ↓
Final Code Solution
```

**Agent Roles**:

1. **Programmer** (`programmer`)
   - **System Prompt**: `SYS_MSG_PROGRAMMER_[FEW/ZERO]_SHOT`
   - **Task Prompt**: `DUAL_AGENT_TASK_CODE_GENERATION`
   - **Role**: Initial code implementation
   - **Task**: _"Implement the following function based on its problem statement. Provide the complete Python function implementation only."_
   - **Output**: Working Python code

2. **Refiner/Reviewer** (`refiner`)
   - **System Prompt**: `SYS_MSG_CODE_REVIEWER_[FEW/ZERO]_SHOT`
   - **Task Prompt**: `DUAL_AGENT_TASK_CODE_REVIEW`
   - **Role**: Review and refine code
   - **Task**: _"Review and refine the implementation. If code is correct, return it unchanged. If you find any issue, fix it. Output only Python code."_
   - **Output**: Improved final code
   - **Behavior Rules**:
     - If correct → returns code unchanged
     - If missing imports → adds them
     - If logical/syntax errors → fixes them
     - Focus: Correctness and completeness only (not style)

**Implementation**: `src/dual_agent_code_generation.py:62-78, 206-234`

**Key Features**:
- Simple two-stage pipeline
- Refiner can fix bugs or improve initial implementation
- Final code from Refiner used for evaluation (line 234)
- Refiner focuses strictly on correctness, not style

---

## 🌐 Multi-Agent Architecture

### Vulnerability Detection (4 Agents)

**Pattern**: Structured Deliberation with Sequential Phases

```
Code Input
    ↓
┌─────────────────────────────────────────┐
│  Phase 1: Security Researcher           │
│  - Identifies potential vulnerabilities │
│  - Analyzes security implications       │
│  - Outputs JSON list of findings        │
└─────────────────────────────────────────┘
    ↓ (Researcher findings)
┌─────────────────────────────────────────┐
│  Phase 2: Code Author                   │
│  - Responds to researcher's findings    │
│  - Defends or acknowledges issues       │
│  - Proposes mitigations                 │
└─────────────────────────────────────────┘
    ↓ (Author's response)
┌─────────────────────────────────────────┐
│  Phase 3: Moderator                     │
│  - Provides neutral summary             │
│  - Compares both perspectives           │
│  - Identifies consensus/disagreement    │
└─────────────────────────────────────────┘
    ↓ (Moderator summary)
┌─────────────────────────────────────────┐
│  Phase 4: Review Board                  │
│  - Makes FINAL VERDICTS (JSON)          │
│  - Assesses severity                    │
│  - Recommends actions                   │
└─────────────────────────────────────────┘
    ↓
Final Decision (valid/invalid per vulnerability)
```

**Agent Roles**:

1. **Security Researcher** (`security_researcher_agent`)
   - **System Prompt**: `SYS_MSG_SECURITY_RESEARCHER_[FEW/ZERO]_SHOT`
   - **Task Prompt**: `MULTI_AGENT_TASK_SECURITY_RESEARCHER`
   - **Role**: Initial vulnerability identification
   - **Task**: _"Analyze the following code for vulnerabilities."_
   - **Output**: JSON list `[{vulnerability, reason, impact}]`

2. **Code Author** (`code_author_agent`)
   - **System Prompt**: `SYS_MSG_CODE_AUTHOR_[FEW/ZERO]_SHOT`
   - **Task Prompt**: `MULTI_AGENT_TASK_CODE_AUTHOR`
   - **Role**: Defense and mitigation proposals
   - **Task**: _"The Security Researcher found: [findings]. Please respond to each finding."_
   - **Output**: JSON responses `[{vulnerability, response-type, reason}]`
   - **Response Types**: mitigation, refutation, acknowledgment

3. **Moderator** (`moderator_agent`)
   - **System Prompt**: `SYS_MSG_MODERATOR_[FEW/ZERO]_SHOT`
   - **Task Prompt**: `MULTI_AGENT_TASK_MODERATOR`
   - **Role**: Neutral summary of debate
   - **Task**: _"Provide a neutral summary of this discussion between Security Researcher and Code Author."_
   - **Output**: JSON `{security_researcher_summary, author_summary}`

4. **Review Board** (`review_board_agent`)
   - **System Prompt**: `SYS_MSG_REVIEW_BOARD_[FEW/ZERO]_SHOT`
   - **Task Prompt**: `MULTI_AGENT_TASK_REVIEW_BOARD`
   - **Role**: Final authoritative decision
   - **Task**: _"Review and decide based on: Moderator Summary, Original Code, Security Researcher Analysis, Code Author Response."_
   - **Output**: JSON array `[{vulnerability, decision, severity, recommended_action, reason}]`
   - **Decision Values**: valid, invalid, partially valid

**Implementation**: `src/multi_agent_vuln_detection_four_agents.py:63-107, 243-287`

**Key Features**:
- **Separation of concerns**: Different agents for detection, defense, mediation, and decision
- **Structured deliberation**: Each phase builds on previous phases (line 243-287)
- **Neutral moderation**: Moderator provides balanced summary without bias
- **Authoritative verdict**: Review Board makes final call based on full discussion
- **Comprehensive context**: Review Board receives ALL previous outputs (line 276-287)

---

### Code Generation (4 Agents)

**Pattern**: Requirements → Implementation → Review → Refinement

```
Problem Specification
    ↓
┌─────────────────────────────────────────┐
│  Phase 1: Requirements Analyst          │
│  - Identifies key requirements          │
│  - Highlights challenges                │
│  - Clarifies edge cases                 │
└─────────────────────────────────────────┘
    ↓ (Requirements analysis)
┌─────────────────────────────────────────┐
│  Phase 2: Programmer                    │
│  - Implements solution                  │
│  - Addresses identified requirements    │
│  - Produces initial code                │
└─────────────────────────────────────────┘
    ↓ (Initial code)
┌─────────────────────────────────────────┐
│  Phase 3: Moderator                     │
│  - Reviews code correctness             │
│  - Checks completeness                  │
│  - Identifies potential issues          │
└─────────────────────────────────────────┘
    ↓ (Moderator verdict)
┌─────────────────────────────────────────┐
│  Phase 4: Review Board (Conditional)    │
│  - Executes ONLY if issues found        │
│  - Provides corrected implementation    │
│  - Ensures all requirements met         │
└─────────────────────────────────────────┘
    ↓
Final Code Solution
```

**Agent Roles**:

1. **Requirements Analyst** (`requirements_analyst`)
   - **System Prompt**: `SYS_MSG_REQUIREMENTS_ANALYST_[ZERO_SHOT]` or `SYS_MSG_REQUIREMENTS_ANALYST`
   - **Task Prompt**: `MULTI_AGENT_TASK_REQUIREMENTS_ANALYST_ZERO_SHOT` or `MULTI_AGENT_TASK_ANALYST`
   - **Role**: Analyze and clarify requirements
   - **Task**: _"Analyze the following programming problem. List the main requirements and challenges in 3-5 concise bullet points."_
   - **Output**: Bulleted list of requirements and challenges

2. **Programmer** (`programmer`)
   - **System Prompt**: `SYS_MSG_PROGRAMMER_MA_[ZERO_SHOT]` or `SYS_MSG_PROGRAMMER_MA`
   - **Task Prompt**: `MULTI_AGENT_TASK_PROGRAMMER_[ZERO_SHOT]` or `MULTI_AGENT_TASK_PROGRAMMER`
   - **Role**: Implement solution based on requirements
   - **Task**: _"Based on this requirements analysis: [analyst_findings], implement the following function. Include all necessary imports and handle all edge cases."_
   - **Output**: Complete Python implementation with imports
   - **Guidelines**: Always include typing imports (List, Tuple, Optional), handle edge cases

3. **Moderator** (`moderator`)
   - **System Prompt**: `SYS_MSG_MODERATOR_CODE_[ZERO_SHOT]` or `SYS_MSG_MODERATOR_CODE`
   - **Task Prompt**: `MULTI_AGENT_TASK_MODERATOR_CODE`
   - **Role**: Review correctness and completeness
   - **Task**: _"Review this implementation. Check for: (1) Missing imports, (2) Requirement coverage, (3) Logical correctness. State whether code is correct or contains bugs."_
   - **Output**: Approval ("CODE LOOKS CORRECT") or list of issues
   - **Focus**: Logic, imports, edge cases only (ignores style)

4. **Review Board** (`review_board`)
   - **System Prompt**: `SYS_MSG_REVIEW_BOARD_CODE_[ZERO_SHOT]` or `SYS_MSG_REVIEW_BOARD_CODE`
   - **Task Prompt**: `MULTI_AGENT_TASK_REVIEW_BOARD_CODE`
   - **Role**: Final refinement (conditional)
   - **Task**: _"Provide the final assessment and corrected implementation based on moderator feedback. Ensure all imports and requirements are included."_
   - **Output**: Final corrected implementation
   - **Trigger Condition**: Only executes if moderator identifies issues

**Implementation**: `src/multi_agent_code_generation.py:69-103, 239-292`

**Optimization**: Phase 4 is **skipped** if moderator approves the code:
```python
# Line 268-278
code_approved = ("CODE LOOKS CORRECT" in moderator_upper or
                 "CORRECT" in moderator_upper or
                 len(moderator_summary.strip()) < 20)

if code_approved:
    # Skip Turn 4 - use initial code
    final_code = initial_code
    stats['skipped_review'] += 1
else:
    # Execute Turn 4 - Review Board revision
```

**Key Features**:
- **Requirements-driven**: Analyst clarifies requirements upfront
- **Systematic review**: Moderator checks before refinement
- **Conditional refinement**: Skip Phase 4 if code is already correct (efficiency)
- **Lower token usage**: Skipping unnecessary refinement reduces costs

---

## 📊 Experimental Results Summary

### Token Usage Comparison (from complete cross-experiment table)

**Vulnerability Detection**:
| Configuration | Avg Tokens |
|--------------|------------|
| RQ1 Single-Agent 30B Instruct | ~1,512 |
| RQ1 Single-Agent 30B Thinking | ~5,557 |
| RQ2 Dual-Agent 30B Instruct Few-shot | 479 |
| RQ2 Multi-Agent 30B Instruct Few-shot | 1,438 |
| RQ2 Multi-Agent 30B Thinking Few-shot | 8,683 |

**Code Generation**:
| Configuration | Avg Tokens |
|--------------|------------|
| RQ1 Single-Agent 30B Instruct | 230-231 |
| RQ2 Dual-Agent 30B Instruct Few-shot | 121 |
| RQ2 Multi-Agent 30B Instruct Few-shot | 1,545 |
| RQ2 Multi-Agent 30B Thinking Zero-shot | 7,724 |

### Performance Insights

**Vulnerability Detection**:
- Best Overall: RQ1 Single-Agent 4B Thinking Few-shot = **58.88% F1**
- Best Dual-Agent: 30B Instruct Few-shot = **51.76% F1**
- Multi-Agent range: **32.70-49.74% F1**

**Code Generation**:
- Best Overall: Multiple configs at **100% Pass@1**
- Dual-Agent range: **46.58-100% Pass@1**
- Multi-Agent range: **90.24-100% Pass@1**

---

## 🔧 Implementation Details

### Communication Pattern

All architectures use **sequential turn-taking**:
```python
# Dual-Agent Example (vulnerability detection)
author_submission = code_author.generate_reply(messages=[{
    "role": "user",
    "content": author_task
}])

analyst_feedback = security_analyst.generate_reply(messages=[{
    "role": "user",
    "content": analyst_task  # includes author_submission
}])
```

```python
# Multi-Agent Example (code generation)
res1 = analyst.generate_reply(messages=[{"content": analyst_task, "role": "user"}])
res2 = programmer.generate_reply(messages=[{"content": programmer_task, "role": "user"}])
res3 = moderator.generate_reply(messages=[{"content": moderator_task, "role": "user"}])
res4 = review_board.generate_reply(messages=[{"content": review_task, "role": "user"}])
```

**Note**: Each agent receives **context from previous agents** but agents do **NOT** have shared conversation history. Each turn is a fresh `generate_reply()` call with explicit context passing via task prompts.

### Prompting Strategies

Both architectures support:
- **Zero-shot**: No examples provided
- **Few-shot**: Examples included in system prompts

System prompts are selected based on `--prompt_type` argument:
```python
if args.prompt_type == "few_shot":
    code_author_prompt = config.SYS_MSG_CODE_AUTHOR_DUAL_FEW_SHOT
    analyst_prompt = config.SYS_MSG_SECURITY_ANALYST_FEW_SHOT
else:
    code_author_prompt = config.SYS_MSG_CODE_AUTHOR_DUAL_ZERO_SHOT
    analyst_prompt = config.SYS_MSG_SECURITY_ANALYST_ZERO_SHOT
```

### Energy Tracking

All experiments use **CodeCarbon** for emissions tracking:
```python
tracker = OfflineEmissionsTracker(
    project_name=exp_name,
    output_dir=result_dir,
    save_to_file=True,
    country_iso_code="CAN"
)
tracker.start()
# ... run inference ...
emissions = tracker.stop()
```

---

## 📁 Source Files

| File | Description |
|------|-------------|
| `src/dual_agent_vuln.py` | Dual-agent vulnerability detection |
| `src/dual_agent_code_generation.py` | Dual-agent code generation |
| `src/multi_agent_vuln_detection_four_agents.py` | Multi-agent (4) vulnerability detection |
| `src/multi_agent_code_generation.py` | Multi-agent (4) code generation |
| `src/agent_utils_vuln.py` | Agent creation utilities for vulnerability tasks |
| `src/config.py` | System prompts and task templates |
| `src/resume_utils.py` | Experiment resume/checkpoint functionality |

---

## 🎯 Design Rationale

### Why Dual-Agent?
- **Efficiency**: Lower token usage, faster execution
- **Focused**: Specialized debate between two perspectives
- **Simplicity**: Easier to debug and understand

### Why Multi-Agent?
- **Deliberation**: More thorough analysis through multiple perspectives
- **Separation of Concerns**: Each agent has a specific role
- **Balanced Decision-Making**: Neutral moderator + authoritative review board
- **Comprehensive**: Better for complex scenarios requiring multi-step reasoning

### Trade-offs
- **Dual-Agent**: Fast but may miss nuanced vulnerabilities
- **Multi-Agent**: Thorough but higher computational cost (2-3x tokens)

---

## 📝 Task Prompt Variables Reference

### Dual-Agent Vulnerability Detection

| Prompt Constant | Variables | Definition | Description |
|----------------|-----------|------------|-------------|
| `DUAL_AGENT_TASK_CODE_SUBMISSION` | `{code}` | `config.py:1019` | Code Author explains the code's intent and design choices |
| `DUAL_AGENT_TASK_FINAL_DECISION` | `{code}`, `{author_response}` | `config.py:1027` | Security Analyst reviews author's defense and makes final JSON decision |
| `DUAL_AGENT_ANALYST_EMPHASIS_WRAPPER` | `{analyst_task}` | `config.py:1045` | Wrapper that increases vulnerability detection sensitivity |

### Dual-Agent Code Generation

| Prompt Constant | Variables | Definition | Description |
|----------------|-----------|------------|-------------|
| `DUAL_AGENT_TASK_CODE_GENERATION` | `{prompt}` | `config.py:1332` | Programmer implements the function from problem statement |
| `DUAL_AGENT_TASK_CODE_REVIEW` | `{prompt}`, `{generated_code}` | `config.py:1379` | Refiner reviews and fixes code if needed |

### Multi-Agent Vulnerability Detection (4 Phases)

| Prompt Constant | Variables | Definition | Description |
|----------------|-----------|------------|-------------|
| `MULTI_AGENT_TASK_SECURITY_RESEARCHER` | `{code}` | `config.py:1135` | Phase 1: Researcher identifies vulnerabilities |
| `MULTI_AGENT_TASK_CODE_AUTHOR` | `{researcher_findings}`, `{code}` | `config.py:1140` | Phase 2: Author responds to each finding |
| `MULTI_AGENT_TASK_MODERATOR` | `{researcher_findings}`, `{author_response}` | `config.py:1148` | Phase 3: Moderator provides neutral summary |
| `MULTI_AGENT_TASK_REVIEW_BOARD` | `{moderator_summary}`, `{code}`, `{researcher_findings}`, `{author_response}` | `config.py:1154` | Phase 4: Review Board makes final verdict |

### Multi-Agent Code Generation (4 Phases)

| Prompt Constant | Variables | Definition | Description |
|----------------|-----------|------------|-------------|
| `MULTI_AGENT_TASK_REQUIREMENTS_ANALYST_ZERO_SHOT` | `{prompt}` | `config.py:1425` | Phase 1: Analyst identifies 3-5 key requirements |
| `MULTI_AGENT_TASK_ANALYST` | `{prompt}` | `config.py:1419` | Phase 1: Analyst (few-shot version) |
| `MULTI_AGENT_TASK_PROGRAMMER_ZERO_SHOT` | `{analyst_findings}`, `{prompt}` | `config.py:1462` | Phase 2: Programmer implements based on requirements |
| `MULTI_AGENT_TASK_PROGRAMMER` | `{analyst_findings}`, `{prompt}` | `config.py:1452` | Phase 2: Programmer (few-shot version) |
| `MULTI_AGENT_TASK_MODERATOR_CODE` | `{prompt}`, `{programmer_response}` | `config.py:1493` | Phase 3: Moderator checks correctness |
| `MULTI_AGENT_TASK_REVIEW_BOARD_CODE` | `{prompt}`, `{moderator_summary}` | `config.py:1529` | Phase 4: Review Board provides corrected implementation (conditional) |

---

## 📚 Related Documentation

- `docs/RQ2_Experiment_Tracking.md` - Experiment execution details
- `docs/ANALYSIS_SUMMARY_RQ2.md` - Complete experimental results
- `docs/rq2_experiment_design.md` - Experimental design rationale
- `results/analysis/rq2/` - Analysis outputs and visualizations
- `src/config.py` - Complete prompt definitions and system messages
