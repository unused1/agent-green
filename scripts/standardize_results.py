#!/usr/bin/env python3
"""
Standardize Results Files - Add missing 'error' column to all result files

This script ensures all result JSONL files have a consistent schema with the 'error' field.
For samples without errors, the field is set to an empty string.

Usage:
    python scripts/standardize_results.py [results_dir]
"""

import json
import sys
from pathlib import Path
import argparse

def standardize_results_file(filepath, backup=True):
    """Add 'error' field to all samples in a JSONL file if missing"""

    if not filepath.exists():
        print(f"⚠️  File not found: {filepath}")
        return False

    # Read all results
    results = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                result = json.loads(line)
                # Add error field if missing (empty string means no error)
                if 'error' not in result:
                    result['error'] = ''
                results.append(result)

    # Create backup if requested
    if backup:
        backup_path = filepath.with_suffix('.jsonl.bak')
        filepath.rename(backup_path)
        print(f"  📦 Backup created: {backup_path.name}")

    # Write back with error field
    with open(filepath, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')

    return True

def main():
    parser = argparse.ArgumentParser(description='Standardize result files by adding error column')
    parser.add_argument('results_dir', nargs='?', default='results/mars',
                       help='Directory containing result files (default: results/mars)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup files')

    args = parser.parse_args()

    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"❌ Directory not found: {results_dir}")
        sys.exit(1)

    print("=" * 60)
    print("STANDARDIZING RESULTS FILES")
    print("=" * 60)
    print(f"Directory: {results_dir}")
    print(f"Backup: {'disabled' if args.no_backup else 'enabled'}")
    print()

    # Find all detailed_results.jsonl files
    result_files = list(results_dir.glob('*_detailed_results.jsonl'))

    if not result_files:
        print("⚠️  No result files found")
        sys.exit(0)

    print(f"Found {len(result_files)} result files")
    print()

    # Process each file
    success_count = 0
    for filepath in sorted(result_files):
        print(f"Processing: {filepath.name}")

        # Count samples before
        with open(filepath, 'r') as f:
            lines = [line for line in f if line.strip()]
            total_samples = len(lines)
            samples_with_error = sum(1 for line in lines if '"error"' in line)

        print(f"  Total samples: {total_samples}")
        print(f"  Samples with 'error' field: {samples_with_error}")

        if samples_with_error == total_samples:
            print(f"  ✓ Already standardized (skipping)")
        else:
            if standardize_results_file(filepath, backup=not args.no_backup):
                print(f"  ✓ Added 'error' field to {total_samples - samples_with_error} samples")
                success_count += 1

        print()

    print("=" * 60)
    print(f"✓ Standardized {success_count} files")
    print("=" * 60)

    if not args.no_backup:
        print("\nBackup files created with .bak extension")
        print("You can remove them with: rm results/mars/*.bak")

if __name__ == '__main__':
    main()
