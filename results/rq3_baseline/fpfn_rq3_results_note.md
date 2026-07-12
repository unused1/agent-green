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

**Blind judge (all 480).** Scores are statistically indistinguishable between
correct (TP/TN, n=240) and incorrect (FP/FN, n=240) predictions on every dimension
(Mann–Whitney U, two-sided):

| dimension | correct | incorrect | Δ | p |
|-----------|:---:|:---:|:---:|:---:|
| completeness | 3.20 | 3.16 | +0.04 | 0.52 |
| clarity | 4.19 | 4.16 | +0.03 | 0.69 |
| actionability | 2.53 | 2.53 | −0.00 | 0.79 |
| informativeness | 2.98 | 2.98 | +0.00 | 0.98 |

The null holds within each family too (Nemotron and Qwen separately, all p > 0.4).
A fluent explanation for a wrong prediction reads as good as one for a correct
prediction when the evaluator cannot see the label — the explanation does not reveal
its own incorrectness. (The *unblinded* judge produced a large spurious gap, e.g.
completeness 3.51 vs 2.23, but that was an artifact of it seeing the ground truth,
not a property of the explanations.)

**Human raters (blinded, Nemotron paired-120, HSv2+Shane consensus).** The humans —
also blinded — are broadly consistent; **no dimension survives multiple-comparison
correction** (Bonferroni α = 0.05/4 = 0.0125):

| dimension | correct (n=60) | incorrect (n=60) | Δ | p |
|-----------|:---:|:---:|:---:|:---:|
| completeness | 3.47 | 3.67 | −0.20 | 0.098 |
| clarity | 3.69 | 3.46 | +0.23 | 0.014 |
| actionability | 2.63 | 2.81 | −0.17 | 0.21 |
| informativeness | 3.26 | 3.29 | −0.03 | 0.94 |

The one hint is **clarity** (correct-prediction explanations rated a touch clearer,
p = 0.014) — but it does *not* pass Bonferroni (0.014 > 0.0125), and completeness
trends the *opposite* way (n.s.). So the human data agrees with the judge in
substance: explanation quality carries at most a faint, non-robust signal about a
prediction's correctness — even blinded human readers cannot reliably tell a correct
explanation from an incorrect one. (Tests use `mannwhitneyu`; see
`fpfn_by_model_mode_breakdown.csv` companion analysis.)

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

## 10. Comparison with the submitted paper and rebuttal commitments

This note's corrected, blinded 480-frame analysis **confirms** some submitted/rebuttal
points, **softens** others, and **contradicts** one. Flagged for the revision.

**Confirms:**
- Dimension ordering `clarity > completeness > informativeness > actionability`
  (RQ3.tex) — §9 shows it holds in *every* model×mode cell.
- Thinking > instruct on completeness / clarity / informativeness, actionability weak
  (RQ3.tex) — §2 reproduces the direction on the blind frame.
- Rebuttal **RA3** (thinking gains are length-mediated, *not* length-independent) —
  §6 and §8 reinforce and extend it: the advantage is also **model-specific**
  (Nemotron only) and **larger under the judge than the human means support**.

**Softens / contrasts:**
- **Human↔LLM agreement.** RQ3.tex reports ρ = 0.56–0.75 across *all* dimensions
  (adjacent 90–97%) on the 30-instance manual sample, framed as validating the judge.
  On the corrected, blinded FP/FN frame (§4, n=120, correct join) only **actionability**
  is strong (ρ=0.777); completeness (0.105), clarity (0.076), and informativeness
  (0.262) are weak (restricted-range). The blanket "moderate-to-strong agreement" should
  be narrowed: the judge tracks humans on **actionability and aggregate ordering**, not
  per-item on the other three dimensions.
- **Cross-model robustness.** The submitted claim is "robust across evaluators," and
  Qwen3-30B was added to confirm generalizability. §6 shows the thinking-explanation
  advantage is **absent for Qwen** (no significant thinking–instruct difference on any
  dimension) — it is a Nemotron phenomenon — and §8 shows the judge amplifies a gap the
  Nemotron humans barely register. So Qwen does not corroborate the robustness claim.

**Contradicts — needs reconciliation before integration:**
- **FP/FN "incorrect explanations are worse" (rebuttal RA4/RA5).** The rebuttal
  committed to reporting that incorrect-prediction explanations score significantly
  lower — completeness **d=0.81** (p<0.001), clarity d=0.33 (p=0.029), informativeness
  **d=0.81** (p<0.001), actionability n.s. — from a 15-snippet / 30-explanation
  Super-49B SA analysis. The corrected, blinded Item-8 frame (§3; 480-row judge + 120
  blinded humans) finds **no significant correct-vs-incorrect difference on any
  dimension** (judge all p>0.5; no human dimension survives Bonferroni). The rebuttal's
  effect size (d≈0.8 on completeness/informativeness) coincides exactly with this note's
  **unblinded** judge (completeness 3.51 vs 2.23) — indicating RA4/RA5 is an
  **unblinding artifact**: the evaluator scores incorrect explanations lower because it
  can see the label, not because the explanations are worse. Under blind evaluation
  (matching the blinded human raters — the methodologically correct setup) the gap
  disappears. **Suggested reframing for RA4/RA5:** "Under blind evaluation, explanation
  quality does not differ between correct and incorrect predictions; the apparent gap
  arises only when the evaluator is shown the ground-truth label — itself a reason to
  evaluate explanations blind." (The rebuttal's 15-snippet set is also much smaller and
  restricted to both-modes-misclassified cases; the 480 frame supersedes it.)

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
