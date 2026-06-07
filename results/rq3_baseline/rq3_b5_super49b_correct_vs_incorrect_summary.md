# RQ3 — Correct vs Incorrect Explanation Quality — Nemotron-Super-49B

Source: super49b_870_llm_judged_opus-4-6_zeroshot.csv (462 rows), super49b_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv (30 rows)

Judge: Claude Opus 4.6 zero-shot. Group split shown overall and per response mode.


## overall

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 462 | 30 | 3.197 ± 1.045 | 2.367 ± 0.765 | 0.830 | 0.806 | 0.728 | 10094.500 | 0.000 |
| clarity | 462 | 30 | 4.063 ± 0.717 | 3.833 ± 0.461 | 0.229 | 0.326 | 0.604 | 8371.500 | 0.029 |
| actionability | 462 | 30 | 2.268 ± 0.889 | 2.000 ± 0.983 | 0.268 | 0.300 | 0.572 | 7921.000 | 0.151 |
| informativeness | 462 | 30 | 2.874 ± 0.937 | 2.133 ± 0.571 | 0.741 | 0.806 | 0.728 | 10092.000 | 0.000 |

## think

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 231 | 15 | 3.390 ± 1.121 | 2.333 ± 0.724 | 1.056 | 0.959 | 0.775 | 2685.000 | 0.000 |
| clarity | 231 | 15 | 4.260 ± 0.724 | 3.867 ± 0.352 | 0.393 | 0.556 | 0.683 | 2366.500 | 0.008 |
| actionability | 231 | 15 | 2.216 ± 0.963 | 2.000 ± 1.000 | 0.216 | 0.224 | 0.552 | 1913.500 | 0.476 |
| informativeness | 231 | 15 | 3.165 ± 1.025 | 2.000 ± 0.378 | 1.165 | 1.165 | 0.820 | 2842.500 | 0.000 |

## inst

| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |
|---|---|---|---|---|---|---|---|---|---|
| completeness | 231 | 15 | 3.004 ± 0.925 | 2.400 ± 0.828 | 0.604 | 0.657 | 0.681 | 2358.000 | 0.014 |
| clarity | 231 | 15 | 3.866 ± 0.656 | 3.800 ± 0.561 | 0.066 | 0.101 | 0.536 | 1857.500 | 0.578 |
| actionability | 231 | 15 | 2.320 ± 0.808 | 2.000 ± 1.000 | 0.320 | 0.390 | 0.598 | 2073.000 | 0.134 |
| informativeness | 231 | 15 | 2.584 ± 0.735 | 2.267 ± 0.704 | 0.318 | 0.434 | 0.608 | 2106.000 | 0.127 |


**Effect size interpretation (Cohen's d, absolute):** ≈0.2 small, ≈0.5 medium, ≈0.8 large.

**CLES** is the probability that a randomly drawn correct-sample score exceeds a randomly drawn incorrect-sample score (0.5 = no preference).
