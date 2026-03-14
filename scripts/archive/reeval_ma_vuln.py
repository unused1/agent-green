#!/usr/bin/env python3
"""
Re-evaluation Script for MA Vuln Results

This script re-parses existing MA Vuln result files using the corrected
extraction logic that properly handles:
1. Markdown-wrapped JSON (```json ... ```)
2. Model-agnostic decision interpretation
3. Improved fallback behavior

Usage:
    python scripts/reeval_ma_vuln.py [--dry-run] [--file <specific_file>]

Options:
    --dry-run       Show what would be changed without modifying files
    --file <path>   Re-evaluate a specific file instead of all MA Vuln files
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report


def regenerate_evaluation_files(predictions, ground_truths, exp_name, result_dir):
    """
    Regenerate evaluation files (replacing originals) based on corrected predictions.

    Generates:
    - {exp_name}_classification_report.csv
    - {exp_name}_classification_report.txt
    - {exp_name}_per_sample_vulnerability_metrics.csv
    - {exp_name}_summary_vulnerability_metrics.csv
    """
    result_dir = Path(result_dir)

    # Calculate metrics
    accuracy = accuracy_score(ground_truths, predictions)
    precision = precision_score(ground_truths, predictions, zero_division=0)
    recall = recall_score(ground_truths, predictions, zero_division=0)
    f1 = f1_score(ground_truths, predictions, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(ground_truths, predictions).ravel()

    # 1. Save classification report (CSV)
    report = classification_report(
        ground_truths,
        predictions,
        target_names=['Not Vulnerable', 'Vulnerable'],
        output_dict=True
    )
    report_df = pd.DataFrame(report).transpose()
    report_csv_path = result_dir / f"{exp_name}_classification_report.csv"
    report_df.to_csv(report_csv_path)
    print(f"  Saved: {report_csv_path.name}")

    # 2. Save classification report (TXT)
    report_txt_path = result_dir / f"{exp_name}_classification_report.txt"
    with open(report_txt_path, 'w') as f:
        f.write(classification_report(
            ground_truths,
            predictions,
            target_names=['Not Vulnerable', 'Vulnerable']
        ))
    print(f"  Saved: {report_txt_path.name}")

    # 3. Save per-sample metrics
    per_sample = []
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

        per_sample.append({
            "Sample Number": idx,
            "Predicted": pred,
            "Ground Truth": truth,
            "Prediction Type": pred_type,
            "Is Correct": is_correct
        })

    per_sample_path = result_dir / f"{exp_name}_per_sample_vulnerability_metrics.csv"
    pd.DataFrame(per_sample).to_csv(per_sample_path, index=False)
    print(f"  Saved: {per_sample_path.name}")

    # 4. Save summary metrics
    summary = {
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1_Score": f1,
        "True_Positives": tp,
        "True_Negatives": tn,
        "False_Positives": fp,
        "False_Negatives": fn,
        "Total_Samples": len(predictions),
        "Correct_Predictions": sum(1 for p, g in zip(predictions, ground_truths) if p == g)
    }

    summary_path = result_dir / f"{exp_name}_summary_vulnerability_metrics.csv"
    pd.DataFrame([summary]).to_csv(summary_path, index=False)
    print(f"  Saved: {summary_path.name}")

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn
    }


def extract_vulnerability_decision_corrected(review_board_response):
    """
    Corrected extraction logic for Review Board responses.

    Handles both Qwen3 (clean JSON) and Nemotron (markdown-wrapped JSON) formats.

    MA Workflow Context:
    - Security Researcher reports vulnerabilities
    - Code Author responds/disputes
    - Moderator summarizes
    - Review Board issues FINAL VERDICT on each vulnerability claim

    Decision Interpretation (Review Board validates/rejects the vulnerability claim):

    VULNERABLE (1) - RB accepts the vulnerability claim as valid:
    - "confirmed", "accept", "valid", "partially valid"
    - "critical", "high", "vulnerable"
    - "accept with mitigation", "fix required"

    SAFE (0) - RB rejects the claim OR says issue was addressed:
    - "no vulnerability", "reject", "invalid", "safe", "not exploitable"
    - "mitigated", "resolved", "fixed" (issue was addressed)
    """
    try:
        # Step 1: Strip markdown code blocks (handles Nemotron's format)
        text = re.sub(r'```(?:json)?\s*', '', review_board_response)
        text = re.sub(r'```\s*', '', text)

        # Step 2: Extract JSON array from response
        match = re.search(r'(\[[\s\S]*\])', text)
        if match:
            json_str = match.group(1)
        else:
            json_str = text.strip()

        verdicts = json.loads(json_str)

        # Step 3: Analyze each verdict
        vuln_signals = 0
        safe_signals = 0

        for v in verdicts:
            decision = v.get('decision', '').lower().strip()
            severity = v.get('severity', '').lower().strip()

            # === SAFE signals (RB rejects claim or says issue addressed) ===
            # Explicit rejection
            if any(kw in decision for kw in ['no vulnerability', 'no_vulnerability', 'reject', 'invalid', 'safe', 'not exploitable']):
                safe_signals += 2
                continue

            # Issue was addressed/resolved
            if any(kw in decision for kw in ['mitigated', 'resolved', 'fixed', 'patched']):
                safe_signals += 2
                continue

            # === VULNERABLE signals (RB accepts the vulnerability claim) ===
            # Explicit confirmation
            if any(kw in decision for kw in ['confirmed', 'vulnerable', 'exploitable']):
                vuln_signals += 2
                continue

            # Qwen3 style validation
            if decision in ['valid', 'partially valid']:
                vuln_signals += 2
                continue

            # Accept = RB accepts the vulnerability claim as valid
            if 'accept' in decision:
                vuln_signals += 2
                continue

            # Severity-based decisions (when decision field contains severity)
            if decision in ['critical', 'high', 'high severity', 'critical severity']:
                vuln_signals += 2
                continue

            # Fix required = vulnerability exists and needs fixing
            if any(kw in decision for kw in ['fix required', 'action required', 'requires fix']):
                vuln_signals += 1
                continue

            # Medium/Low severity as decision = less certain, slight vuln lean
            if decision in ['medium', 'low', 'moderate', 'medium severity', 'low severity']:
                vuln_signals += 1
                continue

            # === AMBIGUOUS - use severity field as tiebreaker ===
            if severity in ['critical', 'high']:
                vuln_signals += 1
            elif severity in ['low', 'medium', 'moderate']:
                # Low/medium severity with unclear decision - slight safe lean
                safe_signals += 1
            # If neither, don't count (truly ambiguous)

        # Build reasoning string
        reasoning = "; ".join(
            f"{v.get('vulnerability','Unknown')}: {v.get('decision','Unknown')} ({v.get('reason','No reason')[:100]})"
            for v in verdicts
        )

        # Decision: more vuln signals than safe signals = vulnerable
        # Tie goes to vulnerable (conservative for security)
        has_vulnerability = vuln_signals >= safe_signals and vuln_signals > 0
        return (1 if has_vulnerability else 0), reasoning, {
            'vuln_signals': vuln_signals,
            'safe_signals': safe_signals,
            'parsed': True,
            'num_verdicts': len(verdicts)
        }

    except Exception as e:
        # Fallback: keyword matching (but exclude overly broad terms)
        text = review_board_response.lower()
        # Only trigger on strong vulnerability indicators, NOT on generic "vulnerability" word
        if any(k in text for k in ['confirmed vulnerability', 'critical vulnerability', 'exploitable']):
            return 1, review_board_response[:500], {'parsed': False, 'fallback': 'strong_vuln_keywords'}
        # Check for explicit safe signals
        if any(k in text for k in ['no vulnerability', 'not vulnerable', 'safe', 'mitigated', 'resolved']):
            return 0, review_board_response[:500], {'parsed': False, 'fallback': 'safe_keywords'}
        # Default to safe if we can't parse (avoid false positives)
        return 0, f"Parse error: {e}", {'parsed': False, 'fallback': 'default_safe', 'error': str(e)}


def process_file(filepath, dry_run=False):
    """Process a single MA Vuln result file."""
    print(f"\n{'='*60}")
    print(f"Processing: {filepath.name}")
    print(f"{'='*60}")

    results = []
    original_preds = []
    corrected_preds = []
    ground_truths = []
    parse_stats = {'parsed': 0, 'fallback': 0}

    with open(filepath) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)

                # Skip evaluation summary lines
                if 'evaluation_summary' in data:
                    results.append(data)
                    continue

                # Get review board response
                full_discussion = data.get('full_discussion', {})
                review_board = full_discussion.get('review_board', '')

                if not review_board:
                    # Try alternate key names
                    for key in ['three_agent_discussion', 'discussion']:
                        if key in data and 'review_board' in data[key]:
                            review_board = data[key]['review_board']
                            break

                if not review_board:
                    print(f"  Warning: No review_board response for idx {data.get('idx')}")
                    results.append(data)
                    continue

                # Store original prediction
                original_pred = data.get('vuln', -1)
                original_preds.append(original_pred)
                ground_truths.append(data.get('ground_truth', data.get('target', -1)))

                # Apply corrected extraction
                corrected_pred, reasoning, stats = extract_vulnerability_decision_corrected(review_board)
                corrected_preds.append(corrected_pred)

                if stats.get('parsed'):
                    parse_stats['parsed'] += 1
                else:
                    parse_stats['fallback'] += 1

                # Update data with corrected values
                data['vuln_original'] = original_pred
                data['vuln'] = corrected_pred
                data['reasoning_corrected'] = reasoning
                data['extraction_stats'] = stats

                results.append(data)

            except json.JSONDecodeError as e:
                print(f"  Error parsing line: {e}")
                continue

    # Calculate metrics
    total = len(ground_truths)
    if total == 0:
        print("  No samples found!")
        return None

    original_correct = sum(1 for o, g in zip(original_preds, ground_truths) if o == g)
    corrected_correct = sum(1 for c, g in zip(corrected_preds, ground_truths) if c == g)

    original_vuln = sum(1 for o in original_preds if o == 1)
    corrected_vuln = sum(1 for c in corrected_preds if c == 1)
    gt_vuln = sum(1 for g in ground_truths if g == 1)

    print(f"\n  Samples: {total}")
    print(f"  Ground truth: {gt_vuln} vuln, {total - gt_vuln} safe")
    print(f"\n  Original predictions: {original_vuln} vuln ({original_vuln/total*100:.1f}%)")
    print(f"  Original accuracy: {original_correct/total*100:.1f}%")
    print(f"\n  Corrected predictions: {corrected_vuln} vuln ({corrected_vuln/total*100:.1f}%)")
    print(f"  Corrected accuracy: {corrected_correct/total*100:.1f}%")
    print(f"\n  Parse stats: {parse_stats['parsed']} parsed, {parse_stats['fallback']} fallback")

    # Show change summary
    changes = sum(1 for o, c in zip(original_preds, corrected_preds) if o != c)
    print(f"\n  Predictions changed: {changes} ({changes/total*100:.1f}%)")

    if not dry_run:
        # Save corrected results
        output_path = filepath.parent / f"{filepath.stem}_corrected.jsonl"
        with open(output_path, 'w') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')
        print(f"\n  Saved corrected results to: {output_path.name}")

        # Save metrics summary
        metrics = {
            'original_file': str(filepath),
            'corrected_file': str(output_path),
            'timestamp': datetime.now().isoformat(),
            'total_samples': total,
            'ground_truth': {'vuln': gt_vuln, 'safe': total - gt_vuln},
            'original': {
                'vuln_predictions': original_vuln,
                'accuracy': original_correct / total,
                'distribution': dict(Counter(original_preds))
            },
            'corrected': {
                'vuln_predictions': corrected_vuln,
                'accuracy': corrected_correct / total,
                'distribution': dict(Counter(corrected_preds))
            },
            'changes': changes,
            'parse_stats': parse_stats
        }

        metrics_path = filepath.parent / f"{filepath.stem}_reeval_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"  Saved metrics to: {metrics_path.name}")

        # Regenerate evaluation files (replacing originals)
        exp_name = filepath.stem.replace('_detailed_results', '')
        print(f"\n  Regenerating evaluation files...")
        regenerate_evaluation_files(corrected_preds, ground_truths, exp_name, filepath.parent)
    else:
        print("\n  [DRY RUN] No files modified")

    return {
        'file': str(filepath),
        'total': total,
        'original_acc': original_correct / total,
        'corrected_acc': corrected_correct / total,
        'changes': changes
    }


def find_ma_vuln_files():
    """Find all MA Vuln result files."""
    results_dir = Path("results")

    # Find all MA Vuln detailed result files
    patterns = [
        "**/MA-vuln-four*detailed*.jsonl",
        "**/MA-vuln-three*detailed*.jsonl",
    ]

    files = []
    for pattern in patterns:
        files.extend(results_dir.glob(pattern))

    # Exclude already corrected files
    files = [f for f in files if '_corrected' not in f.name]

    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser(description="Re-evaluate MA Vuln results with corrected extraction")
    parser.add_argument('--dry-run', action='store_true', help="Show changes without modifying files")
    parser.add_argument('--file', type=str, help="Process a specific file instead of all")
    args = parser.parse_args()

    print("="*60)
    print("MA Vuln Re-evaluation Script")
    print("="*60)

    if args.file:
        files = [Path(args.file)]
    else:
        files = find_ma_vuln_files()

    print(f"\nFound {len(files)} MA Vuln result files to process")

    if args.dry_run:
        print("[DRY RUN MODE - No files will be modified]")

    summaries = []
    for f in files:
        result = process_file(f, dry_run=args.dry_run)
        if result:
            summaries.append(result)

    # Print overall summary
    print("\n" + "="*60)
    print("OVERALL SUMMARY")
    print("="*60)

    if summaries:
        total_samples = sum(s['total'] for s in summaries)
        total_changes = sum(s['changes'] for s in summaries)
        avg_orig_acc = sum(s['original_acc'] * s['total'] for s in summaries) / total_samples
        avg_corr_acc = sum(s['corrected_acc'] * s['total'] for s in summaries) / total_samples

        print(f"\nFiles processed: {len(summaries)}")
        print(f"Total samples: {total_samples}")
        print(f"Total predictions changed: {total_changes} ({total_changes/total_samples*100:.1f}%)")
        print(f"\nAverage original accuracy: {avg_orig_acc*100:.1f}%")
        print(f"Average corrected accuracy: {avg_corr_acc*100:.1f}%")
        print(f"Accuracy improvement: {(avg_corr_acc - avg_orig_acc)*100:+.1f}%")

    print("\nDone!")


if __name__ == "__main__":
    main()
