# RQ3 paired-120 (FP/FN set) — inter-rater reliability summary

Two raters (HS, Shane) independently scored 120 explanations on four dimensions
(completeness, clarity, actionability, informativeness), each on a 1–5 ordinal
scale. This note summarises agreement, for discussion before we finalise the
ratings.

## Krippendorff's alpha (ordinal)

| Dimension       | Krippendorff α | Adjacent (±1) agreement | Exact agreement |
|-----------------|:--------------:|:-----------------------:|:---------------:|
| actionability   | **0.594**      | 92.5%                   | 55.8%           |
| clarity         | 0.213          | 90.0%                   | 38.3%           |
| informativeness | 0.041          | 81.7%                   | 35.0%           |
| completeness    | 0.040          | 80.0%                   | 31.7%           |
| pooled          | 0.368          | —                       | —               |

Reference thresholds (Krippendorff): α ≥ 0.80 reliable · 0.667–0.80 tentative ·
< 0.667 unreliable.

## What the numbers say

- **Adjacent (±1) agreement is high everywhere (80–92%)** — the two raters are
  rarely more than one point apart, i.e. we largely agree on the *ordering* of
  explanation quality.
- **But chance-corrected agreement (α) is low for three of four dimensions.**
  The cause is not carelessness — the notes are thorough and the ±1 closeness is
  strong. It is an **anchor-usage difference**: scores cluster in a narrow 3–4
  band, and the top anchor "5" is used at very different rates between raters
  (mean completeness HS 3.85 vs Shane 3.42). When almost all scores sit in a
  narrow band, α collapses even though the raters are close.
- **Actionability agrees best (α = 0.59)** because both raters use its lower end
  consistently.
- **Completeness and informativeness need the most alignment** — they account
  for 46 of the 67 dimension-level disagreements (≥2-point gaps).

## Suggested next step

A short **calibration + adjudication** pass:
1. Align on anchor definitions — in particular what earns a 4 vs a 5, and when a
   1 or 2 applies.
2. Reconcile the flagged rows to a consensus score. A worksheet listing the 46
   rows with a ≥2-point gap on any dimension (both raters' scores + notes +
   the response text, disagreeing cells highlighted) is provided as
   `fpfn_paired120_adjudication.xlsx`.

Consensus scores from this pass can then be used for the headline analysis, with
α and adjacent-agreement reported transparently.
