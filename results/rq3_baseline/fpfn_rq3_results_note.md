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

## 5. Breakdown by model and mode (LLM judge, all 480)

Blind-judge mean scores split by model × mode:

| model | mode | completeness | clarity | actionability | informativeness |
|-------|------|:---:|:---:|:---:|:---:|
| Nemotron-Super-49B | instruct | 2.74 | 3.86 | 2.38 | 2.47 |
| Nemotron-Super-49B | thinking | 3.20 | 4.22 | 2.43 | 3.04 |
| Qwen3-30B (Instruct model) | instruct | 3.42 | 4.26 | 2.64 | 3.17 |
| Qwen3-30B (Thinking model) | thinking | 3.38 | 4.36 | 2.67 | 3.26 |

## 6. The thinking-mode benefit is model-specific (Nemotron only)

Section 2's thinking > instruct result, re-run **per family** (paired per-snippet Δ =
thinking − instruct, Wilcoxon):

| Dimension | Nemotron Δ | p | Qwen3-30B Δ | p |
|-----------|:---:|:---:|:---:|:---:|
| completeness | **+0.46** | <0.0001 | −0.04 | 0.48 |
| clarity | **+0.37** | <0.0001 | +0.10 | 0.26 |
| informativeness | **+0.57** | <0.0001 | +0.09 | 0.21 |
| actionability | +0.05 | 0.54 (n.s.) | +0.03 | 0.64 |

The aggregate "thinking helps" effect is driven **entirely by Nemotron**. Qwen3-30B
shows no significant thinking–instruct difference on any dimension — the Qwen
*Instruct* model already scores as high as the Qwen *Thinking* model. (For Nemotron
the two modes are one checkpoint toggled; for Qwen they are two separate checkpoints.)

## 7. Human↔LLM agreement, split by mode (Nemotron, correct join)

The Section 4 agreement re-run per mode (join via `fpfn_human_frame_120.csv`:
human local `sample_id` → `entry_id` + `mode` → judge):

| Dimension | instruct ρ (n=60) | thinking ρ (n=60) | pooled ρ (n=120) |
|-----------|:---:|:---:|:---:|
| completeness | **+0.346** (p=0.007) | −0.017 (n.s.) | +0.105 |
| clarity | +0.200 (n.s.) | −0.131 (n.s.) | +0.076 |
| actionability | **+0.843** (p<0.001) | **+0.716** (p<0.001) | +0.777 |
| informativeness | **+0.327** (p=0.011) | +0.023 (n.s.) | +0.262 |

**Actionability agreement is strong in both modes** (ρ ≈ 0.72–0.84). Completeness and
informativeness agreement is real on **instruct** but collapses to ~0 on **thinking**
— i.e. the pooled comp/inf correlations are carried by the instruct half. Adjacent
(±1) agreement stays 62–95% throughout.

## 8. Caveat: the judge amplifies a thinking gap the humans barely register

Nemotron means, human (HSv2+Shane consensus) vs blind judge, by mode:

| | comp | clar | act | inf |
|---|:---:|:---:|:---:|:---:|
| **Human** instruct | 3.60 | 3.51 | 2.80 | 3.12 |
| **Human** thinking | 3.53 | 3.64 | 2.64 | 3.42 |
| **Judge** instruct | 2.63 | 3.83 | 2.38 | 2.38 |
| **Judge** thinking | 3.17 | 4.20 | 2.48 | 2.98 |

Humans rate Nemotron thinking ≈ instruct (Δ within ~0.1–0.3, no clear direction),
whereas the judge sees a large thinking-mode jump (comp +0.54, clar +0.37, inf +0.60).
So the thinking > instruct effect (Section 2/6) is partly a **judge behaviour** — it is
model-specific (Nemotron) and larger under the judge than the human means support.
This should temper how strongly the thinking-vs-instruct claim leans on the judge.

## 9. Dimension ordering is robust to the breakdown

The Section 1 ordering **holds in every cell**:

- **LLM judge — all four model×mode cells**: `clarity > completeness > informativeness > actionability` (strict).
- **Human (Nemotron), by mode**: same, with **clarity ↔ completeness swapping within ~0.1**
  (instruct: comp 3.60 ≥ clar 3.51; thinking: clar 3.64 ≥ comp 3.53) — the "within noise"
  top pair already noted in Section 1. **Informativeness is third and actionability is
  last in every cell.**

The ordering conclusion is therefore not an artifact of pooling models/modes.

## Files

- Human ratings: `fpfn_paired120_rater_HSv2.xlsx`, `fpfn_paired120_rater_Shane.xlsx`
- LLM judge (primary, blind): `fpfn_llm_judged_opus-4-6_blind.csv`
- LLM judge (robustness, unblinded): `fpfn_llm_judged_opus-4-6.csv`
- Frame + unblinding key (full 480): `fpfn_sample_frame.csv`
- **Human-frame mapping (the correct join key)**: `fpfn_human_frame_120.csv` — maps the
  human rater sheets' local `sample_id` (1–120) to `entry_id` + `mode`; join humans →
  this → judge on `entry_id` + `mode` (Nemotron). The rater sheets' `sample_id` is a local
  index and does **not** equal the judge's global `sample_id`.
- By-model/by-mode breakdown (Sections 5–9, tidy): `fpfn_by_model_mode_breakdown.csv`
- Reliability + ordering: `fpfn_paired120_IRR_summary.md`
