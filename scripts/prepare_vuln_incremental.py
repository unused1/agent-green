#!/usr/bin/env python3
"""
Prepare incremental VulTrial dataset for expanded vulnerability detection experiments.

This script:
1. Loads VulTrial-870 and VulTrial-386 datasets
2. Computes set difference by func_hash (870 minus 386) to find 484 new samples
3. Stratified random samples 50 vuln + 50 safe (seed=42) from the new pool
4. Saves the 100-sample incremental dataset to VulTrial_100_incremental.jsonl
5. Creates the combined 486-sample dataset by concatenating 386 + 100

Usage:
    python scripts/prepare_vuln_incremental.py
"""

import json
import random
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VULN_DB = PROJECT_ROOT / "vuln_database"

FILE_386 = VULN_DB / "VulTrial_386_samples_balanced.jsonl"
FILE_870 = VULN_DB / "VulTrial_870_samples_balanced.jsonl"
FILE_100 = VULN_DB / "VulTrial_100_incremental.jsonl"
FILE_486 = VULN_DB / "VulTrial_486_samples_balanced.jsonl"

SEED = 42
N_VULN = 50
N_SAFE = 50
EXPECTED_FIELDS = 15


def load_jsonl(path):
    """Load all entries from a JSONL file."""
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def save_jsonl(entries, path):
    """Save entries to a JSONL file."""
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  Saved {len(entries)} entries to {path.name}")


def main():
    print("=" * 72)
    print("Prepare Incremental VulTrial Dataset")
    print("=" * 72)

    # ---------------------------------------------------------------
    # Step 1: Load datasets
    # ---------------------------------------------------------------
    print("\n1. Loading datasets...")
    entries_386 = load_jsonl(FILE_386)
    entries_870 = load_jsonl(FILE_870)
    print(f"   VulTrial-386: {len(entries_386)} entries")
    print(f"   VulTrial-870: {len(entries_870)} entries")

    # Verify field counts
    for e in entries_386:
        assert len(e) == EXPECTED_FIELDS, f"386 entry has {len(e)} fields, expected {EXPECTED_FIELDS}"
    for e in entries_870:
        assert len(e) == EXPECTED_FIELDS, f"870 entry has {len(e)} fields, expected {EXPECTED_FIELDS}"
    print(f"   Schema check: all entries have {EXPECTED_FIELDS} fields")

    # ---------------------------------------------------------------
    # Step 2: Compute set difference by func_hash
    # ---------------------------------------------------------------
    print("\n2. Computing set difference by func_hash...")
    hashes_386 = set(e["func_hash"] for e in entries_386)
    new_entries = [e for e in entries_870 if e["func_hash"] not in hashes_386]

    target_counts = Counter(e["target"] for e in new_entries)
    print(f"   New samples (not in 386): {len(new_entries)}")
    print(f"   Distribution: vuln={target_counts[1]}, safe={target_counts[0]}")

    # Verify no overlap
    new_hashes = set(e["func_hash"] for e in new_entries)
    overlap = hashes_386 & new_hashes
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping func_hash values!"
    print("   Overlap check: PASS (0 overlapping func_hash)")

    # ---------------------------------------------------------------
    # Step 3: Stratified random sample
    # ---------------------------------------------------------------
    print(f"\n3. Stratified sampling: {N_VULN} vuln + {N_SAFE} safe (seed={SEED})...")
    vuln_pool = [e for e in new_entries if e["target"] == 1]
    safe_pool = [e for e in new_entries if e["target"] == 0]

    assert len(vuln_pool) >= N_VULN, f"Not enough vuln samples: {len(vuln_pool)} < {N_VULN}"
    assert len(safe_pool) >= N_SAFE, f"Not enough safe samples: {len(safe_pool)} < {N_SAFE}"

    rng = random.Random(SEED)
    sampled_vuln = rng.sample(vuln_pool, N_VULN)
    sampled_safe = rng.sample(safe_pool, N_SAFE)
    incremental = sampled_vuln + sampled_safe

    # Sort by idx for deterministic ordering
    incremental.sort(key=lambda e: e["idx"])

    inc_counts = Counter(e["target"] for e in incremental)
    print(f"   Sampled: {len(incremental)} entries (vuln={inc_counts[1]}, safe={inc_counts[0]})")

    # ---------------------------------------------------------------
    # Step 4: Save incremental dataset
    # ---------------------------------------------------------------
    print("\n4. Saving incremental dataset...")
    save_jsonl(incremental, FILE_100)

    # ---------------------------------------------------------------
    # Step 5: Create combined 486-sample dataset
    # ---------------------------------------------------------------
    print("\n5. Creating combined 486-sample dataset...")
    combined = entries_386 + incremental
    combined.sort(key=lambda e: e["idx"])
    save_jsonl(combined, FILE_486)

    # ---------------------------------------------------------------
    # Step 6: Validation checks
    # ---------------------------------------------------------------
    print("\n6. Validation checks...")
    errors = []

    # 6a. No incremental idx in 386
    idx_386 = set(e["idx"] for e in entries_386)
    inc_idx = set(e["idx"] for e in incremental)
    overlap_idx = idx_386 & inc_idx
    if overlap_idx:
        errors.append(f"idx overlap between 386 and incremental: {overlap_idx}")
    else:
        print("   [PASS] No idx overlap between 386 and incremental")

    # 6b. All func_hash unique in combined
    combined_hashes = [e["func_hash"] for e in combined]
    hash_counts = Counter(combined_hashes)
    dup_hashes = {h: c for h, c in hash_counts.items() if c > 1}
    # Note: 386 already has 2 duplicate func_hash values (known duplicates)
    dup_hashes_386 = {h: c for h, c in Counter(e["func_hash"] for e in entries_386).items() if c > 1}
    new_dups = {h: c for h, c in dup_hashes.items() if h not in dup_hashes_386}
    if new_dups:
        errors.append(f"New duplicate func_hash in combined: {new_dups}")
    else:
        print(f"   [PASS] No new duplicate func_hash (pre-existing in 386: {len(dup_hashes_386)})")

    # 6c. Combined count
    combined_counts = Counter(e["target"] for e in combined)
    expected_vuln = Counter(e["target"] for e in entries_386)[1] + N_VULN
    expected_safe = Counter(e["target"] for e in entries_386)[0] + N_SAFE
    if len(combined) != len(entries_386) + len(incremental):
        errors.append(f"Combined count mismatch: {len(combined)} != {len(entries_386)} + {len(incremental)}")
    else:
        print(f"   [PASS] Combined: {len(combined)} entries (vuln={combined_counts[1]}, safe={combined_counts[0]})")
        print(f"          Expected: {len(entries_386) + len(incremental)} (vuln={expected_vuln}, safe={expected_safe})")

    # 6d. Schema match
    ref_keys = sorted(entries_386[0].keys())
    for i, entry in enumerate(incremental):
        if sorted(entry.keys()) != ref_keys:
            errors.append(f"Schema mismatch at incremental entry {i}: {sorted(entry.keys())} != {ref_keys}")
            break
    else:
        print(f"   [PASS] Schema matches ({EXPECTED_FIELDS} fields per entry)")

    # 6e. Reload and verify saved files
    reloaded_100 = load_jsonl(FILE_100)
    reloaded_486 = load_jsonl(FILE_486)
    assert len(reloaded_100) == len(incremental), f"Reload 100: {len(reloaded_100)} != {len(incremental)}"
    assert len(reloaded_486) == len(combined), f"Reload 486: {len(reloaded_486)} != {len(combined)}"
    print(f"   [PASS] File integrity verified (100: {len(reloaded_100)}, 486: {len(reloaded_486)})")

    if errors:
        print(f"\n   ERRORS ({len(errors)}):")
        for err in errors:
            print(f"   [FAIL] {err}")
        return 1

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Summary")
    print("=" * 72)
    print(f"  VulTrial-386:          {FILE_386.name} ({len(entries_386)} samples)")
    print(f"  New pool (870-386):    {len(new_entries)} samples (vuln={target_counts[1]}, safe={target_counts[0]})")
    print(f"  Incremental sample:    {FILE_100.name} ({len(incremental)} samples)")
    print(f"  Combined dataset:      {FILE_486.name} ({len(combined)} samples)")
    print(f"\n  Incremental idx range: {min(e['idx'] for e in incremental)} - {max(e['idx'] for e in incremental)}")
    print(f"  All validation checks: PASSED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
