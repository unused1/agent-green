# RQ3 — Length Confound Analysis (Reviewer A, point 3)

Source: `super49b_870_llm_judged_opus-4-6_zeroshot.csv` (n=462). Length is `len(reasoning)` measured three ways: characters, whitespace-split tokens, and BPE tokens using the Nemotron Llama-3.1 tokenizer (matching the inference model). Judge: Claude Opus 4.6 zero-shot.


## Response length, descriptive statistics

BPE counts use the Nemotron Llama-3.1 tokenizer (matching the inference model family).

| Mode | n | mean_chars | median_chars | mean_split | median_split | mean_bpe | median_bpe |
|---|---|---|---|---|---|---|---|
| think | 231 | 15211 | 14361 | 2481 | 2309 | 3554 | 3326 |
| inst | 231 | 2909 | 2858 | 403 | 399 | 661 | 639 |

**Rank correlation between length units** (Spearman ρ across all 462 rows):
chars↔split=0.993, chars↔bpe=0.989, split↔bpe=0.987 — near-perfect monotonic alignment confirms the choice of length unit does not materially affect Spearman-based results.


## Table 1 — Score ↔ Length correlation

Spearman ρ is the primary statistic (rank-based, robust to skew). Pearson r reported for transparency.

| Split | Length unit | Metric | n | Spearman ρ | p | Pearson r | p |
|---|---|---|---|---|---|---|---|
| overall | chars | completeness | 462 | 0.256 | <0.001 | 0.196 | <0.001 |
| overall | chars | clarity | 462 | 0.362 | <0.001 | 0.264 | <0.001 |
| overall | chars | actionability | 462 | -0.033 | 0.478 | -0.098 | 0.035 |
| overall | chars | informativeness | 462 | 0.365 | <0.001 | 0.308 | <0.001 |
| overall | tokens | completeness | 462 | 0.250 | <0.001 | 0.193 | <0.001 |
| overall | tokens | clarity | 462 | 0.359 | <0.001 | 0.260 | <0.001 |
| overall | tokens | actionability | 462 | -0.033 | 0.476 | -0.096 | 0.038 |
| overall | tokens | informativeness | 462 | 0.362 | <0.001 | 0.306 | <0.001 |
| overall | bpe | completeness | 462 | 0.258 | <0.001 | 0.193 | <0.001 |
| overall | bpe | clarity | 462 | 0.370 | <0.001 | 0.262 | <0.001 |
| overall | bpe | actionability | 462 | -0.008 | 0.862 | -0.087 | 0.061 |
| overall | bpe | informativeness | 462 | 0.372 | <0.001 | 0.306 | <0.001 |
| think | chars | completeness | 231 | 0.105 | 0.112 | 0.105 | 0.110 |
| think | chars | clarity | 231 | 0.049 | 0.458 | 0.097 | 0.141 |
| think | chars | actionability | 231 | -0.108 | 0.101 | -0.121 | 0.065 |
| think | chars | informativeness | 231 | 0.151 | 0.021 | 0.139 | 0.034 |
| think | tokens | completeness | 231 | 0.107 | 0.106 | 0.102 | 0.122 |
| think | tokens | clarity | 231 | 0.054 | 0.416 | 0.093 | 0.157 |
| think | tokens | actionability | 231 | -0.091 | 0.168 | -0.114 | 0.084 |
| think | tokens | informativeness | 231 | 0.157 | 0.017 | 0.137 | 0.037 |
| think | bpe | completeness | 231 | 0.109 | 0.098 | 0.100 | 0.128 |
| think | bpe | clarity | 231 | 0.052 | 0.434 | 0.094 | 0.153 |
| think | bpe | actionability | 231 | -0.085 | 0.196 | -0.105 | 0.113 |
| think | bpe | informativeness | 231 | 0.160 | 0.015 | 0.137 | 0.038 |
| inst | chars | completeness | 231 | 0.107 | 0.106 | 0.213 | 0.001 |
| inst | chars | clarity | 231 | 0.242 | <0.001 | 0.466 | <0.001 |
| inst | chars | actionability | 231 | 0.187 | 0.004 | 0.236 | <0.001 |
| inst | chars | informativeness | 231 | 0.170 | 0.009 | 0.290 | <0.001 |
| inst | tokens | completeness | 231 | 0.087 | 0.187 | 0.194 | 0.003 |
| inst | tokens | clarity | 231 | 0.231 | <0.001 | 0.443 | <0.001 |
| inst | tokens | actionability | 231 | 0.166 | 0.011 | 0.197 | 0.003 |
| inst | tokens | informativeness | 231 | 0.162 | 0.014 | 0.270 | <0.001 |
| inst | bpe | completeness | 231 | 0.123 | 0.062 | 0.227 | <0.001 |
| inst | bpe | clarity | 231 | 0.285 | <0.001 | 0.490 | <0.001 |
| inst | bpe | actionability | 231 | 0.275 | <0.001 | 0.287 | <0.001 |
| inst | bpe | informativeness | 231 | 0.205 | 0.002 | 0.325 | <0.001 |

## Table 2 — Thinking-vs-instruct on all four metrics, controlling for response length

Mode coded as think=1, inst=0. Raw Spearman ρ is mode→score without controls; partial Spearman ρ is the same after partialling out length. A partial coefficient close to the raw value indicates length is not a dominant confound.

| Metric | Length unit | Raw Spearman ρ | Raw p | Partial Spearman ρ | Partial p | 95% CI |
|---|---|---|---|---|---|---|
| completeness | chars | 0.210 | <0.001 | -0.009 | 0.847 | [-0.100, 0.080] |
| completeness | tokens | 0.210 | <0.001 | -0.000 | 0.994 | [-0.090, 0.090] |
| completeness | bpe | 0.210 | <0.001 | -0.013 | 0.777 | [-0.100, 0.080] |
| clarity | chars | 0.311 | <0.001 | 0.016 | 0.733 | [-0.080, 0.110] |
| clarity | tokens | 0.311 | <0.001 | 0.019 | 0.685 | [-0.070, 0.110] |
| clarity | bpe | 0.311 | <0.001 | 0.000 | 0.992 | [-0.090, 0.090] |
| actionability | chars | -0.070 | 0.132 | -0.078 | 0.096 | [-0.170, 0.010] |
| actionability | tokens | -0.070 | 0.132 | -0.078 | 0.095 | [-0.170, 0.010] |
| actionability | bpe | -0.070 | 0.132 | -0.117 | 0.012 | [-0.210, -0.030] |
| informativeness | chars | 0.312 | <0.001 | 0.012 | 0.790 | [-0.080, 0.100] |
| informativeness | tokens | 0.312 | <0.001 | 0.015 | 0.744 | [-0.080, 0.110] |
| informativeness | bpe | 0.312 | <0.001 | -0.001 | 0.987 | [-0.090, 0.090] |

**Interpretation guide:** |ρ| ≈ 0.1 small, ≈ 0.3 moderate, ≈ 0.5 large (Cohen). If partial ρ shrinks substantially toward zero relative to raw ρ, length explains a large share of the mode effect; if it remains comparable, the mode advantage is not driven by length.
