# VulTrial-870 Dataset Notes

## Composition

VulTrial-870 is constructed from two JSONL files:
- `vuln_database/VulTrial_486_samples_balanced.jsonl` — 486 records (484 unique idx)
- `vuln_database/VulTrial_384_incremental.jsonl` — 384 records (384 unique idx)
- **Union**: 868 unique samples (0 overlap between files)

## Duplicate Entries in VulTrial-486

Two `idx` values appear twice in the 486 base file, both benign (target=0):

| idx | target | CWE | func_len | Note |
|-----|--------|-----|----------|------|
| 349259 | 0 (safe) | CWE-200 | 3,559 chars | `squashfs_opendir(...)` |
| 439495 | 0 (safe) | CWE-22 | 3,559 chars | Same function as 349259 |

Both entries are exact duplicates (identical function content and length). The same benign function was paired with two different vulnerable counterparts (CWE-200 and CWE-22) during PrimeVul Pair construction, resulting in the safe function appearing twice in the flat JSONL.

## Impact on Experiments

- All experiment runs processed the full 486 records (including duplicates), so models evaluated these functions twice per config
- When combining 486 + 384 for VulTrial-870 metrics, deduplication by `idx` yields 868 unique samples (435 vulnerable, 433 safe)
- Performance metrics report n=868 per config (some configs show 866–867 due to additional skipped/failed inference entries)

## Reporting Convention

For the paper, we report the dataset as **VulTrial-870** (870 total instances, 435 vulnerable, 435 benign, 50%/50% balanced). The 2 duplicate entries are treated as part of the dataset design rather than data errors — they reflect the PrimeVul Pair pairing structure where one benign function can serve as the counterpart for multiple vulnerable functions.

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
