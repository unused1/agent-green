# VulTrial-870 Dataset Notes

## Composition

VulTrial-870 is constructed from two JSONL files:
- `vuln_database/VulTrial_486_samples_balanced.jsonl` — 486 records (484 unique idx)
- `vuln_database/VulTrial_384_incremental.jsonl` — 384 records (384 unique idx)
- **Union**: 868 unique samples (0 overlap between files)

## Identity: this IS the PrimeVul-Pair test split

VulTrial-870 is the PrimeVul-Pair **test** split (see
`vuln_database/VulTrial_870_PROVENANCE.md`): the idx multiset and the function
code / labels (`func`, `target`) are identical to upstream
`primevul_test_paired.jsonl`. It is a standard benchmark, not a local
construction — so results are comparable to other PrimeVul-Pair work.

The only field difference is `commit_id` on 2 benign records (idx 230147,
187732). Because `commit_id` is the Pairwise-Correct pairing key, this is not
cosmetic: in this file those two benigns are grouped with their vulnerable
partners (2 clean pairs), whereas upstream leaves them orphaned. Net effect: 2
extra clean pairs here vs upstream, no effect on model inputs, labels, or
confusion-matrix metrics.

## Duplicate rows (inherent to PrimeVul, not a construction error)

The PrimeVul test split itself contains **2 duplicate benign functions** — each
appears **twice, byte-identical, both `target=0`** (confirmed in the upstream
file):

| idx | target | CWE | Note |
|-----|--------|-----|------|
| 349259 | 0 (safe) | CWE-200 | appears 2× byte-identical |
| 439495 | 0 (safe) | CWE-22 | appears 2× byte-identical; a *different* function from 349259 (different `func_hash`/length) |

These are **two separate benign functions, each duplicated** — NOT one benign
shared across two pairs (an earlier note claimed this; it was incorrect). Both sit
in **multi-vulnerability commit groups** (each commit fixes 3 vulnerable functions
and carries 2 benign versions), so they fall **outside the clean vulnerable/benign
commit pairs** used for Pairwise-Correct.

## Reporting convention

The dataset is reported as **VulTrial-870** (870 instances, 435 vulnerable / 435
benign), matching the canonical PrimeVul-Pair test set. Metrics are computed on the
**canonical 870** (the 2 inherent duplicates counted as in PrimeVul), so numbers are
comparable to other work on this benchmark. The consolidation de-duplicates by idx
then counts idx 349259 and 439495 twice, reproducing the raw 870 regardless of
per-run resume behaviour.

Impact of the duplicates: ~0.2% on confusion-matrix metrics (F1/accuracy — two
benign weighted twice); **zero on Pairwise-Correct** (multi-vuln commits are
excluded from clean pairs). The unique-idx count is 868 (435 vulnerable / 433
benign), but the reported N is the canonical 870.

## Dataset Statistics (computed on 868 unique samples)

| Metric | Value |
|--------|-------|
| Average function length (LOC, non-empty lines) | 154.5 |
| Median function length (LOC) | 69.0 |
| Min / Max LOC | 4 / 1,979 |
| Std LOC | 265.4 |
| Average token length (whitespace-split) | 533.9 |
| Median token length | 251.0 |
| Min / Max tokens | 8 / 7,772 |
| Distinct CWE categories | 62 |
| Top CWEs | CWE-787 (144), CWE-125 (94), CWE-703 (93), CWE-476 (78), CWE-416 (58) |
