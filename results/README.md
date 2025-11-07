# Results Directory

## Folder Structure

### Vulnerability Detection Experiments (RQ1)

- **`mars/`** - Phase 1: 4B models with old LLM-generated prompts (October 2025)
- **`mars_rerun/`** - Phase 1 rerun: 4B models with new CWE-based prompts (November 2025)
- **`runpod/`** - Phase 2a: 30B MoE models on RunPod H100 GPUs (October 2025)

### Code Generation Experiments (RQ3)

- **`mars_codegen/`** - Phase 3a: 4B models, HumanEval benchmark (November 2025)
- **`runpod_codegen/`** - Phase 3b: 30B models, HumanEval benchmark (Planned)

### Analysis Outputs

- **`analysis_phase2a/`** - Phase 2a classification reports and visualizations
- **`analysis_prompt_comparison/`** - Old vs new prompt comparison analysis

---

**Infrastructure:**
- Mars: SMU server with RTX A5000 GPUs (free, local)
- RunPod: Cloud H100 80GB GPUs (paid, faster)

**Datasets:**
- VulTrial: 386 vulnerable/non-vulnerable code samples (RQ1)
- HumanEval: 164 Python programming problems (RQ3)
