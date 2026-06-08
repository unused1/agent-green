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
| completeness | 3.197 | 2.300 | 0.875 | 0.000 | 3.850 | 2.367 | 1.380 | 0.000 |
| clarity | 4.063 | 3.867 | 0.280 | 0.050 | 4.495 | 4.000 | 0.679 | 0.000 |
| actionability | 2.268 | 1.933 | 0.375 | 0.053 | 2.148 | 2.100 | 0.045 | 0.709 |
| informativeness | 2.874 | 2.100 | 0.843 | 0.000 | 3.578 | 2.067 | 1.500 | 0.000 |

## Thinking mode only

| Metric | Nemotron-Super-49B mean_corr | Nemotron-Super-49B mean_incorr | Nemotron-Super-49B Cohen's d | Nemotron-Super-49B p | Qwen3-30B-A3B mean_corr | Qwen3-30B-A3B mean_incorr | Qwen3-30B-A3B Cohen's d | Qwen3-30B-A3B p |
|---|---|---|---|---|---|---|---|---|
| completeness | 3.390 | 2.200 | 1.081 | 0.000 | 3.791 | 2.133 | 1.553 | 0.000 |
| clarity | 4.260 | 3.867 | 0.556 | 0.008 | 4.523 | 4.000 | 0.791 | 0.000 |
| actionability | 2.216 | 1.933 | 0.294 | 0.317 | 2.187 | 2.000 | 0.170 | 0.542 |
| informativeness | 3.165 | 1.933 | 1.229 | 0.000 | 3.573 | 1.800 | 1.706 | 0.000 |

## Instruct mode only

| Metric | Nemotron-Super-49B mean_corr | Nemotron-Super-49B mean_incorr | Nemotron-Super-49B Cohen's d | Nemotron-Super-49B p | Qwen3-30B-A3B mean_corr | Qwen3-30B-A3B mean_incorr | Qwen3-30B-A3B Cohen's d | Qwen3-30B-A3B p |
|---|---|---|---|---|---|---|---|---|
| completeness | 3.004 | 2.400 | 0.663 | 0.008 | 3.910 | 2.600 | 1.212 | 0.000 |
| clarity | 3.866 | 3.867 | -0.001 | 0.953 | 4.467 | 4.000 | 0.589 | 0.001 |
| actionability | 2.320 | 1.933 | 0.473 | 0.053 | 2.109 | 2.200 | -0.089 | 0.934 |
| informativeness | 2.584 | 2.267 | 0.437 | 0.086 | 3.583 | 2.333 | 1.281 | 0.000 |

## Interpretation

- Consistent direction across models on a metric (same sign of Cohen's d, both p<0.05) means the finding *generalises* beyond Super-49B.

- Divergent direction or magnitude on a metric is informative on its own — it bounds which conclusions are model-specific.

- Effect size interpretation: |d| ≈ 0.2 small, 0.5 medium, 0.8 large.
