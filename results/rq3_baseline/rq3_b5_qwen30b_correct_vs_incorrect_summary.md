# RQ3 — Correct vs Incorrect Explanation Quality — Qwen3-30B-A3B

Source: qwen30b_870_llm_judged_opus-4-6_zeroshot.csv (642 rows), qwen30b_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv (30 rows)

Judge: Claude Opus 4.6 zero-shot. Group split shown overall and per response mode.


## overall

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 642 | 30 | 3.850 ± 1.083 | 2.367 ± 0.890 | 1.484 | 1.380 | 0.837 | 16129.500 | 0.000 |
| clarity | 642 | 30 | 4.495 ± 0.739 | 4.000 ± 0.455 | 0.495 | 0.679 | 0.738 | 14221.500 | 0.000 |
| actionability | 642 | 30 | 2.148 ± 1.059 | 2.100 ± 1.155 | 0.048 | 0.045 | 0.519 | 10001.500 | 0.709 |
| informativeness | 642 | 30 | 3.578 ± 1.020 | 2.067 ± 0.691 | 1.511 | 1.500 | 0.866 | 16682.000 | 0.000 |

## think

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 321 | 15 | 3.791 ± 1.077 | 2.133 ± 0.834 | 1.658 | 1.553 | 0.870 | 4191.000 | 0.000 |
| clarity | 321 | 15 | 4.523 ± 0.671 | 4.000 ± 0.378 | 0.523 | 0.791 | 0.755 | 3637.500 | 0.000 |
| actionability | 321 | 15 | 2.187 ± 1.102 | 2.000 ± 1.069 | 0.187 | 0.170 | 0.545 | 2623.000 | 0.542 |
| informativeness | 321 | 15 | 3.573 ± 1.056 | 1.800 ± 0.561 | 1.773 | 1.706 | 0.905 | 4356.000 | 0.000 |

## inst

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 321 | 15 | 3.910 ± 1.087 | 2.600 ± 0.910 | 1.310 | 1.212 | 0.809 | 3894.000 | 0.000 |
| clarity | 321 | 15 | 4.467 ± 0.802 | 4.000 ± 0.535 | 0.467 | 0.589 | 0.721 | 3473.500 | 0.001 |
| actionability | 321 | 15 | 2.109 ± 1.014 | 2.200 ± 1.265 | -0.091 | -0.089 | 0.494 | 2378.000 | 0.934 |
| informativeness | 321 | 15 | 3.583 ± 0.984 | 2.333 ± 0.724 | 1.249 | 1.281 | 0.830 | 3994.500 | 0.000 |


**Effect size interpretation (Cohen's d, absolute):** ≈0.2 small, ≈0.5 medium, ≈0.8 large.

**CLES** is the probability that a randomly drawn correct-sample score exceeds a randomly drawn incorrect-sample score (0.5 = no preference).
