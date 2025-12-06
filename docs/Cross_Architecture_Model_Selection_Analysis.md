# Cross-Architecture Model Selection Analysis

**Date**: November 27, 2025
**Related Document**: [Cross_Architecture_Validation_Plan.md](./Cross_Architecture_Validation_Plan.md)
**Context**: Selecting the optimal model family to replicate Agent Green experiments (RQ1/RQ2) and validate findings across architectures.

---

## 1. Executive Summary of Top 3 Options

We evaluated three primary candidates to serve as the "Cross-Architecture" validation set against the Qwen3 baseline.

| Rank | Model Candidate | Primary Strength | Critical Trade-off | Verdict |
|------|-----------------|------------------|--------------------|---------|
| **1** | **DeepSeek-R1-Distill-Llama** | **Strict Replication** | Requires Quantization (70B) | **RECOMMENDED** for RQ1/RQ2 |
| **2** | **GPT-OSS-120B** | **Novelty (Spectrum)** | Changes Experiment Design | **Strong Alternative** for new insights |
| **3** | **OLMo 3** | **Openness** | **Missing 32B Instruct** | **Not Viable** for full replication |

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

**Primary Recommendation**: Proceed with **DeepSeek-R1-Distill-Llama** (Option 1).

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

## 6. Document References

- **Validation Plan**: [Cross_Architecture_Validation_Plan.md](./Cross_Architecture_Validation_Plan.md)
- **Distillation Threats**: See Section 2.6 of Validation Plan
- **AI Chat Discussions**:
  - [Anthropic - Expand Models Under Tests.md](./Anthropic%20-%20Expand%20Models%20Under%20Tests.md)
  - [Google - Expand Models Under Tests.md](./Google%20-%20Expand%20Models%20Under%20Tests.md)
