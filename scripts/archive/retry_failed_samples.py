#!/usr/bin/env python3
"""
Retry Failed Samples - Re-run samples that failed due to timeout or were skipped

Usage:
    python scripts/retry_failed_samples.py <results_file.jsonl> [--error-type timeout|skipped|all]

Examples:
    # Retry all failed samples
    python scripts/retry_failed_samples.py results/Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-095820_detailed_results.jsonl

    # Retry only timeout errors
    python scripts/retry_failed_samples.py results/file.jsonl --error-type timeout

    # Retry only skipped samples
    python scripts/retry_failed_samples.py results/file.jsonl --error-type skipped
"""

import json
import sys
import os
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import config
import subprocess


def extract_failed_samples(results_file, error_type='all'):
    """Extract samples that failed from the results file"""
    failed_samples = []

    with open(results_file, 'r') as f:
        for line in f:
            result = json.loads(line)
            if 'error' in result and result['error']:
                # Filter by error type
                if error_type == 'all' or result['error'] == error_type:
                    failed_samples.append(result)

    return failed_samples


def create_retry_dataset(failed_samples, original_dataset_path):
    """Create a temporary dataset with only the failed samples"""
    # Load original dataset to get full sample data
    original_samples = {}
    with open(original_dataset_path, 'r') as f:
        for line in f:
            sample = json.loads(line)
            original_samples[sample['idx']] = sample

    # Create retry dataset
    retry_samples = []
    for failed in failed_samples:
        idx = failed['idx']
        if idx in original_samples:
            retry_samples.append(original_samples[idx])
        else:
            print(f"⚠ Warning: Sample {idx} not found in original dataset")

    return retry_samples


def main():
    parser = argparse.ArgumentParser(description='Retry failed vulnerability detection samples')
    parser.add_argument('results_file', help='Path to detailed_results.jsonl file')
    parser.add_argument('--error-type', choices=['timeout', 'skipped', 'all'],
                       default='all', help='Type of errors to retry (default: all)')
    parser.add_argument('--dataset', help='Path to original dataset (auto-detected if not provided)')

    args = parser.parse_args()

    # Validate results file exists
    if not os.path.exists(args.results_file):
        print(f"❌ Error: Results file not found: {args.results_file}")
        sys.exit(1)

    # Extract failed samples
    print(f"📋 Analyzing {args.results_file}...")
    failed_samples = extract_failed_samples(args.results_file, args.error_type)

    if not failed_samples:
        print(f"✓ No failed samples found with error type '{args.error_type}'")
        return

    print(f"Found {len(failed_samples)} failed samples:")
    for sample in failed_samples:
        print(f"  - Sample {sample['idx']}: {sample.get('error', 'unknown error')}")

    # Detect dataset path if not provided
    if args.dataset:
        dataset_path = args.dataset
    else:
        # Try to auto-detect from config
        dataset_path = os.getenv('VULN_DATASET', config.VULN_DATASET)

    if not os.path.exists(dataset_path):
        print(f"❌ Error: Dataset not found: {dataset_path}")
        print("Please specify dataset path with --dataset flag")
        sys.exit(1)

    print(f"📖 Using dataset: {dataset_path}")

    # Create retry dataset
    retry_samples = create_retry_dataset(failed_samples, dataset_path)

    if not retry_samples:
        print("❌ Error: Could not create retry dataset")
        sys.exit(1)

    # Save retry dataset to temporary file
    retry_dataset_path = "/tmp/retry_dataset.jsonl"
    with open(retry_dataset_path, 'w') as f:
        for sample in retry_samples:
            f.write(json.dumps(sample) + '\n')

    print(f"📝 Created retry dataset: {retry_dataset_path}")
    print("")

    # Prompt user to confirm
    print("=" * 60)
    print(f"Ready to retry {len(retry_samples)} failed samples")
    print(f"Error type filter: {args.error_type}")
    print("")
    print("⚠️  The script will perform these steps in order:")
    print("  1. Create a backup of the original results file (.backup)")
    print("  2. Remove failed samples from the results file")
    print("  3. Re-run the failed samples with fresh attempts")
    print("  4. Append successful results back to the file")
    print("")
    print("💾 Your original data is safe - restore from .backup if needed")
    print("=" * 60)
    response = input("\nProceed with retry? (y/n): ")

    if response.lower() != 'y':
        print("❌ Retry cancelled")
        return

    # Extract experiment design from filename
    # Example: Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-095820_detailed_results.jsonl
    filename = os.path.basename(args.results_file)
    if filename.startswith('Sa-zero'):
        design = 'SA-zero'
    elif filename.startswith('Sa-few'):
        design = 'SA-few'
    else:
        print("❌ Error: Could not determine experiment design from filename")
        sys.exit(1)

    # Create backup of original results file
    backup_file = args.results_file + '.backup'
    import shutil
    shutil.copy2(args.results_file, backup_file)
    print(f"📦 Backup created: {backup_file}")

    # Remove failed samples from results file (so they can be retried)
    failed_indices = {s['idx'] for s in failed_samples}
    with open(args.results_file, 'r') as f:
        all_results = [json.loads(line) for line in f if line.strip()]

    # Filter out failed samples
    successful_results = [r for r in all_results if r['idx'] not in failed_indices]

    # Rewrite results file with only successful samples
    with open(args.results_file, 'w') as f:
        for result in successful_results:
            f.write(json.dumps(result) + '\n')

    print(f"🗑️  Removed {len(failed_samples)} failed samples from results file")
    print(f"✓ {len(successful_results)} successful samples retained")

    # Also update CSV file if it exists
    csv_file = args.results_file.replace('_detailed_results.jsonl', '_detailed_results.csv')
    if os.path.exists(csv_file):
        backup_csv = csv_file + '.backup'
        shutil.copy2(csv_file, backup_csv)
        print(f"📦 CSV backup created: {backup_csv}")

        # Rewrite CSV with header + successful results
        with open(csv_file, 'w') as f:
            f.write("idx,project,commit_id,project_url,commit_url,commit_message,ground_truth,vuln,reasoning,cwe,cve,cve_desc,error\n")
            for result in successful_results:
                def escape_csv_field(field):
                    if field is None:
                        return ""
                    field_str = str(field)
                    if ',' in field_str or '"' in field_str or '\n' in field_str:
                        return '"' + field_str.replace('"', '""') + '"'
                    return field_str

                row = [
                    escape_csv_field(result['idx']),
                    escape_csv_field(result['project']),
                    escape_csv_field(result['commit_id']),
                    escape_csv_field(result['project_url']),
                    escape_csv_field(result['commit_url']),
                    escape_csv_field(result['commit_message']),
                    escape_csv_field(result['ground_truth']),
                    escape_csv_field(result['vuln']),
                    escape_csv_field(result['reasoning']),
                    escape_csv_field(result['cwe']),
                    escape_csv_field(result['cve']),
                    escape_csv_field(result['cve_desc']),
                    escape_csv_field(result.get('error', ''))
                ]
                f.write(','.join(row) + '\n')

    # Set environment variable to use retry dataset
    original_dataset = os.getenv('VULN_DATASET')
    os.environ['VULN_DATASET'] = retry_dataset_path

    try:
        # Run vulnerability detection on retry samples
        print("\n🔄 Starting retry...")
        print("Note: Use Ctrl+C to stop if needed. Progress is saved incrementally.")
        print("")

        # Run single_agent_vuln.py as a subprocess with correct design argument
        project_root = Path(__file__).parent.parent
        script_path = project_root / "src" / "single_agent_vuln.py"

        # Run the script with the design argument
        result = subprocess.run(
            ["python3", str(script_path), design],
            cwd=str(project_root),
            env=os.environ.copy(),
            capture_output=False  # Show output in real-time
        )

        if result.returncode != 0:
            print(f"\n⚠️  Retry completed with errors (exit code: {result.returncode})")
            print(f"Check the results file to see which samples succeeded")
        else:
            print("\n✓ Retry complete!")

        print(f"Results updated in: {args.results_file}")
        print(f"Backup available at: {backup_file}")

    finally:
        # Restore original dataset environment variable
        if original_dataset:
            os.environ['VULN_DATASET'] = original_dataset
        else:
            del os.environ['VULN_DATASET']

        # Clean up temporary file
        if os.path.exists(retry_dataset_path):
            os.remove(retry_dataset_path)
            print(f"🗑️  Cleaned up temporary file: {retry_dataset_path}")


if __name__ == '__main__':
    main()
