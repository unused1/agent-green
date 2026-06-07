# RQ3 — Correct vs Incorrect Explanation Quality — Qwen3-30B-A3B

Source: qwen30b_870_llm_judged_opus-4-6_zeroshot.csv (642 rows), qwen30b_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv (30 rows)

Judge: Claude Opus 4.6 zero-shot. Group split shown overall and per response mode.


## overall

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 642 | 30 | 3.850 ± 1.083 | 2.433 ± 0.858 | 1.417 | 1.319 | 0.830 | 15985.500 | 0.000 |
| clarity | 642 | 30 | 4.495 ± 0.739 | 4.033 ± 0.414 | 0.462 | 0.634 | 0.732 | 14100.000 | 0.000 |
| actionability | 642 | 30 | 2.148 ± 1.059 | 2.167 ± 1.206 | -0.019 | -0.018 | 0.505 | 9733.000 | 0.918 |
| informativeness | 642 | 30 | 3.578 ± 1.020 | 2.100 ± 0.662 | 1.478 | 1.468 | 0.863 | 16621.500 | 0.000 |

## think

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 321 | 15 | 3.791 ± 1.077 | 2.267 ± 0.799 | 1.525 | 1.429 | 0.855 | 4117.000 | 0.000 |
| clarity | 321 | 15 | 4.523 ± 0.671 | 3.933 ± 0.258 | 0.590 | 0.895 | 0.788 | 3792.000 | 0.000 |
| actionability | 321 | 15 | 2.187 ± 1.102 | 2.067 ± 1.100 | 0.120 | 0.109 | 0.527 | 2538.500 | 0.711 |
| informativeness | 321 | 15 | 3.573 ± 1.056 | 1.867 ± 0.640 | 1.707 | 1.639 | 0.892 | 4294.000 | 0.000 |

## inst

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 321 | 15 | 3.910 ± 1.087 | 2.600 ± 0.910 | 1.310 | 1.212 | 0.809 | 3894.000 | 0.000 |
| clarity | 321 | 15 | 4.467 ± 0.802 | 4.133 ± 0.516 | 0.334 | 0.422 | 0.679 | 3270.000 | 0.007 |
| actionability | 321 | 15 | 2.109 ± 1.014 | 2.267 ± 1.335 | -0.158 | -0.153 | 0.484 | 2331.000 | 0.828 |
| informativeness | 321 | 15 | 3.583 ± 0.984 | 2.333 ± 0.617 | 1.249 | 1.286 | 0.836 | 4026.000 | 0.000 |


**Effect size interpretation (Cohen's d, absolute):** ≈0.2 small, ≈0.5 medium, ≈0.8 large.

**CLES** is the probability that a randomly drawn correct-sample score exceeds a randomly drawn incorrect-sample score (0.5 = no preference).
