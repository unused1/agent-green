# VulTrial-870 — provenance

`vuln_database/VulTrial_870_samples_balanced.jsonl` **is the PrimeVul-Pair test
split**, used as the evaluation benchmark in this work.

## Source

- Dataset: **PrimeVul** (Ding et al., 2024), *paired* variant.
- File: `primevul_test_paired.jsonl` from the `colin/PrimeVul` HuggingFace mirror
  (https://huggingface.co/datasets/colin/PrimeVul). A copy is retained at
  `vuln_database/primevul_source/primevul_test_paired.jsonl` for verification.
- **870 instances, 435 vulnerable / 435 benign (50/50 balanced).**

## Fidelity to PrimeVul

Verified against the upstream `primevul_test_paired.jsonl`:

- The **function code (`func`) and label (`target`) are identical** on all 868
  unique idx (0 differences) — model inputs and labels are untouched.
- The idx multiset is identical to the upstream file.
- All fields match **except `commit_id` on 2 records** (idx 230147, 187732, both
  benign / `target=0`). This is *not* purely cosmetic: `commit_id` is the
  Pairwise-Correct pairing key. In this file each of these two benigns carries a
  `commit_id` that groups it with its vulnerable partner (a clean size-2 pair);
  in the upstream file those two benigns have a different `commit_id` that leaves
  them **orphaned** (alone in their commit group). So this file yields **2 more
  clean vulnerable/benign pairs** than the upstream file would — a benign pairing
  fix affecting P-C denominators by 2 pairs, with no effect on model inputs,
  labels, or the confusion-matrix metrics.

sha256 (`VulTrial_870_samples_balanced.jsonl`):
`203d925eaf0ab62fc149cbfe9f295e3ba8b4c10074cfc64508e3de0561587b6d`

## Inherent duplicate rows (from PrimeVul, not introduced here)

The PrimeVul test split itself contains **2 duplicate benign functions** —
`idx 349259` and `idx 439495`, each appearing **twice, byte-identical, both
`target=0`**. This is a property of the upstream benchmark (confirmed in the
original `primevul_test_paired.jsonl`), not a construction artifact here. Both
duplicated benigns sit in **multi-vulnerability commit groups** (each commit fixes
three vulnerable functions and carries two benign versions), so they are outside
the clean vulnerable/benign commit pairs used for Pairwise-Correct.

## Metric convention

Metrics are computed on the **canonical 870** (the two inherent duplicates counted
as they appear in the PrimeVul test set), so results are directly comparable to
other work evaluating on PrimeVul-Pair test. Implementation: the consolidation
de-duplicates by idx and then counts idx 349259 and 439495 twice, reproducing the
raw 870 regardless of per-run resume behaviour. Impact: ~0.2% on confusion-matrix
metrics (F1/accuracy); **zero on Pairwise-Correct** (the affected commits are
multi-vuln groups excluded from clean pairs).
