# Cross-Architecture Model Selection Analysis

**Date**: November 27, 2025 (Updated: December 2025)
**Related Document**: [Cross_Architecture_Validation_Plan.md](./Cross_Architecture_Validation_Plan.md)
**Context**: Selecting the optimal model family to replicate Agent Green experiments (RQ1/RQ2) and validate findings across architectures.

---

## ⚠️ Status Update (December 2025)

**Original Recommendation**: DeepSeek-R1-Distill-Llama was selected as the top candidate.

**Outcome**: DeepSeek-R1-Distill-Llama **failed validation testing** due to a critical technical issue:
- The thinking/non-thinking toggle did not work as expected
- Model produced identical outputs regardless of thinking mode configuration
- Detailed analysis in Section 7 below

**Pivot**: **Nvidia Llama-3.1-Nemotron-Nano-8B-v1** was selected as the replacement:
- Supports thinking toggle via system prompt ("detailed thinking on" / "detailed thinking off")
- Successfully validated with distinct thinking vs non-thinking behavior
- All 8 SA experiments completed successfully on H100 hardware

---

## 1. Executive Summary of Top 3 Options (Original Analysis)

We evaluated three primary candidates to serve as the "Cross-Architecture" validation set against the Qwen3 baseline.

| Rank | Model Candidate | Primary Strength | Critical Trade-off | Verdict |
|------|-----------------|------------------|--------------------|---------|
| ~~**1**~~ | ~~**DeepSeek-R1-Distill-Llama**~~ | ~~**Strict Replication**~~ | ~~Requires Quantization (70B)~~ | ❌ **FAILED** - Thinking toggle non-functional |
| **2** | **GPT-OSS-120B** | **Novelty (Spectrum)** | Changes Experiment Design | **Strong Alternative** for new insights |
| **3** | **OLMo 3** | **Openness** | **Missing 32B Instruct** | **Not Viable** for full replication |
| **NEW** | **Nvidia Nemotron-Nano-8B** | **Working Thinking Toggle** | 8B only (no larger variant) | ✅ **USED** for cross-architecture validation |
| **NEW** | **Nvidia Nemotron-Super-49B** | **Large Model Validation** | Requires 2× H100 | ✅ **IN PROGRESS** for RQ1 49B experiments |
| **NEW** | **GLM-4.6** | **Different Architecture (GLM)** | MoE, 200K context | 🔍 **VIABLE** - `enable_thinking` toggle confirmed |

---

## 2. Detailed Option Analysis

### Option 1: DeepSeek-R1-Distill-Llama (The "Safe Bet")
*Models: 8B & 70B (Llama-3.1/3.3 base) — Both are **Dense** architecture (all parameters active)*

This option provides the cleanest "apples-to-apples" comparison for your existing Qwen3 experiments.

*   **Pros**:
    *   **Perfect Experimental Match**: Replicates the binary "Thinking On/Off" variable exactly as used in Qwen3.
    *   **Architectural Diversity**: Uses Llama architecture (vs Qwen), satisfying the core requirement for cross-family validation.
    *   **Native Support**: `<think>` tags are native and work identically to Qwen.
*   **Cons**:
    *   **Size Mismatch**: Compares Qwen3-4B (4B) vs DS-8B (8B), and Qwen3-30B (30B) vs DS-70B (70B).
    *   **Architecture Type Mismatch (70B)**: Qwen3-30B-A3B is **MoE** (3B active per token), while DS-70B is **Dense** (70B active) — **23× more active parameters**.
    *   **Quantization Required**: The 70B model requires INT8 quantization to fit on your H100.
*   **Scientific Implication**: High internal validity for 8B comparison (both dense, similar precision). The 70B comparison has multiple confounds (MoE vs Dense, size, precision) that must be acknowledged. **8B provides cleaner validation signal.**

### Option 2: GPT-OSS-120B (The "Novelty Bet")
*Models: 20B & 120B (MoE)*

This option changes the nature of the study from "Binary Thinking" to "Variable Reasoning Effort."

*   **Pros**:
    *   **Reasoning Spectrum**: Allows testing `Low`, `Medium`, and `High` reasoning effort. This enables plotting an **Energy vs. Reasoning Depth curve**.
    *   **Efficiency**: MoE architecture (5B active params) is highly efficient.
    *   **True Openness**: Apache 2.0 license.
*   **Cons**:
    *   **Experimental Drift**: It does not strictly "replicate" the Qwen binary condition. It expands it.
    *   **Complexity**: Requires handling 3 states instead of 2.
*   **Scientific Implication**: Higher novelty. Could lead to a more nuanced publication ("The Cost of Deep Thinking"), but risks drifting from the original replication goal.

### Option 3: OLMo 3 (The "Openness Bet")
*Models: 7B & 32B*

The most transparent model, but fatally flawed for this specific 32B replication.

*   **Pros**:
    *   **Gold Standard Openness**: Weights, data, and code are all open.
    *   **Perfect Size Match**: 7B and 32B sizes match Qwen exactly.
*   **Cons**:
    *   **FATAL FLAW**: **No 32B Instruct Model**. AI2 only released `OLMo-3-32B-Think` and `OLMo-3-32B-Base`. There is no "Non-Thinking" instruct equivalent at 32B.
*   **Scientific Implication**: You cannot perform the "Think vs No-Think" comparison at the 32B scale. This makes it unsuitable for the full replication study.

---

## 3. Unsloth Suitability & Implications

**Unsloth** is an optimization library that accelerates training and inference. It is **compatible with all three options** (Llama, GPT-OSS, OLMo 3).

### 3.1 Can we use Unsloth?
**YES.** Unsloth supports:
*   **Llama**: Full support (DeepSeek-Distill-Llama).
*   **GPT-OSS**: Full support (including MoE optimizations).
*   **OLMo 3**: Full support (recently added).

### 3.2 Should we use Unsloth? (Scientific Implications)

Using Unsloth introduces specific considerations for research validity:

#### Scenario A: Inference Only (Your Use Case)
If you use Unsloth solely to **load and run** the models (e.g., for faster inference or 4-bit loading):
*   **Validity Threat**: **Low**.
*   **Reasoning**: Unsloth's inference optimizations (kernel fusion) are mathematically precise or within negligible floating-point error.
*   **Quantization Note**: If you use Unsloth to load models in 4-bit (GGUF/bnb), you **MUST** report this. 4-bit quantization can degrade reasoning performance more than 8-bit.
    *   *Recommendation*: Use **8-bit (INT8)** or **FP16** if possible. Avoid 4-bit for "Thinking" models unless necessary.

#### Scenario B: Fine-Tuning (LoRA/QLoRA)
If you use Unsloth to **fine-tune** models:
*   **Validity Threat**: **High**.
*   **Reasoning**: This modifies the model weights. You are no longer testing the "DeepSeek" model; you are testing "DeepSeek + Your Fine-Tune."
*   **Recommendation**: **DO NOT fine-tune** for this replication study. Use the base/instruct weights as-is.

### 3.3 Final Recommendation on Unsloth

*   **Use Unsloth?**: **Yes**, it is a great tool for efficient loading.
*   **Configuration**:
    *   Load **DeepSeek-R1-Distill-Llama-70B** in **8-bit** (via Unsloth or vLLM).
    *   **Do not use 4-bit** unless hardware strictly demands it (it hurts reasoning).
    *   **Do not fine-tune**.

---

## 4. Final Decision Matrix

| Feature | DeepSeek-Llama | GPT-OSS | OLMo 3 |
| :--- | :--- | :--- | :--- |
| **Replication Fit** | ⭐⭐⭐⭐⭐ (Exact) | ⭐⭐⭐ (Expanded) | ⭐ (Incomplete) |
| **Scientific Interest** | ⭐⭐⭐⭐ (High) | ⭐⭐⭐⭐⭐ (Very High) | ⭐⭐⭐ (Moderate) |
| **Feasibility (H100)** | ⭐⭐⭐ (Needs Quant) | ⭐⭐⭐⭐⭐ (Native MoE) | ⭐⭐⭐⭐⭐ (Native) |
| **Unsloth Support** | ✅ Yes | ✅ Yes | ✅ Yes |

**Original Recommendation**: ~~Proceed with **DeepSeek-R1-Distill-Llama** (Option 1).~~

**Updated Recommendation (Dec 2025)**: DeepSeek failed validation. Proceeded with **Nvidia Nemotron-Nano-8B** instead. See Section 7 for details.

---

## 5. Future Work / Alternative Studies

While DeepSeek-R1-Distill-Llama is recommended for the current replication study, the model evaluation surfaced opportunities for follow-up research:

### 5.1 GPT-OSS Reasoning Spectrum Study

GPT-OSS's reasoning effort parameter (`Low`/`Medium`/`High`) presents a unique opportunity to explore **energy-performance tradeoffs across a reasoning spectrum**, rather than binary thinking modes.

**Potential Research Questions:**
- Does reasoning effort scale linearly with energy consumption?
- Is there a "sweet spot" where moderate reasoning provides optimal performance-per-watt?
- How does the energy curve differ between code generation and vulnerability detection tasks?

**Study Design Sketch:**
| Condition | Reasoning Effort | Expected Energy | Expected Performance |
|-----------|------------------|-----------------|---------------------|
| GPT-OSS-Low | Low | Baseline | Lower |
| GPT-OSS-Med | Medium | ~1.5-2x | Moderate |
| GPT-OSS-High | High | ~2-3x | Highest |

This would enable plotting an **Energy vs. Reasoning Depth curve** - a novel contribution beyond binary comparisons.

### 5.2 OLMo 3 Transparency Study

OLMo 3's **OLMoTrace** capability (tracing outputs to training data) could enable a unique study on:
- Attributing reasoning patterns to specific training examples
- Understanding *why* thinking models produce certain explanations
- Validating explanation faithfulness against training data provenance

**Limitation**: Requires waiting for AI2 to release `OLMo-3-32B-Instruct`, or conducting at 7B scale only.

### 5.3 Size-Controlled Replication

A future study could address the size confound (Qwen3-30B vs DeepSeek-70B) by:
- Using DeepSeek-R1-Distill-Qwen-32B (same size, but same Qwen architecture)
- Comparing both Llama-70B and Qwen-32B distilled variants against Qwen3-30B
- Isolating architecture effects from size effects

### 5.4 DeepSeek-V3.1-Terminus (Best Research Validity)

**DeepSeek-V3.1-Terminus** (671B total, 37B active MoE) offers the **highest research validity** for cross-architecture validation because:

1. **Native hybrid thinking**: Same model supports both thinking and non-thinking modes via chat template change
2. **No distillation confound**: Eliminates "cargo cult reasoning" and "faithfulness confound" validity threats
3. **MoE architecture**: 37B active params - closer to Qwen3-30B-A3B (3B active) than dense 70B

**Current Limitation**: Requires multi-GPU setup (minimum 2× H100 for 160GB VRAM).

**Unsloth Mitigation**: With MoE CPU offloading + dynamic 2-bit quantization:
- **1× H100 80GB + 150GB RAM**: ~5 tok/s (slow but possible)
- **2× H100 160GB**: ~140 tok/s (viable)

```bash
# MoE CPU offloading command
-ot ".ffn_.*_exps.=CPU"
```

**Trade-off**: Aggressive quantization (1-2 bit) may impact reasoning quality.

**Recommendation**: Consider for future work when:
- Multi-GPU infrastructure becomes available, OR
- A pilot study validates that 2-bit quantization doesn't degrade thinking mode performance

---

## 7. DeepSeek Failure Analysis & Nemotron Pivot (December 2025)

### 7.1 DeepSeek-R1-Distill-Llama Testing Results

**Test Date**: December 5-6, 2025

**Issue Discovered**: The thinking/non-thinking toggle did not produce differentiated outputs.

**Validation Attempts**:
1. Tested `enable_thinking` API parameter - no effect
2. Tested `<think>` tag injection in prompts - no effect
3. Tested system prompt variations - no effect
4. Both 8B and 70B variants exhibited the same behavior

**Root Cause Hypothesis**:
- DeepSeek R1 Distill models are **distilled from** the thinking model, meaning the "thinking behavior" is baked into the weights
- Unlike Qwen3 (which has separate Instruct and Think model variants), DeepSeek Distill cannot disable thinking at inference time
- The model always produces reasoning traces regardless of configuration

**Conclusion**: DeepSeek-R1-Distill-Llama is **unsuitable** for binary thinking/non-thinking experiments.

### 7.2 Nemotron Selection Rationale

**Model**: `nvidia/Llama-3.1-Nemotron-Nano-8B-v1`

**Why Nemotron**:
1. **Working Thinking Toggle**: Uses system prompt prefix to control thinking mode
   - Thinking ON: `"detailed thinking on"`
   - Thinking OFF: `"detailed thinking off"`
2. **Validated Behavior**: Produces distinctly different outputs between modes
3. **Llama Architecture**: Provides cross-architecture validation (Llama vs Qwen)
4. **Single Model**: One model supports both modes (no need for separate checkpoints)

**Limitation**: Only 8B variant available (no 49B/70B equivalent for larger-scale validation)

### 7.3 Validation Results Summary

| Experiment | Task | Mode | Prompting | F1/Pass@1 | Energy (kg CO2) |
|------------|------|------|-----------|-----------|-----------------|
| NM-5 | Vuln | Instruct | Zero-shot | 0.25 | 0.133 |
| NM-6 | Vuln | Instruct | Few-shot | 0.49 | 0.062 |
| NM-7 | Vuln | Thinking | Zero-shot | 0.18 | 0.162 |
| NM-8 | Vuln | Thinking | Few-shot | 0.46 | 0.236 |
| NM-13 | Code | Instruct | Zero-shot | 98.17% | 0.316 |
| NM-14 | Code | Instruct | Few-shot | 93.29% | 0.408 |
| NM-15 | Code | Thinking | Zero-shot | 92.07% | 0.530 |
| NM-16 | Code | Thinking | Few-shot | 92.68% | 0.527 |

**Key Finding**: Patterns from Qwen3 experiments validated on Nemotron architecture:
- Few-shot improves vulnerability detection F1
- Instruct mode optimal for code generation
- Thinking mode increases energy consumption

---

## 8. Document References

- **Validation Plan**: [Cross_Architecture_Validation_Plan.md](./Cross_Architecture_Validation_Plan.md)
- **Distillation Threats**: See Section 2.6 of Validation Plan
- **AI Chat Discussions**:
  - [Anthropic - Expand Models Under Tests.md](./Anthropic%20-%20Expand%20Models%20Under%20Tests.md)
  - [Google - Expand Models Under Tests.md](./Google%20-%20Expand%20Models%20Under%20Tests.md)
