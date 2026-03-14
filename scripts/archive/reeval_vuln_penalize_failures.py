#!/usr/bin/env python3
"""
Re-evaluate vulnerability detection results with failure penalty.

This script re-processes existing *_detailed_results.jsonl files using the
normalize_vulnerability_penalize_failures() function, which treats vuln=-1
(skipped/failed samples) as incorrect predictions.

Usage:
    # Re-evaluate a single experiment
    python scripts/reeval_vuln_penalize_failures.py results/rq2_cross_architecture/nemotron_8b_vuln_MA-few_instruct

    # Re-evaluate all MA vuln experiments
    python scripts/reeval_vuln_penalize_failures.py --all-ma

    # Dry run (show what would be done without making changes)
    python scripts/reeval_vuln_penalize_failures.py --all-ma --dry-run

Behavior:
    1. Finds *_detailed_results.jsonl in the specified directory
    2. Loads vuln and ground_truth from each record
    3. Applies normalize_vulnerability_penalize_failures()
    4. Backs up existing summary files to *_orig.csv
    5. Overwrites summary files with new metrics

Author: Auto-generated for RQ2 MA experiment re-evaluation
Date: January 2026
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from glob import glob
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)


def normalize_vulnerability_penalize_failures(prediction, ground_truth):
    """
    Penalize failed samples by treating them as incorrect predictions.
    """
    if prediction is None:
        return 1 - ground_truth
    pred_int = int(prediction)
    if pred_int == -1:
        return 1 - ground_truth
    return pred_int


def load_results_from_jsonl(jsonl_path):
    """Load vuln and ground_truth from detailed results JSONL."""
    results = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line.strip())
                    results.append({
                        'idx': data.get('idx'),
                        'vuln': data.get('vuln'),
                        'ground_truth': data.get('ground_truth', data.get('target')),
                        'skipped': data.get('skipped', False),
                        'error': data.get('error', '')
                    })
                except json.JSONDecodeError:
                    continue
    return results


def count_skipped_samples(results):
    """Count samples with vuln=-1."""
    return sum(1 for r in results if r['vuln'] == -1)


def evaluate_with_penalty(results):
    """Evaluate using the penalty normalization."""
    predictions = []
    ground_truths = []

    for r in results:
        gt = r['ground_truth']
        pred = normalize_vulnerability_penalize_failures(r['vuln'], gt)
        predictions.append(pred)
        ground_truths.append(gt)

    # Calculate metrics
    accuracy = accuracy_score(ground_truths, predictions)
    precision = precision_score(ground_truths, predictions, zero_division=0)
    recall = recall_score(ground_truths, predictions, zero_division=0)
    f1 = f1_score(ground_truths, predictions, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(ground_truths, predictions).ravel()

    return {
        'predictions': predictions,
        'ground_truths': ground_truths,
        'metrics': {
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1_Score': f1,
            'True_Positives': int(tp),
            'True_Negatives': int(tn),
            'False_Positives': int(fp),
            'False_Negatives': int(fn),
            'Total_Samples': len(results),
            'Correct_Predictions': int(tp + tn),
            'Skipped_Samples': count_skipped_samples(results)
        }
    }


def backup_file(filepath):
    """Create backup of file with _orig suffix."""
    if os.path.exists(filepath):
        path = Path(filepath)
        backup_path = path.parent / f"{path.stem}_orig{path.suffix}"
        if not backup_path.exists():  # Don't overwrite existing backup
            shutil.copy2(filepath, backup_path)
            return str(backup_path)
    return None


def save_summary_metrics(metrics, filepath):
    """Save summary metrics to CSV."""
    df = pd.DataFrame([{
        'Accuracy': metrics['Accuracy'],
        'Precision': metrics['Precision'],
        'Recall': metrics['Recall'],
        'F1_Score': metrics['F1_Score'],
        'True_Positives': metrics['True_Positives'],
        'True_Negatives': metrics['True_Negatives'],
        'False_Positives': metrics['False_Positives'],
        'False_Negatives': metrics['False_Negatives'],
        'Total_Samples': metrics['Total_Samples'],
        'Correct_Predictions': metrics['Correct_Predictions'],
        'Skipped_Samples': metrics['Skipped_Samples']
    }])
    df.to_csv(filepath, index=False)


def save_classification_report_files(predictions, ground_truths, base_path):
    """Save classification report as CSV and TXT."""
    report_dict = classification_report(
        ground_truths, predictions,
        target_names=['Not Vulnerable', 'Vulnerable'],
        output_dict=True
    )
    report_df = pd.DataFrame(report_dict).transpose()

    csv_path = f"{base_path}_classification_report.csv"
    txt_path = f"{base_path}_classification_report.txt"

    report_df.to_csv(csv_path)

    with open(txt_path, 'w') as f:
        f.write(classification_report(
            ground_truths, predictions,
            target_names=['Not Vulnerable', 'Vulnerable']
        ))

    return csv_path, txt_path


def save_per_sample_metrics(predictions, ground_truths, filepath):
    """Save per-sample metrics to CSV."""
    sample_metrics = []
    for idx, (pred, truth) in enumerate(zip(predictions, ground_truths), start=1):
        is_correct = pred == truth
        if pred == 1 and truth == 1:
            pred_type = "True Positive"
        elif pred == 1 and truth == 0:
            pred_type = "False Positive"
        elif pred == 0 and truth == 1:
            pred_type = "False Negative"
        else:
            pred_type = "True Negative"

        sample_metrics.append({
            'Sample Number': idx,
            'Predicted': pred,
            'Ground Truth': truth,
            'Prediction Type': pred_type,
            'Is Correct': is_correct
        })

    df = pd.DataFrame(sample_metrics)
    df.to_csv(filepath, index=False)


def process_experiment_dir(exp_dir, dry_run=False):
    """Process a single experiment directory."""
    exp_dir = Path(exp_dir)

    # Find MA vuln detailed results JSONL
    # Prefer _corrected files (extraction bug fix) over originals
    corrected_files = list(exp_dir.glob('MA-vuln-*_detailed_results_corrected.jsonl'))
    original_files = [f for f in exp_dir.glob('MA-vuln-*_detailed_results.jsonl')
                      if '_corrected' not in f.name]

    if corrected_files:
        jsonl_file = corrected_files[0]
        print(f"  Using corrected file: {jsonl_file.name}")
    elif original_files:
        jsonl_file = original_files[0]
        print(f"  Using original file: {jsonl_file.name}")
    else:
        print(f"  No MA-vuln-*_detailed_results.jsonl found in {exp_dir}")
        return None
    print(f"\n  Processing: {jsonl_file.name}")

    # Load results
    results = load_results_from_jsonl(jsonl_file)
    skipped_count = count_skipped_samples(results)
    print(f"  Loaded {len(results)} samples ({skipped_count} skipped/failed)")

    if skipped_count == 0:
        print(f"  No skipped samples - metrics unchanged")
        return {'skipped': 0, 'changed': False}

    # Evaluate with penalty
    eval_results = evaluate_with_penalty(results)
    metrics = eval_results['metrics']

    print(f"  New metrics: Accuracy={metrics['Accuracy']:.2%}, F1={metrics['F1_Score']:.4f}")

    if dry_run:
        print(f"  [DRY RUN] Would update summary files")
        return {'skipped': skipped_count, 'changed': True, 'metrics': metrics}

    # Get base name for output files
    # Strip _corrected and _detailed_results to get base name for output files
    base_name = jsonl_file.stem.replace('_detailed_results_corrected', '').replace('_detailed_results', '')

    # Backup and save summary metrics
    summary_path = exp_dir / f"{base_name}_summary_vulnerability_metrics.csv"
    backup = backup_file(summary_path)
    if backup:
        print(f"  Backed up: {Path(backup).name}")
    save_summary_metrics(metrics, summary_path)
    print(f"  Updated: {summary_path.name}")

    # Backup and save classification report
    report_csv = exp_dir / f"{base_name}_classification_report.csv"
    report_txt = exp_dir / f"{base_name}_classification_report.txt"
    backup_file(report_csv)
    backup_file(report_txt)
    save_classification_report_files(
        eval_results['predictions'],
        eval_results['ground_truths'],
        str(exp_dir / base_name)
    )
    print(f"  Updated: classification_report.csv/.txt")

    # Backup and save per-sample metrics
    per_sample_path = exp_dir / f"{base_name}_per_sample_vulnerability_metrics.csv"
    backup_file(per_sample_path)
    save_per_sample_metrics(
        eval_results['predictions'],
        eval_results['ground_truths'],
        per_sample_path
    )
    print(f"  Updated: per_sample_vulnerability_metrics.csv")

    return {'skipped': skipped_count, 'changed': True, 'metrics': metrics}


def find_ma_vuln_experiments(base_dir):
    """Find all MA vulnerability detection experiment directories."""
    base_dir = Path(base_dir)

    # Find directories containing MA vuln detailed results
    dirs = set()

    # Search patterns for different result locations
    search_patterns = [
        'rq2_cross_architecture/*_vuln_MA-*/*_detailed_results.jsonl',
        'runpod_rq2_pod*/MA-vuln-*_detailed_results.jsonl',
        'runpod_rq2_pod*/results/MA-vuln-*_detailed_results.jsonl',
    ]

    for pattern in search_patterns:
        for jsonl in base_dir.glob(pattern):
            if '_corrected' not in jsonl.name:
                dirs.add(jsonl.parent)

    return sorted(dirs)


def main():
    parser = argparse.ArgumentParser(
        description='Re-evaluate vulnerability results with failure penalty'
    )
    parser.add_argument(
        'exp_dir',
        nargs='?',
        help='Experiment directory to process'
    )
    parser.add_argument(
        '--all-ma',
        action='store_true',
        help='Process all MA vulnerability experiments'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Base results directory (default: results)'
    )

    args = parser.parse_args()

    if not args.exp_dir and not args.all_ma:
        parser.error("Either exp_dir or --all-ma is required")

    print("=" * 70)
    print("Vulnerability Detection Re-evaluation with Failure Penalty")
    print("=" * 70)
    print(f"Method: vuln=-1 → opposite of ground_truth (guaranteed wrong)")
    print(f"Dry run: {args.dry_run}")
    print()

    if args.all_ma:
        # Find all MA vuln experiments
        exp_dirs = find_ma_vuln_experiments(args.results_dir)
        print(f"Found {len(exp_dirs)} MA vulnerability experiments:")
        for d in exp_dirs:
            print(f"  - {d}")
    else:
        exp_dirs = [Path(args.exp_dir)]

    # Process each directory
    summary = []
    for exp_dir in exp_dirs:
        if not exp_dir.exists():
            print(f"\nDirectory not found: {exp_dir}")
            continue

        print(f"\n{'='*70}")
        print(f"Experiment: {exp_dir.name}")
        result = process_experiment_dir(exp_dir, dry_run=args.dry_run)
        if result:
            summary.append({'dir': exp_dir.name, **result})

    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print("=" * 70)

    total_skipped = sum(s.get('skipped', 0) for s in summary)
    changed_count = sum(1 for s in summary if s.get('changed', False))

    print(f"Experiments processed: {len(summary)}")
    print(f"Experiments with changes: {changed_count}")
    print(f"Total skipped samples penalized: {total_skipped}")

    if args.dry_run:
        print("\n[DRY RUN] No files were modified")


if __name__ == '__main__':
    main()
