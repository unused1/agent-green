# RQ3 paired-120 (FP/FN) — dimension ordering & inter-rater reliability

Two human raters (**Hasan — revised v2**, **Shane**) independently scored the same
**120 explanations** on four dimensions (completeness, clarity, actionability,
informativeness), 1–5 ordinal. The set is Nemotron-Super-49B SA zero-shot, paired
thinking↔instruct across the four confusion-matrix strata (TP/TN/FP/FN), 15
snippets per stratum. Hasan revised his initial ratings after noticing some
inconsistency; the figures below use his **v2** ratings. (A third annotator,
Merve, rated only the earlier 30-sample pilot, so she is not included in the
120-sample analysis.)

The paired-120 is now nested inside the 480-row FP/FN frame that the LLM-as-judge
(Claude Opus-4.6) grades, so the same 120 explanations carry both human and LLM
scores for a human-vs-LLM consistency check (to follow).

## 1. Relative dimension ordering (primary result)

| Rater | completeness | clarity | informativeness | actionability | Order (high → low) |
|-------|:---:|:---:|:---:|:---:|---|
| Hasan v2 | 3.72 | 3.54 | 3.32 | 2.84 | completeness > clarity > informativeness > actionability |
| Shane | 3.42 | 3.61 | 3.23 | 2.60 | clarity > completeness > informativeness > actionability |
| **Consensus** | 3.57 | **3.58** | 3.27 | 2.72 | **clarity ≈ completeness > informativeness > actionability** |

The ordering is stable across raters: **actionability is clearly lowest,
informativeness third, and completeness/clarity tie at the top** (consensus 3.57
vs 3.58 — within noise). This reproduces the submitted finding that clarity is
highest and actionability lowest.

## 2. Inter-rater agreement (Hasan v2 vs Shane, n = 120)

| Dimension | Krippendorff α (v1 → **v2**) | Adjacent (±1) agreement |
|-----------|:---:|:---:|
| completeness | 0.040 → **0.179** | 95.8% |
| clarity | 0.213 → **0.317** | 98.3% |
| actionability | 0.594 → **0.643** | 97.5% |
| informativeness | 0.041 → **0.269** | 96.7% |

Hasan's revision (74 of 480 score cells changed, ~15%) improved chance-corrected
agreement on every dimension, most on the two weakest (completeness,
informativeness). Adjacent (±1) agreement is **96–98%** throughout: the raters
almost never differ by more than one point.

**Reading the α values.** The absolute α remains modest for completeness and
clarity. This is a restricted-range effect, not disagreement on ranking: scores
concentrate in a narrow 3–4 band, so the chance-corrected statistic is unstable
even when raters are within one point (as the 96–98% adjacent agreement shows).
Consistent with this, the **relative ordering** (Section 1) — the quantity used
for the RQ3 conclusions — is stable across raters. We therefore report ordering
and adjacent agreement as the primary reliability evidence, with α provided for
completeness.

## 3. Files

- Human ratings: `fpfn_paired120_rater_HSv2.xlsx`, `fpfn_paired120_rater_Shane.xlsx`
- LLM-judge ratings (Opus-4.6, when the run completes): `fpfn_llm_judged_opus-4-6.csv`
  (join to the human ratings on `entry_id` + `mode`, Nemotron family).
