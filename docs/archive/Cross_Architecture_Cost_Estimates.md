# Cross-Architecture Validation: Cost Estimates

**Purpose**: Budget planning for Llama-Nemotron replication experiments
**Related Document**: [Cross_Architecture_Validation_Plan.md](./Cross_Architecture_Validation_Plan.md)
**Date**: December 6, 2025
**Last Updated**: December 7, 2025
**Status**: Pending Professor Approval

---

## 1. Executive Summary

| Item | Value |
|------|-------|
| **Total Experiments** | 48 (16 RQ1 + 32 RQ2) |
| **Estimated GPU-Hours** | 164 hours (single-GPU equivalent) |
| **Base Compute Cost** | $530 |
| **With Contingency** | **$665-750** |
| **Wall-Clock Time** | ~55 hours (parallel execution) |
| **Platform** | RunPod H100 SXM 80GB |

### Key Cost Difference from Original Estimate

| Factor | DeepSeek (Original) | Nemotron (Updated) | Impact |
|--------|---------------------|--------------------|----|
| 49B Hardware | Single H100 | **2× H100 required** | +70% for 49B experiments |
| 8B Hardware | Single H100 | Single H100 | No change |
| Model Size | 8B + 70B | 8B + 49B | Slightly faster inference |

**Why cost increased**: Nemotron-Super-49B requires tensor parallelism across 2× H100 GPUs, effectively doubling the cost for 49B experiments (~50% of total).

---

## 2. Hardware Requirements (Validated Dec 7, 2025)

| Model | GPUs Required | Precision | Cost/Hour | Notes |
|-------|---------------|-----------|-----------|-------|
| Nemotron-Nano-8B | 1× H100 SXM | FP16 | $2.69/hr | Validated ✅ |
| Nemotron-Super-49B | **2× H100 SXM** | FP8 or FP16 | **$5.38/hr** | Validated ✅ |

**RunPod Pricing (Dec 2025)**:
- 1× H100 SXM 80GB: $2.69/hr USD
- 2× H100 SXM 80GB: $5.38/hr USD (2× single GPU rate)

---

## 3. Experiment Scope

### 3.1 Experiments by Category

| Category | Count | 8B Experiments | 49B Experiments |
|----------|-------|----------------|-----------------|
| **RQ1 Single-Agent Vuln** | 8 | 4 | 4 |
| **RQ1 Single-Agent Code** | 8 | 4 | 4 |
| **RQ2 Dual-Agent Vuln** | 8 | 4 | 4 |
| **RQ2 Dual-Agent Code** | 8 | 4 | 4 |
| **RQ2 Multi-Agent Vuln** | 8 | 4 | 4 |
| **RQ2 Multi-Agent Code** | 8 | 4 | 4 |
| **Total** | **48** | **24** | **24** |

### 3.2 Model Configuration

| Model | Experiments | GPUs | Cost Rate | Hardware Notes |
|-------|-------------|------|-----------|----------------|
| Nemotron-Nano-8B | 24 | 1× H100 | $2.69/hr | FP16, 64K context |
| Nemotron-Super-49B | 24 | 2× H100 | $5.38/hr | FP8/FP16, 64K context, tensor-parallel=2 |

---

## 4. Runtime Estimates

### 4.1 Adjustment Factors (Nemotron vs Qwen3)

| Factor | Adjustment | Rationale |
|--------|------------|-----------|
| 8B vs 4B | 1.5-2× slower | Larger dense model |
| 49B vs 30B-MoE | 2-2.5× slower | Dense (49B active) vs MoE (3B active), but tensor parallel helps |
| Thinking mode | 3-5× vs Instruct | Verbose reasoning output (same as Qwen3) |

### 4.2 Detailed Runtime Breakdown

#### RQ1 Single-Agent Experiments (16 total)

| Experiment | Model | Mode | Prompting | Est. Duration | Count | GPU-Hours | Cost |
|------------|-------|------|-----------|---------------|-------|-----------|------|
| SA-Vuln | 8B | Instruct | Few/Zero | 1.0 hr | 2 | 2.0 | $5.38 |
| SA-Vuln | 8B | Thinking | Few/Zero | 3.0 hr | 2 | 6.0 | $16.14 |
| SA-Vuln | 49B | Instruct | Few/Zero | 1.5 hr | 2 | 6.0* | $16.14 |
| SA-Vuln | 49B | Thinking | Few/Zero | 4.0 hr | 2 | 16.0* | $43.04 |
| SA-Code | 8B | Instruct | Few/Zero | 0.5 hr | 2 | 1.0 | $2.69 |
| SA-Code | 8B | Thinking | Few/Zero | 1.5 hr | 2 | 3.0 | $8.07 |
| SA-Code | 49B | Instruct | Few/Zero | 1.0 hr | 2 | 4.0* | $10.76 |
| SA-Code | 49B | Thinking | Few/Zero | 2.5 hr | 2 | 10.0* | $26.90 |
| **RQ1 Subtotal** | | | | | **16** | **48.0** | **$129.12** |

*49B GPU-hours counted as 2× (tensor parallel across 2 GPUs)*

#### RQ2 Dual-Agent Experiments (16 total)

| Experiment | Model | Mode | Est. Duration | Count | GPU-Hours | Cost |
|------------|-------|------|---------------|-------|-----------|------|
| DA-Vuln | 8B | Instruct | 1.0 hr | 2 | 2.0 | $5.38 |
| DA-Vuln | 8B | Thinking | 2.0 hr | 2 | 4.0 | $10.76 |
| DA-Vuln | 49B | Instruct | 2.0 hr | 2 | 8.0* | $21.52 |
| DA-Vuln | 49B | Thinking | 4.0 hr | 2 | 16.0* | $43.04 |
| DA-Code | 8B | Instruct | 0.5 hr | 2 | 1.0 | $2.69 |
| DA-Code | 8B | Thinking | 1.5 hr | 2 | 3.0 | $8.07 |
| DA-Code | 49B | Instruct | 1.0 hr | 2 | 4.0* | $10.76 |
| DA-Code | 49B | Thinking | 2.5 hr | 2 | 10.0* | $26.90 |
| **DA Subtotal** | | | | **16** | **48.0** | **$129.12** |

#### RQ2 Multi-Agent Experiments (16 total)

| Experiment | Model | Mode | Est. Duration | Count | GPU-Hours | Cost |
|------------|-------|------|---------------|-------|-----------|------|
| MA-Vuln | 8B | Instruct | 1.5 hr | 2 | 3.0 | $8.07 |
| MA-Vuln | 8B | Thinking | 3.0 hr | 2 | 6.0 | $16.14 |
| MA-Vuln | 49B | Instruct | 2.5 hr | 2 | 10.0* | $26.90 |
| MA-Vuln | 49B | Thinking | 6.0 hr | 2 | 24.0* | $64.56 |
| MA-Code | 8B | Instruct | 1.0 hr | 2 | 2.0 | $5.38 |
| MA-Code | 8B | Thinking | 2.5 hr | 2 | 5.0 | $13.45 |
| MA-Code | 49B | Instruct | 1.5 hr | 2 | 6.0* | $16.14 |
| MA-Code | 49B | Thinking | 4.0 hr | 2 | 16.0* | $43.04 |
| **MA Subtotal** | | | | **16** | **72.0** | **$193.68** |

### 4.3 Total Runtime Summary

| Category | Experiments | GPU-Hours | Cost |
|----------|-------------|-----------|------|
| RQ1 Single-Agent | 16 | 48.0 | $129.12 |
| RQ2 Dual-Agent | 16 | 48.0 | $129.12 |
| RQ2 Multi-Agent | 16 | 72.0 | $193.68 |
| **Total** | **48** | **168.0** | **$451.92** |

---

## 5. Cost Calculation

### 5.1 Detailed Cost Breakdown

| Item | Calculation | Cost |
|------|-------------|------|
| **Core Experiments** | 168 GPU-hours (see above) | $451.92 |
| **Model Download (8B)** | ~0.5 hrs × $2.69 | $1.35 |
| **Model Download (49B)** | ~1 hr × $5.38 (2× H100) | $5.38 |
| **Setup & Pilot Testing** | ~10 hrs mixed | $35.00 |
| **Validation Testing** | Already done (Dec 7) | $0.00 |
| **Subtotal (Base)** | | **$493.65** |
| | | |
| **Contingency (25%)** | Buffer for restarts, errors | $123.41 |
| **Total with Contingency** | | **$617.06** |

### 5.2 Budget Request Options

| Option | Amount | Coverage |
|--------|--------|----------|
| **Conservative** | $620 | Base + 25% contingency |
| **Recommended** | $700 | Base + 40% contingency (safer buffer) |
| **Maximum** | $800 | Allows for 50%+ reruns if needed |

### 5.3 Cost Comparison: 8B-Only vs Full (8B + 49B)

| Scenario | Experiments | GPU-Hours | Estimated Cost |
|----------|-------------|-----------|----------------|
| **8B Only** | 24 | 38.0 | ~$150-180 |
| **49B Only** | 24 | 130.0 | ~$400-450 |
| **Full (8B + 49B)** | 48 | 168.0 | **$620-700** |

**Recommendation**: Running both 8B and 49B provides better cross-architecture validation (comparing against Qwen3-4B and Qwen3-30B respectively).

---

## 6. Execution Strategy

### 6.1 Recommended: Parallel Pod Deployment

| Pod | Assignment | GPUs | Wall-Clock | Cost |
|-----|------------|------|------------|------|
| Pod 1 | 8B-Instruct (all RQ1+RQ2) | 1× H100 | ~8 hrs | $22 |
| Pod 2 | 8B-Thinking (all RQ1+RQ2) | 1× H100 | ~24 hrs | $65 |
| Pod 3 | 49B-Instruct (all RQ1+RQ2) | 2× H100 | ~17 hrs | $91 |
| Pod 4 | 49B-Thinking (all RQ1+RQ2) | 2× H100 | ~42 hrs | $226 |
| **Total** | | | **~42 hrs** | **$404** |

**Note**: Pods 3 & 4 use 2× H100 configuration for 49B tensor parallelism.

### 6.2 Alternative: Sequential on Single 2× H100 Pod

| Approach | Duration | Cost | Trade-off |
|----------|----------|------|-----------|
| All sequential on 2× H100 | ~95 hrs (~4 days) | $511 | Simple but longer |
| 2 pods (8B + 49B separate) | ~55 hrs (~2.3 days) | $451 | Balanced |
| 4 pods (max parallel) | ~42 hrs (~1.8 days) | $404 | Fastest |

**Recommendation**: 4-pod parallel execution (same or lower cost, faster completion).

---

## 7. Risk Factors & Mitigations

### 7.1 Cost Overrun Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Context overflow (MA-Thinking) | Medium | +10-20% time | Resume functionality, chunked prompts |
| 49B tensor parallel issues | Low | +5-10% time | Already validated with vLLM |
| 49B-Thinking exceeds estimate | Medium | +15-25% time | 25-40% contingency buffer |
| Pod startup/shutdown overhead | Low | +5% time | Included in setup estimate |

### 7.2 Contingency Usage Scenarios

| Scenario | Additional Cost | Notes |
|----------|-----------------|-------|
| Smooth execution | $0 | Unlikely (some issues expected) |
| Minor issues (10% reruns) | ~$70 | Normal variance |
| Moderate issues (20% reruns) | ~$140 | Within recommended budget |
| Major issues (30%+ reruns) | ~$200+ | May need max budget |

---

## 8. Comparison: Original DeepSeek vs Updated Nemotron

| Metric | DeepSeek (Original) | Nemotron (Updated) | Change |
|--------|---------------------|--------------------|----|
| Large model | 70B (single H100 INT8) | 49B (2× H100 FP8/FP16) | +100% GPU cost for large model |
| Small model | 8B (single H100) | 8B (single H100) | No change |
| Thinking toggle | ❌ NOT WORKING | ✅ VALIDATED | Blocker resolved |
| Base cost estimate | $330 | $494 | +50% |
| With contingency | $400-475 | $620-700 | +55% |

**Why the cost increase is justified**:
1. ✅ Nemotron actually works (DeepSeek R1 Distill didn't support non-thinking mode)
2. ✅ Full precision (FP16) available vs INT8 quantization workaround
3. ✅ True architectural diversity (Llama-based vs Qwen-based)
4. ✅ Hardware validated - no surprises during experiments

---

## 9. Summary for Funding Request

```
PROJECT: Llama-Nemotron Cross-Architecture Validation
PURPOSE: Validate RQ1/RQ2 generalizability beyond Qwen3

SCOPE:
- 48 experiments (16 RQ1 Single-Agent + 32 RQ2 Multi-Agent)
- Models: Nemotron-Nano-8B (1× H100) + Nemotron-Super-49B (2× H100)
- Tasks: Vulnerability Detection + Code Generation

HARDWARE (Validated Dec 7, 2025):
- 8B: Single H100 SXM 80GB, FP16
- 49B: 2× H100 SXM 80GB, FP8 or FP16, tensor-parallel=2

COMPUTE REQUIREMENTS:
- Platform: RunPod H100 SXM 80GB @ $2.69/hr per GPU (USD)
- GPU-Hours: ~168 hours (8B: 38 hrs @ $2.69, 49B: 130 hrs @ $5.38)
- Wall-Clock: ~42 hours (4 pods parallel)

BUDGET REQUEST:
- Base compute: $494
- Setup + contingency: $126-206
- Total: $620-700 USD (recommended: $700)

COMPARISON TO ORIGINAL ESTIMATE:
- Original (DeepSeek): $400-475
- Updated (Nemotron): $620-700 (+55%)
- Reason: 49B requires 2× H100 for tensor parallelism

TIMELINE: ~2-3 days execution + 1 day analysis
```

---

## 10. Approval & Tracking

| Date | Action | Status |
|------|--------|--------|
| 2025-12-06 | Cost estimate prepared (DeepSeek) | Complete |
| 2025-12-07 | Updated for Nemotron (2× H100 for 49B) | Complete |
| 2025-12-07 | Hardware validated on RunPod | Complete |
| TBD | Professor review | Pending |
| TBD | Funding approved | Pending |
| TBD | Experiments executed | Pending |
| TBD | Actual vs estimated reconciliation | Pending |

---

## Appendix: Actual Cost Tracking (Post-Execution)

*To be filled after experiments complete*

| Pod | Assignment | GPUs | Planned Hours | Actual Hours | Planned Cost | Actual Cost | Variance |
|-----|------------|------|---------------|--------------|--------------|-------------|----------|
| Pod 1 | 8B-Instruct | 1× H100 | 8 | - | $22 | - | - |
| Pod 2 | 8B-Thinking | 1× H100 | 24 | - | $65 | - | - |
| Pod 3 | 49B-Instruct | 2× H100 | 17 | - | $91 | - | - |
| Pod 4 | 49B-Thinking | 2× H100 | 42 | - | $226 | - | - |
| **Total** | | | **91** | - | **$404** | - | - |

**Notes on variances**: *(to be added)*
