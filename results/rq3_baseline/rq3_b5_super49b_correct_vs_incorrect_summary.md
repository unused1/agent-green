# RQ3 — Correct vs Incorrect Explanation Quality — Nemotron-Super-49B

Source: super49b_870_llm_judged_opus-4-6_zeroshot.csv (462 rows), super49b_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv (30 rows)

Judge: Claude Opus 4.6 zero-shot. Group split shown overall and per response mode.


## overall

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 462 | 30 | 3.197 ± 1.045 | 2.300 ± 0.651 | 0.897 | 0.875 | 0.749 | 10383.000 | 0.000 |
| clarity | 462 | 30 | 4.063 ± 0.717 | 3.867 ± 0.346 | 0.196 | 0.280 | 0.593 | 8225.000 | 0.050 |
| actionability | 462 | 30 | 2.268 ± 0.889 | 1.933 ± 0.944 | 0.335 | 0.375 | 0.596 | 8262.000 | 0.053 |
| informativeness | 462 | 30 | 2.874 ± 0.937 | 2.100 ± 0.548 | 0.774 | 0.843 | 0.739 | 10246.500 | 0.000 |

## think

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 231 | 15 | 3.390 ± 1.121 | 2.200 ± 0.676 | 1.190 | 1.081 | 0.796 | 2759.000 | 0.000 |
| clarity | 231 | 15 | 4.260 ± 0.724 | 3.867 ± 0.352 | 0.393 | 0.556 | 0.683 | 2366.500 | 0.008 |
| actionability | 231 | 15 | 2.216 ± 0.963 | 1.933 ± 0.961 | 0.283 | 0.294 | 0.573 | 1986.500 | 0.317 |
| informativeness | 231 | 15 | 3.165 ± 1.025 | 1.933 ± 0.458 | 1.231 | 1.229 | 0.830 | 2876.000 | 0.000 |

## inst

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 231 | 15 | 3.004 ± 0.925 | 2.400 ± 0.632 | 0.604 | 0.663 | 0.693 | 2401.500 | 0.008 |
| clarity | 231 | 15 | 3.866 ± 0.656 | 3.867 ± 0.352 | -0.001 | -0.001 | 0.504 | 1746.000 | 0.953 |
| actionability | 231 | 15 | 2.320 ± 0.808 | 1.933 ± 0.961 | 0.387 | 0.473 | 0.626 | 2170.500 | 0.053 |
| informativeness | 231 | 15 | 2.584 ± 0.735 | 2.267 ± 0.594 | 0.318 | 0.437 | 0.622 | 2153.500 | 0.086 |


**Effect size interpretation (Cohen's d, absolute):** ≈0.2 small, ≈0.5 medium, ≈0.8 large.

**CLES** is the probability that a randomly drawn correct-sample score exceeds a randomly drawn incorrect-sample score (0.5 = no preference).
