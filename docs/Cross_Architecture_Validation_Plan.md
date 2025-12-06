# Cross-Architecture Validation Plan

**Purpose**: Replicate RQ1 and RQ2 experiments using alternative model architectures to validate generalizability of findings beyond Qwen3
**Date**: November 26, 2025
**Last Updated**: December 6, 2025
**Status**: Phase 1 - Code Preparation

---

## Progress Tracker

### Overall Status

| Phase | Description | Status | Progress |
|-------|-------------|--------|----------|
| Phase 0 | Planning & Approval | ✅ Complete | 100% |
| Phase 1 | Code Preparation | ✅ Complete | 100% |
| Phase 2 | vLLM Deployment & Validation | ⏳ Pending | 0% |
| Phase 3 | RQ1 Experiments (16 SA) | ⏳ Pending | 0% |
| Phase 4 | RQ2 Experiments (32 DA/MA) | ⏳ Pending | 0% |
| Phase 5 | Analysis & Comparison | ⏳ Pending | 0% |

### Phase 1: Code Preparation Checklist

| Task | File/Script | Status |
|------|-------------|--------|
| Create DeepSeek env config (8B) | `.env.deepseek` | ✅ Done |
| Create DeepSeek env config (70B) | `.env.deepseek.70b` | ✅ Done |
| Create DeepSeek config module | `src/config_deepseek.py` | ✅ Done |
| Create vLLM deployment script | `scripts/deploy_deepseek_vllm.sh` | ✅ Done |
| Create validation script | `scripts/validate_deepseek_modes.py` | ✅ Done |
| Standardize context length (64K) | All configs | ✅ Done |
| Create config selector module | `src/config_selector.py` | ✅ Done |
| Update experiment scripts for DeepSeek | 12 scripts updated | ✅ Done |

### Phase 2: Deployment & Validation Checklist

| Test | Model | Mode | Status |
|------|-------|------|--------|
| TC-1 (Math) | 8B | Thinking | ⏳ |
| TC-1 (Math) | 8B | Non-Thinking | ⏳ |
| TC-1 (Math) | 70B | Thinking | ⏳ |
| TC-1 (Math) | 70B | Non-Thinking | ⏳ |
| TC-2 (Vuln) | 8B | Thinking | ⏳ |
| TC-2 (Vuln) | 8B | Non-Thinking | ⏳ |
| TC-2 (Vuln) | 70B | Thinking | ⏳ |
| TC-2 (Vuln) | 70B | Non-Thinking | ⏳ |
| TC-3 (Code) | 8B | Thinking | ⏳ |
| TC-3 (Code) | 8B | Non-Thinking | ⏳ |
| TC-3 (Code) | 70B | Thinking | ⏳ |
| TC-3 (Code) | 70B | Non-Thinking | ⏳ |

### Experiment Progress (48 Total)

#### RQ1 Single-Agent (16 experiments)

| ID | Task | Model | Mode | Prompting | Status |
|----|------|-------|------|-----------|--------|
| DS-1 | Vuln | 70B | Instruct | Few-shot | ⏳ |
| DS-2 | Vuln | 70B | Instruct | Zero-shot | ⏳ |
| DS-3 | Vuln | 70B | Thinking | Few-shot | ⏳ |
| DS-4 | Vuln | 70B | Thinking | Zero-shot | ⏳ |
| DS-5 | Vuln | 8B | Instruct | Few-shot | ⏳ |
| DS-6 | Vuln | 8B | Instruct | Zero-shot | ⏳ |
| DS-7 | Vuln | 8B | Thinking | Few-shot | ⏳ |
| DS-8 | Vuln | 8B | Thinking | Zero-shot | ⏳ |
| DS-9 | Code | 70B | Instruct | Few-shot | ⏳ |
| DS-10 | Code | 70B | Instruct | Zero-shot | ⏳ |
| DS-11 | Code | 70B | Thinking | Few-shot | ⏳ |
| DS-12 | Code | 70B | Thinking | Zero-shot | ⏳ |
| DS-13 | Code | 8B | Instruct | Few-shot | ⏳ |
| DS-14 | Code | 8B | Instruct | Zero-shot | ⏳ |
| DS-15 | Code | 8B | Thinking | Few-shot | ⏳ |
| DS-16 | Code | 8B | Thinking | Zero-shot | ⏳ |

#### RQ2 Dual-Agent (16 experiments)

| ID | Task | Model | Mode | Prompting | Status |
|----|------|-------|------|-----------|--------|
| DS-17 | Vuln | 70B | Instruct | Few-shot | ⏳ |
| DS-18 | Vuln | 70B | Instruct | Zero-shot | ⏳ |
| DS-19 | Vuln | 70B | Thinking | Few-shot | ⏳ |
| DS-20 | Vuln | 70B | Thinking | Zero-shot | ⏳ |
| DS-21 | Vuln | 8B | Instruct | Few-shot | ⏳ |
| DS-22 | Vuln | 8B | Instruct | Zero-shot | ⏳ |
| DS-23 | Vuln | 8B | Thinking | Few-shot | ⏳ |
| DS-24 | Vuln | 8B | Thinking | Zero-shot | ⏳ |
| DS-33 | Code | 70B | Instruct | Few-shot | ⏳ |
| DS-34 | Code | 70B | Instruct | Zero-shot | ⏳ |
| DS-35 | Code | 70B | Thinking | Few-shot | ⏳ |
| DS-36 | Code | 70B | Thinking | Zero-shot | ⏳ |
| DS-37 | Code | 8B | Instruct | Few-shot | ⏳ |
| DS-38 | Code | 8B | Instruct | Zero-shot | ⏳ |
| DS-39 | Code | 8B | Thinking | Few-shot | ⏳ |
| DS-40 | Code | 8B | Thinking | Zero-shot | ⏳ |

#### RQ2 Multi-Agent (16 experiments)

| ID | Task | Model | Mode | Prompting | Status |
|----|------|-------|------|-----------|--------|
| DS-25 | Vuln | 70B | Instruct | Few-shot | ⏳ |
| DS-26 | Vuln | 70B | Instruct | Zero-shot | ⏳ |
| DS-27 | Vuln | 70B | Thinking | Few-shot | ⏳ |
| DS-28 | Vuln | 70B | Thinking | Zero-shot | ⏳ |
| DS-29 | Vuln | 8B | Instruct | Few-shot | ⏳ |
| DS-30 | Vuln | 8B | Instruct | Zero-shot | ⏳ |
| DS-31 | Vuln | 8B | Thinking | Few-shot | ⏳ |
| DS-32 | Vuln | 8B | Thinking | Zero-shot | ⏳ |
| DS-41 | Code | 70B | Instruct | Few-shot | ⏳ |
| DS-42 | Code | 70B | Instruct | Zero-shot | ⏳ |
| DS-43 | Code | 70B | Thinking | Few-shot | ⏳ |
| DS-44 | Code | 70B | Thinking | Zero-shot | ⏳ |
| DS-45 | Code | 8B | Instruct | Few-shot | ⏳ |
| DS-46 | Code | 8B | Instruct | Zero-shot | ⏳ |
| DS-47 | Code | 8B | Thinking | Few-shot | ⏳ |
| DS-48 | Code | 8B | Thinking | Zero-shot | ⏳ |

### Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Completed |
| 🟡 | In Progress |
| ⏳ | Pending |
| ❌ | Failed/Blocked |
| 🔄 | Needs Retry |

---

## 1. Objective

Strengthen the generalizability of research findings by running the same experimental configurations with alternative model architectures that offer comparable thinking/instruct variants to Qwen3. This validates whether observed patterns (single-agent performance, multi-agent coordination overhead, thinking mode effects) are model-agnostic or Qwen-specific.

### Research Questions Addressed
- **RQ1**: Do single-agent performance patterns hold across model families?
- **RQ2**: Is multi-agent coordination overhead consistent across different base models?

---

## 2. Model Selection

### 2.0 Models Considered for Cross-Architecture Validation

To validate findings beyond Qwen3, we evaluated multiple open-source model families with thinking/non-thinking capabilities. Below is a comprehensive comparison.

#### Selection Criteria
1. **Thinking Mode Support**: Must have explicit reasoning/chain-of-thought capability
2. **Non-Thinking Mode**: Must also support direct instruction-following
3. **Open Weights**: Must be available for local deployment
4. **Size Variants**: Prefer models with multiple sizes for comparison
5. **Practical Deployment**: Must be feasible on available hardware (H100 80GB)

#### Models Evaluated

| Model Family | Developer | Sizes Available | Thinking Mode | Architecture | Status |
|--------------|-----------|-----------------|---------------|--------------|--------|
| **Qwen3** | Alibaba | 0.6B, 4B, 8B, 14B, 32B, 30B-A3B, 235B | ✅ Hybrid toggle | Dense / MoE | ✅ Current baseline |
| **DeepSeek-R1** | DeepSeek | 671B (37B active) | ✅ Native `<think>` | MoE (256 experts) | 🔍 Under consideration |
| **DeepSeek-R1-Distill** | DeepSeek | 1.5B, 7B, 8B, 14B, 32B, 70B | ✅ Native `<think>` | Dense (Qwen/Llama base) | ✅ **Recommended** |
| **OLMo 3** | AI2 | 7B, 32B | ⚠️ 7B: Think+Instruct; 32B: Think only | Dense (fully open) | ⚠️ 32B lacks Instruct |
| **GLM-4** | Zhipu AI | 9B, 26B (GLM-4-Plus) | ✅ Thinking mode | GLM (bidirectional) | 🔍 Under consideration |
| **Kimi K2** | Moonshot AI | 1T (32B active) | ✅ Instruct/Thinking variants | MoE (256K ctx) | ⚠️ Large but viable |
| **Llama-Nemotron** | NVIDIA/Meta | 8B, 49B, 253B | ✅ System prompt toggle | Llama-based | 🔍 Under consideration |
| **GPT-OSS** | OpenAI | 21B, 117B (MoE) | ✅ Reasoning effort (Low/Med/High) | MoE (MXFP4) | ✅ **Strong alternative** |
| **MiniMax-M1** | MiniMax | Various | ✅ Thinking budget control | Dense | 🔍 Under consideration |

#### Detailed Model Profiles

##### 1. Qwen3 (Current Baseline)
- **Developer**: Alibaba Cloud
- **Sizes**: 0.6B, 4B, 8B, 14B, 32B, 30B-A3B (MoE), 235B (MoE)
- **Thinking Mode**: Hybrid toggle via `enable_thinking=True/False`
- **Context**: 128K tokens
- **Languages**: 119 languages supported
- **Status**: ✅ Already tested in RQ1/RQ2

##### 2. DeepSeek-R1 / V3 (Original)
- **Developer**: DeepSeek AI
- **Sizes**: 671B total (37B active per token)
- **Architecture**: MoE with 256 experts
- **Thinking Mode**: Native `<think>...</think>` tags (R1), standard instruct (V3)
- **Context**: 128K tokens
- **Performance**: Competitive with GPT-4 and OpenAI o1
- **Deployment**: Requires 8+ H100 GPUs or CPU offloading
- **Status**: ⚠️ High cost, but strongest validation

##### 3. DeepSeek-R1-Distill (Qwen/Llama)
- **Developer**: DeepSeek AI
- **Release**: January 2025 (v0528 update May 2025)
- **Distillation Source**: DeepSeek-R1 (671B, 37B active) via 800k reasoning samples
- **Variants**:
  - **Qwen-based**: 1.5B, 7B, 14B, 32B (distilled to Qwen2.5 architecture)
  - **Llama-based**: 8B (Llama-3.1-8B-Base), 70B (Llama-3.3-70B-Instruct)
- **Thinking Mode**: Native `<think>...</think>` tags inherited from R1 training
- **Context**: 128K tokens
- **Tensor Format**: BF16
- **License**: MIT (respecting base model licenses: Llama 3.1/3.3)

**Benchmark Performance (Llama variants)**:

| Benchmark | 8B | 70B | Notes |
|-----------|-----|-----|-------|
| MATH-500 (Pass@1) | 89.1% | 94.5% | Competitive with o1-mini |
| AIME 2024 (Pass@1) | 50.4% | 70.0% | Math olympiad |
| AIME 2024 (Cons@64) | 80.0% | 86.7% | Consensus voting |
| GPQA Diamond | 49.0% | 65.2% | Graduate-level QA |
| LiveCodeBench | 39.6% | 57.5% | Code generation |
| Codeforces Rating | 1205 | 1633 | Competitive programming |

**Usage Recommendations**:
- Temperature: 0.5-0.7 recommended
- Avoid system prompts; embed all instructions in user prompt
- Enforce thinking by starting assistant response with `<think>\n`
- For math: Request step-by-step reasoning with boxed final answers

**HuggingFace**:
- `deepseek-ai/DeepSeek-R1-Distill-Llama-8B`
- `deepseek-ai/DeepSeek-R1-Distill-Llama-70B`

- **Status**: ✅ **Recommended** (Llama variants for architecture diversity)

##### 4. GLM-4 (ChatGLM)
- **Developer**: Zhipu AI (China)
- **Sizes**: GLM-4-9B, GLM-4-Plus (26B)
- **Thinking Mode**: Supports reasoning mode
- **Architecture**: GLM (General Language Model) - bidirectional attention
- **Context**: 128K tokens
- **Languages**: Strong Chinese + English
- **Unique**: Different architecture from decoder-only Qwen/Llama
- **Status**: 🔍 Worth considering for architectural diversity

##### 5. GPT-OSS (OpenAI Open Reasoning)
- **Developer**: OpenAI
- **Release**: August 5, 2025 (first open-weight release since GPT-2 in 2019)
- **Sizes**:
  - **gpt-oss-20b**: 21B total params (3.6B active per token)
  - **gpt-oss-120b**: 117B total params (5.1B active per token)
- **Architecture**: Mixture of Experts (MoE) with native MXFP4 quantization
- **Thinking Mode**: Three reasoning effort levels (Low/Medium/High) - trades latency vs. performance
- **Context**: Standard transformer context
- **License**: Apache 2.0 (fully open for commercial use and fine-tuning)

**Key Features**:
- **Full Chain-of-Thought**: Complete access to model's reasoning process
- **Native Quantization**: MXFP4 post-trained (120B runs on single H100 80GB, 20B fits in 16GB)
- **Fine-tunable**: Full parameter fine-tuning supported
- **Agentic**: Native function calling, web browsing, Python execution, Structured Outputs

**Performance**:
| Model | Performance Level | Hardware Requirement |
|-------|-------------------|---------------------|
| gpt-oss-120b | Near OpenAI o4-mini | 1x H100 80GB |
| gpt-oss-20b | Near OpenAI o3-mini | 16GB VRAM (edge-friendly) |

**Training**:
- 2.1M H100-hours (120B) / ~210k H100-hours (20B)
- RL techniques from o3 and frontier systems

**Inference Support**: transformers, vLLM, llama.cpp, Ollama

**HuggingFace**: `openai/gpt-oss-20b`, `openai/gpt-oss-120b`

- **Status**: ✅ **Strong alternative** - Apache 2.0, efficient MoE, reasoning effort control

##### 6. Kimi K2
- **Developer**: Moonshot AI
- **Size**: 1 Trillion total parameters (32B active) - MoE architecture
- **Context**: 256K tokens
- **Variants**:
  - **Kimi-K2-Instruct**: General-purpose, speed-focused, no long thinking (temp=0.6 recommended)
  - **Kimi-K2-Thinking**: Complex reasoning with transparent step-by-step logic (temp=1.0 recommended)
- **Thinking Mode**: ✅ Native thinking with interleaved reasoning in agentic tool-use
- **Unique Features**:
  - Strong tool-calling capabilities (200-300 sequential calls)
  - Native INT4 quantization for K2-Thinking
  - State-of-the-art on Humanity's Last Exam (HLE) and BrowseComp benchmarks
  - Training cost: ~$4.6 million
- **HuggingFace**: `moonshotai/Kimi-K2-Instruct`, `moonshotai/Kimi-K2-Thinking`
- **Status**: ⚠️ Very large (1T params), but has clear Instruct/Thinking variants

##### 7. OLMo 3
- **Developer**: AI2 (Allen Institute for AI)
- **Release**: November 2025
- **Sizes**: 7B, 32B
- **Context**: 65,536 tokens (16× larger than OLMo 2)
- **License**: Apache 2.0

**Variant Availability Matrix**:

| Variant | 7B | 32B | Purpose |
|---------|-----|-----|---------|
| **Base** | ✅ | ✅ | Foundation model |
| **Instruct** | ✅ | ❌ **Not available** | Chat, quick-response, tool use |
| **Think** | ✅ | ✅ | Long-horizon reasoning, explicit CoT |
| **RL Zero** | ✅ | ✅ | Experimental RL research |

**⚠️ Important**: There is **NO OLMo 3-32B-Instruct** variant. The Instruct model is only available at 7B.

- **Thinking Mode**: ✅ OLMo 3-Think generates explicit step-by-step reasoning (like OpenAI o1)
- **Unique Features**:
  - **Fully open**: Weights + training data (Dolma 3, 9.3T tokens) + code + training recipes
  - **OLMoTrace**: Tool for tracing outputs back to training data in real-time
  - OLMo 3-Think (7B) matches Qwen3-8B on MATH benchmarks
  - OLMo 3-Think (32B) matches Qwen3-32B-Thinking while trained on 6× fewer tokens
- **HuggingFace**:
  - `allenai/OLMo-3-7B-Instruct` (non-thinking)
  - `allenai/OLMo-3-7B-Think` (thinking)
  - `allenai/OLMo-3-32B-Think` (thinking only - no Instruct equivalent)
- **Status**: ⚠️ Limited for cross-validation - 32B lacks Instruct variant for Think vs Non-Think comparison

##### 8. Llama-Nemotron
- **Developer**: NVIDIA + Meta
- **Sizes**: 8B (Nano), 49B (Super), 253B (Ultra)
- **Thinking Mode**: System prompt toggle (`detailed thinking on/off`)
- **Architecture**: Llama-based with NVIDIA optimizations
- **Unique**: Optimized for inference on NVIDIA hardware
- **Status**: 🔍 Strong option, Llama architecture

##### 9. MiniMax-M1
- **Developer**: MiniMax
- **Thinking Mode**: "Thinking Budget" control
- **Architecture**: Dense
- **Status**: 🔍 Interesting thinking budget mechanism

#### Summary Comparison Matrix

| Model | True Arch Diversity | Thinking Support | Practical Size | Open Weights | Recommendation |
|-------|---------------------|------------------|----------------|--------------|----------------|
| DeepSeek-R1-Distill-**Llama** | ✅ Llama base | ✅ Native `<think>` | ✅ 8B, 70B | ✅ Yes | ⭐ **Primary choice** |
| **OLMo 3** | ⚠️ Decoder-only | ⚠️ 7B: Think+Instruct, 32B: Think only | ✅ 7B, 32B | ✅ **Fully open** | ⚠️ 32B lacks Instruct |
| GLM-4 | ✅ GLM arch | ✅ Yes | ✅ 9B, 26B | ✅ Yes | 🥉 **Alternative** |
| Llama-Nemotron | ⚠️ Llama base | ✅ Prompt-based | ✅ 8B, 49B | ✅ Yes | 🔍 Consider |
| Kimi K2 | ✅ Native MoE | ✅ Instruct/Thinking | ❌ 1T (32B active) | ✅ Yes | ⚠️ Large but viable |
| DeepSeek-R1 (671B) | ✅ Native MoE | ✅ Native | ❌ Very large | ✅ Yes | ⚠️ High cost |
| GPT-OSS | ✅ MoE arch | ✅ Effort param (Low/Med/High) | ✅ 20B, 120B (MoE efficient) | ✅ Apache 2.0 | 🥈 **Strong alternative** |

**Key Updates from Research:**
- **GPT-OSS**: OpenAI's first open-weight release (Aug 2025) - Apache 2.0, MoE with native MXFP4 quantization
- **OLMo 3**: First fully open thinking model, BUT **32B only has Think variant** (no 32B-Instruct). Only 7B has both Think and Instruct for comparison.
- **Kimi K2**: Confirmed Instruct/Thinking variants with 256K context and native INT4 quantization

---

### 2.1 DeepSeek Model Family Overview

DeepSeek offers several model variants. Understanding the hierarchy is important for selecting the right model for cross-architecture validation.

#### Original DeepSeek Models (Native Architecture)

| Model | Total Params | Active Params | Architecture | Purpose |
|-------|-------------|---------------|--------------|---------|
| **DeepSeek-V3** | 671B | 37B | MoE (256 experts) | General instruct model |
| **DeepSeek-R1** | 671B | 37B | MoE (256 experts) | Reasoning/thinking model |

- **DeepSeek-V3** (Dec 2024): Base instruct model, competitive with GPT-4
- **DeepSeek-R1** (Jan 2025): Reasoning model with native `<think>` tags, competitive with OpenAI o1

#### Distilled Models (R1 Reasoning → Smaller Architectures)

DeepSeek distilled R1's reasoning capabilities into smaller, more accessible models:

```
DeepSeek-R1 (671B original)
    │
    ├── Distilled to Qwen2.5 base → DeepSeek-R1-Distill-Qwen-1.5B/7B/14B/32B
    │
    └── Distilled to Llama base → DeepSeek-R1-Distill-Llama-8B/70B
```

### 2.2 Model Selection Considerations

#### ❌ Option A: DeepSeek-R1-Distill-Qwen (NOT RECOMMENDED)

| Qwen3 Model | DeepSeek-Qwen Equivalent | Issue |
|-------------|--------------------------|-------|
| Qwen3-4B | DeepSeek-R1-Distill-Qwen-7B | Same Qwen architecture |
| Qwen3-30B | DeepSeek-R1-Distill-Qwen-32B | Same Qwen architecture |

**Problem**: These models are built on **Qwen2.5 architecture**, sharing the same:
- Base architecture
- Tokenizer
- Fundamental capabilities/limitations

**Implication**: Comparing Qwen3 vs DeepSeek-R1-Distill-Qwen would essentially be "Qwen3 vs Qwen2.5 with R1 fine-tuning" — **not true cross-architecture validation**. This weakens generalizability claims.

#### ✅ Option B: DeepSeek-R1-Distill-Llama (RECOMMENDED)

| Qwen3 Model | DeepSeek-Llama Equivalent | Base Architecture |
|-------------|---------------------------|-------------------|
| Qwen3-4B-Instruct | DeepSeek-R1-Distill-Llama-8B (non-thinking) | Llama-3.1-8B |
| Qwen3-4B-Thinking | DeepSeek-R1-Distill-Llama-8B (thinking) | Llama-3.1-8B |
| Qwen3-30B-Instruct | DeepSeek-R1-Distill-Llama-70B (non-thinking) | Llama-3.3-70B |
| Qwen3-30B-Thinking | DeepSeek-R1-Distill-Llama-70B (thinking) | Llama-3.3-70B |

**Advantages**:
- Completely different architecture (Llama vs Qwen)
- Different tokenizer
- Different training data
- Native `<think>` tag support (same as Qwen3-Thinking)
- Strengthens generalizability claims

#### ⚠️ Option C: Original DeepSeek-R1/V3 (671B)

**Advantages**:
- True native DeepSeek architecture
- Strongest generalizability claim

**Challenges**:
| Model | VRAM Required | GPUs Needed | Estimated Cost |
|-------|---------------|-------------|----------------|
| DeepSeek-R1 (671B FP16) | ~1.3TB | 8-16x H100 | ~$1,500-2,000 for full replication |
| DeepSeek-R1 (INT8) | ~670GB | 8x H100 | ~$1,200-1,500 |

**Practicality**: Significantly more expensive and complex to deploy.

#### 🔮 Option D: DeepSeek-V3.1-Terminus (671B) - Future Consideration

**Model**: DeepSeek-V3.1-Terminus (671B total, 37B active MoE)

**Advantages**:
- ✅ **Native hybrid thinking**: Same model supports both thinking and non-thinking via chat template
- ✅ **No distillation confound**: Eliminates "cargo cult reasoning" validity threat
- ✅ **MoE architecture**: 37B active params comparable to Qwen3-30B-A3B (3B active)
- ✅ **MIT license**: Fully open for research
- ✅ **Best research validity**: Same weights for both modes

**VRAM Requirements**:

| Precision | VRAM | Hardware | Speed |
|-----------|------|----------|-------|
| FP16/BF16 | ~1.5TB | 20× H100 | Fast |
| FP8 | ~750GB | 10× H100 | Fast |
| INT4 (Q4) | ~386GB | 5× H100 | Medium |
| **UD-Q2_K_XL** (2.7-bit) | ~251GB | 3× H100 | Medium |
| **TQ1_0** (1.6-bit) | ~170GB | 2× H100 | Medium |

**Unsloth MoE Offloading Option**:

With Unsloth's dynamic quantization + MoE CPU offloading:

| Configuration | VRAM | RAM | Speed | Feasibility |
|---------------|------|-----|-------|-------------|
| 1× H100 80GB + MoE offload | 80GB | ~150GB | ~5 tok/s | ⚠️ Slow but possible |
| 2× H100 160GB | 160GB | - | ~140 tok/s | ✅ Viable |

**Command for MoE Offloading**:
```bash
# Offload all MoE layers to CPU RAM
-ot ".ffn_.*_exps.=CPU"

# Offload from layer 6+ only (better GPU utilization)
-ot "\.(6|7|8|9|[0-9][0-9])\.ffn_(gate|up|down)_exps.=CPU"
```

**Trade-offs**:
- ⚠️ **Speed**: 5 tok/s with offloading vs 140 tok/s native
- ⚠️ **Quantization impact**: 1-2 bit may degrade reasoning quality
- ⚠️ **Complexity**: Requires llama.cpp/Ollama, not vLLM

**Verdict**: **Best option for research validity** but requires either:
1. Multi-GPU setup (2× H100), OR
2. Accept slow inference (~5 tok/s) with aggressive quantization

**Recommendation**: Consider for **future work** if multi-GPU infrastructure becomes available, or as a **pilot study** to validate that aggressive quantization doesn't degrade thinking mode performance.

### 2.3 Final Recommendation: DeepSeek-R1-Distill-Llama

**Selected Models**:

| Qwen3 (Current) | DeepSeek Equivalent | Size | Base | Architecture |
|-----------------|---------------------|------|------|--------------|
| Qwen3-4B | **DeepSeek-R1-Distill-Llama-8B** | 8B | Llama-3.1-8B | Dense vs Dense ✅ |
| Qwen3-30B-A3B | **DeepSeek-R1-Distill-Llama-70B** | 70B | Llama-3.3-70B | **MoE vs Dense** ⚠️ |

**Rationale**:
1. **True architectural diversity**: Llama vs Qwen (different tokenizer, architecture, training)
2. **Native thinking support**: `<think>` tags work identically to Qwen3-Thinking
3. **Practical cost**: ~$800-1,000 vs $1,500+ for original 671B models
4. **Manageable VRAM**: 70B fits on 1x H100 with INT8 quantization

**Status**: Pending professor approval before proceeding.

### 2.4 Model Details

#### DeepSeek-R1-Distill-Llama-8B
- **HuggingFace**: `deepseek-ai/DeepSeek-R1-Distill-Llama-8B`
- **Base**: Llama-3.1-8B architecture with R1 reasoning capabilities distilled
- **Architecture**: **Dense** (8B params, all active)
- **VRAM**: ~16GB (FP16), ~8GB (INT8)
- **Context**: 128K tokens
- **Thinking Mode**: Use `<think>...</think>` tags for chain-of-thought

#### DeepSeek-R1-Distill-Llama-70B
- **HuggingFace**: `deepseek-ai/DeepSeek-R1-Distill-Llama-70B`
- **Base**: Llama-3.3-70B architecture with R1 reasoning capabilities distilled
- **Architecture**: **Dense** (70B params, all active)
- **VRAM**: ~140GB (FP16), ~70GB (INT8)
- **Context**: 128K tokens
- **Thinking Mode**: Use `<think>...</think>` tags for chain-of-thought
- **Deployment**: 1x H100 80GB with INT8 quantization, or 2x H100 with FP16

### 2.5 Thinking vs Non-Thinking Mode

DeepSeek-R1-Distill-Llama models support both modes via system prompting:

**Non-Thinking (Instruct) Mode**:
```
System: You are a helpful assistant. Provide direct answers without showing reasoning.
```

**Thinking Mode**:
```
System: You are a helpful assistant. Think step-by-step before answering.
```
The model will output `<think>...</think>` blocks containing reasoning.

### 2.5.1 Confounding Variables Summary

The cross-architecture comparison introduces several confounding variables that must be documented and acknowledged:

#### Comparison Matrix with Confounds

| Variable | Qwen3-4B vs DS-8B | Qwen3-30B vs DS-70B | Validity Impact |
|----------|-------------------|---------------------|-----------------|
| **Architecture Family** | Qwen vs Llama | Qwen vs Llama | ✅ Desired (primary goal) |
| **Architecture Type** | Dense vs Dense | **MoE vs Dense** | ⚠️ Confound (30B only) |
| **Total Parameters** | 4B vs 8B (2×) | 30B vs 70B (2.3×) | ⚠️ Confound |
| **Active Parameters** | 4B vs 8B | **3B vs 70B (23×)** | ⚠️ **Major confound** |
| **Precision** | BF16 vs FP16 | BF16 vs INT8 | ⚠️ Confound (30B only) |
| **Distillation** | Native vs Distilled | Native vs Distilled | ⚠️ Confound |
| **Temperature** | 0.0 vs 0.0 | 0.0 vs 0.0 | ✅ Controlled (matched) |

#### Confound Severity by Model Size

**8B Comparison (Cleaner):**
| Confound | Severity | Notes |
|----------|----------|-------|
| Architecture family | ✅ **Desired** | Qwen vs Llama - this is the goal |
| Size (4B vs 8B) | ⚠️ Low | 2× difference, both small models |
| Precision (BF16 vs FP16) | ✅ Minimal | Essentially equivalent |
| Architecture type | ✅ None | Both dense |
| Temperature | ✅ Controlled | Both use 0.0 (deterministic) |

**70B Comparison (More Confounded):**
| Confound | Severity | Notes |
|----------|----------|-------|
| Architecture family | ✅ **Desired** | Qwen vs Llama - this is the goal |
| Size (30B vs 70B) | ⚠️ Medium | 2.3× total parameters |
| Active params (3B vs 70B) | ❌ **High** | 23× more compute per token |
| Precision (BF16 vs INT8) | ⚠️ Medium | INT8 ~99% quality retention |
| Architecture type (MoE vs Dense) | ❌ **High** | Fundamentally different inference |
| Temperature | ✅ Controlled | Both use 0.0 (deterministic) |

#### Interpretation Guidance

**If results are SIMILAR between Qwen3 and DeepSeek:**
- Strong evidence that findings generalize across architectures
- Confounds did not significantly impact outcomes

**If results DIFFER between Qwen3 and DeepSeek:**
- Cannot conclusively attribute to architecture family alone
- Must consider: size, precision, MoE vs Dense, distillation effects
- **8B comparison provides cleaner signal** than 70B comparison

#### Recommendation for Analysis

1. **Primary validation**: Use 8B comparison (fewer confounds)
2. **Secondary validation**: Use 70B comparison with caveats
3. **Reporting**: Explicitly list all confounds in thesis/paper
4. **Conclusion framing**: "Results suggest generalization" rather than "Results prove generalization"

---

## 2.6 Research Validity Considerations: Distillation, Quantization & Unsloth

### Critical Context

The DeepSeek-R1-Distill models (both Qwen and Llama variants) are **distilled** from the original 671B DeepSeek-R1. This raises important research validity considerations that must be documented and addressed.

### 2.6.1 Threats from Distillation

Distillation transfers capabilities from large "teacher" models to smaller "student" models. However, this introduces specific threats to empirical research:

| Threat | Description | Impact on RQ |
|--------|-------------|--------------|
| **Faithfulness Confound** | Distilled models learn to reproduce outputs that *look* like reasoning but may not have internalized actual reasoning process | **RQ3 (Critical)** - Cannot distinguish genuine reasoning from learned patterns |
| **Cargo Cult Reasoning** | Model mimics the *format* of reasoning (tags) without cognitive depth | **RQ1 (High)** - May explain "reasoning artifacts" in thinking models |
| **Teacher Confound** | In MAS, if all agents are distilled from same teacher, they share blind spots | **RQ2 (Medium)** - May explain sycophancy and lack of error correction |
| **Energy Metrics Confound** | Distilled models have different inference characteristics than teachers | **RQ4 (High)** - "Energy per unit of genuine reasoning" becomes unmeasurable |
| **Benchmark Contamination** | Teacher models may have seen evaluation patterns; distillation concentrates these | **All RQs** - Risk of memorized patterns vs. generalization |

**Severity by Research Question:**

| RQ | Threat Level | Notes |
|----|--------------|-------|
| RQ1 (Reasoning) | High | Cannot distinguish native reasoning from learned imitation |
| RQ2 (MAS vs SA) | Medium | Inter-agent dynamics may reflect inherited behaviors |
| RQ3 (Faithfulness) | **Critical** | Explanations may be learned artifacts, not causal traces |
| RQ4 (Efficiency) | High | Distillation changes compute-to-capability relationship |

### 2.6.2 Alternatives to Distillation

To reduce hosting requirements while preserving model fidelity, consider these alternatives:

#### Quantization (Most Research-Friendly) ✅

Reduces weight precision while keeping **exact same** model architecture and weights.

| Quantization | Memory Reduction | Quality Retention | Research Validity |
|--------------|------------------|-------------------|-------------------|
| FP16 → INT8 | 50% | ~99% | Excellent |
| FP16 → INT4 | 75% | ~95-98% | Very Good |
| FP16 → 2-bit | 87% | ~90-95% | Good |

**Formats:**
- **GGUF (Q4_K_M, Q5_K_M)**: Best for CPU/GPU hybrid, works with llama.cpp, Ollama
- **GPTQ**: GPU-focused, works with vLLM, HuggingFace
- **AWQ**: GPU with activation-aware quantization

**Warning for Thinking Models**: Aggressive 4-bit quantization degrades logic/math significantly more than creative writing. Use **8-bit (Q8)** or **FP8** for reasoning models.

#### CPU/GPU Hybrid Offloading ✅

Allows running massive models on consumer hardware by splitting computation.

**KTransformers Performance:**
- Supports DeepSeek-R1/V3 671B on single 24GB VRAM GPU + 382GB DRAM
- Up to 27.79× speedup vs llama.cpp
- Example: 3090TI 24GB + 96GB DDR5 achieves >3 tok/sec for DeepSeek-R1 671B

#### Speculative Decoding (Mathematically Lossless) ✅

Samples faster **without any changes to outputs**. Output distribution is mathematically identical to original model.

#### Structured Pruning ⚠️

Removes entire rows/columns of weight matrices. More invasive than quantization but less than distillation.

### 2.6.3 Comparison of Techniques

| Technique | Architecture | Weights | Reasoning Process | Research Validity |
|-----------|--------------|---------|-------------------|-------------------|
| **Distillation** | Different (student) | Learned new | Mimicked | ❌ Poor |
| **Quantization** | Identical | Same (lower precision) | Preserved | ✅ Excellent |
| **Offloading** | Identical | Identical | Preserved | ✅ Excellent |
| **Speculative Decoding** | Identical | Identical | Preserved (mathematically) | ✅ Perfect |
| **Pruning** | Modified | Subset of original | Partially preserved | ⚠️ Moderate |

### 2.6.4 Unsloth Analysis

Unsloth offers two different capabilities with different research implications:

#### Dynamic Quantization (GGUFs) — ✅ Safe for Research

Unsloth's Dynamic v2.0 quantization intelligently quantizes important layers to higher bits (8-bit) while unimportant layers use lower bits (2-bit). This is **not distillation** — it's intelligent layer-wise quantization.

**Model Naming Guide (HuggingFace):**
- `unsloth/Qwen3-30B-A3B-GGUF` → **Quantized only** (safe)
- `unsloth/Qwen3-30B-bnb-4bit` → Dynamic 4-bit quants (generally safe)

| RQ | Threat Level | Notes |
|----|--------------|-------|
| RQ1 (Reasoning) | ✅ Low | Same reasoning processes, lower precision |
| RQ2 (MAS vs SA) | ✅ Low | Original coordination dynamics preserved |
| RQ3 (Faithfulness) | ✅ Low | Explanations reflect actual model inference |
| RQ4 (Efficiency) | ✅ Low | Comparable, with documented precision trade-off |

#### Fine-tuning with LoRA/QLoRA — ⚠️ Poses Threats

Unsloth also provides fine-tuning framework that modifies model behavior:

- `username/model-unsloth-finetuned` → **Fine-tuned** (poses threats to RQ3)

### 2.6.5 Implications for This Study

**Current Plan (DeepSeek-R1-Distill-Llama):**

The recommended models ARE distilled, which introduces the validity threats above. However:

1. **Cross-Architecture Validation Goal**: The primary goal is testing if findings generalize across architectures (Llama vs Qwen), not studying distillation effects
2. **Consistent Methodology**: Both Qwen3-Thinking and DeepSeek-R1-Distill use similar thinking mechanisms
3. **Documented Limitation**: Explicitly acknowledge distillation as a threat to validity in the final report

**Mitigation Strategies:**

1. **Document lineage explicitly**: Note distillation status as potential threat
2. **Use quantization when possible**: For VRAM reduction, prefer quantization over smaller distilled variants
3. **Treat distillation as variable**: If results differ significantly, distillation could be a confounding factor to investigate
4. **Consider native models for RQ3**: For faithfulness research specifically, original 671B models may be necessary

**Alternative Approach (If Budget Allows):**

Run a subset of experiments with the **original DeepSeek-R1 671B** using:
- INT8 quantization (~670GB, 8x H100)
- Or KTransformers CPU/GPU hybrid on high-RAM workstation

This would provide a "gold standard" comparison point for the distilled model results.

### 2.6.6 References

- Anthropic discussion: `docs/Anthropic - Expand Models Under Tests.md`
- Google discussion: `docs/Google - Expand Models Under Tests.md`
- Unsloth documentation: https://docs.unsloth.ai
- KTransformers: https://github.com/kvcache-ai/ktransformers

---

## 3. Experiments to Replicate

### Scope: H100 RunPod Experiments Only (Excluding Mars/RTX A5000)

From the 60 total Qwen3 experiments, **50 were run on H100** (RunPod). These will be replicated.

### Excluded Mars Experiments (10 total)

| # | Task | Model | Prompting | Platform | Reason for Exclusion |
|---|------|-------|-----------|----------|---------------------|
| 7 | Vuln | 4B Instruct | Few-shot (pre-CWE) | RTX A5000 | Mars server |
| 8 | Vuln | 4B Instruct | Few-shot | RTX A5000 | Mars server |
| 10 | Vuln | 4B Instruct | Zero-shot | RTX A5000 | Mars server |
| 12 | Vuln | 4B Thinking | Few-shot (pre-CWE) | RTX A5000 | Mars server |
| 13 | Vuln | 4B Thinking | Few-shot | RTX A5000 | Mars server |
| 15 | Vuln | 4B Thinking | Zero-shot | RTX A5000 | Mars server |
| 21 | Code | 4B Instruct | Few-shot | RTX A5000 | Mars server |
| 23 | Code | 4B Instruct | Zero-shot | RTX A5000 | Mars server |
| 25 | Code | 4B Thinking | Few-shot | RTX A5000 | Mars server |
| 27 | Code | 4B Thinking | Zero-shot | RTX A5000 | Mars server |

### Experiments to Replicate (48 total)

#### RQ1 Single-Agent Vulnerability Detection (8 experiments)

| New # | Original # | Model | Prompting | Expected GPU |
|-------|------------|-------|-----------|--------------|
| DS-1 | 2 | 70B Instruct | Few-shot | H100 |
| DS-2 | 3 | 70B Instruct | Zero-shot | H100 |
| DS-3 | 5 | 70B Thinking | Few-shot | H100 |
| DS-4 | 6 | 70B Thinking | Zero-shot | H100 |
| DS-5 | 9 | 8B Instruct | Few-shot | H100 |
| DS-6 | 11 | 8B Instruct | Zero-shot | H100 |
| DS-7 | 14 | 8B Thinking | Few-shot | H100 |
| DS-8 | 16 | 8B Thinking | Zero-shot | H100 |

*Note: Pre-CWE few-shot experiments (Original #1, #4) excluded - superseded by improved prompt format.*

#### RQ1 Single-Agent Code Generation (8 experiments)

| New # | Original # | Model | Prompting | Expected GPU |
|-------|------------|-------|-----------|--------------|
| DS-9 | 17 | 70B Instruct | Few-shot | H100 |
| DS-10 | 18 | 70B Instruct | Zero-shot | H100 |
| DS-11 | 19 | 70B Thinking | Few-shot | H100 |
| DS-12 | 20 | 70B Thinking | Zero-shot | H100 |
| DS-13 | 22 | 8B Instruct | Few-shot | H100 |
| DS-14 | 24 | 8B Instruct | Zero-shot | H100 |
| DS-15 | 26 | 8B Thinking | Few-shot | H100 |
| DS-16 | 28 | 8B Thinking | Zero-shot | H100 |

#### RQ2 Dual-Agent Vulnerability Detection (8 experiments)

| New # | Original # | Model | Prompting | Expected GPU |
|-------|------------|-------|-----------|--------------|
| DS-17 | 29 | 70B Instruct | Few-shot | H100 |
| DS-18 | 30 | 70B Instruct | Zero-shot | H100 |
| DS-19 | 31 | 70B Thinking | Few-shot | H100 |
| DS-20 | 32 | 70B Thinking | Zero-shot | H100 |
| DS-21 | 33 | 8B Instruct | Few-shot | H100 |
| DS-22 | 34 | 8B Instruct | Zero-shot | H100 |
| DS-23 | 35 | 8B Thinking | Few-shot | H100 |
| DS-24 | 36 | 8B Thinking | Zero-shot | H100 |

#### RQ2 Multi-Agent Vulnerability Detection (8 experiments)

| New # | Original # | Model | Prompting | Expected GPU |
|-------|------------|-------|-----------|--------------|
| DS-25 | 37 | 70B Instruct | Few-shot | H100 |
| DS-26 | 38 | 70B Instruct | Zero-shot | H100 |
| DS-27 | 39 | 70B Thinking | Few-shot | H100 |
| DS-28 | 40 | 70B Thinking | Zero-shot | H100 |
| DS-29 | 41 | 8B Instruct | Few-shot | H100 |
| DS-30 | 42 | 8B Instruct | Zero-shot | H100 |
| DS-31 | 43 | 8B Thinking | Few-shot | H100 |
| DS-32 | 44 | 8B Thinking | Zero-shot | H100 |

#### RQ2 Dual-Agent Code Generation (8 experiments)

| New # | Original # | Model | Prompting | Expected GPU |
|-------|------------|-------|-----------|--------------|
| DS-33 | 45 | 70B Instruct | Few-shot | H100 |
| DS-34 | 46 | 70B Instruct | Zero-shot | H100 |
| DS-35 | 47 | 70B Thinking | Few-shot | H100 |
| DS-36 | 48 | 70B Thinking | Zero-shot | H100 |
| DS-37 | 49 | 8B Instruct | Few-shot | H100 |
| DS-38 | 50 | 8B Instruct | Zero-shot | H100 |
| DS-39 | 51 | 8B Thinking | Few-shot | H100 |
| DS-40 | 52 | 8B Thinking | Zero-shot | H100 |

#### RQ2 Multi-Agent Code Generation (8 experiments)

| New # | Original # | Model | Prompting | Expected GPU |
|-------|------------|-------|-----------|--------------|
| DS-41 | 53 | 70B Instruct | Few-shot | H100 |
| DS-42 | 54 | 70B Instruct | Zero-shot | H100 |
| DS-43 | 55 | 70B Thinking | Few-shot | H100 |
| DS-44 | 56 | 70B Thinking | Zero-shot | H100 |
| DS-45 | 57 | 8B Instruct | Few-shot | H100 |
| DS-46 | 58 | 8B Instruct | Zero-shot | H100 |
| DS-47 | 59 | 8B Thinking | Few-shot | H100 |
| DS-48 | 60 | 8B Thinking | Zero-shot | H100 |

---

## 4. Infrastructure Plan

### RunPod Configuration

| Model | GPU Required | VRAM Needed | Recommended Instance |
|-------|--------------|-------------|---------------------|
| DeepSeek-R1-Distill-Llama-8B | 1x H100 | ~16GB FP16 | H100 SXM 80GB |
| DeepSeek-R1-Distill-Llama-70B | 1x H100 | ~70GB INT8 / ~140GB FP16 | H100 SXM 80GB (INT8) |

**Note**: The 70B model requires INT8 quantization to fit on a single H100 80GB. Alternatively, use 2x H100 with tensor parallelism for FP16.

### Precision Comparison (Qwen3 Baseline vs DeepSeek)

| Model | Qwen3 Baseline | DeepSeek Equivalent | Baseline Precision | DeepSeek Precision | Notes |
|-------|----------------|---------------------|--------------------|--------------------|-------|
| Small | Qwen3-4B | DS-R1-Distill-Llama-8B | **BF16** | **FP16** | Comparable precision |
| Large | Qwen3-30B-A3B | DS-R1-Distill-Llama-70B | **BF16** | **INT8** | Quantization required |

**Important**: The Qwen3 baseline experiments used **BF16 (bfloat16) with no quantization** (vLLM `--dtype bfloat16`). The DeepSeek 70B model requires INT8 quantization due to VRAM constraints. This is a documented limitation - INT8 typically retains ~99% quality but should be acknowledged in the analysis.

### Temperature Setting

| Setting | Qwen3 Baseline | DeepSeek Replication | Decision |
|---------|----------------|---------------------|----------|
| Temperature | **0.0** | **0.0** | ✅ Match baseline |

**Baseline Configuration**: Qwen3 experiments used `temperature = 0.0` (deterministic/greedy decoding) configured in `src/config.py`.

**DeepSeek Recommendation Discrepancy**: DeepSeek-R1-Distill documentation recommends `temperature 0.5-0.7` for reasoning tasks. However, for **fair cross-architecture comparison**, we will use **temperature = 0.0** to match the Qwen3 baseline exactly.

**Rationale**:
- Ensures consistent experimental conditions across model families
- Eliminates temperature as a confounding variable
- Maintains reproducibility (deterministic outputs)
- Any performance differences can be attributed to model architecture, not sampling strategy

**Future Work**: A follow-up study could explore optimal temperature settings per model family.

### Pod Strategy

Mirroring Qwen3 setup:
- **2 pods for 8B models** (parallel execution)
- **2 pods for 70B models** (parallel execution, INT8 quantization)
- **Total: 4 pods** running concurrently

### Estimated Runtime

Based on Qwen3 timings (adjusted for larger 70B model):
- **Vulnerability Detection**: ~2-4 hours per configuration (386 samples)
- **Code Generation**: ~1-2 hours per configuration (164 samples)
- **Total per pod**: ~30-48 hours for all assigned experiments
- **Total wall-clock time**: ~48-60 hours (with parallel execution)

### Estimated Cost

See **[Cross_Architecture_Cost_Estimates.md](./Cross_Architecture_Cost_Estimates.md)** for detailed breakdown.

**Summary**:
- **Platform**: RunPod H100 SXM 80GB @ $2.69/hr (USD)
- **GPU-Hours**: ~116 hours
- **Base Cost**: ~$312
- **With Contingency**: **$400-475 USD** (recommended)

**Status**: Pending professor approval

---

## 5. Code Changes Required

### 5.1 Environment Configuration

Create `.env.deepseek`:
```bash
# DeepSeek Model Configuration (Llama-based)
MODEL_PROVIDER=vllm
VLLM_BASE_URL=http://localhost:8000/v1

# 8B Model (Llama-3.1 base)
MODEL_NAME_8B=deepseek-ai/DeepSeek-R1-Distill-Llama-8B

# 70B Model (Llama-3.3 base)
MODEL_NAME_70B=deepseek-ai/DeepSeek-R1-Distill-Llama-70B

# Thinking mode toggle
ENABLE_REASONING=true  # or false for instruct mode
```

### 5.2 vLLM Deployment Commands

**8B Model** (FP16):
```bash
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-R1-Distill-Llama-8B \
    --max-model-len 65536 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9
```

**70B Model** (INT8 quantization for single H100):
```bash
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-R1-Distill-Llama-70B \
    --max-model-len 65536 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.95 \
    --quantization int8
```

**70B Model** (FP16 with 2x H100 tensor parallelism - alternative):
```bash
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-R1-Distill-Llama-70B \
    --max-model-len 65536 \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9
```

### 5.3 Code Modifications

1. **Update `src/config.py`**: Add DeepSeek-Llama model configurations
2. **Update thinking tag handling**: DeepSeek uses `<think>...</think>` (same as Qwen3)
3. **Update results directory**: `results/deepseek_rq1/`, `results/deepseek_rq2/`

---

## 6. Thinking Mode Validation Tests

### 6.1 Purpose

Before running full experiments, verify that:
1. **Thinking mode** produces `<think>...</think>` reasoning blocks
2. **Non-thinking mode** produces direct answers without reasoning tags
3. Output parsing is compatible with existing code

### 6.2 Test Prompts

#### Test Case 1: Simple Reasoning Task

**Prompt**:
```
What is 17 * 24? Show your work.
```

**Expected Thinking Mode Output**:
```
<think>
To calculate 17 * 24:
- 17 * 20 = 340
- 17 * 4 = 68
- 340 + 68 = 408
</think>

The answer is 408.
```

**Expected Non-Thinking Mode Output**:
```
17 * 24 = 408
```

#### Test Case 2: Vulnerability Detection Sample

**Prompt** (simplified):
```
Analyze this code for security vulnerabilities:

```c
void copy_input(char *input) {
    char buffer[64];
    strcpy(buffer, input);
}
```

Is this code vulnerable? Answer with 1 (vulnerable) or 0 (not vulnerable).
```

**Expected Thinking Mode Output**:
```
<think>
Let me analyze this code:
1. The function takes an unbounded char pointer input
2. It copies to a fixed 64-byte buffer using strcpy
3. strcpy does not check bounds - classic buffer overflow
4. This is CWE-120: Buffer Copy without Checking Size of Input
</think>

1
```

**Expected Non-Thinking Mode Output**:
```
1
```

#### Test Case 3: Code Generation Sample

**Prompt** (HumanEval style):
```
def add_two_numbers(a: int, b: int) -> int:
    """Return the sum of two integers."""
```

**Expected Thinking Mode Output**:
```
<think>
This is a simple function to add two integers.
I need to return a + b.
</think>

def add_two_numbers(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b
```

**Expected Non-Thinking Mode Output**:
```
def add_two_numbers(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b
```

### 6.3 System Prompts for Mode Control

#### Thinking Mode System Prompt
```
You are a helpful AI assistant. Think through problems step-by-step before providing your answer. Show your reasoning process.
```

#### Non-Thinking (Instruct) Mode System Prompt
```
You are a helpful AI assistant. Provide direct, concise answers without showing your reasoning process. Do not use <think> tags.
```

### 6.4 Validation Checklist

| Test | Model | Mode | Check | Status |
|------|-------|------|-------|--------|
| TC-1 | 8B | Thinking | `<think>` tags present | [ ] |
| TC-1 | 8B | Non-Thinking | No `<think>` tags | [ ] |
| TC-1 | 70B | Thinking | `<think>` tags present | [ ] |
| TC-1 | 70B | Non-Thinking | No `<think>` tags | [ ] |
| TC-2 | 8B | Thinking | Reasoning + classification | [ ] |
| TC-2 | 8B | Non-Thinking | Direct classification only | [ ] |
| TC-2 | 70B | Thinking | Reasoning + classification | [ ] |
| TC-2 | 70B | Non-Thinking | Direct classification only | [ ] |
| TC-3 | 8B | Thinking | Reasoning + code | [ ] |
| TC-3 | 8B | Non-Thinking | Direct code only | [ ] |
| TC-3 | 70B | Thinking | Reasoning + code | [ ] |
| TC-3 | 70B | Non-Thinking | Direct code only | [ ] |

### 6.5 Validation Script

Create `scripts/validate_deepseek_modes.py`:
```python
"""
Validate DeepSeek thinking/non-thinking mode configuration.
Run this before starting full experiments.
"""

import requests
import json

VLLM_URL = "http://localhost:8000/v1/chat/completions"

TEST_PROMPTS = [
    {"name": "Math", "prompt": "What is 17 * 24? Show your work."},
    {"name": "Vuln", "prompt": "Is strcpy(buffer, input) with fixed buffer vulnerable? Answer 1 or 0."},
    {"name": "Code", "prompt": "Complete: def add(a, b): # return sum"},
]

def test_mode(system_prompt: str, mode_name: str):
    print(f"\n{'='*60}")
    print(f"Testing {mode_name} mode")
    print('='*60)

    for test in TEST_PROMPTS:
        response = requests.post(VLLM_URL, json={
            "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": test["prompt"]}
            ],
            "max_tokens": 500,
            "temperature": 0.0
        })

        content = response.json()["choices"][0]["message"]["content"]
        has_think_tags = "<think>" in content

        print(f"\n[{test['name']}] Has <think> tags: {has_think_tags}")
        print(f"Response preview: {content[:200]}...")

if __name__ == "__main__":
    # Test thinking mode
    test_mode(
        "You are a helpful assistant. Think step-by-step before answering.",
        "THINKING"
    )

    # Test non-thinking mode
    test_mode(
        "You are a helpful assistant. Provide direct answers without showing reasoning. Do not use <think> tags.",
        "NON-THINKING"
    )
```

### 6.6 Success Criteria

**PASS**: Proceed to full experiments if:
- [x] Thinking mode consistently produces `<think>` blocks (>90% of responses)
- [x] Non-thinking mode produces no `<think>` tags (>95% of responses)
- [x] Output format compatible with existing parsing logic
- [x] Response quality appears reasonable (not gibberish)

**FAIL**: Investigate and adjust prompts if:
- [ ] Thinking mode doesn't produce reasoning
- [ ] Non-thinking mode still includes `<think>` tags
- [ ] Output format breaks parsing
- [ ] Model refuses to respond or produces errors

---

## 7. Execution Plan

### Phase 1: Setup & Validation (Day 1)

- [ ] Create DeepSeek-specific environment configuration
- [ ] Test vLLM deployment with both models (8B and 70B)
- [ ] **Run thinking mode validation tests** (Section 6)
  - [ ] Execute `scripts/validate_deepseek_modes.py`
  - [ ] Complete validation checklist (12 test combinations)
  - [ ] Verify `<think>` tag behavior in both modes
- [ ] Run 2 task-specific validation samples per model size
  - [ ] 1 vulnerability detection sample (with known label)
  - [ ] 1 code generation sample (HumanEval)
- [ ] Verify output format compatibility with existing parsing logic
- [ ] **Gate check**: Only proceed if validation criteria pass (Section 6.6)

### Phase 2: RQ1 Single-Agent (Days 2-3)

- [ ] Deploy 8B and 70B models on separate pods
- [ ] Execute DS-1 to DS-18 (18 experiments)
- [ ] Monitor energy consumption via CodeCarbon
- [ ] Download and verify results

### Phase 3: RQ2 Multi-Agent (Days 4-5)

- [ ] Execute DS-19 to DS-50 (32 experiments)
- [ ] Handle potential context overflow (especially MA-Thinking)
- [ ] Download and verify results

### Phase 4: Analysis (Day 6)

- [ ] Create DeepSeek analysis notebook
- [ ] Generate cross-model comparison visualizations
- [ ] Statistical analysis: Qwen3 vs DeepSeek
- [ ] Update research documentation

---

## 7. Expected Outcomes

### Validation Scenarios

| Outcome | Implication |
|---------|-------------|
| **Similar patterns to Qwen3** | Findings generalize across model families |
| **Different patterns** | Model-specific effects; findings may be Qwen-specific |
| **Mixed results** | Some findings generalize, others are model-dependent |

### Key Metrics to Compare

1. **F1 Score** (Vulnerability Detection)
2. **Pass@1** (Code Generation)
3. **Energy Consumption** (kWh)
4. **Token Verbosity** (Avg tokens per sample)
5. **Agent Architecture Impact** (Single vs Dual vs Multi)

---

## 8. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| DeepSeek output format differs | Pre-test output parsing; adjust extraction logic |
| 70B model OOM on H100 | Use INT8 quantization (required for single H100) |
| Context overflow in MA-Thinking | Same restart strategy as Qwen3 |
| Higher cost than estimated | Set RunPod spending limit; prioritize critical experiments |

---

## 9. Documentation Updates Required

After completion:
- [ ] Create `ANALYSIS_SUMMARY_DeepSeek.md`
- [ ] Update `research_question.md` with cross-model findings
- [ ] Add DeepSeek results to comparison notebook
- [ ] Update final report with generalizability analysis

---

## Appendix: Quick Reference

### Model Naming Convention

| Model | Instruct Mode | Thinking Mode |
|-------|---------------|---------------|
| 8B | `DS-8B-Inst` | `DS-8B-Think` |
| 70B | `DS-70B-Inst` | `DS-70B-Think` |

### Results Directory Structure

```
results/
├── deepseek_rq1/
│   ├── SA-vuln_DS-8B-Inst_few-shot_*.jsonl
│   ├── SA-vuln_DS-8B-Think_zero-shot_*.jsonl
│   ├── SA-code_DS-70B-Inst_*.jsonl
│   └── ...
└── deepseek_rq2/
    ├── DA-vuln_DS-8B-Inst_*.jsonl
    ├── MA-vuln_DS-70B-Think_*.jsonl
    └── ...
```
