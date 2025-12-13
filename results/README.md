# Experiment Results Directory

This directory contains all experimental results for the agent-green project, organized chronologically and by experiment type.

## Directory Structure

```
results/
├── mars/                    # Phase 1: Initial 4B experiments (Oct 11, 2025)
├── mars_rerun/              # Phase 1b: 4B re-runs with improved CWE prompts (Oct 11, 2025)
├── runpod/                  # Phase 2a: Initial 30B experiments (Oct 20, 2025)
├── runpod_rerun/            # Phase 2b: 30B re-runs + 4B hardware comparison (Nov 2-8, 2025)
├── mars_codegen/            # Phase 3a: Code generation on Mars 4B (Nov 6-7, 2025)
├── runpod_codegen/          # Phase 3b: Code generation on RunPod 30B (Nov 7, 2025)
├── runpod_rq2_pod1-8/       # Phase 4: RQ2 Multi-Agent experiments (Nov 15-17, 2025)
├── rq2_cross_architecture/  # Phase 5: Cross-architecture validation with Nemotron (Dec 9-10, 2025)
├── analysis/                # Analysis outputs from Jupyter notebooks
└── analysis_prompt_comparison/ # Prompt comparison analysis outputs
```

---

## Chronological Experiment Timeline

### **Phase 1: Initial Vulnerability Detection (Oct 11, 2025)**

**Purpose**: Establish baseline vulnerability detection performance with 4B models

**Hardware**: Mars (NVIDIA RTX A5000)

**Directories**:
- `results/mars/` - Initial experiments
- `results/mars_rerun/` - Re-runs with improved CWE prompts (same day)

**Experiments**:
| Experiment | Model | Samples | Configuration | Status |
|------------|-------|---------|---------------|--------|
| Baseline Zero-shot | Qwen3-4B-Instruct | 386 | Temperature: 0.0 | ✅ |
| Baseline Few-shot | Qwen3-4B-Instruct | 386 | Temperature: 0.0 | ✅ |
| Thinking Zero-shot | Qwen3-4B-Thinking | 386 | Temperature: 0.0 | ✅ |
| Thinking Few-shot | Qwen3-4B-Thinking | 386 | Temperature: 0.0 | ✅ |

**Key Findings**:
- Established ~50-53% accuracy baseline for vulnerability detection
- Both Instruct and Thinking models showed similar performance
- Improved CWE prompts in mars_rerun/ yielded consistent results

**Notes**:
- `mars/` and `mars_rerun/` conducted on same day with different prompt versions
- mars_rerun/ contains results with enhanced CWE descriptions

---

### **Phase 2a: 30B Model Experiments (Oct 20, 2025)**

**Purpose**: Evaluate larger 30B models for improved performance

**Hardware**: RunPod (NVIDIA H100 80GB HBM3)

**Directory**: `results/runpod/`

**Experiments**:
| Experiment | Model | Samples | Timestamp | Status |
|------------|-------|---------|-----------|--------|
| 30B Instruct Zero-shot | Qwen3-30B-Instruct | 386 | Oct 20, 11:59 | ✅ |
| 30B Instruct Few-shot | Qwen3-30B-Instruct | 386 | Oct 20 | ✅ |
| 30B Thinking Zero-shot | Qwen3-30B-Thinking | 386 | Oct 20 | ✅ |
| 30B Thinking Few-shot | Qwen3-30B-Thinking | 386 | Oct 20 | ✅ |

**Key Findings**:
- First experiments with H100 GPU infrastructure
- Larger models for potential performance improvements

---

### **Phase 2b: Re-runs & Hardware Comparison (Nov 2-8, 2025)**

**Purpose**:
1. Re-run 30B models with improved prompts (Nov 2)
2. Compare 4B performance on different hardware: Mars (RTX A5000) vs RunPod (H100) (Nov 8)

**Hardware**: RunPod (NVIDIA H100 80GB HBM3)

**Directory**: `results/runpod_rerun/`

**Experiments**:

**30B Re-runs with Improved Prompts (Nov 2, 2025):**
| Experiment | Model | Samples | Timestamp | Status |
|------------|-------|---------|-----------|--------|
| 30B Instruct Zero-shot | Qwen3-30B-Instruct | 386 | Nov 2, 05:23 | ✅ |
| 30B Instruct Few-shot | Qwen3-30B-Instruct | 386 | Nov 2 | ✅ |
| 30B Thinking Zero-shot | Qwen3-30B-Thinking | 386 | Nov 2 | ✅ |
| 30B Thinking Few-shot | Qwen3-30B-Thinking | 386 | Nov 2, 07:11 | ✅ |

**4B Hardware Comparison (Nov 8, 2025):**
| Experiment | Model | Hardware | Accuracy | Energy | Timestamp | Status |
|------------|-------|----------|----------|--------|-----------|--------|
| 4B Thinking Zero-shot | Qwen3-4B-Thinking | H100 | 50.26% | 2.849 kWh | Nov 8, 02:07 | ✅ |
| 4B Thinking Few-shot | Qwen3-4B-Thinking | H100 | 52.59% | TBD kWh | Nov 8, 02:55 | ✅ |

**Key Findings**:
- Direct hardware comparison: Same models on different GPUs
- Energy efficiency analysis: H100 vs RTX A5000

**Notes**:
- codecarbon emissions.csv files contain multiple entries when applicable
- Example: `codecarbon_thinking_sa-few/emissions.csv` has both 30B (Nov 2) and 4B (Nov 8) entries

---

### **Phase 3a: Code Generation on Mars (Nov 6-7, 2025)**

**Purpose**: Evaluate code generation capabilities using HumanEval benchmark

**Hardware**: Mars (NVIDIA RTX A5000)

**Dataset**: HumanEval (164 Python programming problems)

**Directory**: `results/mars_codegen/`

**Experiments**:
| Experiment | Model | Samples | Pass@1 | Energy | Runtime | Timestamp | Status |
|------------|-------|---------|--------|--------|---------|-----------|--------|
| Baseline Zero-shot | Qwen3-4B-Instruct | 164 | TBD | TBD kWh | TBD | Nov 6, 23:15 | ✅ |
| Baseline Few-shot | Qwen3-4B-Instruct | 164 | TBD | TBD kWh | TBD | Nov 6 | ✅ |
| Thinking Zero-shot | Qwen3-4B-Thinking | 164 | TBD | TBD kWh | TBD | Nov 6 | ✅ |
| Thinking Few-shot | Qwen3-4B-Thinking | 164 | **99.39%** | 0.309 kWh | 3.4h | Nov 7, 22:00 | ✅ |

**Key Findings**:
- Excellent code generation performance (99%+ Pass@1)
- Energy efficient compared to vulnerability detection
- HumanEval: Industry-standard benchmark for code generation

**Notes**:
- File naming includes evaluation results: `*_detailed_results_evaluation.json`
- Includes evaluated CSV with pass/fail status

---

### **Phase 3b: Code Generation on RunPod (Nov 7, 2025)**

**Purpose**: Evaluate 30B models for code generation

**Hardware**: RunPod (NVIDIA H100 80GB HBM3)

**Dataset**: HumanEval (164 Python programming problems)

**Directory**: `results/runpod_codegen/`

**Experiments**:
| Experiment | Model | Samples | Timestamp | Status |
|------------|-------|---------|-----------|--------|
| 30B Baseline Zero-shot | Qwen3-30B-Instruct | 164 | Nov 7, 13:25 | ✅ |
| 30B Baseline Few-shot | Qwen3-30B-Instruct | 164 | Nov 7 | ✅ |
| 30B Thinking Zero-shot | Qwen3-30B-Thinking | 164 | Nov 7 | ✅ |
| 30B Thinking Few-shot | Qwen3-30B-Thinking | 164 | Nov 7 | ✅ |

**Key Findings**:
- Larger models for code generation comparison
- H100 hardware performance evaluation

---

### **Phase 4: RQ2 Multi-Agent Experiments (Nov 15-17, 2025)**

**Purpose**: Compare Dual-Agent and Multi-Agent architectures against Single-Agent baseline (RQ2)

**Hardware**: RunPod (NVIDIA H100 80GB HBM3)

**Directories**: `results/runpod_rq2_pod1` through `results/runpod_rq2_pod8`

**Experiments**: 32 total experiments (16 vulnerability detection + 16 code generation)

| Pod | Model | Type | Prompting | Experiments | Status |
|-----|-------|------|-----------|-------------|--------|
| **pod1** | 4B | Instruct | Zero-shot | DA-vuln, DA-code, MA-vuln, MA-code | ✅ |
| **pod2** | 4B | Thinking | Zero-shot | DA-vuln, DA-code, MA-vuln, MA-code | ✅ |
| **pod3** | 4B | Instruct | Few-shot | DA-vuln, DA-code, MA-vuln, MA-code | ✅ |
| **pod4** | 4B | Thinking | Few-shot | DA-vuln, DA-code, MA-vuln, MA-code | ✅ |
| **pod5** | 30B | Instruct | Zero-shot | DA-vuln, DA-code, MA-vuln, MA-code | ✅ |
| **pod6** | 30B | Thinking | Zero-shot | DA-vuln, DA-code, MA-vuln, MA-code | ✅ |
| **pod7** | 30B | Instruct | Few-shot | DA-vuln, DA-code, MA-vuln, MA-code | ✅ |
| **pod8** | 30B | Thinking | Few-shot | DA-vuln, DA-code, MA-vuln, MA-code | ✅ |

**Key Findings**:
- **Dual-Agent (DA)**: Two agents in adversarial debate (vulnerability detection) or code review (code generation)
- **Multi-Agent (MA)**: Four agents in structured deliberation phases
- All experiments use CWE-enhanced prompts for vulnerability detection
- Energy and emissions tracked via CodeCarbon emissions.csv in each pod directory

**File Naming Convention**:
```
DA-{task}-{agents}-{prompting}_shot_Qwen-{model}_*
MA-{task}-{phases}-{prompting}_shot_Qwen-{model}_*

Examples:
- DA-vuln-two-zero_shot_Qwen-Qwen3-4B-Instruct-2507_vuln_*
- MA-code-four-few_shot_Qwen-Qwen3-30B-A3B-Thinking-2507_*
```

**Notes**:
- Some pods have nested `results/` subdirectory (e.g., pod1)
- Pod1 contains one interrupted experiment (235757) that was completed in a second session (235404)
- Emissions.csv in each pod may contain multiple experiment sessions

---

### **Phase 5: Cross-Architecture Validation with Nemotron (Dec 9-10, 2025)**

**Purpose**: Validate RQ1/RQ2 findings generalize beyond Qwen3 using NVIDIA Llama-Nemotron model family

**Hardware**: RunPod (4× NVIDIA H100 80GB HBM3 pods in parallel)

**Model**: `nvidia/Llama-3.1-Nemotron-Nano-8B-v1`

**Directory**: `results/rq2_cross_architecture/`

**Sub-directories**:
```
rq2_cross_architecture/
├── nemotron_8b_vuln_SA-zero_instruct/   # NM-5: Vuln detection, zero-shot, instruct mode
├── nemotron_8b_vuln_SA-zero_thinking/   # NM-7: Vuln detection, zero-shot, thinking mode
├── nemotron_8b_vuln_SA-few_instruct/    # NM-6: Vuln detection, few-shot, instruct mode
├── nemotron_8b_vuln_SA-few_thinking/    # NM-8: Vuln detection, few-shot, thinking mode
├── nemotron_8b_code_SA-zero_instruct/   # NM-13: Code generation, zero-shot, instruct mode
├── nemotron_8b_code_SA-zero_thinking/   # NM-15: Code generation, zero-shot, thinking mode
├── nemotron_8b_code_SA-few_instruct/    # NM-14: Code generation, few-shot, instruct mode
└── nemotron_8b_code_SA-few_thinking/    # NM-16: Code generation, few-shot, thinking mode
```

**Experiments**:

| ID | Task | Prompting | Mode | F1/Pass@1 | Energy (kg CO2) | Status |
|----|------|-----------|------|-----------|-----------------|--------|
| NM-5 | Vuln | Zero-shot | Instruct | F1=0.25 | 0.1334 | ✅ |
| NM-6 | Vuln | Few-shot | Instruct | **F1=0.49** | 0.0618 | ✅ |
| NM-7 | Vuln | Zero-shot | Thinking | F1=0.18 | 0.0850 | ✅ |
| NM-8 | Vuln | Few-shot | Thinking | F1=0.46 | 0.2404 | ✅ |
| NM-13 | Code | Zero-shot | Instruct | **98.17%** | 0.3993 | ✅ |
| NM-14 | Code | Few-shot | Instruct | 93.29% | 0.6777 | ✅ |
| NM-15 | Code | Zero-shot | Thinking | 92.07% | 0.4290 | ✅ |
| NM-16 | Code | Few-shot | Thinking | 92.68% | 0.4055 | ✅ |

**Key Findings**:
1. **Vulnerability Detection**: Few-shot Instruct (NM-6) achieves best F1 (0.49) with lowest energy (0.0618 kg CO2)
2. **Code Generation**: Zero-shot Instruct (NM-13) achieves best Pass@1 (98.17%) - Thinking mode hurts performance
3. **Consistent with Qwen3**: Prompting strategy matters more than reasoning mode for classification; Instruct outperforms Thinking for code generation
4. **Total Energy**: 2.43 kg CO2 across all 8 experiments

**Toggle Mechanism**: Unlike Qwen3's API parameter, Nemotron uses system prompt prefix:
- Thinking: `"detailed thinking on\n\n{system_prompt}"`
- Instruct: `"detailed thinking off\n\n{system_prompt}"`

---

## Data Organization

### File Naming Convention

**Vulnerability Detection:**
```
{Design}_{Model}_{Timestamp}_detailed_results.jsonl
{Design}_{Model}_{Timestamp}_summary_vulnerability_metrics.csv
{Design}_{Model}_{Timestamp}_classification_report.txt
{Design}_{Model}_{Timestamp}_energy_tracking.json
```

**Code Generation:**
```
{Design}_{Model}_{Timestamp}_detailed_results.jsonl
{Design}_{Model}_{Timestamp}_detailed_results_evaluation.json
{Design}_{Model}_{Timestamp}_detailed_results_evaluated.csv
```

**Energy Tracking:**
```
codecarbon_{model_type}_{design}/emissions.csv
```

Where:
- `Design`: SA-zero (zero-shot) or SA-few (few-shot)
- `Model`: Full model name (e.g., Qwen-Qwen3-4B-Thinking-2507)
- `model_type`: baseline or thinking
- `design`: sa-zero or sa-few

### CodeCarbon Directory Structure

Each experiment has a dedicated codecarbon subdirectory for emissions tracking:

```
results/
└── {experiment_dir}/
    └── codecarbon_{model_type}_{design}/
        └── emissions.csv
```

**Important Notes**:
- Emissions.csv files may contain **multiple session entries** when experiments were re-run
- Example: `runpod_rerun/codecarbon_thinking_sa-few/emissions.csv` contains:
  - Session 1: 30B Thinking Few-shot (Nov 2, 2025)
  - Session 2: 4B Thinking Few-shot (Nov 8, 2025)
- Always check `project_name` field to identify which experiment each row belongs to

---

## Hardware Specifications

### Mars Server (Local)
- **GPU**: NVIDIA RTX A5000 (24GB VRAM)
- **CPU**: AMD EPYC 7643 48-Core Processor
- **RAM**: 503.5 GB
- **Location**: Singapore
- **Used for**: 4B model experiments (all phases)

### RunPod (Cloud)
- **GPU**: NVIDIA H100 80GB HBM3
- **CPU**: Intel Xeon Platinum 8468 (160-192 cores)
- **RAM**: 1511-2015 GB
- **Location**: Canada
- **Used for**: 30B model experiments + 4B hardware comparison

---

## Datasets

### Vulnerability Detection
- **Dataset**: VulTrial (balanced subset)
- **Samples**: 386 vulnerable/benign code pairs
- **Source**: `vuln_database/VulTrial_386_samples_balanced.jsonl`
- **Task**: Binary classification (vulnerable vs benign)

### Code Generation
- **Dataset**: HumanEval
- **Samples**: 164 Python programming problems
- **Source**: `data/HumanEval.jsonl`
- **Metric**: Pass@1 (percentage solved correctly on first attempt)

---

## Model Configurations

### Qwen3-4B-Instruct-2507
- **Type**: Baseline instruction-tuned model
- **Size**: 4 billion parameters
- **Context**: 65536 tokens
- **Endpoint**: vLLM OpenAI-compatible API

### Qwen3-4B-Thinking-2507
- **Type**: Reasoning/thinking model
- **Size**: 4 billion parameters
- **Context**: 65536 tokens
- **Special**: Supports chain-of-thought reasoning
- **Endpoint**: vLLM OpenAI-compatible API

### Qwen3-30B-A3B-Instruct-2507
- **Type**: Baseline instruction-tuned model
- **Size**: 30 billion parameters
- **Context**: 65536 tokens

### Qwen3-30B-A3B-Thinking-2507
- **Type**: Reasoning/thinking model
- **Size**: 30 billion parameters
- **Context**: 65536 tokens

---

## Experiment Parameters

**Common across all experiments:**
- Temperature: 0.0 (deterministic)
- Max tokens: Auto (based on model context)
- GPU memory utilization: 0.9
- Tool calling: Enabled (where applicable)

**Prompting Strategies:**
- **Zero-shot**: Task description only, no examples
- **Few-shot**: Task description + 2-3 example demonstrations

---

## Analysis Notebooks

Analysis performed in `/notebooks/`:

1. `rq1_analysis.ipynb` - Performance metrics and error analysis
2. `rq1_codecarbon_analysis.ipynb` - Hardware energy breakdown
3. `rq1_phase2a_analysis.ipynb` - 30B model analysis
4. `rq1_phase2a_codecarbon_analysis.ipynb` - 30B energy analysis
5. `rq1_prompt_comparison_analysis.ipynb` - Zero-shot vs Few-shot
6. `rq1_prompt_comparison_codecarbon_analysis.ipynb` - Prompt strategy energy

**Outputs**: `results/analysis/` and `results/analysis_prompt_comparison/`

---

## Key Research Questions

**RQ1**: How do model size and reasoning capabilities affect vulnerability detection accuracy and energy efficiency?

**RQ2**: What is the trade-off between prompting strategy (zero-shot vs few-shot) and performance/energy consumption?

**RQ3**: How does hardware (RTX A5000 vs H100) impact performance and energy efficiency for the same models?

**RQ4**: How do vulnerability detection and code generation tasks compare in terms of model performance and energy requirements?

---

## Data Quality Notes

### Known Issues

1. **Resume Logic Bug (Fixed Nov 7, 2025)**:
   - Issue: Code generation script resume logic matched old vulnerability detection files
   - Affected: `mars_codegen/Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251011-103534_detailed_results.jsonl`
   - Resolution: File contained mixed data (386 vuln + 164 codegen entries)
   - Fix: Split into separate files with correct timestamps
   - Current: `Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-220000_detailed_results.jsonl` (164 entries, clean)

2. **Duplicate Samples**:
   - VulTrial dataset has 2 duplicate entries (indices 349259, 439495)
   - Total unique samples: 384 (out of 386)
   - See `docs/dataset_duplicate_analysis.md` for details

3. **Missing Emissions Directories**:
   - Some early experiments may not have codecarbon subdirectories
   - Check for `emissions.csv` in parent directory as fallback

4. **RQ2 Pod1 Interrupted Experiment (Nov 15, 2025)**:
   - Experiment: `DA-vuln-two-zero_shot_Qwen-Qwen3-4B-Instruct-2507_vuln_20251115-235757`
   - Issue: First attempt interrupted after 5.5 seconds (F1=33.33%, incomplete)
   - Resolution: Successfully completed in second session (235404) with F1=47.81%
   - Status: Interrupted experiment (235757) excluded from analysis; only successful run (235404) included

5. **Nemotron Toggle Bug (Fixed Dec 8, 2025)**:
   - Issue: `prepend_thinking_toggle()` function was defined but never called by experiment scripts
   - Affected: All 8 initial Nemotron experiments (Dec 7-8) ran without proper Thinking/Instruct toggle
   - Resolution: Added toggle application to all 7 experiment scripts
   - Status: All 8 experiments re-run with fix applied (Dec 9-10, 2025)

---

**Last Updated**: 2025-12-10
**Total Experiments**: 72 (32 RQ1 Qwen3 + 32 RQ2 Qwen3 + 8 Cross-Architecture Nemotron)
  - **RQ1 (Qwen3)**: 16 vulnerability detection + 16 code generation (Single-Agent)
  - **RQ2 (Qwen3)**: 16 vulnerability detection + 16 code generation (8 Dual-Agent + 8 Multi-Agent each)
  - **Cross-Architecture (Nemotron 8B)**: 4 vulnerability detection + 4 code generation (Single-Agent)
**Total Samples Processed**: ~39,600 (72 experiments × ~550 avg samples)
**Hardware Used**: Mars RTX A5000 + RunPod H100
**Models Evaluated**: 5 (Qwen3 4B/30B × Instruct/Thinking + Nemotron-Nano-8B)
**Agent Architectures**: 3 (Single-Agent, Dual-Agent, Multi-Agent)
