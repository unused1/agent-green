# Cross-Architecture Validation: Cost Estimates

**Purpose**: Budget planning for DeepSeek-R1-Distill-Llama replication experiments
**Related Document**: [Cross_Architecture_Validation_Plan.md](./Cross_Architecture_Validation_Plan.md)
**Date**: December 6, 2025
**Status**: Pending Professor Approval

---

## 1. Executive Summary

| Item | Value |
|------|-------|
| **Total Experiments** | 48 (16 RQ1 + 32 RQ2) |
| **Estimated GPU-Hours** | 116 hours |
| **Base Compute Cost** | $312 |
| **With Contingency** | **$400-475** |
| **Wall-Clock Time** | ~50 hours (4 pods parallel) |
| **Platform** | RunPod H100 SXM 80GB @ $2.69/hr (USD) |

---

## 2. Reference Data: Qwen3 Experiments

Actual runtimes from completed Qwen3 experiments (source: `emissions.csv`):

| Experiment Type | Qwen3 Model | Duration | Samples | Time/Sample |
|----------------|-------------|----------|---------|-------------|
| SA-Vuln (Instruct) | 4B | ~30-40 min | 386 | ~5 sec |
| SA-Vuln (Thinking) | 4B | ~2-3 hrs | 386 | ~25 sec |
| DA-Vuln (Instruct) | 4B | ~27 min | 386 | ~4 sec |
| DA-Vuln (Thinking) | 4B | ~30-45 min | 386 | ~6 sec |
| MA-Vuln (Instruct) | 4B | ~40-60 min | 386 | ~8 sec |
| MA-Vuln (Thinking) | 4B | ~2-3 hrs | 386 | ~25 sec |
| Code Gen (all types) | 4B | ~12-25 min | 164 | ~6-9 sec |

**Qwen3 RQ2 Total**: 8 H100 GPUs × 72 hours = ~$2,000 compute (60 experiments × multiple runs)

---

## 3. DeepSeek Experiment Scope

### 3.1 Experiments by Category

| Category | Count | Description |
|----------|-------|-------------|
| **RQ1 Single-Agent Vuln** | 8 | 4 × 70B + 4 × 8B |
| **RQ1 Single-Agent Code** | 8 | 4 × 70B + 4 × 8B |
| **RQ2 Dual-Agent Vuln** | 8 | 4 × 70B + 4 × 8B |
| **RQ2 Dual-Agent Code** | 8 | 4 × 70B + 4 × 8B |
| **RQ2 Multi-Agent Vuln** | 8 | 4 × 70B + 4 × 8B |
| **RQ2 Multi-Agent Code** | 8 | 4 × 70B + 4 × 8B |
| **Total** | **48** | H100 experiments only |

*Note: Pre-CWE few-shot experiments excluded (superseded by improved prompt format).*

### 3.2 Model Breakdown

| Model | Precision | Experiments | Notes |
|-------|-----------|-------------|-------|
| DeepSeek-R1-Distill-Llama-8B | FP16 | 24 | Fits on single H100 |
| DeepSeek-R1-Distill-Llama-70B | INT8 | 26 | Requires quantization |

---

## 4. Runtime Estimates

### 4.1 Adjustment Factors (DeepSeek vs Qwen3)

| Factor | Adjustment | Rationale |
|--------|------------|-----------|
| 8B vs 4B | 1.5-2× slower | Larger dense model |
| 70B vs 30B-MoE | 2-3× slower | Dense (70B active) vs MoE (3B active) |
| INT8 quantization | ~1.1× slower | Minor overhead |
| Thinking mode | 3-5× vs Instruct | Verbose reasoning output |

### 4.2 Detailed Runtime Breakdown

#### RQ1 Single-Agent Experiments (16 total)

| Experiment | Model | Mode | Prompting | Est. Duration | Count | Subtotal |
|------------|-------|------|-----------|---------------|-------|----------|
| SA-Vuln | 8B | Instruct | Few/Zero | 1.0 hr | 2 | 2.0 hrs |
| SA-Vuln | 8B | Thinking | Few/Zero | 3.0 hr | 2 | 6.0 hrs |
| SA-Vuln | 70B | Instruct | Few/Zero | 1.5 hr | 2 | 3.0 hrs |
| SA-Vuln | 70B | Thinking | Few/Zero | 5.0 hr | 2 | 10.0 hrs |
| SA-Code | 8B | Instruct | Few/Zero | 0.5 hr | 2 | 1.0 hrs |
| SA-Code | 8B | Thinking | Few/Zero | 1.5 hr | 2 | 3.0 hrs |
| SA-Code | 70B | Instruct | Few/Zero | 1.0 hr | 2 | 2.0 hrs |
| SA-Code | 70B | Thinking | Few/Zero | 3.0 hr | 2 | 6.0 hrs |
| **RQ1 Subtotal** | | | | | **16** | **33.0 hrs** |

#### RQ2 Dual-Agent Experiments (16 total)

| Experiment | Model | Mode | Est. Duration | Count | Subtotal |
|------------|-------|------|---------------|-------|----------|
| DA-Vuln | 8B | Instruct | 1.0 hr | 2 | 2.0 hrs |
| DA-Vuln | 8B | Thinking | 2.0 hr | 2 | 4.0 hrs |
| DA-Vuln | 70B | Instruct | 2.0 hr | 2 | 4.0 hrs |
| DA-Vuln | 70B | Thinking | 5.0 hr | 2 | 10.0 hrs |
| DA-Code | 8B | Instruct | 0.5 hr | 2 | 1.0 hrs |
| DA-Code | 8B | Thinking | 1.5 hr | 2 | 3.0 hrs |
| DA-Code | 70B | Instruct | 1.0 hr | 2 | 2.0 hrs |
| DA-Code | 70B | Thinking | 3.0 hr | 2 | 6.0 hrs |
| **DA Subtotal** | | | | **16** | **32.0 hrs** |

#### RQ2 Multi-Agent Experiments (16 total)

| Experiment | Model | Mode | Est. Duration | Count | Subtotal |
|------------|-------|------|---------------|-------|----------|
| MA-Vuln | 8B | Instruct | 1.5 hr | 2 | 3.0 hrs |
| MA-Vuln | 8B | Thinking | 3.5 hr | 2 | 7.0 hrs |
| MA-Vuln | 70B | Instruct | 3.0 hr | 2 | 6.0 hrs |
| MA-Vuln | 70B | Thinking | 7.0 hr | 2 | 14.0 hrs |
| MA-Code | 8B | Instruct | 1.0 hr | 2 | 2.0 hrs |
| MA-Code | 8B | Thinking | 2.5 hr | 2 | 5.0 hrs |
| MA-Code | 70B | Instruct | 2.0 hr | 2 | 4.0 hrs |
| MA-Code | 70B | Thinking | 5.0 hr | 2 | 10.0 hrs |
| **MA Subtotal** | | | | **16** | **51.0 hrs** |

### 4.3 Total Runtime Summary

| Category | Experiments | GPU-Hours |
|----------|-------------|-----------|
| RQ1 Single-Agent | 16 | 33.0 |
| RQ2 Dual-Agent | 16 | 32.0 |
| RQ2 Multi-Agent | 16 | 51.0 |
| **Total** | **48** | **116.0 hrs** |

---

## 5. Cost Calculation

### 5.1 RunPod Pricing

| GPU Type | On-Demand | Community/Spot | Notes |
|----------|-----------|----------------|-------|
| H100 SXM 80GB | **$2.69/hr** | ~$1.99/hr | Current pricing (Dec 2025) |
| H100 PCIe 80GB | $1.99-2.39/hr | ~$1.50/hr | Alternative option |

**Selected**: H100 SXM 80GB @ $2.69/hr USD (updated from earlier $3.99/hr)

**Note**: All prices in USD. Qwen3 experiments used older $3.99/hr pricing.

### 5.2 Cost Breakdown

| Item | Calculation | Cost |
|------|-------------|------|
| **Core Experiments** | 116 hrs × $2.69/hr | $312.04 |
| **Model Download** | ~2 hrs (8B: 16GB + 70B: 140GB) | $5.38 |
| **Setup & Pilot Testing** | ~5 hrs debugging/validation | $13.45 |
| **Subtotal (Base)** | | **$330.87** |
| | | |
| **Contingency (25%)** | Buffer for restarts, errors | $82.72 |
| **Total with Contingency** | | **$413.59** |

### 5.3 Budget Request Options

| Option | Amount | Coverage |
|--------|--------|----------|
| **Conservative** | $415 | Base + 25% contingency |
| **Recommended** | $475 | Base + 45% contingency (safe buffer) |
| **Maximum** | $550 | Allows for partial reruns if needed |

---

## 6. Execution Strategy

### 6.1 Parallel Pod Deployment (4 Pods)

| Pod | Assignment | GPU-Hours | Est. Duration | Cost |
|-----|------------|-----------|---------------|------|
| Pod 1 | 8B-Instruct (all RQ1+RQ2) | ~14 hrs | ~14 hrs | $38 |
| Pod 2 | 8B-Thinking (all RQ1+RQ2) | ~32 hrs | ~32 hrs | $86 |
| Pod 3 | 70B-Instruct (all RQ1+RQ2) | ~22 hrs | ~22 hrs | $59 |
| Pod 4 | 70B-Thinking (all RQ1+RQ2) | ~50 hrs | ~50 hrs | $135 |
| **Total** | | **118 hrs** | **50 hrs wall-clock** | **$318** |

**Note**: Parallel execution reduces wall-clock time from ~118 hours to ~50 hours.

### 6.2 Alternative: Sequential Execution (1 Pod)

| Approach | Duration | Cost | Trade-off |
|----------|----------|------|-----------|
| Sequential | ~118 hrs (~5 days) | $318 | Cheaper, slower |
| 2 Pods | ~60 hrs (~2.5 days) | $318 | Moderate parallelism |
| 4 Pods | ~50 hrs (~2 days) | $318 | Maximum parallelism |

**Recommendation**: 4 pods parallel (same cost, faster completion)

---

## 7. Risk Factors & Mitigations

### 7.1 Cost Overrun Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Context overflow (MA-Thinking) | Medium | +10-20% time | Resume functionality, restarts |
| vLLM compatibility issues | Low | +5-10% time | Pilot testing before main runs |
| 70B-Thinking exceeds estimate | Medium | +15-25% time | 25% contingency buffer |
| INT8 quantization issues | Low | +5% time | Test with sample prompts first |

### 7.2 Contingency Usage Scenarios

| Scenario | Additional Cost | Notes |
|----------|-----------------|-------|
| Smooth execution | $0 | Unlikely (some issues expected) |
| Minor issues (10% reruns) | ~$50 | Normal variance |
| Moderate issues (20% reruns) | ~$100 | Within contingency |
| Major issues (30%+ reruns) | ~$150+ | May need additional funding |

---

## 8. Comparison to Qwen3 Experiments

| Metric | Qwen3 RQ2 | DeepSeek (Planned) | Ratio |
|--------|-----------|--------------------|----|
| Experiments | 60 | 48 | 80% |
| Runs per experiment | 1-3 | 1 | 33-100% |
| Total GPU-hours | ~576 hrs (8×72) | ~116 hrs | 20% |
| Total cost | ~$2,000 (@ $3.99/hr) | ~$400-475 (@ $2.69/hr) | 20-24% |

**Why lower cost?**
1. Single-run design (no statistical replication)
2. Fewer experiments (48 vs 60)
3. Parallel execution efficiency

---

## 9. Summary for Funding Request

```
PROJECT: DeepSeek Cross-Architecture Validation
PURPOSE: Validate RQ1/RQ2 generalizability beyond Qwen3

SCOPE:
- 48 experiments (16 RQ1 Single-Agent + 32 RQ2 Multi-Agent)
- Models: DeepSeek-R1-Distill-Llama-8B and 70B
- Tasks: Vulnerability Detection + Code Generation

COMPUTE REQUIREMENTS:
- Platform: RunPod H100 SXM 80GB @ $2.69/hr (USD)
- GPU-Hours: ~116 hours
- Wall-Clock: ~50 hours (4 pods parallel)

BUDGET REQUEST:
- Base compute: $312
- Setup + contingency: $88-163
- Total: $400-475 USD (recommended: $475)

TIMELINE: ~2-3 days execution + 1 day analysis
```

---

## 10. Approval & Tracking

| Date | Action | Status |
|------|--------|--------|
| 2025-12-06 | Cost estimate prepared | Complete |
| TBD | Professor review | Pending |
| TBD | Funding approved | Pending |
| TBD | Experiments executed | Pending |
| TBD | Actual vs estimated reconciliation | Pending |

---

## Appendix: Actual Cost Tracking (Post-Execution)

*To be filled after experiments complete*

| Pod | Planned Hours | Actual Hours | Planned Cost | Actual Cost | Variance |
|-----|---------------|--------------|--------------|-------------|----------|
| Pod 1 | 15 | - | $60 | - | - |
| Pod 2 | 35 | - | $140 | - | - |
| Pod 3 | 25 | - | $100 | - | - |
| Pod 4 | 55 | - | $220 | - | - |
| **Total** | **130** | - | **$520** | - | - |

**Notes on variances**: *(to be added)*
