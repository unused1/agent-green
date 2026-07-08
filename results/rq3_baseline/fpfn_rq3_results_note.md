# RQ3 explanation quality on the FP/FN frame — results note

Scope: explanation-quality evaluation extended to all four confusion-matrix
strata (TP, TN, FP, FN), scaled to a 480-row frame (Nemotron-Super-49B +
Qwen3-30B, SA zero-shot, paired thinking↔instruct per snippet). Human ratings
(Hasan v2, Shane) cover the nested **paired-120** (Nemotron) subset; the
LLM-as-judge (Claude **Opus-4.6**) grades all 480. Four dimensions, 1–5 Likert:
completeness, clarity, actionability, informativeness.

## Method note — the judge is blinded to match the human raters

The FP/FN human raters were **blinded to prediction correctness** (the rater sheet
carries no ground-truth column; the instructions state "correctness is hidden").
The judge is therefore run in a **blind** configuration (source code + response
only; ground-truth label, CWE, and CVE description withheld), so it evaluates the
same information the humans did. An initial unblinded run — which fed the judge
the ground truth — was discarded for the human comparison because it materially
changed the scores (see the last section); it is retained only as a robustness
reference (`fpfn_llm_judged_opus-4-6.csv`). The primary results below use the
**blind** judge (`fpfn_llm_judged_opus-4-6_blind.csv`).

## 1. Dimension ordering (human and LLM agree)

Both the human consensus and the blind LLM judge rank the four dimensions
identically:

> **clarity > completeness > informativeness > actionability**

Actionability is clearly lowest for both; clarity and completeness sit at the top
(human consensus 3.58 vs 3.57 — within noise). This reproduces the submitted
finding and holds on the expanded FP/FN frame.

## 2. Thinking vs instruct (blind judge, 240 paired snippets)

Thinking-mode explanations are rated significantly higher on three of four
dimensions (paired Wilcoxon):

| Dimension | Δ (thinking − instruct) | p |
|-----------|:---:|:---:|
| informativeness | +0.33 | < 0.0001 |
| clarity | +0.23 | < 0.0001 |
| completeness | +0.21 | < 0.0001 |
| actionability | +0.04 | 0.44 (n.s.) |

This matches the submitted RQ3 result (thinking improves completeness, clarity,
informativeness; actionability is the weak exception).

## 3. Explanation quality is comparable on correct and incorrect predictions

Under the blind judge, explanation-quality scores are essentially **equal** for
correct (TP/TN) and incorrect (FP/FN) predictions:

| | completeness | clarity | actionability | informativeness |
|---|:---:|:---:|:---:|:---:|
| correct (TP/TN) | 3.20 | 4.19 | 2.53 | 2.98 |
| incorrect (FP/FN) | 3.16 | 4.16 | 2.53 | 2.98 |

A fluent explanation for a wrong prediction reads as good as one for a correct
prediction when the evaluator cannot see the label — the explanation does not
reveal its own incorrectness. (The unblinded judge produced a large apparent gap,
e.g. completeness 3.51 vs 2.23, but that was an artifact of it knowing the true
label; it is not a property of the explanations.)

## 4. Human ↔ LLM agreement (paired-120, blind judge)

| Dimension | Spearman ρ (human vs LLM) | p | Adjacent (±1) |
|-----------|:---:|:---:|:---:|
| actionability | **0.777** | < 0.001 | 92.5% |
| informativeness | 0.262 | 0.004 | 76.7% |
| completeness | 0.105 | 0.256 (n.s.) | 70.0% |
| clarity | 0.076 | 0.408 (n.s.) | 88.3% |

Agreement is strong on actionability and modest elsewhere. As with the
human-human reliability, the weak per-sample correlations are a restricted-range
effect (scores concentrate in a 3–4 band), while **adjacent agreement stays
70–93%** and the **aggregate ordering matches** (Section 1). The judge is
therefore used to support aggregate and ordering conclusions, not per-sample
scoring; the judge is also systematically a little stricter than the humans on
completeness/informativeness (bias −0.6 to −0.7) and slightly more generous on
clarity (+0.44).

## Files

- Human ratings: `fpfn_paired120_rater_HSv2.xlsx`, `fpfn_paired120_rater_Shane.xlsx`
- LLM judge (primary, blind): `fpfn_llm_judged_opus-4-6_blind.csv`
- LLM judge (robustness, unblinded): `fpfn_llm_judged_opus-4-6.csv`
- Frame + unblinding key: `fpfn_sample_frame.csv` (join to humans on `entry_id` + `mode`, Nemotron family)
- Reliability + ordering: `fpfn_paired120_IRR_summary.md`
