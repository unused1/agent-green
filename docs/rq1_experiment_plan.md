# RQ1 Experiment Plan: Effectiveness of Reasoning-Enabled LLMs

## Research Question
**RQ1:** Do reasoning-enabled LLMs out-perform non-reasoning baselines on log parsing, log analysis, vulnerability detection, technical debt detection, and code generation?

---

## 1. Overview

### 1.1 Objective
Compare the performance of reasoning-enabled LLMs against non-reasoning baselines across five software engineering tasks while measuring accuracy, energy consumption, and computational cost.

### 1.2 Hypothesis
Reasoning-enabled LLMs will demonstrate superior accuracy on complex software engineering tasks at the cost of increased energy consumption and inference time compared to non-reasoning baselines.

### 1.3 Infrastructure Approach
- **Platform:** RunPod with vLLM for high-performance inference
- **GPU:** H100 80GB or A100 80GB for optimal performance
- **Reasoning Model:** QwQ-32B-Preview (Qwen reasoning model)
- **Baseline Models:** Qwen2.5-Coder-7B-Instruct, Qwen2.5-Coder-32B-Instruct
- **Deployment:** vLLM with OpenAI-compatible API

---

## 1.5 RQ1 Preliminary Findings (Qwen3-4B Vulnerability Detection)

### 1.5.1 Completed Experiments
**Status:** ✅ COMPLETED (October 2025)

**Models Tested:**
- Qwen3-4B-Instruct (Baseline)
- Qwen3-4B-Thinking (Reasoning mode)

**Dataset:** VulTrial 384 unique vulnerability samples (balanced)

**Configurations:** Zero-shot and Few-shot prompting

### 1.5.2 Key Findings

**Performance Results:**

| Configuration | Accuracy | Precision | Recall | F1 Score |
|---|---|---|---|---|
| **Thinking Zero-shot** ⭐ | 53.00% | 56.31% | **30.05%** | **39.19%** |
| Thinking Few-shot | 51.30% | 53.85% | 18.13% | 27.13% |
| Baseline Zero-shot | 50.26% | 50.91% | 14.51% | 22.58% |
| Baseline Few-shot | 51.04% | 62.50% | 5.18% | 9.57% |

**Key Observations:**
1. ✅ Thinking mode achieves **2.1x higher F1 score** (33.16% avg vs 16.08% avg)
2. ✅ Recall improvement: **+14.24pp** (critical for security - fewer missed vulnerabilities)
3. ⚠️ **Few-shot paradox**: Few-shot prompting WORSENS performance for both models
4. ⚠️ Zero-shot consistently outperforms few-shot across all metrics

**Energy Results:**

| Metric | Baseline (Avg) | Thinking (Avg) | Ratio |
|---|---|---|---|
| CO2 per experiment | 0.134 kg | 0.589 kg | 4.39x |
| Energy per experiment | 0.789 kWh | 3.465 kWh | 4.39x |

**Energy Observations:**
1. Thinking mode uses **4.39x more energy** than Baseline
2. Few-shot uses **less energy** than zero-shot (more efficient)
3. GPU dominates energy consumption (43% of total)
4. Trade-off: 0.16 kWh per percentage point F1 improvement

### 1.5.3 Unexpected Finding: Few-Shot Degradation

**The Paradox:**
- ❌ Few-shot prompting **does NOT improve** performance
- ❌ Few-shot actually **decreases** F1 score for Thinking mode (39.19% → 27.13%)
- ❌ Few-shot **severely degrades** Baseline recall (14.51% → 5.18%)
- ✅ Few-shot **reduces** energy consumption (more efficient inference)

### 1.5.4 Hypotheses for Few-Shot Degradation

**Hypothesis 1: Context Overload in Small Models (Sycophancy)**
- **Theory**: For smaller models (4B parameters), few-shot examples act as noise rather than guidance
- **Mechanism**: Model attempts to pattern-match examples rather than reason about the actual problem
- **Evidence**:
  - Dramatic F1 drop in Thinking few-shot (39.19% → 27.13%)
  - Severe recall collapse in Baseline few-shot (14.51% → 5.18%)
  - Pattern suggests over-fitting to example format rather than understanding task
- **Sycophantic behavior**: Model may be trying to "please" by mimicking example style rather than applying reasoning
- **Context window saturation**: 4B models may struggle with long prompts containing examples + actual task

**Hypothesis 2: Reduced Cognitive Load (Energy Efficiency)**
- **Theory**: Few-shot examples provide "shortcuts" that reduce thinking/reasoning steps
- **Mechanism**: Model can pattern-match rather than reason deeply, using less computation
- **Evidence**:
  - Few-shot consistently uses less energy than zero-shot
  - Baseline few-shot: 73% of zero-shot energy
  - Thinking few-shot: 61% of zero-shot energy
- **Implication**: Less thinking = lower energy BUT also lower accuracy for complex tasks

**Hypothesis 3: Scale-Dependent Few-Shot Effectiveness**
- **Theory**: Few-shot prompting may work better for larger models (>7B parameters)
- **Rationale**:
  - Larger models have more capacity to process examples without context saturation
  - Larger models can better distinguish between example patterns and task requirements
  - Larger models may have better few-shot learning capabilities from pre-training
- **Testable prediction**: Few-shot should improve with model size (7B → 32B → 70B)

### 1.5.5 Implications for Future Experiments

**Questions to Address:**
1. **RQ1-Extended**: Does few-shot effectiveness improve with model scale?
   - Test Qwen2.5-Coder 7B, 32B models with same task
   - Test QwQ-32B-Preview (reasoning) with few-shot
   - Measure if larger models benefit from few-shot examples

2. **RQ2**: Does the few-shot paradox extend to other tasks?
   - Test on code generation (HumanEval dataset)
   - Test on log parsing (HDFS dataset)
   - Determine if vulnerability detection is unique or generalizable

3. **RQ3**: Can we optimize few-shot for small models?
   - Test with fewer examples (1-shot vs 3-shot)
   - Test with different example selection strategies
   - Test with simplified examples

**Design Recommendations:**
1. ✅ Prioritize zero-shot for small models (4B-7B)
2. ⚠️ Test few-shot effectiveness across model scales
3. ✅ Include energy measurements for all configurations
4. ✅ Focus on larger models (32B+) for production deployments

---

## 1.6 RQ1 Extended Experiments

Based on preliminary findings, RQ1 will be extended with two additional experimental phases:

### Phase 2: Scale-Dependent Few-Shot Analysis

**Objective:** Test if few-shot effectiveness improves with model scale (addressing the few-shot paradox observed in 4B models)

**Models to Add:**

| Model | Total Params | Active Params | Type | Few-Shot Config | Infrastructure | VRAM Required |
|-------|-------------|---------------|------|-----------------|----------------|---------------|
| Qwen3-30B-A3B-Instruct-2507 | 30B | 3B (MoE) | Baseline | Zero-shot, 3-shot | Mars GPU Server (A5000 24GB) or RunPod A6000 | ~30 GB |
| Qwen3-30B-A3B-Thinking-2507 | 30B | 3B (MoE) | Reasoning | Zero-shot, 3-shot | Mars GPU Server (A5000 24GB) or RunPod A6000 | ~30 GB |
| Qwen3-235B-A22B-Instruct-2507 | 235B | 22B (MoE) | Baseline | Zero-shot, 3-shot | RunPod H100 (80GB) | ~120-150 GB |
| Qwen3-235B-A22B-Thinking-2507 | 235B | 22B (MoE) | Reasoning | Zero-shot, 3-shot | RunPod H100 (80GB) | ~120-150 GB |

**Note on Model Architecture:**
- **Qwen3-30B-A3B**: MoE model with 30B total parameters, only 3B activated per token
  - More efficient than dense 30B (similar to 3-4B inference cost)
  - Unsloth optimized version can run on 30GB VRAM
- **Qwen3-235B-A22B**: Flagship MoE model with 235B total, 22B activated per token
  - State-of-the-art reasoning capabilities
  - Requires multi-GPU setup or cloud H100 instance

**Task:** Vulnerability Detection (VulTrial dataset) - same as Phase 1 for direct comparison

**Hypotheses to Test:**
- **H1**: Few-shot effectiveness increases with model scale (active parameters: 4B → 3B MoE → 22B MoE)
- **H2**: 30B-A3B models show positive few-shot benefit (unlike 4B dense models)
- **H3**: Reasoning models benefit more from few-shot at larger scales
- **H4**: MoE architecture provides better energy efficiency than dense models at scale
- **H5**: Energy cost per performance gain decreases with model scale (due to MoE efficiency)

**Metrics:**
- Performance: Accuracy, Precision, Recall, F1 score (per-class and macro)
- Energy: kWh, CO2 emissions per experiment
- Few-shot delta: (Few-shot F1 - Zero-shot F1) / Zero-shot F1 × 100%
- Energy-performance tradeoff per model scale
- MoE efficiency: Energy per active parameter vs dense models

**Expected Outcomes:**
1. Identify model scale threshold where few-shot becomes beneficial
2. Quantify scale-dependent few-shot effectiveness across 4B → 30B-A3B → 235B-A22B
3. Compare energy costs across model scales and architectures (dense vs MoE)
4. Determine optimal model scale for production deployment (accuracy vs energy tradeoff)

---

### Phase 3: Task Generalization - Code Generation

**Objective:** Test if reasoning advantage and few-shot patterns generalize from discriminative (classification) to generative (code generation) tasks

**Dataset:** HumanEval (164 Python programming problems with test cases)

**Models:** Same as Phase 2 (Qwen3-30B-A3B Instruct/Thinking + Qwen3-235B-A22B Instruct/Thinking)

**Why Code Generation:**
- **Different cognitive task**: Generation vs classification
- **Standardized benchmark**: HumanEval widely used
- **Executable validation**: Test cases provide objective ground truth
- **Complexity levels**: Problems range from easy to hard

**Evaluation Metrics:**
- **Primary**: Pass@1, Pass@10 (test case success rate)
- **Secondary**:
  - Syntax correctness rate
  - Compilation success rate
  - Solution efficiency metrics
  - Energy per successful solution
  - Inference time per problem

**Problem Analysis:**
- Categorize by difficulty: Easy (1-50), Medium (51-120), Hard (121-164)
- Analyze reasoning benefit vs problem complexity
- Compare few-shot effectiveness on generation vs classification

**Hypotheses:**
- **H1**: Reasoning advantage persists in generative tasks
- **H2**: Few-shot behavior differs between generation and classification
- **H3**: Reasoning provides larger benefit for algorithmically complex problems
- **H4**: Energy-performance tradeoff differs by task type

---

## 1.7 Complete RQ1 Experimental Scope

**RQ1 Structure:**
- **Phase 1**: Small Dense Model (4B) + Vulnerability Detection - ✅ COMPLETED
  - Finding: Thinking 2.1x better F1, few-shot paradox discovered
  - Models: Qwen3-4B-Instruct-2507, Qwen3-4B-Thinking-2507

- **Phase 2**: Large MoE Models (30B-A3B, 235B-A22B) + Vulnerability Detection - 🔄 PLANNED
  - Goal: Test scale-dependent few-shot hypothesis
  - Models: Qwen3-30B-A3B & Qwen3-235B-A22B (both Instruct + Thinking variants)

- **Phase 3**: Code Generation (HumanEval) - 🔄 PLANNED
  - Purpose: Test task generalization hypothesis
  - Models: Same as Phase 2 (Qwen3-30B-A3B & Qwen3-235B-A22B Instruct + Thinking)

**Total Experiments for Complete RQ1:**

| Phase | Task | Models | Configs | Total Experiments |
|-------|------|--------|---------|-------------------|
| Phase 1 (✅ Done) | Vulnerability Detection | 2 (4B Instruct, 4B Thinking) | 2 prompts (zero/few-shot) × 2 models | 4 |
| Phase 2 (🔄 Planned) | Vulnerability Detection | 4 (30B-A3B & 235B-A22B, both Instruct + Thinking) | 2 prompts × 4 models | 8 |
| Phase 3 (🔄 Planned) | Code Generation (HumanEval) | 4 (same as Phase 2) | 2 prompts × 4 models | 8 |
| **TOTAL** | | **10 unique model configs** | | **20 experiments** |

**Breakdown by Model:**
- Qwen3-4B-Instruct-2507: 2 experiments (zero-shot, few-shot) - ✅ DONE
- Qwen3-4B-Thinking-2507: 2 experiments (zero-shot, few-shot) - ✅ DONE
- Qwen3-30B-A3B-Instruct-2507: 4 experiments (2 tasks × 2 prompts) - 🔄 PLANNED
- Qwen3-30B-A3B-Thinking-2507: 4 experiments (2 tasks × 2 prompts) - 🔄 PLANNED
- Qwen3-235B-A22B-Instruct-2507: 4 experiments (2 tasks × 2 prompts) - 🔄 PLANNED
- Qwen3-235B-A22B-Thinking-2507: 4 experiments (2 tasks × 2 prompts) - 🔄 PLANNED

**Note:** Phase 1 completed (4 experiments), need 16 additional experiments for Phases 2 & 3

**Priority:**
1. **High**: Phase 2 (extends RQ1 findings, tests main hypothesis)
2. **High**: Phase 3 (task generalization is key finding)
3. **Medium**: Additional agent configurations (if time/budget permits)

---

## 2. Model Selection

### 2.1 Reasoning-Enabled Models
| Model | Parameters | Context | Reasoning Capability | VRAM Required |
|-------|-----------|---------|---------------------|---------------|
| **QwQ-32B-Preview** | 32B | 32K | Yes (explicit CoT) | ~70GB |
| Qwen3-Thinking-4B | 4B | 32K | Yes (implicit) | ~10GB |

### 2.2 Non-Reasoning Baselines
| Model | Parameters | Context | Type | VRAM Required |
|-------|-----------|---------|------|---------------|
| **Qwen2.5-Coder-7B-Instruct** | 7B | 128K | Standard | ~16GB |
| **Qwen2.5-Coder-32B-Instruct** | 32B | 128K | Standard | ~70GB |
| DeepSeek-Coder-33B-Instruct | 33B | 16K | Standard | ~70GB |

### 2.3 Comparison Strategy
- **Primary Comparison:** QwQ-32B-Preview (reasoning) vs Qwen2.5-Coder-32B-Instruct (non-reasoning)
  - Same parameter count (~32B) for fair comparison
  - Isolates reasoning capability as the variable
- **Secondary Comparison:** QwQ-32B-Preview vs Qwen2.5-Coder-7B-Instruct
  - Tests if reasoning compensates for smaller model size
- **Control:** DeepSeek-Coder-33B-Instruct as additional baseline

---

## 3. Tasks and Datasets

### 3.1 Log Parsing
**Objective:** Extract structured templates from unstructured log messages

**Dataset:**
- HDFS 200 sampled logs (`logs/HDFS_200_sampled.log`)
- Ground truth: `logs/HDFS_200_sampled_log_structured.csv`
- 200 samples with proportional stratified sampling

**Existing Code:**
- `src/no_agents.ipynb` - Non-agentic approach
- `src/single_agent.ipynb` - Single agent
- `src/two_agents.ipynb` - Parser + verifier
- `src/multi_agents.ipynb` - Multi-agent system

**Metrics:**
- Parsing accuracy (exact template match)
- Average edit distance (Levenshtein)
- Average LCS (Longest Common Subsequence)
- Energy consumption (kWh, kg CO2)
- Inference time per log

**Agent Configurations to Test:**
1. Non-Agentic (NA) - Direct LLM calls
2. Single Agent (SA) - One parser agent
3. Dual Agents (DA) - Parser + verifier
4. Multi-Agent (MA) - Full agentic workflow

### 3.2 Log Analysis
**Objective:** Analyze logs for anomalies, patterns, and root causes

**Dataset:**
- Use HDFS 2k logs for extended analysis
- Create anomaly detection tasks
- Root cause analysis scenarios

**Status:** ⚠️ **TO BE IMPLEMENTED**

**Proposed Approach:**
- Extend existing log parsing notebooks
- Add anomaly detection prompts
- Create ground truth for anomaly labels
- Implement pattern recognition tasks

**Metrics:**
- Anomaly detection F1 score
- Pattern identification accuracy
- Root cause diagnosis accuracy
- Response time
- Energy consumption

### 3.3 Vulnerability Detection
**Objective:** Identify security vulnerabilities in code functions

**Dataset:**
- VulTrial balanced dataset: `vuln_database/VulTrial_386_samples_balanced.jsonl`
- 386 samples (balanced vulnerable/non-vulnerable)
- Real-world CVEs with CWE classifications

**Existing Code:**
- `src/no_agent_vuln_detection.py` - Direct LLM calls
- `src/single_agent_vuln.py` - Single agent approach
- `src/dual_agent_vuln.py` - Security analyst + code author
- `src/multi_agent_vuln.py` - Multi-agent review board

**Metrics:**
- Accuracy (with 3 normalization strategies)
- Precision, Recall, F1 score
- Confusion matrix
- Energy consumption
- Inference time per sample

**Agent Configurations:**
1. Non-Agentic (NA)
2. Single Agent (SA) - Few-shot and zero-shot
3. Dual Agents (DA) - Analyst + author dialog
4. Multi-Agent (MA) - Researcher, author, moderator, review board

### 3.4 Technical Debt Detection
**Objective:** Identify code smells, technical debt, and maintainability issues

**Status:** ⚠️ **TO BE IMPLEMENTED**

**Proposed Dataset:**
- SonarQube dataset or custom annotated dataset
- Code smells: Long methods, duplicated code, complex conditionals
- Maintainability indices
- ~200-500 samples

**Proposed Implementation:**
- Adapt vulnerability detection scripts structure
- Create prompts for technical debt categories
- Implement scoring system (0-5 scale)
- Add multi-label classification support

**Metrics:**
- Multi-label classification metrics
- Severity assessment accuracy
- F1 scores per debt type
- Energy consumption

### 3.5 Code Generation
**Objective:** Generate correct, functional Python code from specifications

**Dataset:**
- HumanEval dataset (if available in `vuln_database/`)
- Alternative: Create custom programming problems
- ~164 problems with test cases

**Existing Code:**
- `src/no_agent_code_generation.py` - Direct generation
- `src/single_agent_code_generation.py` - Single agent
- `src/dual_agent_code_generation.py` - Generator + reviewer
- `src/multi_agent_code_generation.py` - Requirements analyst + programmer + moderator + review board
- `src/evaluate_code_generation.py` - Evaluation with test execution

**Metrics:**
- Pass@k (pass@1, pass@10)
- Test case pass rate
- Code quality metrics
- Compilation success rate
- Energy consumption

**Agent Configurations:**
1. No Agent - Direct generation
2. Single Agent - Code generator
3. Dual Agent - Generator + reviewer
4. Multi-Agent - Full workflow with refinement

---

## 4. Infrastructure Setup

### 4.1 RunPod Configuration

#### Option 1: Single Pod (Recommended for initial testing)
```yaml
GPU: H100 80GB or A100 80GB
Container: vllm/vllm-openai:latest
Container Disk: 200 GB
Volume Disk: 100 GB
Volume Mount: /workspace
```

#### Option 2: Multi-Pod (For parallel experiments)
- Pod 1: QwQ-32B-Preview (reasoning)
- Pod 2: Qwen2.5-Coder-32B-Instruct (baseline)
- Pod 3: Qwen2.5-Coder-7B-Instruct (lightweight baseline)

### 4.2 vLLM Start Commands

**QwQ-32B-Preview (Reasoning Model):**
```bash
--host 0.0.0.0 \
--port 8000 \
--model Qwen/QwQ-32B-Preview \
--download-dir /workspace/models \
--dtype auto \
--gpu-memory-utilization 0.95 \
--max-model-len 8192 \
--trust-remote-code \
--api-key YOUR_SECURE_API_KEY
```

**Qwen2.5-Coder-32B-Instruct (Baseline):**
```bash
--host 0.0.0.0 \
--port 8000 \
--model Qwen/Qwen2.5-Coder-32B-Instruct \
--download-dir /workspace/models \
--dtype auto \
--gpu-memory-utilization 0.95 \
--max-model-len 8192 \
--trust-remote-code \
--api-key YOUR_SECURE_API_KEY
```

**Qwen2.5-Coder-7B-Instruct (Lightweight):**
```bash
--host 0.0.0.0 \
--port 8000 \
--model Qwen/Qwen2.5-Coder-7B-Instruct \
--download-dir /workspace/models \
--dtype auto \
--gpu-memory-utilization 0.90 \
--max-model-len 8192 \
--trust-remote-code \
--api-key YOUR_SECURE_API_KEY
```

### 4.3 Environment Configuration

**.env File:**
```bash
# Project paths
PROJECT_ROOT=/path/to/agent-green

# RunPod Endpoints (update with actual RunPod URLs)
QWQ_32B_ENDPOINT=https://xxx-8000.proxy.runpod.net/v1
QWEN_32B_ENDPOINT=https://yyy-8000.proxy.runpod.net/v1
QWEN_7B_ENDPOINT=https://zzz-8000.proxy.runpod.net/v1

# API Keys
QWQ_API_KEY=your_secure_api_key_1
QWEN_32B_API_KEY=your_secure_api_key_2
QWEN_7B_API_KEY=your_secure_api_key_3

# Default model
LLM_MODEL=Qwen/QwQ-32B-Preview
OLLAMA_HOST=https://xxx-8000.proxy.runpod.net/v1
```

---

## 5. Code Modifications Required

### 5.1 Update ollama_utils.py for vLLM
**File:** `src/ollama_utils.py`

**Changes Needed:**
- Add vLLM server start/stop functions (may not be needed for RunPod)
- Or create `vllm_utils.py` for RunPod API interaction
- Add health check functions for remote endpoints

**New Functions:**
```python
def check_vllm_health(endpoint_url, api_key):
    """Check if vLLM endpoint is healthy"""

def get_vllm_models(endpoint_url, api_key):
    """List available models on vLLM endpoint"""
```

### 5.2 Modify Inference Functions
**Files to Update:**
- `src/no_agents.ipynb` → Convert to `.py` for batch execution
- `src/no_agent_vuln_detection.py`
- `src/no_agent_code_generation.py`
- All agent-based scripts

**Required Changes:**
```python
# Replace Ollama calls with OpenAI-compatible API
import openai

def ask_llm_vllm(model, prompt, api_base, api_key):
    """Query vLLM with OpenAI-compatible API"""
    client = openai.OpenAI(
        base_url=api_base,
        api_key=api_key
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=2048
    )

    return response.choices[0].message.content
```

### 5.3 Add Reasoning Mode Control
**File:** `src/config.py`

**Add Configuration:**
```python
# Reasoning configuration
ENABLE_REASONING = os.getenv('ENABLE_REASONING', 'false').lower() == 'true'
REASONING_MODEL = "Qwen/QwQ-32B-Preview"
BASELINE_MODEL = "Qwen/Qwen2.5-Coder-32B-Instruct"

# Dynamic model selection
if ENABLE_REASONING:
    LLM_MODEL = REASONING_MODEL
else:
    LLM_MODEL = BASELINE_MODEL
```

### 5.4 Create Batch Execution Scripts
**New Files Needed:**
- `src/batch_run_log_parsing.py` - Run all log parsing configs
- `src/batch_run_vulnerability.py` - Run all vulnerability configs
- `src/batch_run_code_generation.py` - Run all code generation configs
- `src/batch_run_all_tasks.py` - Master script for all tasks

**Example Structure:**
```python
def run_experiment(model_config, task, agent_config, dataset):
    """
    Run single experiment configuration

    Args:
        model_config: Dict with model endpoint, API key
        task: "log_parsing", "vulnerability", "code_generation"
        agent_config: "no_agent", "single", "dual", "multi"
        dataset: Path to dataset file
    """
    # Implementation
```

### 5.5 Implement Log Analysis (New Task)
**New File:** `src/log_analysis.py`

**Components:**
- Anomaly detection prompts
- Pattern recognition tasks
- Root cause analysis
- Ground truth creation utility

### 5.6 Implement Technical Debt Detection (New Task)
**New Files:**
- `src/no_agent_tech_debt.py`
- `src/single_agent_tech_debt.py`
- `src/dual_agent_tech_debt.py`
- `src/multi_agent_tech_debt.py`
- `src/tech_debt_evaluation.py`

**Dataset Creation:**
- Collect code samples with known technical debt
- Annotate with debt categories
- Create evaluation metrics

### 5.7 Enhanced Evaluation Framework
**New File:** `src/evaluation_rq1.py`

**Features:**
- Unified evaluation across all tasks
- Statistical significance testing
- Comparative analysis (reasoning vs non-reasoning)
- Visualization generation
- Cost-benefit analysis

---

## 6. Experimental Design

### 6.1 Variables

**Independent Variables:**
1. **Model Type:** Reasoning-enabled vs Non-reasoning
2. **Agent Configuration:** No-agent, Single, Dual, Multi-agent
3. **Task Type:** Log parsing, log analysis, vulnerability detection, tech debt, code generation
4. **Prompt Strategy:** Zero-shot vs Few-shot (where applicable)

**Dependent Variables:**
1. **Accuracy Metrics:**
   - Log parsing: Exact match, edit distance, LCS
   - Vulnerability: Accuracy, precision, recall, F1
   - Tech debt: Multi-label F1, severity accuracy
   - Code generation: Pass@k, test pass rate

2. **Resource Metrics:**
   - Energy consumption (kWh)
   - Carbon emissions (kg CO2)
   - Inference time (seconds)
   - Token usage
   - Cost ($)

**Control Variables:**
- Temperature: 0.0 (deterministic)
- Max tokens: Consistent across models
- Context window: 8K tokens (balanced for all models)
- Number of runs: 3 per configuration
- Dataset: Same samples for all models

### 6.2 Experiment Matrix

| Task | Model | Agent Config | Prompt | Runs | Total Experiments |
|------|-------|--------------|--------|------|-------------------|
| Log Parsing | 3 models | 4 configs | 2 strategies | 3 | 72 |
| Log Analysis* | 3 models | 4 configs | 2 strategies | 3 | 72 |
| Vulnerability | 3 models | 4 configs | 2 strategies | 3 | 72 |
| Tech Debt* | 3 models | 4 configs | 2 strategies | 3 | 72 |
| Code Gen | 3 models | 4 configs | 1 strategy | 3 | 36 |
| **TOTAL** | | | | | **324** |

*New implementations required

### 6.3 Execution Strategy

**Phase 1: Existing Tasks (Week 1-2)**
1. Log Parsing (4 agent configs × 3 models × 3 runs = 36 experiments)
2. Vulnerability Detection (4 × 3 × 3 = 36 experiments)
3. Code Generation (4 × 3 × 3 = 36 experiments)
**Subtotal:** 108 experiments

**Phase 2: New Implementations (Week 3-4)**
1. Log Analysis implementation and testing
2. Technical Debt Detection implementation and testing
**Subtotal:** 144 experiments

**Phase 3: Full Evaluation (Week 5)**
1. Run all 324 experiments
2. Statistical analysis
3. Result visualization

### 6.4 Execution Order
1. Start with No-Agent configuration (fastest, baseline)
2. Progress to Single Agent
3. Then Dual Agent
4. Finally Multi-Agent (most complex)

**Within each agent configuration:**
1. Run lightweight model first (Qwen2.5-7B)
2. Then baseline 32B model
3. Finally reasoning model (QwQ-32B)

---

## 7. Data Collection and Analysis

### 7.1 Result File Structure
```
results/
├── rq1_log_parsing/
│   ├── QwQ-32B_NA_zero_run1_results.json
│   ├── QwQ-32B_NA_zero_run1_emissions.csv
│   ├── Qwen25-32B_NA_zero_run1_results.json
│   ├── ...
├── rq1_vulnerability/
│   ├── QwQ-32B_SA_few_run1_results.jsonl
│   ├── ...
├── rq1_code_generation/
│   ├── QwQ-32B_DA_run1_results.jsonl
│   ├── ...
├── rq1_log_analysis/
│   └── ...
└── rq1_tech_debt/
    └── ...
```

### 7.2 Consolidated Analysis
**File:** `results/rq1_consolidated_results.csv`

**Columns:**
- experiment_id
- task (log_parsing, vulnerability, etc.)
- model_name
- model_type (reasoning/non-reasoning)
- agent_config (NA, SA, DA, MA)
- prompt_strategy (zero-shot, few-shot)
- run_number (1-3)
- accuracy
- precision (if applicable)
- recall (if applicable)
- f1_score (if applicable)
- energy_kwh
- emissions_kg_co2
- inference_time_seconds
- total_tokens
- cost_usd
- timestamp

### 7.3 Statistical Analysis

**Comparisons:**
1. **Primary:** QwQ-32B vs Qwen2.5-32B (reasoning effect)
2. **Secondary:** QwQ-32B vs Qwen2.5-7B (reasoning vs size)
3. **Control:** All models vs each other

**Statistical Tests:**
- Paired t-tests for accuracy comparisons
- ANOVA for multi-group comparisons
- Effect size calculations (Cohen's d)
- Confidence intervals (95%)
- Bonferroni correction for multiple comparisons

**Metrics to Analyze:**
- Mean accuracy improvement
- Resource consumption tradeoffs
- Cost-effectiveness ratios
- Task-specific performance patterns

### 7.4 Visualization

**Charts to Generate:**
1. Accuracy comparison across tasks (bar charts)
2. Energy consumption vs accuracy (scatter plots)
3. Resource usage by agent configuration (heatmaps)
4. Cost-benefit analysis (2D plots)
5. Task-specific detailed breakdowns
6. Statistical significance markers

---

## 8. Cost Estimation

### 8.1 GPU Costs (RunPod H100 80GB @ $3.50/hour)

**Per Experiment:**
- Log parsing: ~10 minutes = $0.58
- Vulnerability: ~20 minutes = $1.17
- Code generation: ~30 minutes = $1.75
- Log analysis: ~15 minutes = $0.88 (estimated)
- Tech debt: ~15 minutes = $0.88 (estimated)

**Total for 324 Experiments:**
- Estimated time: ~85 hours
- Estimated cost: **~$300**

**With 3 parallel pods:**
- Time: ~28-30 hours
- Cost: **~$300** (same, but faster completion)

### 8.2 Cost Optimization

**Strategies:**
1. Use Spot instances (50-70% cheaper): **~$100-150**
2. Run overnight/off-peak hours
3. Batch experiments efficiently
4. Use A100 80GB instead of H100: ~$2/hour = **~$170**
5. Auto-stop idle pods (30-minute timeout)

**Recommended Budget:** **$200-300** for full RQ1 study

---

## 9. Timeline

### Week 1-2: Infrastructure & Existing Tasks
- Day 1-2: RunPod setup, model deployment, testing
- Day 3-5: Code modifications for vLLM integration
- Day 6-10: Run log parsing, vulnerability, code generation experiments
- Day 11-14: Preliminary analysis and debugging

### Week 3-4: New Implementations
- Day 15-18: Implement log analysis task
- Day 19-22: Implement technical debt detection
- Day 23-28: Test and validate new tasks

### Week 5: Full Evaluation
- Day 29-32: Run all 324 experiments
- Day 33-35: Statistical analysis and visualization

### Week 6: Documentation
- Day 36-38: Write up results
- Day 39-42: Create presentation materials

**Total Duration:** 6 weeks

---

## 10. Risk Mitigation

### 10.1 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| RunPod pod interruption | High | Use on-demand pods, save incrementally |
| Model OOM errors | Medium | Reduce context length, use quantization |
| API rate limits | Low | Implement retry logic, exponential backoff |
| Network connectivity | Medium | Local result caching, retry mechanisms |
| Data loss | High | Auto-backup to network volume, git commits |

### 10.2 Experimental Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Low accuracy baselines | Medium | Verify prompts, check model loading |
| Inconsistent results | Medium | Increase runs from 3 to 5 |
| Missing datasets | High | Prepare datasets before starting |
| Incomplete evaluations | Medium | Implement robust error handling |

### 10.3 Resource Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Budget overrun | High | Monitor costs daily, use spot instances |
| Time overrun | Medium | Prioritize core experiments, defer extras |
| GPU unavailability | Medium | Reserve pods in advance, have backup regions |

---

## 11. Success Criteria

### 11.1 Minimum Viable Results
✓ Complete 200+ experiments across 3+ tasks
✓ Clear accuracy comparison between reasoning and non-reasoning
✓ Energy consumption data for all experiments
✓ Statistical significance established (p < 0.05)
✓ Cost-benefit analysis completed

### 11.2 Ideal Results
✓ All 324 experiments completed
✓ All 5 tasks implemented and evaluated
✓ Comprehensive statistical analysis
✓ Publication-ready visualizations
✓ Reproducible experimental framework

### 11.3 Key Research Outputs
1. Comparative performance data (reasoning vs non-reasoning)
2. Resource consumption analysis
3. Task-specific insights
4. Agent configuration recommendations
5. Cost-effectiveness guidelines

---

## 12. File Manifest

### 12.1 Existing Files (To Be Used)
```
# Log Parsing
src/no_agents.ipynb
src/single_agent.ipynb
src/two_agents.ipynb
src/multi_agents.ipynb
src/tool-based_agents.ipynb
logs/HDFS_200_sampled.log
logs/HDFS_200_sampled_log_structured.csv

# Vulnerability Detection
src/no_agent_vuln_detection.py
src/single_agent_vuln.py
src/dual_agent_vuln.py
src/multi_agent_vuln.py
src/vuln_evaluation.py
vuln_database/VulTrial_386_samples_balanced.jsonl

# Code Generation
src/no_agent_code_generation.py
src/single_agent_code_generation.py
src/dual_agent_code_generation.py
src/multi_agent_code_generation.py
src/evaluate_code_generation.py

# Utilities
src/config.py
src/evaluation.py
src/log_utils.py
src/ollama_utils.py
src/agent_utils.py
src/agent_utils_vuln.py
```

### 12.2 Files To Be Created
```
# Infrastructure
src/vllm_utils.py                    # vLLM/RunPod helper functions
src/batch_runner.py                  # Batch experiment execution

# Log Analysis (New Task)
src/no_agent_log_analysis.py
src/single_agent_log_analysis.py
src/dual_agent_log_analysis.py
src/multi_agent_log_analysis.py
src/log_analysis_evaluation.py
logs/log_analysis_dataset.jsonl

# Technical Debt Detection (New Task)
src/no_agent_tech_debt.py
src/single_agent_tech_debt.py
src/dual_agent_tech_debt.py
src/multi_agent_tech_debt.py
src/tech_debt_evaluation.py
vuln_database/tech_debt_dataset.jsonl

# Evaluation & Analysis
src/evaluation_rq1.py               # Unified RQ1 evaluation
src/statistical_analysis_rq1.py     # Statistical tests
src/visualization_rq1.py            # Generate plots

# Batch Execution
scripts/batch_log_parsing.sh
scripts/batch_vulnerability.sh
scripts/batch_code_generation.sh
scripts/batch_log_analysis.sh
scripts/batch_tech_debt.sh
scripts/run_all_rq1.sh              # Master script

# Documentation
docs/rq1_results.md                 # Results documentation
docs/rq1_analysis.md                # Analysis report
```

### 12.3 Configuration Files To Update
```
.env                                 # Add RunPod endpoints
src/config.py                        # Add reasoning mode configs
requirements.txt                     # Add OpenAI library
```

---

## 13. Next Steps

### Immediate Actions (Before Experiments)
1. ✅ Review and approve this experiment plan
2. ⬜ Set up RunPod account and create pods
3. ⬜ Deploy QwQ-32B and Qwen2.5-Coder models on vLLM
4. ⬜ Update code for vLLM compatibility
5. ⬜ Test single experiment end-to-end
6. ⬜ Prepare missing datasets (log analysis, tech debt)

### Implementation Priority
1. **High Priority:** Modify existing scripts for vLLM
2. **High Priority:** Create batch execution framework
3. **Medium Priority:** Implement log analysis task
4. **Medium Priority:** Implement technical debt task
5. **Low Priority:** Advanced visualizations

### Validation Steps
1. Run 1 experiment per task manually
2. Verify result file formats
3. Check energy tracking accuracy
4. Validate evaluation metrics
5. Test batch execution on 10 samples

---

## 14. References

### Documentation
- QwQ-32B-Preview: https://huggingface.co/Qwen/QwQ-32B-Preview
- Qwen2.5-Coder: https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct
- vLLM Documentation: https://docs.vllm.ai/
- RunPod Documentation: https://docs.runpod.io/
- AG2 Framework: https://github.com/ag2ai/ag2
- CodeCarbon: https://codecarbon.io/

### Datasets
- HDFS Logs: https://github.com/logpai/loghub
- VulTrial: https://github.com/VulTrial/VulTrial
- HumanEval: https://github.com/openai/human-eval

---

## Appendix A: Sample Commands

### Deploy Models on RunPod
```bash
# Terminal 1: QwQ-32B (Reasoning)
vllm serve Qwen/QwQ-32B-Preview \
  --host 0.0.0.0 --port 8000 \
  --dtype auto --gpu-memory-utilization 0.95 \
  --max-model-len 8192 --trust-remote-code

# Terminal 2: Qwen2.5-32B (Baseline)
vllm serve Qwen/Qwen2.5-Coder-32B-Instruct \
  --host 0.0.0.0 --port 8001 \
  --dtype auto --gpu-memory-utilization 0.95 \
  --max-model-len 8192 --trust-remote-code
```

### Run Experiments
```bash
# Single experiment
ENABLE_REASONING=true python src/no_agent_vuln_detection.py

# Batch experiments
./scripts/run_all_rq1.sh
```

### Check Results
```bash
# View results
cat results/rq1_consolidated_results.csv

# Generate plots
python src/visualization_rq1.py

# Statistical analysis
python src/statistical_analysis_rq1.py
```


