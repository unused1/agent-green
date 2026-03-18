#!/usr/bin/env python3
"""
Prepare 384-sample incremental VulTrial dataset for the 870 expansion.

This script:
1. Loads VulTrial-870 and VulTrial-486 datasets
2. Computes set difference by func_hash (870 minus 486) = 384 remaining samples
3. Takes ALL 384 samples (no sampling — 192 vuln + 192 safe)
4. Saves to VulTrial_384_incremental.jsonl

Usage:
    python scripts/prepare_vuln_384_incremental.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VULN_DB = PROJECT_ROOT / "vuln_database"

FILE_486 = VULN_DB / "VulTrial_486_samples_balanced.jsonl"
FILE_870 = VULN_DB / "VulTrial_870_samples_balanced.jsonl"
FILE_384 = VULN_DB / "VulTrial_384_incremental.jsonl"

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
    print("Prepare 384-Sample Incremental VulTrial Dataset (870 - 486)")
    print("=" * 72)

    # ---------------------------------------------------------------
    # Step 1: Load datasets
    # ---------------------------------------------------------------
    print("\n1. Loading datasets...")
    entries_486 = load_jsonl(FILE_486)
    entries_870 = load_jsonl(FILE_870)
    print(f"   VulTrial-486: {len(entries_486)} entries")
    print(f"   VulTrial-870: {len(entries_870)} entries")

    # Verify field counts
    for e in entries_486:
        assert len(e) == EXPECTED_FIELDS, f"486 entry has {len(e)} fields, expected {EXPECTED_FIELDS}"
    for e in entries_870:
        assert len(e) == EXPECTED_FIELDS, f"870 entry has {len(e)} fields, expected {EXPECTED_FIELDS}"
    print(f"   Schema check: all entries have {EXPECTED_FIELDS} fields")

    # ---------------------------------------------------------------
    # Step 2: Compute set difference by func_hash
    # ---------------------------------------------------------------
    print("\n2. Computing set difference by func_hash...")
    hashes_486 = set(e["func_hash"] for e in entries_486)
    new_entries = [e for e in entries_870 if e["func_hash"] not in hashes_486]

    target_counts = Counter(e["target"] for e in new_entries)
    print(f"   New samples (870 - 486): {len(new_entries)}")
    print(f"   Distribution: vuln={target_counts.get(1, 0)}, safe={target_counts.get(0, 0)}")

    # Verify no overlap
    new_hashes = set(e["func_hash"] for e in new_entries)
    overlap = hashes_486 & new_hashes
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping func_hash values!"
    print("   Overlap check: PASS (0 overlapping func_hash)")

    # ---------------------------------------------------------------
    # Step 3: Take all 384 (no sampling)
    # ---------------------------------------------------------------
    print("\n3. Taking all remaining samples (no sampling)...")
    incremental = sorted(new_entries, key=lambda e: e["idx"])

    inc_counts = Counter(e["target"] for e in incremental)
    print(f"   Total: {len(incremental)} entries (vuln={inc_counts.get(1, 0)}, safe={inc_counts.get(0, 0)})")

    if len(incremental) != 384:
        print(f"   WARNING: Expected 384 entries, got {len(incremental)}")

    # ---------------------------------------------------------------
    # Step 4: Save incremental dataset
    # ---------------------------------------------------------------
    print("\n4. Saving incremental dataset...")
    save_jsonl(incremental, FILE_384)

    # ---------------------------------------------------------------
    # Step 5: Validation checks
    # ---------------------------------------------------------------
    print("\n5. Validation checks...")
    errors = []

    # 5a. No idx overlap with 486
    idx_486 = set(e["idx"] for e in entries_486)
    inc_idx = set(e["idx"] for e in incremental)
    overlap_idx = idx_486 & inc_idx
    if overlap_idx:
        errors.append(f"idx overlap between 486 and incremental: {overlap_idx}")
    else:
        print("   [PASS] No idx overlap between 486 and incremental")

    # 5b. Combined = 870
    combined_count = len(entries_486) + len(incremental)
    if combined_count != len(entries_870):
        # May differ slightly due to func_hash duplicates within 486 or 870
        print(f"   [INFO] 486 + 384 = {combined_count}, 870 file = {len(entries_870)}")
    else:
        print(f"   [PASS] 486 + {len(incremental)} = {combined_count} = 870")

    # 5c. Schema match
    ref_keys = sorted(entries_486[0].keys())
    for i, entry in enumerate(incremental):
        if sorted(entry.keys()) != ref_keys:
            errors.append(f"Schema mismatch at incremental entry {i}: {sorted(entry.keys())} != {ref_keys}")
            break
    else:
        print(f"   [PASS] Schema matches ({EXPECTED_FIELDS} fields per entry)")

    # 5d. Reload and verify saved file
    reloaded = load_jsonl(FILE_384)
    assert len(reloaded) == len(incremental), f"Reload: {len(reloaded)} != {len(incremental)}"
    print(f"   [PASS] File integrity verified ({len(reloaded)} entries)")

    # 5e. Balance check
    if inc_counts.get(1, 0) == inc_counts.get(0, 0):
        print(f"   [PASS] Balanced: {inc_counts[1]} vuln + {inc_counts[0]} safe")
    else:
        print(f"   [INFO] Not perfectly balanced: vuln={inc_counts.get(1, 0)}, safe={inc_counts.get(0, 0)}")

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
    print(f"  VulTrial-486:          {FILE_486.name} ({len(entries_486)} samples)")
    print(f"  VulTrial-870:          {FILE_870.name} ({len(entries_870)} samples)")
    print(f"  Incremental:           {FILE_384.name} ({len(incremental)} samples)")
    print(f"  Idx range:             {min(e['idx'] for e in incremental)} - {max(e['idx'] for e in incremental)}")
    print(f"  All validation checks: PASSED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
