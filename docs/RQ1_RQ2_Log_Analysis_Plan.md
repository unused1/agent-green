# Log Analysis Experiments Plan (RQ1 & RQ2)

## 1. Overview

### 1.1 Research Questions Addressed

**RQ1 (Phase I)**: Do reasoning-enabled LLMs out-perform non-reasoning baselines on **log analysis**?
- Compare Thinking vs Instruct models on log anomaly detection
- Single-Agent (SA) configuration only
- Matched toolchains and budgets

**RQ2 (Phase II)**: How do multi-agent setups compare to single-agent execution on **log analysis**?
- SA vs DA (planner-executor) vs MA (proposer-reviewer)
- Log analysis selected as representative task per research design
- Tests whether agentic orchestration amplifies or substitutes reasoning gains

### 1.2 Model Selection

**Primary Model Family**: Qwen3 (per supervisor guidance)
- **Qwen3-4B-Instruct** / **Qwen3-4B-Thinking**: Smaller model for efficiency comparison
- **Qwen3-30B-A3B-Instruct** / **Qwen3-30B-A3B-Thinking**: Larger model for capability comparison

**Rationale**: Focusing on a single model family allows deeper analysis of reasoning and agentic effects without confounding cross-architecture variability. Cross-architecture validation (Nemotron) was conducted in vulnerability detection and code generation experiments.

### 1.3 Distinction: Log Parsing vs Log Analysis

| Aspect | Log Parsing (Existing) | Log Analysis (New) |
|--------|----------------------|-------------------|
| **Task** | Extract templates from log messages | Detect anomalies, patterns, root causes |
| **Output** | Structured template string | Classification (normal/anomaly) + explanation |
| **Metrics** | Exact match, edit distance, LCS | Accuracy, Precision, Recall, F1 |
| **Ground Truth** | Template strings | Anomaly labels per log sequence |
| **Scripts** | `single_agent.ipynb`, `no_agents.ipynb` | `single_agent_log_analysis.py` |

### 1.4 Why Log Analysis for Phase II

Per the research design (research_question.md):
> "Phase II narrows to two representative tasks where tools materially affect outcomes — log analysis and code generation"

Log analysis benefits from:
- **Log filtering tools**: Filter by severity, time window, component
- **Pattern matching tools**: Regex-based anomaly signatures
- **Aggregation tools**: Count occurrences, frequency analysis

---

## 2. Dataset

### 2.1 HDFS Anomaly Detection Dataset

**Source**: LogHub / Loghub-2.0 (HDFS)

**Reference**:
> Zhu, J., He, S., He, P., Liu, J., & Lyu, M. R. (2023). Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics. arXiv:2008.06448. https://doi.org/10.48550/arXiv.2008.06448

**Original Source**:
> Xu, W., Huang, L., Fox, A., Patterson, D., & Jordan, M. I. (2009). Detecting large-scale system problems by mining console logs. SOSP '09.

### 2.2 Dataset Statistics

| Attribute | Value |
|-----------|-------|
| **Total Sessions** | 385 block-level sessions |
| **Normal Sessions** | 373 (96.9%) |
| **Anomaly Sessions** | 12 (3.1%) |
| **Total Size** | 1.6 MB (session files) |
| **Lines per Session** | Min: 2, Max: 222, Mean: 20.2, Median: 19.0 |

### 2.3 Data Files

```
data/
├── HDFS_385_sampled.log                        # Raw log file (56 KB)
├── HDFS_anomaly_label_385_session_sampled.csv  # Ground truth labels
└── HDFS_385_sampled_sessions/                  # 385 individual session files
    ├── blk_-1020777178747598310.log
    ├── blk_-1062096421709347708.log
    └── ... (383 more)
```

### 2.4 Data Format

**Log message format**:
```
YYMMDD HHMMSS PID LEVEL COMPONENT: MESSAGE
```

**Example**:
```
081110 110842 10054 INFO dfs.DataNode$DataXceiver: Receiving block blk_-1020777178747598310 src: /10.251.215.192:49866 dest: /10.251.215.192:50010
```

**Anomaly label format** (CSV):
```csv
BlockId,Label
blk_-1608999687919862906,Anomaly
blk_7503483334202473044,Normal
```

---

## 3. Task Definition

### 3.1 Primary Task: Session-Level Anomaly Detection

**Input**: Sequence of log messages (session/block)
**Output**: Binary classification (Normal/Anomaly) + Explanation

**Sample Prompt**:
```
Analyze the following HDFS log sequence for anomalies:

[LOG SEQUENCE]
081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_123 terminating
081109 203616 149 INFO dfs.DataNode$PacketResponder: PacketResponder 2 for block blk_123 terminating
081109 203617 150 ERROR dfs.DataNode$PacketResponder: Exception in PacketResponder for block blk_123
...

Based on your analysis:
1. Is this log sequence indicative of an ANOMALY or NORMAL operation?
2. Provide a brief explanation of your reasoning.

Answer format:
Classification: [ANOMALY/NORMAL]
Explanation: [Your reasoning]
```

### 3.2 Anomaly Indicators

Common HDFS anomaly indicators:
- ERROR or WARN log levels
- Block replication failures
- DataNode communication timeouts
- Unexpected termination of services
- Missing or corrupted blocks ("BlockInfo not found")

---

## 4. Experimental Design

### 4.1 Experiment Summary

| Phase | Focus | Experiments |
|-------|-------|-------------|
| Phase I (RQ1) | Reasoning effectiveness (SA only) | 8 |
| Phase II (RQ2) | Agentic moderation (DA + MA) | 16 |
| **Total** | | **24** |

### 4.2 Phase I (RQ1): Reasoning Effectiveness - Single-Agent Only

**Configuration Matrix** (8 experiments):

| Model | Mode | Prompting | Samples | Experiments |
|-------|------|-----------|---------|-------------|
| Qwen3-4B | Instruct | Zero-shot | 385 | 1 |
| Qwen3-4B | Instruct | Few-shot | 385 | 1 |
| Qwen3-4B | Thinking | Zero-shot | 385 | 1 |
| Qwen3-4B | Thinking | Few-shot | 385 | 1 |
| Qwen3-30B-A3B | Instruct | Zero-shot | 385 | 1 |
| Qwen3-30B-A3B | Instruct | Few-shot | 385 | 1 |
| Qwen3-30B-A3B | Thinking | Zero-shot | 385 | 1 |
| Qwen3-30B-A3B | Thinking | Few-shot | 385 | 1 |
| **Total** | | | | **8 experiments** |

### 4.3 Phase II (RQ2): Agentic Moderation - Dual-Agent and Multi-Agent

**Agent Configurations**:

1. **Single-Agent (SA)**: Baseline from Phase I
   - Direct model query with full context

2. **Dual-Agent (DA) - Planner-Executor**:
   - **Planner**: Decomposes log analysis into sub-tasks
   - **Executor**: Performs each sub-task (filtering, pattern matching, classification)

3. **Multi-Agent (MA) - Proposer-Reviewer**:
   - **Analyzer**: Initial anomaly classification
   - **Reviewer**: Validates classification, checks for false positives/negatives
   - **Moderator**: Final decision resolution

**Phase II Experiment Matrix** (16 experiments):

| Model | Mode | Prompting | Agent Config | Experiments |
|-------|------|-----------|--------------|-------------|
| Qwen3-4B | Instruct | Zero-shot | DA | 1 |
| Qwen3-4B | Instruct | Few-shot | DA | 1 |
| Qwen3-4B | Thinking | Zero-shot | DA | 1 |
| Qwen3-4B | Thinking | Few-shot | DA | 1 |
| Qwen3-4B | Instruct | Zero-shot | MA | 1 |
| Qwen3-4B | Instruct | Few-shot | MA | 1 |
| Qwen3-4B | Thinking | Zero-shot | MA | 1 |
| Qwen3-4B | Thinking | Few-shot | MA | 1 |
| Qwen3-30B-A3B | Instruct | Zero-shot | DA | 1 |
| Qwen3-30B-A3B | Instruct | Few-shot | DA | 1 |
| Qwen3-30B-A3B | Thinking | Zero-shot | DA | 1 |
| Qwen3-30B-A3B | Thinking | Few-shot | DA | 1 |
| Qwen3-30B-A3B | Instruct | Zero-shot | MA | 1 |
| Qwen3-30B-A3B | Instruct | Few-shot | MA | 1 |
| Qwen3-30B-A3B | Thinking | Zero-shot | MA | 1 |
| Qwen3-30B-A3B | Thinking | Few-shot | MA | 1 |
| **Total** | | | | **16 experiments** |

### 4.4 Full Experiment Matrix

| # | Model | Mode | Prompting | Agent | Phase |
|---|-------|------|-----------|-------|-------|
| 1 | Qwen3-4B | Instruct | Zero-shot | SA | I |
| 2 | Qwen3-4B | Instruct | Few-shot | SA | I |
| 3 | Qwen3-4B | Thinking | Zero-shot | SA | I |
| 4 | Qwen3-4B | Thinking | Few-shot | SA | I |
| 5 | Qwen3-30B | Instruct | Zero-shot | SA | I |
| 6 | Qwen3-30B | Instruct | Few-shot | SA | I |
| 7 | Qwen3-30B | Thinking | Zero-shot | SA | I |
| 8 | Qwen3-30B | Thinking | Few-shot | SA | I |
| 9 | Qwen3-4B | Instruct | Zero-shot | DA | II |
| 10 | Qwen3-4B | Instruct | Few-shot | DA | II |
| 11 | Qwen3-4B | Thinking | Zero-shot | DA | II |
| 12 | Qwen3-4B | Thinking | Few-shot | DA | II |
| 13 | Qwen3-4B | Instruct | Zero-shot | MA | II |
| 14 | Qwen3-4B | Instruct | Few-shot | MA | II |
| 15 | Qwen3-4B | Thinking | Zero-shot | MA | II |
| 16 | Qwen3-4B | Thinking | Few-shot | MA | II |
| 17 | Qwen3-30B | Instruct | Zero-shot | DA | II |
| 18 | Qwen3-30B | Instruct | Few-shot | DA | II |
| 19 | Qwen3-30B | Thinking | Zero-shot | DA | II |
| 20 | Qwen3-30B | Thinking | Few-shot | DA | II |
| 21 | Qwen3-30B | Instruct | Zero-shot | MA | II |
| 22 | Qwen3-30B | Instruct | Few-shot | MA | II |
| 23 | Qwen3-30B | Thinking | Zero-shot | MA | II |
| 24 | Qwen3-30B | Thinking | Few-shot | MA | II |

---

## 5. Implementation

### 5.1 Available Scripts

Scripts pulled from upstream repository:

| File | Status | Description |
|------|--------|-------------|
| `src/single_agent_log_analysis.py` | ✅ Ready | SA runner for log analysis |
| `src/two_agent_log_analysis.py` | ✅ Ready | DA (planner-executor) |
| `src/multi_agent_log_analysis.py` | ✅ Ready | MA (proposer-reviewer) |
| `src/no_agents_log_analysis.py` | ✅ Ready | Direct LLM baseline |
| `src/config.py` | ✅ Updated | Log analysis prompts |
| `src/log_utils.py` | ✅ Updated | Log reading utilities |

### 5.2 Prompt Templates

Prompts are defined in `src/config.py`:
- `TASK_PROMPT_LOG_ANALYSIS`: Task description
- `SYS_MSG_SINGLE_LOG_ANALYSIS_ZERO_SHOT`: Zero-shot system prompt
- `SYS_MSG_SINGLE_LOG_ANALYSIS_FEW_SHOT`: Few-shot system prompt
- `SYS_MSG_LOG_ANALYSIS_CRITIC_ZERO_SHOT`: Critic prompt for MA
- `SYS_MSG_LOG_ANALYSIS_CRITIC_FEW_SHOT`: Critic prompt for MA (few-shot)

### 5.3 Evaluation Metrics

**Primary Metrics**:
- Accuracy: (TP + TN) / Total
- Precision: TP / (TP + FP)
- Recall: TP / (TP + FN) - Critical for anomaly detection
- F1 Score: Harmonic mean

**Secondary Metrics**:
- False Positive Rate
- False Negative Rate
- Energy consumption (kWh, kg CO2 via CodeCarbon)
- Inference time per session

---

## 6. Cost Estimate

### 6.1 GPU Server Costs

**Pricing**: RunPod H100 SXM 80GB @ US$2.69/hr

| Phase | Model | Experiments | Duration (hrs) | Cost |
|-------|-------|-------------|----------------|------|
| Phase I | Qwen3-4B | 4 | 8.2 | $22.06 |
| Phase I | Qwen3-30B | 4 | 8.4 | $22.60 |
| Phase II | Qwen3-4B | 8 | 22.7 | $60.94 |
| Phase II | Qwen3-30B | 8 | 14.6 | $39.32 |
| **Total** | | **24** | **53.9 hrs** | **$144.92** |

### 6.2 SOTA Comparison (Optional)

| Model | Provider | Est. Cost |
|-------|----------|-----------|
| Claude Sonnet 4.5 | OpenRouter | ~$25 |

### 6.3 Budget Summary

| Item | Cost (USD) | Cost (SGD) |
|------|------------|------------|
| Base Cost | $170 | $230 |
| Setup & pilot | +$30 | +$40 |
| **With 40% buffer** | **$280** | **$380** |

---

## 7. Expected Outcomes

### 7.1 RQ1 Hypotheses

**H1**: Thinking mode improves anomaly detection accuracy
- **Prediction**: +5-15% F1 improvement over Instruct baseline
- **Rationale**: Anomaly detection benefits from systematic reasoning through log patterns

**H2**: Few-shot with canonical examples improves performance
- **Prediction**: Based on vulnerability detection findings, high-quality few-shot examples should outperform zero-shot
- **Test**: Compare zero-shot vs few-shot with validated anomaly examples

### 7.2 RQ2 Hypotheses

**H3**: DA (planner-executor) may improve for complex sessions
- **Prediction**: Benefit when log filtering reduces noise
- **Risk**: Overhead may not justify gains for simple cases

**H4**: MA (proposer-reviewer) reduces false positives
- **Prediction**: Review step catches incorrect classifications
- **Risk**: May introduce inter-agent sycophancy (per RQ2_DA_MA_Hypothesis.md)

**H5**: SA optimal for log analysis (matching RQ2 vulnerability findings)
- **Prediction**: Multi-agent overhead outweighs benefits
- **Rationale**: Log analysis is classification task, similar to vulnerability detection

---

## 8. Risk Mitigation

### 8.1 Dataset Risks

| Risk | Mitigation |
|------|-----------|
| Imbalanced dataset (~3% anomaly) | Stratified evaluation, focus on F1/Recall |
| Session length variability | Truncate long sessions to max tokens |

### 8.2 Technical Risks

| Risk | Mitigation |
|------|-----------|
| Log sequences too long | Truncate to max tokens, summarize |
| Model hallucination | Structured output format, confidence scores |
| Energy tracking issues | Use established CodeCarbon setup |

### 8.3 Experimental Risks

| Risk | Mitigation |
|------|-----------|
| Few-shot examples poor quality | Validate with domain expert |
| Results inconsistent with vuln detection | Document as finding, investigate |

---

## 9. Next Actions

### Immediate

1. ✅ Pull upstream changes (scripts available)
2. ✅ Update experiment plan (this document)
3. ⬜ Submit budget request for SGD 380
4. ⬜ Pilot run with 50 sessions to validate estimates

### After Budget Approval

5. ⬜ Run Phase I experiments (8 SA experiments)
6. ⬜ Analyze Phase I results
7. ⬜ Run Phase II experiments (16 DA/MA experiments)
8. ⬜ Final analysis and documentation

---

## Document History

- **Created**: 2026-01-10
- **Updated**: 2026-01-17 (Revised to focus on Qwen3 models only per supervisor guidance)
- **Author**: Log Analysis Planning Session
- **Status**: Ready for budget approval
