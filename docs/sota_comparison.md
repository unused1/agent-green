# SOTA Comparison Study

## Research Justification

### Why Vulnerability Detection?

Vulnerability detection is the task where all tested models perform worst, with accuracy hovering around 50% (essentially random guessing):

| Model | Mean Accuracy | Mean F1 |
|-------|---------------|---------|
| Nemotron-Super-49B | 52.1% | 53.3% |
| Qwen3-30B-A3B-Instruct | 51.3% | 49.6% |
| Qwen3-30B-A3B-Thinking | 50.4% | 48.3% |
| Qwen3-4B-Instruct | 50.6% | 40.0% |
| Qwen3-4B-Thinking | 50.3% | 49.8% |
| Nemotron-Nano-8B | 49.4% | 45.6% |

This near-random performance provides **maximum differentiation potential** for SOTA comparison:

1. **If SOTA achieves significantly higher accuracy (e.g., 70%+)**:
   - Suggests training data exposure (VulTrial dataset contamination)
   - Or superior security reasoning capability
   - Opens hypothesis for further investigation

2. **If SOTA also achieves ~50% accuracy**:
   - Confirms inherent task difficulty
   - Validates our findings across model families
   - Suggests fundamental limitations in LLM vulnerability detection

### Why Single-Agent (SA)?

SA is the optimal design for vulnerability detection, outperforming multi-agent architectures:

| Design | Mean Accuracy | Mean F1 |
|--------|---------------|---------|
| SA | 52.7% | 49.1% |
| DA | 50.3% | 57.6% |
| MA | 49.0% | 34.1% |

Using SA ensures:
- **Clean baseline comparison** without confounding factors from agent orchestration
- **Isolates model capability** rather than architectural effects
- **Matches optimal configuration** for this specific task

### Comparison with Other Tasks

| Task | Mean Accuracy/Pass@1 | Best Design | SOTA Value |
|------|---------------------|-------------|------------|
| Code Generation | 95-98% | MA | Low (ceiling effect) |
| Vulnerability Detection | ~50% | SA | **High (random baseline)** |
| Log Analysis | ~30% | MA | Medium (but MA optimal) |

## Experimental Design

### Models

| Model | Type | API | Rationale |
|-------|------|-----|-----------|
| Claude Sonnet 4.5 | Non-reasoning | OpenRouter | Baseline SOTA (comparable to Qwen3 Instruct) |
| Claude Opus 4.5 | Extended thinking | OpenRouter | Reasoning SOTA (comparable to Qwen3 Thinking) |

### Experiment Matrix

| Model | Design | Prompting | Status |
|-------|--------|-----------|--------|
| Sonnet 4.5 | SA | zero-shot | 🔲 Pending |
| Sonnet 4.5 | SA | few-shot | 🔲 Pending |
| Opus 4.5 | SA | zero-shot | 🔲 Pending |
| Opus 4.5 | SA | few-shot | 🔲 Pending |

**Total: 4 experiments** (2 models × 2 prompting strategies)

### Dataset

- **VulTrial Dataset**: 386 C/C++ functions with vulnerability labels
- Same dataset used for all previous vulnerability detection experiments
- Binary classification: vulnerable (1) vs non-vulnerable (0)

### Metrics

- **Accuracy**: Overall classification correctness
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **F1 Score**: Harmonic mean of precision and recall
- **Emissions**: Carbon footprint via CodeCarbon (if applicable)

## Implementation Notes

### OpenRouter Configuration

```bash
# Environment variables
OPENROUTER_API_KEY=<your-key>
OPENROUTER_API_BASE=https://openrouter.ai/api/v1

# Model IDs
SONNET_MODEL=anthropic/claude-sonnet-4
OPUS_MODEL=anthropic/claude-opus-4
```

### Expected Outcomes

1. **Baseline establishment**: How do frontier models compare on security tasks?
2. **Reasoning effect**: Does extended thinking (Opus) improve vulnerability detection?
3. **Cross-family validation**: Do findings from Qwen3/Nemotron generalize?

---

**Created**: 2026-01-24
**Branch**: `sota-comparison`
**Status**: Setup in progress
