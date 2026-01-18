# Log Analysis Experiments - Cost Estimate

## 1. Experiment Design Summary

### 1.1 Phase I (RQ1): Reasoning Effectiveness - Single-Agent Only

**16 experiments** total:
- 2 model families (Qwen3, Nemotron)
- 4 model variants (4B, 30B, 8B, 49B)
- 2 modes (Instruct, Thinking)
- 2 prompting strategies (Zero-shot, Few-shot)

### 1.2 Phase II (RQ2): Agentic Moderation - Dual-Agent and Multi-Agent

**32 experiments** total:
- 2 model families (Qwen3, Nemotron)
- 4 model variants (4B, 30B, 8B, 49B)
- 2 modes (Instruct, Thinking)
- 2 prompting strategies (Zero-shot, Few-shot)
- 2 agent architectures (Dual-Agent, Multi-Agent)

### 1.3 Total Experiments

| Phase | Experiments |
|-------|-------------|
| Phase I (SA) | 16 |
| Phase II (DA + MA) | 32 |
| **Total** | **48** |

---

## 2. Reference Data: Past Experiments

### 2.1 Vulnerability Detection Experiments (386 samples)

| Model | Design | Mode | Duration (hrs) |
|-------|--------|------|----------------|
| Qwen3-4B | SA | Instruct | 0.76-0.87 |
| Qwen3-4B | SA | Thinking | 2.87-3.69 |
| Qwen3-4B | DA | Instruct | 0.45 |
| Qwen3-4B | DA | Thinking | 3.36-3.93 |
| Qwen3-4B | MA | Instruct | 0.37-1.72 |
| Qwen3-4B | MA | Thinking | 5.81-6.54 |
| Qwen3-30B | SA | Instruct | 0.70 |
| Qwen3-30B | SA | Thinking | 2.81-4.34 |
| Qwen3-30B | DA | Instruct | 0.70-1.38 |
| Qwen3-30B | DA | Thinking | 3.58-4.34 |
| Qwen3-30B | MA | Instruct | 0.44-0.50 |
| Qwen3-30B | MA | Thinking | 1.84 |
| Nemotron-8B | SA | Instruct | 0.35-0.74 |
| Nemotron-8B | SA | Thinking | 0.47-1.31 |
| Nemotron-8B | DA | Instruct | 1.40-3.28 |
| Nemotron-8B | DA | Thinking | 1.62-2.78 |
| Nemotron-8B | MA | Instruct | 6.09-9.12 |
| Nemotron-8B | MA | Thinking | 11.51-12.95 |

---

## 3. Cost Projection

### 3.1 Pricing

- **RunPod H100 SXM 80GB**: US$2.69/hr per GPU
- **Nemotron-49B**: Requires 2× H100 (tensor parallelism) = US$5.38/hr
- Reference: https://www.runpod.io/gpu-models/h100-sxm

### 3.2 Dataset

Log Analysis dataset: **385 sessions** (comparable to vulnerability detection's 386 samples)

---

## 4. Phase I (RQ1): Single-Agent Experiments

### 4.1 Qwen3-4B (SA)

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 0.80 hrs | $2.15 |
| Instruct | Few-shot | 0.80 hrs | $2.15 |
| Thinking | Zero-shot | 3.30 hrs | $8.88 |
| Thinking | Few-shot | 3.30 hrs | $8.88 |
| **Subtotal** | | **8.20 hrs** | **$22.06** |

### 4.2 Qwen3-30B (SA)

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 0.70 hrs | $1.88 |
| Instruct | Few-shot | 0.70 hrs | $1.88 |
| Thinking | Zero-shot | 3.50 hrs | $9.42 |
| Thinking | Few-shot | 3.50 hrs | $9.42 |
| **Subtotal** | | **8.40 hrs** | **$22.60** |

### 4.3 Nemotron-8B (SA)

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 0.55 hrs | $1.48 |
| Instruct | Few-shot | 0.55 hrs | $1.48 |
| Thinking | Zero-shot | 0.90 hrs | $2.42 |
| Thinking | Few-shot | 0.90 hrs | $2.42 |
| **Subtotal** | | **2.90 hrs** | **$7.80** |

### 4.4 Nemotron-49B (SA) - 2× H100

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 1.00 hrs | $5.38 |
| Instruct | Few-shot | 1.00 hrs | $5.38 |
| Thinking | Zero-shot | 2.00 hrs | $10.76 |
| Thinking | Few-shot | 2.00 hrs | $10.76 |
| **Subtotal** | | **6.00 hrs** | **$32.28** |

### 4.5 Phase I Summary

| Model | Experiments | Duration (hrs) | Cost |
|-------|-------------|----------------|------|
| Qwen3-4B | 4 | 8.20 | $22.06 |
| Qwen3-30B | 4 | 8.40 | $22.60 |
| Nemotron-8B | 4 | 2.90 | $7.80 |
| Nemotron-49B | 4 | 6.00 | $32.28 |
| **Phase I Total** | **16** | **25.50 hrs** | **$84.74** |

---

## 5. Phase II (RQ2): Dual-Agent and Multi-Agent Experiments

### 5.1 Qwen3-4B (DA + MA)

**Dual-Agent:**

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 0.45 hrs | $1.21 |
| Instruct | Few-shot | 0.45 hrs | $1.21 |
| Thinking | Zero-shot | 3.65 hrs | $9.82 |
| Thinking | Few-shot | 3.65 hrs | $9.82 |
| **DA Subtotal** | | **8.20 hrs** | **$22.06** |

**Multi-Agent:**

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 1.05 hrs | $2.82 |
| Instruct | Few-shot | 1.05 hrs | $2.82 |
| Thinking | Zero-shot | 6.18 hrs | $16.62 |
| Thinking | Few-shot | 6.18 hrs | $16.62 |
| **MA Subtotal** | | **14.46 hrs** | **$38.88** |

**Qwen3-4B Total**: 8 experiments, 22.66 hrs, **$60.94**

### 5.2 Qwen3-30B (DA + MA)

**Dual-Agent:**

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 1.04 hrs | $2.80 |
| Instruct | Few-shot | 1.04 hrs | $2.80 |
| Thinking | Zero-shot | 3.96 hrs | $10.65 |
| Thinking | Few-shot | 3.96 hrs | $10.65 |
| **DA Subtotal** | | **10.00 hrs** | **$26.90** |

**Multi-Agent:**

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 0.47 hrs | $1.26 |
| Instruct | Few-shot | 0.47 hrs | $1.26 |
| Thinking | Zero-shot | 1.84 hrs | $4.95 |
| Thinking | Few-shot | 1.84 hrs | $4.95 |
| **MA Subtotal** | | **4.62 hrs** | **$12.42** |

**Qwen3-30B Total**: 8 experiments, 14.62 hrs, **$39.32**

### 5.3 Nemotron-8B (DA + MA)

**Dual-Agent:**

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 2.34 hrs | $6.29 |
| Instruct | Few-shot | 2.34 hrs | $6.29 |
| Thinking | Zero-shot | 2.20 hrs | $5.92 |
| Thinking | Few-shot | 2.20 hrs | $5.92 |
| **DA Subtotal** | | **9.08 hrs** | **$24.42** |

**Multi-Agent:**

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 7.61 hrs | $20.47 |
| Instruct | Few-shot | 7.61 hrs | $20.47 |
| Thinking | Zero-shot | 12.23 hrs | $32.90 |
| Thinking | Few-shot | 12.23 hrs | $32.90 |
| **MA Subtotal** | | **39.68 hrs** | **$106.74** |

**Nemotron-8B Total**: 8 experiments, 48.76 hrs, **$131.16**

### 5.4 Nemotron-49B (DA + MA) - 2× H100

**Dual-Agent:**

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 3.50 hrs | $18.83 |
| Instruct | Few-shot | 3.50 hrs | $18.83 |
| Thinking | Zero-shot | 3.30 hrs | $17.75 |
| Thinking | Few-shot | 3.30 hrs | $17.75 |
| **DA Subtotal** | | **13.60 hrs** | **$73.16** |

**Multi-Agent:**

| Mode | Prompting | Est. Duration | Est. Cost |
|------|-----------|---------------|-----------|
| Instruct | Zero-shot | 10.00 hrs | $53.80 |
| Instruct | Few-shot | 10.00 hrs | $53.80 |
| Thinking | Zero-shot | 16.00 hrs | $86.08 |
| Thinking | Few-shot | 16.00 hrs | $86.08 |
| **MA Subtotal** | | **52.00 hrs** | **$279.76** |

**Nemotron-49B Total**: 8 experiments, 65.60 hrs, **$352.92**

### 5.5 Phase II Summary

| Model | Experiments | Duration (hrs) | Cost |
|-------|-------------|----------------|------|
| Qwen3-4B | 8 | 22.66 | $60.94 |
| Qwen3-30B | 8 | 14.62 | $39.32 |
| Nemotron-8B | 8 | 48.76 | $131.16 |
| Nemotron-49B | 8 | 65.60 | $352.92 |
| **Phase II Total** | **32** | **151.64 hrs** | **$584.34** |

---

## 6. SOTA Model Comparison (API-Based)

To benchmark against state-of-the-art commercial models, 1 experiment on **Vulnerability Detection**:

| Model | Provider | Input Cost | Output Cost | Est. Tokens | Est. Cost |
|-------|----------|------------|-------------|-------------|-----------|
| Claude Sonnet 4.5 | OpenRouter | $3/1M | $15/1M | ~2M in, ~0.4M out | ~$12 |

**With buffer (2×)**: US$25 (to account for retries, extended reasoning)

Reference: https://openrouter.ai/pricing

---

## 7. Total Cost Summary

### 7.1 Base Costs

| Category | Experiments | Duration (hrs) | Cost |
|----------|-------------|----------------|------|
| Phase I (SA) | 16 | 25.50 | $84.74 |
| Phase II (DA + MA) | 32 | 151.64 | $584.34 |
| SOTA API (Vuln) | 1 | - | $25.00 |
| **Total** | **49** | **177.14 hrs** | **$694.08** |

### 7.2 Contingency and Buffer

| Item | Cost |
|------|------|
| Base Cost | $694.08 |
| Setup & pilot testing | +$40.00 |
| **Subtotal** | **$734.08** |
| With 25% contingency | $917.60 |
| **Recommended (40% buffer)** | **$1,027.71** |

### 7.3 Final Budget Request

| Currency | Amount |
|----------|--------|
| **USD** | **$1,030** |
| **SGD** (@ 1.35) | **$1,390** |

---

## 8. Cost Breakdown by GPU Configuration

| GPU Config | Models | Experiments | Duration (hrs) | Cost |
|------------|--------|-------------|----------------|------|
| 1× H100 @ $2.69/hr | Qwen3-4B, Qwen3-30B, Nemotron-8B | 36 | 105.54 | $283.90 |
| 2× H100 @ $5.38/hr | Nemotron-49B | 12 | 71.60 | $385.20 |
| API (OpenRouter) | Claude Sonnet 4.5 | 1 | - | $25.00 |
| **Total** | | **49** | **177.14** | **$694.10** |

---

## 9. Assumptions and Notes

### 9.1 Duration Estimates

- Based on vulnerability detection experiments (386 samples ≈ 385 sessions)
- Log analysis may be faster due to simpler output (0/1 binary classification)
- Thinking mode adds ~3-4× overhead compared to Instruct
- Multi-Agent experiments show highest variability and longest runtimes

### 9.2 Nemotron-49B Requirements

- Model weights: ~94GB (FP16)
- Single H100 memory: 80GB
- Requires tensor parallelism across 2× H100 GPUs
- Validated on Dec 7, 2025

### 9.3 Scope Adjustments (If Needed)

**To reduce costs:**

| Adjustment | Savings | New Total |
|------------|---------|-----------|
| Skip Nemotron-49B entirely | -$385 | ~$309 |
| Skip MA experiments only | -$438 | ~$256 |
| Skip Phase II entirely | -$584 | ~$110 |

---

## 10. Action Items

1. ✅ Pull upstream changes (log analysis scripts already available)
2. ✅ Update experiment plan for consistency
3. ⬜ Submit budget request for **SGD 1,390**
4. ⬜ Pilot run with 50 sessions to validate estimates

---

## Document History

- **Created**: 2026-01-11
- **Updated**: 2026-01-13 (revised experiment matrix: 48 total experiments)
- **Based on**: consolidated_emissions.csv analysis
- **Hardware**: RunPod H100 SXM 80GB
