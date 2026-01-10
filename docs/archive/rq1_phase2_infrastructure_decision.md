# RQ1 Phase 2 Infrastructure Decision

**Date**: 2025-10-20
**Decision**: Use RunPod single GPU instances instead of Mars multi-GPU setup
**Status**: Selected for Phase 2 experiments

---

## Context

For RQ1 Phase 2, we need to run Qwen3-30B-A3B models which require ~30GB VRAM. Mars server has 4× RTX A5000 GPUs (24GB each).

## Options Evaluated

### Option 1: Mars Single GPU with Quantization ❌
**Approach**: Use FP8 quantization + Unsloth to fit 30B-A3B on single A5000 (24GB)

**Pros:**
- Free infrastructure (Mars server)
- Maintains single-GPU architecture from Phase 1

**Cons:**
- Introduces quantization variable (4B models were FP16/BF16)
- May not fit even with optimization (~20-22GB with FP8, but tight)
- Different precision affects both performance and energy
- **Confounds results**: Can't separate model scale effects from quantization effects

**Decision**: ❌ **Not Preferred** - Introduces too many variables for research validity

---

### Option 2: Mars Multi-GPU with Tensor Parallelism ❌
**Approach**: Use vLLM tensor parallelism (`--tensor-parallel-size 2`) across 2× A5000 GPUs

**Pros:**
- Free infrastructure
- Can fit larger models
- vLLM and CodeCarbon both support multi-GPU

**Cons:**
- **Different architecture from Phase 1** (single GPU → multi-GPU)
- Adds inter-GPU communication overhead
- Energy measurement becomes more complex (aggregated across GPUs)
- **Confounds results**: Can't isolate whether differences are due to:
  - Model scale (4B dense → 30B MoE)
  - GPU architecture (single → tensor parallel)
  - Communication overhead
  - Memory access patterns
- Less reproducible (multi-GPU synchronization adds variables)

**vLLM Multi-GPU Details:**
```bash
# Would require this configuration
--tensor-parallel-size 2  # Split across 2 GPUs
--gpu-memory-utilization 0.90  # Use more VRAM per GPU
```

**CodeCarbon Multi-GPU Details:**
- Automatically detects and aggregates all GPUs in CUDA_VISIBLE_DEVICES
- Sums energy across devices
- Works, but adds complexity to analysis

**Decision**: ❌ **Not Preferred** - Introduces architectural confounding variables

---

### Option 3: RunPod Single Large GPU ✅
**Approach**: Use cloud GPU instances with sufficient VRAM for single-GPU deployment

**Infrastructure Options:**

| GPU Model | VRAM | RunPod Cost/hr | Fits 30B-A3B? | Fits 235B-A22B? | Notes |
|-----------|------|----------------|---------------|-----------------|-------|
| **A6000** | 48GB | ~$0.79 | ❌ No (needs ~60GB) | ❌ No | - |
| **A100 40GB** | 40GB | ~$1.39 | ❌ No (needs ~60GB) | ❌ No | - |
| **A100 80GB** | 80GB | ~$1.39 | ✅ Yes | ⚠️ Tight (need 120-150GB) | Cheaper option |
| **H100 80GB** | 80GB | ~$2.49 | ✅ Yes ⭐ | ✅ Yes (with optimization) | **Recommended**: Better network → reliable downloads |

**Pros:**
- ✅ **Maintains single-GPU architecture** from Phase 1
- ✅ **No architectural confounds** - only model scale changes
- ✅ Same vLLM configuration (just different model size)
- ✅ Clean energy comparisons (single GPU → single GPU)
- ✅ Can run both 30B-A3B and 235B-A22B with same setup
- ✅ Reproducible and well-documented

**Cons:**
- 💰 Cost: ~$1-4/hour vs free Mars server
- ⏱️ Need to manage cloud instances

**Decision**: ✅ **SELECTED** - Best for research validity

---

## Final Decision

### Recommended Infrastructure for Phase 2:

**For Qwen3-30B-A3B models:**
- **Platform**: RunPod
- **Template**: Jupyter Notebook + PyTorch
- **GPU**: H100 SXM 80GB recommended (~$2.49/hr) or A100 SXM 80GB (~$1.39/hr)
  - A6000 48GB and A100 40GB are insufficient
  - **H100 advantage**: Better network connectivity → vLLM auto-download (Method 1) works reliably without XET CDN errors
  - Tested successfully: H100 pods had no download issues with HuggingFace models
- **Volume Disk**: 100GB minimum (persistent storage for /workspace)
  - 50GB Volume Disk insufficient for model download + experiments
  - Use Volume Disk (not Container Disk) as it persists when pod is stopped
- **Cost**: H100 ~$2.49/hour (recommended) or A100 ~$1.39/hour
- **Configuration**: Single GPU, same vLLM settings as Phase 1
- **File Transfer**: Direct SSH with scp (automated scripts) + Jupyter UI backup
- **Model Download**: Method 1 (vLLM auto-download) worked successfully on H100
- **Overhead**: Jupyter adds <0.5% total energy, <0.1% GPU energy (negligible)
- **Memory requirement**: ~60GB GPU VRAM with vLLM overhead (model + KV cache + buffers)
- **Disk requirement**: ~50GB Volume Disk for model files + temp space + results
- **Estimated cost**: 2 pods × 2 hours × $2.49 = ~$9.96 for Phase 2a (H100)

**For Qwen3-235B-A22B models:**
- **Platform**: RunPod
- **GPU**: H100 80GB (2× for tensor parallelism, or wait for Phase 2b decision)
- **Cost**: ~$2.99-3.50/hour per GPU
- **Configuration**: May require tensor parallelism (2× H100)
- **Estimated cost**: 4 experiments × 4 hours × $3.50 × 2 = ~$112

**Alternative for 235B-A22B**:
- Defer to Phase 2b after analyzing 30B-A3B results
- Consider if scale jump from 30B-A3B (3B active) to 235B-A22B (22B active) is necessary
- May be sufficient to show trend with 4B → 30B-A3B

---

## Justification for Research Paper

When documenting in the paper, we will state:

> **Infrastructure Consistency**: To maintain experimental validity and enable direct
> performance-energy comparisons across model scales, all experiments were conducted
> on single-GPU configurations. While Mars server (NVIDIA RTX A5000 24GB) was
> sufficient for 4B models (Phase 1), larger models required cloud instances with
> greater VRAM capacity. Qwen3-30B-A3B experiments used RunPod A6000 (48GB) instances
> with Jupyter Notebook environment for convenient file management. Baseline measurements
> confirmed that Jupyter adds minimal overhead (<0.5% total system energy, <0.1% GPU
> energy). The single-GPU architecture was maintained to avoid introducing tensor
> parallelism as a confounding variable. This ensured that observed differences in
> energy consumption and performance could be attributed solely to model scale and
> architecture (dense vs MoE), not to deployment configuration.

---

## Implementation Plan

### Phase 2a: Qwen3-30B-A3B Models (Immediate)

1. **Setup RunPod account** (if not already done)
2. **Reserve A6000 48GB instance**
3. **Install dependencies**:
   - vLLM (same version as Phase 1)
   - CodeCarbon 2.7.1
   - Docker setup
4. **Run 4 experiments**:
   - Qwen3-30B-A3B-Instruct-2507 (zero-shot, few-shot)
   - Qwen3-30B-A3B-Thinking-2507 (zero-shot, few-shot)
5. **Download results** to local for analysis
6. **Estimated total cost**: ~$11-15

### Phase 2b: Qwen3-235B-A22B Models (After 2a Analysis)

**Decision point**: After analyzing 30B-A3B results, determine if 235B-A22B is necessary:
- If 30B-A3B shows clear few-shot improvement → 235B-A22B adds confirmation
- If 30B-A3B still shows few-shot degradation → may skip 235B-A22B (trend established)
- If results are inconclusive → 235B-A22B provides additional data point

**If proceeding**:
1. **Reserve H100 80GB instances** (may need 2× for tensor parallelism)
2. **Test model loading** with single H100 + aggressive optimization
3. **Run 4 experiments** if feasible on single GPU
4. **Estimated cost**: $50-150 depending on configuration

---

## Consistency Matrix

| Dimension | Phase 1 (4B) | Phase 2a (30B-A3B) | Phase 2b (235B-A22B) | Consistent? |
|-----------|--------------|-------------------|----------------------|-------------|
| **GPU Count** | 1 | 1 | 1 (or 2 if necessary) | ✅ (mostly) |
| **GPU Architecture** | NVIDIA RTX A5000 | NVIDIA A6000/A100 | NVIDIA H100 | ⚠️ Different models |
| **VRAM** | 24GB | 40-48GB | 80GB (×2) | ⚠️ Different capacity |
| **vLLM Version** | Same | Same | Same | ✅ |
| **CodeCarbon** | 2.7.1 | 2.7.1 | 2.7.1 | ✅ |
| **Precision** | BF16/FP16 | BF16/FP16 | BF16/FP16 | ✅ |
| **Quantization** | None | None | None | ✅ |
| **Parallelism** | None | None | TBD | ⚠️ May need TP |
| **Dataset** | VulTrial 384 | VulTrial 384 | VulTrial 384 | ✅ |
| **Prompts** | Zero/Few-shot | Zero/Few-shot | Zero/Few-shot | ✅ |

**Key Consistency**: Model architecture (single GPU, no quantization, same software) remains constant where possible. GPU hardware differences are **controlled variables** (documented and analyzed separately).

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| RunPod GPU unavailability | Medium | High | Reserve pods 24h in advance, have backup regions |
| Cost overrun | Low | Medium | Set budget alerts, estimate conservatively |
| Different GPU affects results | Medium | High | Document GPU specs, run calibration test, report in paper |
| 235B model won't fit single GPU | High | High | Plan for tensor parallelism OR skip 235B (trend from 4B→30B sufficient) |

---

## Decision Summary

- [x] Options evaluated and documented
- [x] Cost estimated for selected approach
- [x] Research validity considerations addressed
- [x] Implementation plan created
- [ ] Ready for implementation

---

*Last Updated: 2025-10-20*
*Decision Maker: Research Team*
*Status: Awaiting confirmation to proceed with implementation*
