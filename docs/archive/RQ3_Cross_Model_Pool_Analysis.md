# RQ3 Phase A: Cross-Model Correct Prediction Pool Analysis

**Date**: 2026-02-24
**Purpose**: Inform sampling strategy for Phase A human evaluation under the constraint that sampled source code must be correctly predicted by multiple models.

## Background

The original Phase A sampling selected correct predictions independently per experiment (one model, one mode, one prompting style). A revised requirement mandates that sampled source code be correctly predicted across models, ensuring cross-model agreement on the correct answer before evaluating explanation quality.

This analysis computes eligible pool sizes under various constraint levels using the 386-sample balanced vulnerability dataset (193 vulnerable, 193 safe) across 16 SA (Single-Agent) vulnerability detection experiments.

**Data source**: Per-sample correctness from `*_per_sample_vulnerability_metrics.csv` files, referenced via `results/consolidated_performance.csv`.

**Models**: Qwen3-4B, Qwen3-30B-A3B, Nemotron-Nano-8B, Nemotron-Super-49B
**Configurations**: 2 modes (thinking, instruct) × 2 prompting (zero-shot, few-shot) = 4 per model = 16 total

---

## D1 — All 16 SA Experiments Correct

**Description**: The strictest constraint — a source code sample is eligible only if *all 4 models in all 4 configurations* (16 experiments total) predicted correctly.

| Pool | TP | TN |
|------|-----|-----|
| **9** | 0 | 9 |

**Interpretation**: Far too restrictive for any meaningful sampling. Only 9 samples survive, all true negatives (safe code correctly identified as safe). No vulnerable code is represented.

---

## D2 — Per Mode × Prompting, All 4 Models Correct

**Description**: Within each mode × prompting combination, a sample is eligible only if *all 4 models* predicted correctly for that specific configuration. This preserves the stratified sampling design while enforcing cross-model agreement.

| Stratum | Pool | TP | TN |
|---------|------|-----|-----|
| thinking zero-shot | 47 | 1 | 46 |
| thinking few-shot | 38 | 3 | 35 |
| instruct zero-shot | 89 | 0 | 89 |
| instruct few-shot | 83 | 1 | 82 |

**Interpretation**: Pool sizes are sufficient for sampling (38–89 per stratum), but almost entirely TN. Instruct zero-shot has *zero* TP. The SA design's strong TN bias (TPR=0.321) is amplified when requiring unanimity across 4 models.

---

## D3 — Per Mode, All 4 Models Correct (Both Prompting Styles)

**Description**: A sample must be correctly predicted by all 4 models in *both* zero-shot and few-shot for a given mode. Stricter than D2 because it requires consistency across prompting styles.

| Mode | Pool | TP | TN |
|------|------|-----|-----|
| thinking | 13 | 0 | 13 |
| instruct | 52 | 0 | 52 |

**Interpretation**: Highly restrictive, especially for thinking mode (only 13). No TP in either mode. Not viable for balanced sampling.

---

## D4 — Per Prompting, All 4 Models Correct (Both Modes)

**Description**: A sample must be correctly predicted by all 4 models in *both* thinking and instruct modes for a given prompting style. Stricter than D2 because it requires consistency across modes.

| Prompting | Pool | TP | TN |
|-----------|------|-----|-----|
| zero-shot | 31 | 0 | 31 |
| few-shot | 25 | 0 | 25 |

**Interpretation**: Small pools, zero TP. Not viable.

---

## D5 — Relaxed: ≥3-of-4 Models Correct Per Stratum

**Description**: Within each mode × prompting combination, a sample is eligible if *at least 3 of the 4 models* predicted correctly. This relaxation allows one model to disagree while maintaining majority agreement.

| Stratum | ≥4 models | ≥3 models | ≥2 models |
|---------|-----------|-----------|-----------|
| thinking zero-shot | 47 (1 TP) | **154 (41 TP)** | 265 (103 TP) |
| thinking few-shot | 38 (3 TP) | **147 (29 TP)** | 268 (98 TP) |
| instruct zero-shot | 89 (0 TP) | **166 (17 TP)** | 245 (59 TP) |
| instruct few-shot | 83 (1 TP) | **165 (15 TP)** | 239 (56 TP) |

**Interpretation**: The ≥3 threshold recovers significant TP diversity (15–41 per stratum) with pool sizes of 147–166. The jump from 4-of-4 to 3-of-4 is dramatic because Nemotron-Nano-8B (the weakest model) is typically the excluded one.

---

## D5b — 3 Specific Models: Qwen3-4B, Qwen3-30B-A3B, Nemotron-Super-49B

**Description**: Instead of an arbitrary "3-of-4" relaxation, this approach explicitly selects 3 models with sufficient individual accuracy, excluding Nemotron-Nano-8B (near-chance SA accuracy of 0.487–0.526, 0 TP in instruct zero-shot). Methodologically defensible as "models meeting a minimum performance threshold."

### All 12 strata correct (3 models × 4 configs)

| Pool | TP | TN |
|------|-----|-----|
| **18** | 4 | 14 |

### Per mode × prompting (all 3 models correct)

| Stratum | Pool | TP | TN |
|---------|------|-----|-----|
| thinking zero-shot | **88** | 39 | 49 |
| thinking few-shot | **70** | 20 | 50 |
| instruct zero-shot | **106** | 17 | 89 |
| instruct few-shot | **107** | 13 | 94 |

### Per mode (all 3 models correct, both prompting styles)

| Mode | Pool | TP | TN |
|------|------|-----|-----|
| thinking | 32 | 10 | 22 |
| instruct | 66 | 8 | 58 |

### Per prompting (all 3 models correct, both modes)

| Prompting | Pool | TP | TN |
|-----------|------|-----|-----|
| zero-shot | 47 | 13 | 34 |
| few-shot | 38 | 4 | 34 |

### Comparison: 4-of-4 vs 3 specific models vs 3-of-4 any

| Stratum | 4-of-4 | 3 specific (excl. Nano-8B) | 3-of-4 any |
|---------|--------|---------------------------|------------|
| thinking zero-shot | 47 (1 TP) | **88 (39 TP)** | 154 (41 TP) |
| thinking few-shot | 38 (3 TP) | **70 (20 TP)** | 147 (29 TP) |
| instruct zero-shot | 89 (0 TP) | **106 (17 TP)** | 166 (17 TP) |
| instruct few-shot | 83 (1 TP) | **107 (13 TP)** | 165 (15 TP) |

**Interpretation**: The 3-specific-model approach nearly matches D5 "3-of-4 any" for TP recovery (especially in instruct strata where the numbers are identical), confirming Nemotron-Nano-8B is consistently the excluded model. Pool sizes of 70–107 per stratum are comfortable for sampling 3 per model × 3 models = 9 samples per stratum.

---

## D8 — Per Model Family (Qwen vs Nemotron), All Strata Correct

**Description**: Groups models by architecture family: Qwen (4B + 30B) and Nemotron (8B + 49B). A sample must be correctly predicted by *both models in the family* across *all 4 configurations* (8 strata per family).

| Family | Pool | TP | TN |
|--------|------|-----|-----|
| **Qwen** (4B + 30B) | **54** | 7 | 47 |
| **Nemotron** (8B + 49B) | **21** | 0 | 21 |

**Interpretation**: Qwen family has moderate agreement (54 samples, some TP). Nemotron family is dragged down by Nano-8B's weak performance.

---

## D8b — Per Model Family, Per Mode × Prompting Stratum

**Description**: Within each mode × prompting configuration, both models in the family must predict correctly.

| Family | Stratum | Pool | TP | TN |
|--------|---------|------|-----|-----|
| Qwen | thinking zero-shot | **136** | 43 | 93 |
| Qwen | thinking few-shot | **139** | 28 | 111 |
| Qwen | instruct zero-shot | **141** | 30 | 111 |
| Qwen | instruct few-shot | **143** | 25 | 118 |
| Nemotron | thinking zero-shot | **74** | 2 | 72 |
| Nemotron | thinking few-shot | **93** | 31 | 62 |
| Nemotron | instruct zero-shot | **136** | 0 | 136 |
| Nemotron | instruct few-shot | **125** | 3 | 122 |

**Interpretation**: Qwen family achieves large pools (136–143) with meaningful TP (25–43) across all strata. Nemotron family has 0 TP in instruct zero-shot (inherited from Nano-8B's 0 TP in that configuration).

---

## D9 — Per Individual Model, All 4 Configs Correct

**Description**: A sample must be correctly predicted by a single model across all 4 of its configurations (thinking/instruct × zero-shot/few-shot). Measures each model's internal consistency.

| Model | Pool | TP | TN |
|-------|------|-----|-----|
| Qwen3-4B | **122** | 11 | 111 |
| Qwen3-30B-A3B | **92** | 35 | 57 |
| Nemotron-Nano-8B | **139** | 0 | 139 |
| Nemotron-Super-49B | **46** | 18 | 28 |

**Interpretation**: Nemotron-Nano-8B has 0 TP — it never correctly predicts a vulnerable sample across all 4 configs. Qwen3-30B-A3B has the best TP ratio (35/92 = 38%). Nemotron-Super-49B has fewer total consistent samples (46) but good TP ratio (18/46 = 39%).

---

## D9b — Per Individual Model, Per Mode × Prompting (Single Experiment Baseline)

**Description**: Correctness counts for each individual experiment — no cross-model constraint. This is the baseline that the original Phase A sampling drew from. Format: Pool (TP/TN).

| Model | think-zero | think-few | inst-zero | inst-few |
|-------|-----------|----------|----------|---------|
| Qwen3-4B | 197 (54/143) | 202 (42/160) | 207 (34/173) | 203 (30/173) |
| Qwen3-30B-A3B | 215 (102/113) | 205 (83/122) | 209 (93/116) | 217 (92/125) |
| Nemotron-Nano-8B | 188 (5/183) | 191 (46/145) | 191 (0/191) | 188 (17/171) |
| Nemotron-Super-49B | 217 (142/75) | 216 (131/85) | 201 (64/137) | 193 (55/138) |

**Interpretation**: Per-experiment accuracies range from 48.7% (Nemotron-Nano-8B thinking zero-shot) to 56.2% (Nemotron-Super-49B thinking zero-shot). Nemotron-Nano-8B has 0 TP in instruct zero-shot and only 5 TP in thinking zero-shot, making it the systematic bottleneck in any cross-model constraint.

---

## D9c — Per Individual Model, Per Mode (Both Prompting Styles Correct)

**Description**: A sample must be correctly predicted by a single model in both zero-shot and few-shot for a given mode. Measures within-model consistency across prompting styles.

| Model | thinking | instruct |
|-------|----------|----------|
| Qwen3-4B | 143 (20 TP, 123 TN) | 180 (21 TP, 159 TN) |
| Qwen3-30B-A3B | 149 (63 TP, 86 TN) | 149 (59 TP, 90 TN) |
| Nemotron-Nano-8B | 144 (4 TP, 140 TN) | 171 (0 TP, 171 TN) |
| Nemotron-Super-49B | 138 (96 TP, 42 TN) | 139 (31 TP, 108 TN) |

**Interpretation**: Nemotron-Super-49B in thinking mode is notably TP-heavy (96/138 = 70%), the inverse of most other configurations. Qwen3-30B-A3B shows balanced TP/TN across both modes.

---

## D9d — Per Individual Model, Per Prompting (Both Modes Correct)

**Description**: A sample must be correctly predicted by a single model in both thinking and instruct modes for a given prompting style. Measures within-model consistency across reasoning modes.

| Model | zero-shot | few-shot |
|-------|-----------|----------|
| Qwen3-4B | 159 (23 TP, 136 TN) | 159 (14 TP, 145 TN) |
| Qwen3-30B-A3B | 153 (72 TP, 81 TN) | 138 (51 TP, 87 TN) |
| Nemotron-Nano-8B | 183 (0 TP, 183 TN) | 161 (17 TP, 144 TN) |
| Nemotron-Super-49B | 111 (54 TP, 57 TN) | 103 (35 TP, 68 TN) |

**Interpretation**: Nemotron-Nano-8B has 0 TP in zero-shot across both modes — it defaults to "safe" in zero-shot regardless of reasoning mode. Nemotron-Super-49B has the most balanced zero-shot pool (54/57 ≈ 1:1 TP:TN).

---

## Key Observations

1. **Nemotron-Nano-8B is the systematic bottleneck**: Near-chance accuracy (48.7–52.6%), 0 TP in instruct zero-shot, only 5 TP in thinking zero-shot. Including it in any cross-model constraint eliminates nearly all TP from the pool.

2. **The 3-specific-model approach (D5b) is the practical sweet spot**: Excluding Nemotron-Nano-8B recovers TP diversity while maintaining cross-model agreement. Pool sizes of 70–107 per stratum with 13–39 TP per stratum.

3. **SA design has inherent TN bias**: Models default to predicting "safe" in SA mode (TPR=0.321, TNR=0.729). Cross-model intersection amplifies this bias because models are more likely to agree on easy TN cases than on correctly identifying vulnerable code.

4. **Thinking mode produces more TP agreement** than instruct mode across all constraint levels, likely because the extended reasoning process helps models converge on correct vulnerability identification.
