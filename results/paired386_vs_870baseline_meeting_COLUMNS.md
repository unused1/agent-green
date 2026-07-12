# `paired386_vs_870baseline_meeting.csv` — column dictionary

One row per configuration. It combines the **submitted baselines** (SA / DA / MA /
NoAgent on VulTrial-870) with the revision's **Item 5** (budget-matched
single-agent) and **Item 9** (VulAgent-lite) runs on the pair-preserving
VulTrial-386. Built by `scripts/build_meeting_table.py`.

## Grouping / identity

| Column | Meaning |
|--------|---------|
| `block` | Row group: `baseline-870` (submitted designs, full 870 set), `baseline-386` (same designs re-scored on the 386 paired subset), `Item5` (budget-SA), `Item9` (VulAgent-lite). |
| `design` | Method: `NoAgent`, `SA`, `DA`, `MA-A(freeform)` = Option A, `MA-B(constrained)` = Option B, `budget-selfrev2/4`, `budget-bon4`, `vulagent-lite`. |
| `model`, `model_family` | Backbone LLM and family (`Qwen` / `Nemotron`). |
| `mode` | `instruct` or `thinking` (reasoning on). |
| `prompting` | `zero-shot` or `few-shot`. The freeform baselines (NoAgent/SA/DA/MA-A) and Item 5/9 are `zero-shot` only. The constrained MA (`MA-B(constrained)`) has BOTH — its `few-shot` rows are the newer Option-B few-shot cells across all 6 models (super49b/qwen30b/qwen4b/nano8b × instruct/thinking). |
| `sample_set` | Evaluation set the metrics are computed on: `VulTrial-870` (the canonical PrimeVul-Pair test split) or `VulTrial-386-paired` (193 balanced commit pairs). |
| `n_total` | Records evaluated. For `VulTrial-870` this is the **canonical 870**: reads dedup by idx to 868 unique, then the **2 inherent PrimeVul duplicate benigns** (idx 349259, 439495 — byte-identical rows present in the upstream `primevul_test_paired.jsonl`) are counted twice in the flat confusion matrix. A value of `869` means that run is missing one of the two dup idx. See `vuln_database/VulTrial_870_PROVENANCE.md`. P-C is unaffected (those idx sit in multi-vuln commits outside clean pairs). |
| `n_pairs` | Clean vulnerable/benign commit pairs used for `pc` (both members present, one of each label). |

## Detection metrics

| Column | Meaning |
|--------|---------|
| `f1_submitted` | F1 **as in the submitted paper** (parse `original_submitted`). Blank for `baseline-386` and new methods (no submitted counterpart). |
| `f1` | F1 under the **corrected parse** (current replication package). This is the headline F1. |
| `f1_delta` | `f1 - f1_submitted` (corrected − submitted). Large only for MA (the Option-A reparse); ~0 for SA/DA/NoAgent. Blank where no submitted value. |
| `corrected_parse` | Which corrected parse `f1` uses: `canonical` (SA/DA/NoAgent), `optionA` (MA freeform), `optionB` (MA constrained), `paired386(new)` (Item 5/9). |
| `precision`, `recall` | Corrected-parse precision / recall. |
| `fpr` | False-positive rate = FP / (FP + TN). |
| `ppr` | Positive-prediction rate = (TP + FP) / N — the fraction of samples flagged "vulnerable" (a high value signals flag-everything behaviour). |
| `pc` | **Pairwise-Correct** — the revision's headline metric; harshly penalises over-flagging (see "How Pairwise-Correct works" below). Fraction of clean vulnerable/benign commit pairs where the model labels BOTH members correctly. |
| `fp_submitted`, `fp` | False-positive counts, submitted vs corrected parse. |

## How Pairwise-Correct (`pc`) works

**Pairing comes from `commit_id`.** VulTrial-870 is the PrimeVul-Pair test split:
PrimeVul pairs each *vulnerable* function with its *fixed (benign)* version from the
**same security-fix commit**, so the two records share a `commit_id`. A **pair** is
the set of records sharing a `commit_id`; a **clean/valid pair** is a commit group
of size 2 with exactly one vulnerable (`target=1`) and one benign (`target=0`)
member (`n_pairs` counts these).

**Formula.** With `P` = the set of clean pairs and `correct(x)` = 1 when the model's
prediction for member `x` equals its ground-truth label (and `x` was not skipped):

```
Pairwise-Correct  =  |{ (v, b) ∈ P : correct(v) = 1 AND correct(b) = 1 }|  /  |P|
```

i.e. a pair scores only when the model gets **both** the vulnerable and the benign
member right; getting one wrong fails the whole pair.

**Why it matters.** P-C is strictly harder than F1/accuracy and specifically
punishes the *flag-everything* degeneracy: a model that calls everything vulnerable
nails the vulnerable member but misses the benign member, so **every pair fails**.
This is why the constrained MA (`MA-B(constrained)`, FPR ~0.6–0.9) shows low P-C
(~10–25%) despite mid F1 — the paired structure exposes non-discrimination that a
flat confusion matrix hides.

**Two implementations (agree on the common size-2 case).**
- `scripts/build_meeting_table.py` (`raw_metrics`) — the P-C reported in this sheet:
  keeps only clean size-2 `{0,1}` commit groups; `pc` = both-correct pairs / clean
  pairs.
- `scripts/append_optionb_constrained.py` (`perf_and_pc`, → `pairwise_correct_all_configs.csv`):
  groups by `commit_id`, pairs **consecutive** records `(i, i+1)`, **excludes** any
  pair with a skipped member, and buckets each pair into `pc` (both correct),
  `pv` (both→vulnerable), `pb` (both→benign), `pr` (mixed); `pc_pct = pc / total_pairs`.
  On VulTrial-870 the pairs are overwhelmingly size-2 balanced, so the two agree.

## Cost / energy

| Column | Meaning |
|--------|---------|
| `mean_calls` | Average LLM calls per sample. **Measured** for Item 5/9; **design-nominal** for baselines (NoAgent/SA = 1, DA = 2, MA = 4). |
| `total_energy_kwh` | Total measured energy of the run (codecarbon). `baseline-870` = full 870 run; `Item5/9` = 386 run. **Blank on `baseline-386`** — those rows are a metric subset of the 870 run, so see the matching `baseline-870` row for run energy. |
| `total_energy_kgco2` | Total CO₂ (kg) of the run. |
| `wh_per_sample` | Energy per sample = `total_energy_kwh` × 1000 / n. For `baseline-386` this is carried over from the parent 870 run (per-sample energy is intrinsic to model×design). **Includes GPU idle/wall-clock overhead — see caveat.** |
| `wh_per_call` | `wh_per_sample` / `mean_calls`. Per-call energy; more stable across runs than per-sample. |
| `avg_gpu_power_w` | Average GPU power during the run. **Low value + long `duration_hours` = idle-heavy run**, which inflates the energy figures (esp. Qwen). |
| `duration_hours` | Wall-clock hours of the run. |
| `num_sessions` | codecarbon measurement sessions summed (interrupted / sharded runs have > 1). |
| `skipped` | Samples excluded from metrics (context-overflow / no prediction). |

## Caveats for the reader

1. **Energy comparability.** `wh_per_sample` and `total_energy_kwh` include GPU **idle time**, so they are only comparable within a measurement campaign. The 870 baselines and the 386 Item 5/9 runs are different campaigns. **Qwen-30B is a sparse MoE (~3B active)** and idled at ~150 W over many hours in the baseline runs vs ~350 W in the recent runs — so **Qwen energy is not directly comparable across `block`s**. **Nemotron-49B** drew ~1000 W in both campaigns and *is* comparable. When comparing energy, prefer `wh_per_call` and check `avg_gpu_power_w` / `duration_hours`.
2. **Sample sets differ.** `baseline-870` metrics are on the canonical 870 (the 2 inherent PrimeVul duplicate benigns double-counted; see caveat on `n_total`); everything on `VulTrial-386-paired` is on the same 193 pairs — use the `-386` rows and Item 5/9 for true same-sample comparison. F1/PPR/FPR across 870 vs 386 are indicative, not identical-sample.
3. **MA parsing choice.** `MA-A(freeform)` uses **Option A** (affirmative reparse) and `MA-B(constrained)` uses **Option B**; both differ substantially from the submitted MA parse (see `f1_delta` on the `baseline-870` MA-A rows, +0.21 to +0.56). This is a parsing-methodology decision, not a bug.
4. **P-C denominators.** 870 P-C is over clean size-2 commit pairs (`n_pairs`, ~409–421); the 386 set is fully pair-preserving (193 pairs).
