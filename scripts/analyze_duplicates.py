#!/usr/bin/env python3
"""
Analyze Duplicate Samples in Dataset

Identifies duplicate samples and provides detailed information about them.
"""

import json
from collections import defaultdict

dataset_path = 'vuln_database/VulTrial_386_samples_balanced.jsonl'

# Track all samples by index
samples_by_idx = defaultdict(list)

with open(dataset_path, 'r') as f:
    for line_num, line in enumerate(f, 1):
        sample = json.loads(line)
        samples_by_idx[sample['idx']].append({
            'line_number': line_num,
            'sample': sample
        })

# Find duplicates
duplicates = {idx: entries for idx, entries in samples_by_idx.items() if len(entries) > 1}

print("=" * 80)
print("DATASET DUPLICATE ANALYSIS")
print("=" * 80)
print(f"Dataset: {dataset_path}")
print(f"Total lines: {sum(len(entries) for entries in samples_by_idx.values())}")
print(f"Unique samples: {len(samples_by_idx)}")
print(f"Duplicate samples: {len(duplicates)}")
print()

if duplicates:
    print("DUPLICATE DETAILS:")
    print("=" * 80)

    for idx, entries in sorted(duplicates.items()):
        print(f"\nIndex: {idx}")
        print(f"Occurrences: {len(entries)}")

        # Show details from first occurrence
        first = entries[0]['sample']
        print(f"Project: {first['project']}")
        print(f"CVE: {first.get('cve', 'N/A')}")
        print(f"CWE: {first.get('cwe', 'N/A')}")
        print(f"Ground Truth: {first['target']}")
        print(f"Commit ID: {first['commit_id'][:12]}...")

        print(f"\nLine numbers in dataset:")
        for entry in entries:
            print(f"  - Line {entry['line_number']}")

        # Check if duplicates are identical
        first_json = json.dumps(entries[0]['sample'], sort_keys=True)
        all_identical = all(
            json.dumps(entry['sample'], sort_keys=True) == first_json
            for entry in entries
        )

        if all_identical:
            print("  Status: ✓ All occurrences are identical")
        else:
            print("  Status: ⚠ Occurrences differ!")
            print("  Differences:")
            for i, entry in enumerate(entries[1:], 1):
                for key in first.keys():
                    if entry['sample'].get(key) != first.get(key):
                        print(f"    Line {entry['line_number']}, field '{key}':")
                        print(f"      First: {first.get(key)}")
                        print(f"      This:  {entry['sample'].get(key)}")

        print("-" * 80)
else:
    print("✓ No duplicates found")

print()
print("RECOMMENDATION:")
print("-" * 80)
print("For analysis and reporting:")
print(f"  - Use actual sample count: {len(samples_by_idx)} unique samples")
print(f"  - Report coverage as X/{len(samples_by_idx)} (not X/{sum(len(e) for e in samples_by_idx.values())})")
print("  - Reference docs/dataset_duplicate_analysis.md for documentation")
print()
