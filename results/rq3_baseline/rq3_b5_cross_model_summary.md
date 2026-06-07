# RQ3 — Cross-model Correct-vs-Incorrect Explanation Quality

Cross-model summary addressing Reviewer C #7 (RQ3 generalisability beyond Nemotron-Super-49B). Each row reports the correct-vs-incorrect comparison for one metric, side-by-side across the two models.

Judge: Claude Opus 4.6 zero-shot. Same incorrect-intersection methodology (15 snippets stratified 8 FP + 7 FN × {think, inst}, seed=42) applied to both models.


## Sample sizes

| Model | n_correct | n_incorrect |
|---|---|---|
| Nemotron-Super-49B | 462 | 30 |
| Qwen3-30B-A3B | 642 | 30 |

## Overall (both modes pooled)

| Metric | Nemotron-Super-49B mean_corr | Nemotron-Super-49B mean_incorr | Nemotron-Super-49B Cohen's d | Nemotron-Super-49B p | Qwen3-30B-A3B mean_corr | Qwen3-30B-A3B mean_incorr | Qwen3-30B-A3B Cohen's d | Qwen3-30B-A3B p |
|---|---|---|---|---|---|---|---|---|
| completeness | 3.197 | 2.367 | 0.806 | 0.000 | 3.850 | 2.433 | 1.319 | 0.000 |
| clarity | 4.063 | 3.833 | 0.326 | 0.029 | 4.495 | 4.033 | 0.634 | 0.000 |
| actionability | 2.268 | 2.000 | 0.300 | 0.151 | 2.148 | 2.167 | -0.018 | 0.918 |
| informativeness | 2.874 | 2.133 | 0.806 | 0.000 | 3.578 | 2.100 | 1.468 | 0.000 |

## Thinking mode only

| Metric | Nemotron-Super-49B mean_corr | Nemotron-Super-49B mean_incorr | Nemotron-Super-49B Cohen's d | Nemotron-Super-49B p | Qwen3-30B-A3B mean_corr | Qwen3-30B-A3B mean_incorr | Qwen3-30B-A3B Cohen's d | Qwen3-30B-A3B p |
|---|---|---|---|---|---|---|---|---|
| completeness | 3.390 | 2.333 | 0.959 | 0.000 | 3.791 | 2.267 | 1.429 | 0.000 |
| clarity | 4.260 | 3.867 | 0.556 | 0.008 | 4.523 | 3.933 | 0.895 | 0.000 |
| actionability | 2.216 | 2.000 | 0.224 | 0.476 | 2.187 | 2.067 | 0.109 | 0.711 |
| informativeness | 3.165 | 2.000 | 1.165 | 0.000 | 3.573 | 1.867 | 1.639 | 0.000 |

## Instruct mode only

| Metric | Nemotron-Super-49B mean_corr | Nemotron-Super-49B mean_incorr | Nemotron-Super-49B Cohen's d | Nemotron-Super-49B p | Qwen3-30B-A3B mean_corr | Qwen3-30B-A3B mean_incorr | Qwen3-30B-A3B Cohen's d | Qwen3-30B-A3B p |
|---|---|---|---|---|---|---|---|---|
| completeness | 3.004 | 2.400 | 0.657 | 0.014 | 3.910 | 2.600 | 1.212 | 0.000 |
| clarity | 3.866 | 3.800 | 0.101 | 0.578 | 4.467 | 4.133 | 0.422 | 0.007 |
| actionability | 2.320 | 2.000 | 0.390 | 0.134 | 2.109 | 2.267 | -0.153 | 0.828 |
| informativeness | 2.584 | 2.267 | 0.434 | 0.127 | 3.583 | 2.333 | 1.286 | 0.000 |

## Interpretation

- Consistent direction across models on a metric (same sign of Cohen's d, both p<0.05) means the finding *generalises* beyond Super-49B.

- Divergent direction or magnitude on a metric is informative on its own — it bounds which conclusions are model-specific.

- Effect size interpretation: |d| ≈ 0.2 small, 0.5 medium, 0.8 large.
