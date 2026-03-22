# Experiment Results Directory

This directory contains all experimental results for the agent-green project, organized chronologically and by experiment type.

## Directory Structure

```
results/
├── mars/                    # Phase 1: Initial 4B vuln detection (Oct 11, 2025)
├── mars_rerun/              # Phase 1b: 4B vuln detection re-runs with improved CWE prompts (Oct 11, 2025)
├── mars_codegen/            # Phase 3a: Code generation on Mars 4B (Nov 6-7, 2025)
├── runpod/                  # Phase 2a: Initial 30B vuln detection (Oct 20, 2025)
├── runpod_rerun/            # Phase 2b: 30B+4B vuln detection re-runs (Nov 2-8, 2025)
├── runpod_codegen/          # Phase 3b: Code generation on RunPod 4B+30B (Nov 7, 2025)
├── runpod_codegen_rerun/    # Phase 3c: Qwen3 code generation reruns with reasoning (Feb 7, 2026)
├── runpod_rq2_pod1-8/       # Phase 4: RQ2 Multi-Agent experiments (Nov 15-17, 2025)
├── rq2_cross_architecture/  # Phase 5-6: Cross-architecture validation with Nemotron 8B+49B (Dec 9-Jan 2026)
├── rq2_nm8b_ma_rerun_20260103/ # Rerun verification for Nemotron 8B MA Vuln experiments (Jan 3, 2026)
├── runpod_log_analysis/     # Phase 7: RQ3 Log Analysis experiments (Jan 2026)
├── runpod_vuln_incremental/ # Phase 8: Incremental 100-sample vuln detection runs (Mar 2026)
├── runpod_vuln_486/         # Phase 8b: Merged 486-sample vuln detection results (386+100)
├── runpod_vuln_incremental_pod1_raw/ # Raw download from Pod 1 (Qwen3-30B incremental)
├── runpod_vuln_incremental_pod2_raw/ # Raw download from Pod 2 (Qwen3-4B incremental)
├── runpod_vuln_incremental_pod3_raw/ # Raw download from Pod 3 (Nemotron-Super-49B Instruct)
├── runpod_vuln_incremental_pod4_raw/ # Raw download from Pod 4 (Nemotron-Nano-8B Instruct)
├── runpod_vuln_incremental_pod5_raw/ # Raw download from Pod 5 (Nemotron-Super-49B Thinking)
├── runpod_vuln_incremental_pod6_raw/ # Raw download from Pod 6 (Nemotron-Nano-8B Thinking)
├── runpod_vuln_incremental_pod7_raw/ # Raw download from Pod 7 (Nemotron-Super-49B MA-few Thinking)
├── runpod_vuln_384_incremental/ # Phase 9: 384-sample incremental results staging (48 SA/DA/MA configs, for 870 merge)
├── runpod_vuln_870/         # Phase 9: Merged 870-sample vuln detection results (486+384)
├── runpod_870_batch1_raw/   # Phase 9 raw: SA instruct × 384 incr (4 models)
├── runpod_870_batch2_raw/   # Phase 9 raw: SA thinking × 384 incr (4 models)
├── runpod_870_batch3_raw/   # Phase 9 raw: DA instruct × 384 incr (4 models)
├── runpod_870_batch4_raw/   # Phase 9 raw: DA thinking × 384 incr (4 models)
├── runpod_870_batch5_raw/   # Phase 9 raw: MA instruct × 384 incr (4 models)
├── runpod_870_batch6_raw/   # Phase 9 raw: MA thinking × 384 incr (4 models)
├── runpod_870_batch7_raw/   # Phase 9 raw: NA instruct × 384 incr (4 models)
├── runpod_870_batch8_raw/   # Phase 9 raw: NA thinking × 384 incr (4 models)
├── runpod_na486_raw/        # Phase 9 raw: NA × 486 original samples (4 models × 2 modes)
├── rq3_baseline/            # RQ3 Phase A: Baseline sampling, pool analysis, and rater sheets
├── sota_comparison/         # SOTA comparison: Claude Opus 4.5 & Sonnet 4.5 vuln detection (Jan 2026)
├── analysis/                # Analysis outputs from Jupyter notebooks (Phase 1-2)
├── analysis_prompt_comparison/ # Prompt comparison analysis outputs
├── analysis_phase2a/        # Phase 2a analysis outputs
└── analysis_rq1/            # RQ1 cross-architecture analysis outputs
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

### **Phase 3c: Code Generation Reruns with Reasoning (Feb 7, 2026)**

**Purpose**: Rerun Qwen3 SA Thinking codegen experiments to recover thinking content lost in original runs due to a script versioning issue (see `docs/RQ3_Baseline_Sampling.md` Section 6)

**Hardware**: RunPod (NVIDIA H100 80GB HBM3)

**Dataset**: HumanEval (164 Python programming problems)

**Directory**: `results/runpod_codegen_rerun/`

**Experiments**:
| Experiment | Model | Samples | Pass@1 | Status |
|------------|-------|---------|--------|--------|
| SA Zero-shot | Qwen3-4B-Thinking | 164 | 98.78% (162/164) | ✅ |
| SA Few-shot | Qwen3-4B-Thinking | 164 | 97.56% (160/164) | ✅ |
| SA Zero-shot | Qwen3-30B-Thinking | 164 | 98.17% (161/164) | ✅ |
| SA Few-shot | Qwen3-30B-Thinking | 164 | 96.95% (159/164) | ✅ |

**Key Findings**:
- All rerun results contain the `reasoning` field with full thinking content (`</think>` tags present)
- Pass@1 scores show minor variation from original runs (within vLLM non-determinism)
- Original results in `runpod_codegen/` are preserved; reruns supersede them in consolidated files via deduplication priority

**Notes**:
- These reruns serve exclusively for RQ3 thinking content recovery (explanation baseline sampling)
- Original (Nov 2025) result files in `runpod_codegen/` lack the `reasoning` field because the script did not yet save it
- The corrected script (post-commit `bb54a9e`, Nov 22, 2025) saves `result['reasoning'] = response_text`

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

### **Phase 5: Cross-Architecture Validation with Nemotron SA (Dec 9-16, 2025)**

**Purpose**: Validate RQ1 findings generalize beyond Qwen3 using NVIDIA Llama-Nemotron model family

**Hardware**: RunPod (4× NVIDIA H100 80GB HBM3 pods in parallel)

**Models**:
- `nvidia/Llama-3.1-Nemotron-Nano-8B-v1` (8B parameters)
- `nvidia/Llama-3.3-Nemotron-Super-49B-v1` (49B parameters)

**Directory**: `results/rq2_cross_architecture/`

**Sub-directories (Single-Agent)**:
```
rq2_cross_architecture/
├── nemotron_8b_vuln_SA-zero_instruct/   # NM-5: 8B Vuln, zero-shot, instruct
├── nemotron_8b_vuln_SA-zero_thinking/   # NM-7: 8B Vuln, zero-shot, thinking
├── nemotron_8b_vuln_SA-few_instruct/    # NM-6: 8B Vuln, few-shot, instruct
├── nemotron_8b_vuln_SA-few_thinking/    # NM-8: 8B Vuln, few-shot, thinking
├── nemotron_8b_code_SA-zero_instruct/   # NM-13: 8B Code, zero-shot, instruct
├── nemotron_8b_code_SA-zero_thinking/   # NM-15: 8B Code, zero-shot, thinking
├── nemotron_8b_code_SA-few_instruct/    # NM-14: 8B Code, few-shot, instruct
├── nemotron_8b_code_SA-few_thinking/    # NM-16: 8B Code, few-shot, thinking
├── nemotron_49b_vuln_SA-zero_instruct/  # NM-1: 49B Vuln, zero-shot, instruct
├── nemotron_49b_vuln_SA-zero_thinking/  # NM-3: 49B Vuln, zero-shot, thinking
├── nemotron_49b_vuln_SA-few_instruct/   # NM-2: 49B Vuln, few-shot, instruct
├── nemotron_49b_vuln_SA-few_thinking/   # NM-4: 49B Vuln, few-shot, thinking
├── nemotron_49b_code_SA-zero_instruct/  # NM-9: 49B Code, zero-shot, instruct
├── nemotron_49b_code_SA-zero_thinking/  # NM-11: 49B Code, zero-shot, thinking
├── nemotron_49b_code_SA-few_instruct/   # NM-10: 49B Code, few-shot, instruct
└── nemotron_49b_code_SA-few_thinking/   # NM-12: 49B Code, few-shot, thinking
```

**Nemotron-Nano-8B Experiments (Dec 9-10)**:

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

**Nemotron-Super-49B Experiments (Dec 12-16)**:

| ID | Task | Prompting | Mode | F1/Pass@1 | Energy (kg CO2) | Status |
|----|------|-----------|------|-----------|-----------------|--------|
| NM-1 | Vuln | Zero-shot | Instruct | F1=0.54 | 0.4215 | ✅ |
| NM-2 | Vuln | Few-shot | Instruct | F1=0.58 | 0.3673 | ✅ |
| NM-3 | Vuln | Zero-shot | Thinking | **F1=0.64** | 2.5072 | ✅ |
| NM-4 | Vuln | Few-shot | Thinking | F1=0.63 | 2.0544 | ✅ |
| NM-9 | Code | Zero-shot | Instruct | 91.46% | 0.2999 | ✅ |
| NM-10 | Code | Few-shot | Instruct | **100.00%** | 0.1152 | ✅ |
| NM-11 | Code | Zero-shot | Thinking | 92.07% | 4.7379 | ✅ |
| NM-12 | Code | Few-shot | Thinking | **100.00%** | 2.3128 | ✅ |

**Key Findings**:
1. **Vulnerability Detection**: Nemotron-49B Thinking achieves best F1 (0.64) but at 10x energy cost vs 8B
2. **Code Generation**: Nemotron-49B achieves 100% Pass@1 in few-shot modes
3. **Thinking Mode Overhead**: 49B thinking uses 11.85x more energy than instruct mode
4. **Architecture Comparison**: Qwen3-4B MoE achieves comparable performance to Nemotron-8B dense at ~5x lower energy
5. **Total Energy**: 2.43 kg CO2 (8B) + 12.82 kg CO2 (49B) = 15.25 kg CO2 across all 16 Nemotron experiments

**Toggle Mechanism**: Unlike Qwen3's API parameter, Nemotron uses system prompt prefix:
- Thinking: `"detailed thinking on\n\n{system_prompt}"`
- Instruct: `"detailed thinking off\n\n{system_prompt}"`

---

### **Phase 6: Cross-Architecture Validation with Nemotron DA/MA (Dec 23, 2025 - Jan 3, 2026)**

**Purpose**: Validate RQ2 findings (Dual-Agent and Multi-Agent) generalize beyond Qwen3

**Hardware**: RunPod (1-2× NVIDIA H100 80GB HBM3 pods)

**Model**: `nvidia/Llama-3.1-Nemotron-Nano-8B-v1` (8B parameters)

**Sub-directories (Dual-Agent)**:
```
rq2_cross_architecture/
├── nemotron_8b_vuln_DA-zero_instruct/   # NM-22: 8B DA Vuln, zero-shot, instruct
├── nemotron_8b_vuln_DA-few_instruct/    # NM-21: 8B DA Vuln, few-shot, instruct
├── nemotron_8b_vuln_DA-zero_think/      # NM-24: 8B DA Vuln, zero-shot, thinking
├── nemotron_8b_vuln_DA-few_think/       # NM-23: 8B DA Vuln, few-shot, thinking
├── nemotron_8b_code_DA-zero_instruct/   # NM-38: 8B DA Code, zero-shot, instruct
├── nemotron_8b_code_DA-few_instruct/    # NM-37: 8B DA Code, few-shot, instruct
├── nemotron_8b_code_DA-zero_think/      # NM-40: 8B DA Code, zero-shot, thinking
└── nemotron_8b_code_DA-few_think/       # NM-39: 8B DA Code, few-shot, thinking
```

**Sub-directories (Multi-Agent)**:
```
rq2_cross_architecture/
├── nemotron_8b_vuln_MA-zero_instruct/   # NM-30: 8B MA Vuln, zero-shot, instruct ✅
├── nemotron_8b_vuln_MA-few_instruct/    # NM-29: 8B MA Vuln, few-shot, instruct ✅
├── nemotron_8b_vuln_MA-zero_think/      # NM-32: 8B MA Vuln, zero-shot, thinking ✅
├── nemotron_8b_vuln_MA-few_think/       # NM-31: 8B MA Vuln, few-shot, thinking ✅
├── nemotron_8b_code_MA-zero_instruct/   # NM-46: 8B MA Code, zero-shot, instruct ✅
├── nemotron_8b_code_MA-few_instruct/    # NM-45: 8B MA Code, few-shot, instruct ✅
├── nemotron_8b_code_MA-zero_think/      # NM-48: 8B MA Code, zero-shot, thinking ✅
└── nemotron_8b_code_MA-few_think/       # NM-47: 8B MA Code, few-shot, thinking ✅
```

**Nemotron-8B Dual-Agent Experiments (Dec 23-25)**:

| ID | Task | Prompting | Mode | Accuracy/Pass@1 | Energy (kg CO2) | Status |
|----|------|-----------|------|-----------------|-----------------|--------|
| NM-21 | Vuln | Few-shot | Instruct | TBD | TBD | ✅ Complete (Dec 23) |
| NM-22 | Vuln | Zero-shot | Instruct | TBD | TBD | ✅ Complete (Dec 23) |
| NM-23 | Vuln | Few-shot | Thinking | TBD | TBD | ✅ Complete (Dec 23) |
| NM-24 | Vuln | Zero-shot | Thinking | TBD | TBD | ✅ Complete (Dec 23) |
| NM-37 | Code | Few-shot | Instruct | 100% | 0.659 | ✅ Complete (Dec 24) |
| NM-38 | Code | Zero-shot | Instruct | 98.17% | 1.044 | ✅ Complete (Dec 24) |
| NM-39 | Code | Few-shot | Thinking | 90.24% | 1.248 | ✅ Complete (Dec 25) |
| NM-40 | Code | Zero-shot | Thinking | 95.12% | 0.872 | ✅ Complete (Dec 25) |

**Nemotron-8B Multi-Agent Experiments (Dec 25, 2025 - Jan 3, 2026)**:

| ID | Task | Prompting | Mode | Accuracy | Energy (kg CO2) | Sessions | Context Overflow Skips | Status |
|----|------|-----------|------|----------|-----------------|----------|------------------------|--------|
| NM-29 | Vuln | Few-shot | Instruct | 50% | 1.048 | 18 | 17/384 (4.4%) | ✅ Complete |
| NM-30 | Vuln | Zero-shot | Instruct | 50% | 0.807 | 26 | 25/384 (6.5%) | ✅ Complete |
| NM-31 | Vuln | Few-shot | Thinking | 50% | 1.143 | 35 | 34/384 (8.9%) | ✅ Complete |
| NM-32 | Vuln | Zero-shot | Thinking | 50% | 1.377 | 40 | 39/384 (10.2%) | ✅ Complete |
| NM-45 | Code | Few-shot | Instruct | 96.34% | 0.542 | 1 | - | ✅ Complete |
| NM-46 | Code | Zero-shot | Instruct | 98.78% | 0.815 | 1 | - | ✅ Complete |
| NM-47 | Code | Few-shot | Thinking | 92.68% | 0.886 | 5 | - | ✅ Complete |
| NM-48 | Code | Zero-shot | Thinking | 87.80% | 0.873 | 4 | - | ✅ Complete |

**Key Observations**:
1. **Context Overflow Issues**: MA experiments frequently hit 64K context limit due to 4-agent multi-turn conversations
2. **Context Overflow Skips**: When a sample causes context overflow, the experiment crashes. On resume, the `auto_resume_ma_vuln.sh` script automatically skips the problematic sample (option 2) and writes a placeholder record with `skipped=true`, `error=USER_SKIP`, `vuln=-1`. Thinking mode has higher skip rate (8.9-10.2%) than Instruct mode (4.4-6.5%) due to longer reasoning outputs.
3. **Sessions**: MA experiments require multiple resume sessions (18-40 sessions due to context overflows). Each session = one crash/restart cycle.
4. **Energy**: MA experiments consume more energy due to multi-turn agent coordination overhead
5. **Extraction Bug Fix (Dec 29, 2025)**: Fixed JSON extraction logic to handle Nemotron's markdown-wrapped JSON responses (commit c8793c6). Original responses preserved in `_corrected.jsonl` files with re-evaluated predictions.
6. **Rerun Verification (Jan 3, 2026)**: Full rerun of all 4 MA Vuln experiments confirmed 100% reproducibility. Results archived in `results/rq2_nm8b_ma_rerun_20260103/`

---

### **Phase 7: RQ3 Log Analysis Experiments (Jan 18, 2026)**

**Purpose**: Evaluate LLM-based log anomaly detection on HDFS logs with different agent architectures

**Hardware**: RunPod (NVIDIA H100 80GB HBM3)

**Dataset**: HDFS Log Sessions (385 sessions, binary anomaly labels)

**Directory**: `results/runpod_log_analysis/`

**Sub-directories**:
```
runpod_log_analysis/
├── SA-zero_Qwen3-4B-Instruct/   # ✅ Single-Agent Zero-shot Instruct
├── SA-few_Qwen3-4B-Instruct/    # ✅ Single-Agent Few-shot Instruct
├── SA-zero_Qwen3-4B-Thinking/   # ✅ Single-Agent Zero-shot Thinking
├── SA-few_Qwen3-4B-Thinking/    # ✅ Single-Agent Few-shot Thinking
├── DA-zero_Qwen3-4B-Instruct/   # ✅ Dual-Agent Zero-shot Instruct
├── DA-few_Qwen3-4B-Instruct/    # ✅ Dual-Agent Few-shot Instruct
├── DA-zero_Qwen3-4B-Thinking/   # ✅ Dual-Agent Zero-shot Thinking
├── DA-few_Qwen3-4B-Thinking/    # ✅ Dual-Agent Few-shot Thinking
├── MA-zero_Qwen3-4B-Instruct/   # ✅ Multi-Agent Zero-shot Instruct
├── MA-few_Qwen3-4B-Instruct/    # ✅ Multi-Agent Few-shot Instruct
├── MA-zero_Qwen3-4B-Thinking/   # ✅ Multi-Agent Zero-shot Thinking
├── MA-few_Qwen3-4B-Thinking/    # ✅ Multi-Agent Few-shot Thinking
├── SA-zero_Qwen3-30B-Instruct/  # ✅ Single-Agent Zero-shot Instruct (30B)
├── SA-few_Qwen3-30B-Instruct/   # ✅ Single-Agent Few-shot Instruct (30B)
├── SA-zero_Qwen3-30B-Thinking/  # ✅ Single-Agent Zero-shot Thinking (30B)
├── SA-few_Qwen3-30B-Thinking/   # ✅ Single-Agent Few-shot Thinking (30B)
├── DA-zero_Qwen3-30B-Instruct/  # ✅ Dual-Agent Zero-shot Instruct (30B)
├── DA-few_Qwen3-30B-Instruct/   # ✅ Dual-Agent Few-shot Instruct (30B)
├── DA-zero_Qwen3-30B-Thinking/  # ✅ Dual-Agent Zero-shot Thinking (30B)
├── DA-few_Qwen3-30B-Thinking/   # ✅ Dual-Agent Few-shot Thinking (30B)
├── MA-zero_Qwen3-30B-Instruct/  # ✅ Multi-Agent Zero-shot Instruct (30B)
├── MA-few_Qwen3-30B-Instruct/   # ✅ Multi-Agent Few-shot Instruct (30B)
├── MA-zero_Qwen3-30B-Thinking/  # ✅ Multi-Agent Zero-shot Thinking (30B)
└── MA-few_Qwen3-30B-Thinking/   # ✅ Multi-Agent Few-shot Thinking (30B)
```

**Experiments (Qwen3-4B)**:

| Design | Prompting | Model | Accuracy | F1 | Emissions (kg CO2) | Status |
|--------|-----------|-------|----------|-----|-------------------|--------|
| SA | Zero-shot | Instruct | 24.9% | 5.2% | 0.00095 | ✅ |
| SA | Few-shot | Instruct | 22.3% | 6.3% | 0.00114 | ✅ |
| SA | Zero-shot | Thinking | 3.6% | 6.3% | 0.489 | ✅ |
| SA | Few-shot | Thinking | 3.4% | 6.0% | 0.506 | ✅ |
| DA | Zero-shot | Instruct | 17.4% | 5.5% | 0.108 | ✅ |
| DA | Few-shot | Instruct | 21.0% | 5.4% | 0.109 | ✅ |
| DA | Zero-shot | Thinking | 38.4% | 7.1% | 1.480 | ✅ |
| DA | Few-shot | Thinking | 52.7% | 6.2% | 1.383 | ✅ |
| MA | Zero-shot | Instruct | **66.2%** | 14.7% | 0.104 | ✅ |
| MA | Few-shot | Instruct | 40.0% | 8.1% | 0.103 | ✅ |
| MA | Zero-shot | Thinking | 80.8% | 2.6% | 0.517 | ✅ |
| MA | Few-shot | Thinking | **94.3%** | 0.0% | 0.725 | ✅ |

**Experiments (Qwen3-30B)**:

| Design | Prompting | Model | Accuracy | F1 | Emissions (kg CO2) | Status |
|--------|-----------|-------|----------|-----|-------------------|--------|
| SA | Zero-shot | Instruct | 9.9% | 5.4% | 0.00179 | ✅ |
| SA | Few-shot | Instruct | 20.5% | 7.3% | 0.00182 | ✅ |
| SA | Zero-shot | Thinking | 3.9% | 5.6% | 0.431 | ✅ |
| SA | Few-shot | Thinking | 56.1% | 2.3% | 0.391 | ✅ |
| DA | Zero-shot | Instruct | 10.1% | 5.5% | 0.108 | ✅ |
| DA | Few-shot | Instruct | 14.5% | 6.3% | 0.110 | ✅ |
| DA | Zero-shot | Thinking | 19.5% | 3.7% | 0.630 | ✅ |
| DA | Few-shot | Thinking | 31.9% | 5.1% | 0.696 | ✅ |
| MA | Zero-shot | Instruct | 24.2% | 5.2% | 0.111 | ✅ |
| MA | Few-shot | Instruct | 22.9% | 5.1% | 0.111 | ✅ |
| MA | Zero-shot | Thinking | 19.7% | 3.7% | 0.730 | ✅ |
| MA | Few-shot | Thinking | 31.9% | 5.1% | 0.791 | ✅ |

**Key Findings**:
1. **MA-few Thinking (4B) achieves best accuracy (94.3%)** - Combination of multi-agent deliberation and thinking mode
2. **MA-zero Thinking (4B) second best (80.8%)** - Strong performance even without examples
3. **MA-zero Instruct (4B) achieves best F1 (14.7%)** - Balanced precision-recall trade-off
4. **DA architecture rescues Thinking models (4B)** - SA Thinking: 3-4% → DA Thinking: 38-53% accuracy
5. **Thinking mode uses ~5-7x more energy** than Instruct in MA architecture
6. **30B consistently underperforms 4B** - Larger model over-predicts anomalies (high FP rate across all architectures)
7. **Few-shot helps DA/MA Thinking (30B)** - MA-few Thinking (31.9%) outperforms MA-zero Thinking (19.7%)
8. **4B MA Thinking with few-shot achieves high accuracy but zero F1** - Predicts almost everything as normal (high TN, low TP)

**Agent Architectures**:
- **NA (No-Agent)**: Direct LLM call without agent framework
- **SA (Single-Agent)**: Single agent with AutoGen framework
- **DA (Dual-Agent)**: Parser agent + Anomaly detector agent
- **MA (Multi-Agent)**: User proxy + Parser + Anomaly detector + Critic agents

**Key Features**:
- Resume capability for interrupted experiments
- Incremental result saving after each session
- Energy tracking across resume sessions

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
- **Dataset**: VulTrial (balanced subset, expanded)
- **Samples**: 486 vulnerable/benign code pairs (243 vuln + 243 safe)
- **Source**: `vuln_database/VulTrial_486_samples_balanced.jsonl` (combined ground truth)
- **Original**: 386 samples from `VulTrial_386_samples_balanced.jsonl`
- **Incremental**: 100 samples from `VulTrial_100_incremental.jsonl` (50 vuln + 50 safe, drawn from VulTrial-870 pool)
- **Task**: Binary classification (vulnerable vs benign)
- **Note**: Some MA/Thinking configs have 484-485 samples due to context overflow skips in the original 386-sample runs

### Code Generation
- **Dataset**: HumanEval
- **Samples**: 164 Python programming problems
- **Source**: `data/HumanEval.jsonl`
- **Metric**: Pass@1 (percentage solved correctly on first attempt)

### Log Analysis (RQ3)
- **Dataset**: HDFS Log Sessions
- **Samples**: 385 log sessions (sampled from HDFS_2k dataset)
- **Source**: `data/HDFS_385_sampled_sessions/`
- **Ground Truth**: `data/HDFS_anomaly_label_385_session_sampled.csv`
- **Task**: Binary classification (normal vs anomalous log session)
- **Metrics**: Accuracy, Precision, Recall, F1 Score

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

### nvidia/Llama-3.1-Nemotron-Nano-8B-v1
- **Type**: Dense instruction-tuned model (NVIDIA Llama-Nemotron family)
- **Size**: 8 billion parameters
- **Toggle**: System prompt prefix (`detailed thinking on/off`)
- **Note**: Supports both instruct and thinking modes via toggle

### nvidia/Llama-3.3-Nemotron-Super-49B-v1
- **Type**: Dense instruction-tuned model (NVIDIA Llama-Nemotron family)
- **Size**: 49 billion parameters
- **Toggle**: System prompt prefix (`detailed thinking on/off`)
- **Note**: Largest model evaluated; extreme thinking mode energy overhead (11.85x)

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
7. `rq1_cross_architecture_analysis.ipynb` - Cross-architecture comparison (Qwen3 vs Nemotron)

**Outputs**:
- `results/analysis/` - Phase 1 analysis
- `results/analysis_phase2a/` - Phase 2a analysis
- `results/analysis_prompt_comparison/` - Prompt comparison analysis
- `results/analysis_rq1/` - Cross-architecture analysis (Qwen3 4B/30B vs Nemotron 8B/49B)

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

6. **Vulnerability Think-Tag Parsing Bug (Fixed Feb 9, 2026)**:
   - Issue: Vuln prediction parsers searched entire model output (including `<think>...</think>` blocks) for keywords, causing false positives when reasoning mentioned vulnerability terms but the final answer was "not vulnerable"
   - Affected: 25 JSONL files across SA/DA/MA designs (3,019 predictions changed)
   - Resolution: Fixed via `scripts/fix_vuln_think_tag_parsing.py`; all 54 evaluation files regenerated; consolidated metrics and RQ3 baseline samples updated
   - Status: Fix applied, all downstream metrics and analyses updated

7. **Vulnerability Keyword Parser False Positives (Fixed Feb 22, 2026)**:
   - Issue: SA vuln prediction parser had two bugs: (a) YES patterns checked before NO, causing "no vulnerability detected" to match "vulnerability detected"; (b) broad generic fallback keywords ("buffer overflow", "memory leak", etc.) matched in negative contexts
   - Affected: SA vuln JSONL files (1,021 predictions changed across 37 files, Instruct mode most impacted)
   - Impact on RQ3: All 16 strata in Phase A rater set affected (pool size changes propagated through seeded RNG); 42 of 48 samples replaced
   - Resolution: Fixed parser in 4 source files; re-parsed via `scripts/fix_vuln_keyword_parsing.py`; evaluation, consolidation, and RQ3 baseline re-generated
   - Status: Fix applied, all downstream metrics and analyses updated

---

### **RQ3 Phase A: Baseline Explanation Sampling (Feb–Mar 2026)**

**Purpose**: Stratified sampling of LLM-generated explanations for human rater evaluation of explanation quality (RQ3)

**Directory**: `results/rq3_baseline/`

**Contents**:

| File | Description |
|------|-------------|
| `rq3_baseline_samples.csv` | Combined baseline samples across all 3 tasks |
| `rq3_baseline_samples_vulnerability_detection.csv` | Vuln detection samples (16 strata: 4 models × 2 modes × 2 outcomes) |
| `rq3_baseline_samples_code_generation.csv` | Code generation samples (16 strata) |
| `rq3_baseline_samples_log_analysis.csv` | Log analysis samples (16 strata) |
| `rq3_phase_a_rater_sheet.csv` | Final Phase A rater sheet for human evaluation |
| `rq3_phase_a_rater_sheet_shanev2.xlsx` | Rater sheet with scores (Excel format) |
| `rq3_phase_a_draft_scores.csv` | Draft explanation quality scores |
| `rq3_phase_a_prelim_*.csv/xlsx` | Preliminary versions (pre-keyword-fix) |
| `rq3_sampling_summary.txt` | Summary statistics of the sampling process |
| `rq3_pool_*.png` | Pool analysis visualizations (heatmaps, TP/TN composition, intersections) |

**Methodology**:
- Stratified by model × reasoning mode × correctness outcome (TP/TN for vuln/log, pass/fail for code)
- 3 samples per stratum (seed=42), drawn from Single-Agent zero-shot results
- See `docs/RQ3_Baseline_Sampling.md` for full methodology

---

### **SOTA Comparison: Claude API Vulnerability Detection (Jan 24, 2026)**

**Purpose**: Establish SOTA baseline using commercial frontier models for vulnerability detection comparison

**Hardware**: Anthropic API (cloud)

**Directory**: `results/sota_comparison/`

**Sub-directories**:
```
sota_comparison/
├── SA-zero_Claude-Opus-4.5/    # SA Zero-shot with Claude Opus 4.5
├── SA-few_Claude-Opus-4.5/     # SA Few-shot with Claude Opus 4.5
├── SA-zero_Claude-Sonnet-4.5/  # SA Zero-shot with Claude Sonnet 4.5
└── SA-few_Claude-Sonnet-4.5/   # SA Few-shot with Claude Sonnet 4.5
```

**Experiments**:

| Experiment | Model | Samples | Prompting | Status |
|------------|-------|---------|-----------|--------|
| SA Zero-shot | Claude Opus 4.5 | 386 | Zero-shot | ✅ |
| SA Few-shot | Claude Opus 4.5 | 386 | Few-shot | ✅ |
| SA Zero-shot | Claude Sonnet 4.5 | 386 | Zero-shot | ✅ |
| SA Few-shot | Claude Sonnet 4.5 | 386 | Few-shot | ✅ |

**Notes**:
- Each sub-directory contains `*_detailed_results.jsonl` and `*_summary_metrics.csv`
- These runs serve as frontier SOTA baselines for comparison against local open-source models
- No energy tracking (API-based inference, no local GPU)

---

### **Phase 8 Raw Downloads: Incremental Pod Results (Mar 6-8, 2026)**

**Purpose**: Raw results downloaded from RunPod pods during Phase 8 incremental runs, preserved for provenance

**Directories**: `results/runpod_vuln_incremental_pod1_raw/` through `pod7_raw/`

| Pod | Model | Mode | Configs | Status |
|-----|-------|------|---------|--------|
| Pod 1 | Qwen3-30B-A3B | Instruct + Thinking | 12 (SA/DA/MA × zero/few) | ✅ |
| Pod 2 | Qwen3-4B | Instruct + Thinking | 12 (SA/DA/MA × zero/few) | ✅ |
| Pod 3 | Nemotron-Super-49B | Instruct | 6 (SA/DA/MA × zero/few) | ✅ |
| Pod 4 | Nemotron-Nano-8B | Instruct | 6 (SA/DA/MA × zero/few) | ✅ |
| Pod 5 | Nemotron-Super-49B | Thinking | 5 (SA/DA × zero/few + MA-zero) | ✅ |
| Pod 6 | Nemotron-Nano-8B | Thinking | 6 (SA/DA/MA × zero/few) | ✅ |
| Pod 7 | Nemotron-Super-49B | Thinking | 1 (MA-few) | ✅ |

**Contents per pod**: JSONL result files, CodeCarbon emissions files (SA dirs + main emissions.csv + .bak rotation files), evaluation CSVs and reports.

**Notes**:
- These are raw staging directories preserved for provenance; the working copies were reorganized into `runpod_vuln_incremental/` for merging
- The `.bak` files are CodeCarbon rotation artifacts from schema changes between tracker instances

---

### Phase 8: Incremental Vulnerability Detection Expansion (Mar 2026)

**Purpose**: Expand vulnerability detection dataset from 386 to 486 samples for improved statistical power.

**Hardware**: RunPod (NVIDIA H100 80GB HBM3)

**Directories**:
- `results/runpod_vuln_incremental/` — Raw inference results on 100 incremental samples (50 vuln + 50 safe)
- `results/runpod_vuln_486/` — Merged results (386 + 100 = 486 samples) with re-evaluated metrics

**Dataset**: `vuln_database/VulTrial_100_incremental.jsonl` — 100 new samples drawn from VulTrial-870 pool (stratified random, seed=42)

**Experiments**: All 48 vulnerability detection configurations (4 models × 2 modes × 2 prompting × 3 designs) re-run on the 100 incremental samples.

**Merge Process**:
1. Incremental results produced by standard experiment scripts using `VULN_DATASET` env var override
2. Merged with original 386-sample results via `scripts/merge_vuln_incremental.py`
3. Re-evaluated on combined 486-sample ground truth (`VulTrial_486_samples_balanced.jsonl`)
4. Consolidated via `scripts/consolidate_performance.py` (source type `runpod_vuln_486`, priority 10)

**Notes**:
- The `runpod_vuln_incremental/` directory is excluded from consolidation (partial results)
- Only the merged `runpod_vuln_486/` results are included in final analysis
- Emissions from incremental runs are tracked separately in `runpod_vuln_incremental/`

---

### Phase 9: VulTrial-870 Expansion (Mar 17-21, 2026)

**Purpose**: Expand vulnerability detection from 486 → 870 samples for improved statistical power and generalizability.

**Hardware**: RunPod (up to 8× NVIDIA H100 80GB HBM3 pods in parallel)

**Dataset**: `vuln_database/VulTrial_384_incremental.jsonl` — 384 new samples (192 vuln + 192 safe), set difference of VulTrial-870 minus VulTrial-486.

**Directories**:
- `results/runpod_vuln_384_incremental/` — Staged JSONL files ready for merging (flat, from all batches)
- `results/runpod_vuln_870/` — Merged results (486 + 384 = 870 samples) with re-evaluated metrics
- `results/runpod_870_batch{1-8}_raw/` — Raw pod downloads preserved for provenance

**Raw Download Structure**:
```
runpod_870_batch1_raw/          # Batch 1: SA instruct (8/8 done)
├── pod1_qwen4b/                # Qwen3-4B-Instruct SA zero+few (384 each)
├── pod2_qwen30b/               # Qwen3-30B-Instruct SA zero+few (384 each)
├── pod3_nano8b/                # Nemotron-Nano-8B instruct SA zero+few (384 each)
└── pod4_super49b/              # Nemotron-Super-49B instruct SA zero+few (384 each)

runpod_870_batch2_raw/          # Batch 2: SA thinking (8/8 done)
├── pod1_qwen4b/                # Qwen3-4B-Thinking SA zero (384) + SA few partial (131, looping)
├── pod1_qwen4b_resumed/        # Qwen3-4B-Thinking SA few resumed (384, idx 210271 skipped)
├── pod2_qwen30b/               # Qwen3-30B-Thinking SA zero+few (384 each)
├── pod3_nano8b/                # Nemotron-Nano-8B thinking SA zero+few (384 each)
│   └── _stray_da_from_chain/   # Stray DA files from B2→B3 chain (provenance)
└── pod4_super49b/              # Nemotron-Super-49B thinking SA zero+few (384 each)

runpod_870_batch3_raw/          # Batch 3: DA instruct (8/8 done)
├── pod1_qwen4b/                # Qwen3-4B-Instruct DA zero+few (385 each)
├── pod2_qwen30b/               # Qwen3-30B-Instruct DA zero+few (385 each)
├── pod3_nano8b/                # Nemotron-Nano-8B instruct DA zero+few (385 each)
└── pod4_super49b/              # Nemotron-Super-49B instruct DA zero+few (385 each)

runpod_870_batch4_raw/          # Batch 4: DA thinking (8/8 done)
├── pod1_qwen4b/                # Qwen3-4B-Thinking DA zero+few (385 each)
├── pod2_qwen30b/               # Qwen3-30B-Thinking DA zero (385)
├── pod2_qwen30b_few/           # Qwen3-30B-Thinking DA few (385, separate pod)
├── pod3_nano8b/                # Nemotron-Nano-8B thinking DA zero+few (385 each)
└── pod4_super49b/              # Nemotron-Super-49B thinking DA zero+few (385 each)

runpod_870_batch5_raw/          # Batch 5: MA instruct (8/8 done)
├── pod1_qwen4b/                # Qwen3-4B-Instruct MA zero+few (384 each)
├── pod2_qwen30b/               # Qwen3-30B-Instruct MA zero+few (384 each)
├── pod3_nano8b/                # Nemotron-Nano-8B instruct MA zero+few (383/382)
└── pod4_super49b/              # Nemotron-Super-49B instruct MA zero+few (384 each)

runpod_870_batch6_raw/          # Batch 6: MA thinking (8/8 done)
├── pod1_qwen4b/                # Qwen3-4B-Thinking MA zero+few (384/383)
├── pod2_qwen30b/               # Qwen3-30B-Thinking MA zero (384)
│   └── _stray_ma_few/          # Stray MA-few start (3 lines, provenance)
├── pod2_qwen30b_few/           # Qwen3-30B-Thinking MA few (384, separate pod)
├── pod3_nano8b/                # Nemotron-Nano-8B thinking MA zero+few (384 each, 44+31 sessions)
└── pod4_super49b/              # Nemotron-Super-49B thinking MA zero+few (384 each)

runpod_870_batch7_raw/          # Batch 7: NA instruct on 384 incremental
├── pod1_qwen4b/                # Qwen3-4B-Instruct NA zero+few (384 each)
├── pod3_nano8b/                # Nemotron-Nano-8B instruct NA zero+few (384 each)
└── pod4_super49b/              # Nemotron-Super-49B instruct NA zero+few (384 each)
                                # Qwen3-30B-Instruct: running on pods

runpod_870_batch8_raw/          # Batch 8: NA thinking on 384 incremental
└── pod3_nano8b/                # Nemotron-Nano-8B thinking NA zero+few (384 each)
                                # Others: running on pods

runpod_na486_raw/               # NA on original 486 samples (separate from 384 incremental)
├── nano8b_inst/                # Nemotron-Nano-8B instruct NA zero+few (486 each)
├── nano8b_think/               # Nemotron-Nano-8B thinking NA zero (486) + stray few
├── qwen4b_inst/                # Qwen3-4B-Instruct NA zero+few (486 each)
├── qwen4b_think/               # Qwen3-4B-Thinking NA zero (486) + stray few
├── qwen4b_think_few/           # Qwen3-4B-Thinking NA few (486)
├── qwen30b_inst/               # Qwen3-30B-Instruct NA zero+few (486 each)
├── qwen30b_think_few_split1/   # Qwen3-30B-Thinking NA few split 1/4 (121 samples)
├── qwen30b_think_few_split2/   # Qwen3-30B-Thinking NA few split 2/4 (121 samples)
├── qwen30b_think_few_split3/   # Qwen3-30B-Thinking NA few split 3/4 (121 samples)
├── qwen30b_think_few_split4/   # Qwen3-30B-Thinking NA few split 4/4 (123 samples)
├── super49b_inst/              # Nemotron-Super-49B instruct NA zero+few (486 each)
├── super49b_think_zero/        # Nemotron-Super-49B thinking NA zero (486)
└── super49b_think_few/         # Nemotron-Super-49B thinking NA few (486)
├── qwen30b_think_zero/         # Qwen3-30B-Thinking NA zero (486)
```

**Batch Plan — 384 Incremental** (8 batches: 48 SA/DA/MA + 16 NA = 64 configs):

| Batch | Design × Mode | Configs | Status |
|-------|---------------|---------|--------|
| 1 | SA instruct | 8/8 done | All downloaded |
| 2 | SA thinking | 8/8 done | All downloaded (4B few-shot: 1 sample skipped via resume) |
| 3 | DA instruct | 8/8 done | All downloaded |
| 4 | DA thinking | 8/8 done | All downloaded |
| 5 | MA instruct | 8/8 done | All downloaded |
| 6 | MA thinking | 8/8 done | All downloaded |
| 7 | NA instruct | **8/8 done** | All downloaded |
| 8 | NA thinking | **8/8 done** | All downloaded |

**NA on 486 Original** (16 configs, separate runs):

| | 4B-I | 4B-T | 30B-I | 30B-T | N8B-I | N8B-T | 49B-I | 49B-T |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **zero** | done | done | done | done | done | done | done | done |
| **few** | done | done | done | done* | done | done | done | done |

**Progress Matrix — All Experiments:**

| | 4B-I | 4B-T | 30B-I | 30B-T | N8B-I | N8B-T | 49B-I | 49B-T |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **SA zero (384)** | done | done | done | done | done | done | done | done |
| **SA few (384)** | done | done | done | done | done | done | done | done |
| **DA zero (384)** | done | done | done | done | done | done | done | done |
| **DA few (384)** | done | done | done | done | done | done | done | done |
| **MA zero (384)** | done | done | done | done | done | done | done | done |
| **MA few (384)** | done | done | done | done | done | done | done | done |
| **NA zero (384)** | done | done | done | done | done | done | done | done |
| **NA few (384)** | done | done | done | done | done | done | done | done |
| **NA zero (486)** | done | done | done | done | done | done | done | done |
| **NA few (486)** | done | done | done | done* | done | done | done | done |

*30B-Think NA few 486 completed via 4-way dataset split across 4 pods (121+121+121+123=486). 30B-Think NA zero 486 completed on single pod.

**Merge Process**:
1. SA/DA/MA incremental 384-sample results staged in `runpod_vuln_384_incremental/` (48/48 complete)
2. NA 384 incremental results in `runpod_870_batch7_raw/` and `runpod_870_batch8_raw/`
3. NA 486 original results in `runpod_na486_raw/`
4. Nemotron thinking files tagged with `_thinking` suffix (since same model name for both modes)
5. Merged with existing 486-sample results via `scripts/merge_vuln_870.py`
6. Re-evaluated on combined 870-sample ground truth (`VulTrial_870_samples_balanced.jsonl`)
7. NA results: 384 incremental + 486 original concatenated for full 870 coverage
8. 30B-Think NA few 486: 4 split JONLs concatenated, emissions summed from 4 pods

**Key Notes**:
- DA results have 385 lines (384 samples + 1 skipped/failed sample from resume logic)
- Nemotron uses same model file for instruct and thinking; mode toggled via system prompt
- Batch scripts include auto-resume with skip-on-failure (`echo "2"` piped for DA/MA)
- B3→B4 chaining requires manual download + cleanup between batches (completion check can't distinguish instruct vs thinking DA filenames)
- RQ3 human-rated entries (15 entry_ids) locked as forced includes in `rq3_generate_human_rating_set.py`
- Qwen3-30B-A3B-Thinking vLLM loading fails on fresh pods with 50GB container disk (model ~60GB); requires shared /workspace storage (280TB+)
- Nemotron-Super-49B also fails on 150GB local disk pods; requires shared /workspace storage
- Nano-8B MA thinking had frequent context overflow crashes (44 sessions for MA-zero, 31 for MA-few)
- NA thinking generates very long responses (~23K chars avg, up to 51K) without max_tokens limit — same as SA thinking (~21K avg)
- CodeCarbon emissions.csv only written on tracker.stop() or flush() — not during periodic measurements. Process kills lose emissions data.
- CodeCarbon emissions.csv rotation creates numbered .bak files during multi-session runs; all merged into main emissions.csv per folder
- 30B-Think NA few 486 was split across 4 pods (121+121+121+123 samples each) to parallelize the slowest experiment

---

**Last Updated**: 2026-03-22
**Total Experiments**: 120 consolidated on 486 samples + 80 on 870 expansion (all complete)
  - **Vulnerability Detection — 486 samples** (48 SA/DA/MA configs): 4 models × 2 modes × 2 prompting × 3 designs
  - **Vulnerability Detection — 870 expansion** (80 configs, all complete): 48 SA/DA/MA on 384 incr + 16 NA on 384 incr + 16 NA on 486 orig
  - **Code Generation** (48 configs on 164 problems): 4 models × 2 modes × 2 prompting × 3 designs (SA/DA/MA)
  - **Log Analysis** (24 configs on 385 sessions): 2 models × 2 modes × 2 prompting × 3 designs (SA/DA/MA)
**Total Samples Processed**: ~105,000+ (48 vuln × ~486 + 48 vuln × 384 + 32 NA vuln × ~870 + 48 code × 164 + 24 log × 385)
**Hardware Used**: Mars RTX A5000 + RunPod H100 (up to 14 pods in parallel)
**Models Evaluated**: 4 (Qwen3 4B/30B + Nemotron-Nano-8B + Nemotron-Super-49B) × 2 modes (Instruct/Thinking)
**Agent Architectures**: 4 (No-Agent, Single-Agent, Dual-Agent, Multi-Agent)
**Tasks**: 3 (Vulnerability Detection, Code Generation, Log Analysis)
