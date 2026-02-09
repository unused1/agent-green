#!/usr/bin/env python3
"""
Regenerate vulnerability detection evaluation metrics from corrected JSONL files.

After fix_vuln_think_tag_parsing.py corrects the vuln predictions in JSONL files,
this script regenerates:
  - *_summary_vulnerability_metrics.csv (basic, conservative, strict)
  - *_per_sample_vulnerability_metrics.csv (basic, conservative, strict)
  - *_classification_report.csv and .txt (basic, conservative, strict)

Usage:
    python scripts/regenerate_vuln_evaluation.py
"""

import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VULN_DATASET = PROJECT_ROOT / "vuln_database" / "VulTrial_386_samples_balanced.jsonl"


# ---------------------------------------------------------------------------
# Evaluation functions (self-contained to avoid config import issues)
# ---------------------------------------------------------------------------

def load_ground_truth_list(file_path):
    """Load ground truth labels as ordered list."""
    labels = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line.strip())
                if 'target' in data:
                    labels.append(data['target'])
    return labels


def load_ground_truth_dict(file_path):
    """Load ground truth labels as dict keyed by idx."""
    gt = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line.strip())
                if 'idx' in data and 'target' in data:
                    gt[data['idx']] = data['target']
    return gt


def evaluate_and_save(predictions, ground_truth_labels, exp_name, results_dir):
    """Evaluate and save metrics for a single normalization variant."""
    total_samples = len(ground_truth_labels)

    accuracy = accuracy_score(ground_truth_labels, predictions)
    precision = precision_score(ground_truth_labels, predictions, zero_division=0)
    recall = recall_score(ground_truth_labels, predictions, zero_division=0)
    f1 = f1_score(ground_truth_labels, predictions, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(ground_truth_labels, predictions).ravel()

    # Per-sample metrics
    sample_metrics = []
    correct = 0
    for idx, (pred, truth) in enumerate(zip(predictions, ground_truth_labels), start=1):
        is_correct = pred == truth
        if is_correct:
            correct += 1
        if pred == 1 and truth == 1:
            ptype = "True Positive"
        elif pred == 1 and truth == 0:
            ptype = "False Positive"
        elif pred == 0 and truth == 1:
            ptype = "False Negative"
        else:
            ptype = "True Negative"
        sample_metrics.append({
            "Sample Number": idx, "Predicted": pred,
            "Ground Truth": truth, "Prediction Type": ptype,
            "Is Correct": is_correct,
        })

    # Save summary
    summary_file = os.path.join(results_dir, f"{exp_name}_summary_vulnerability_metrics.csv")
    pd.DataFrame([{
        "Accuracy": accuracy, "Precision": precision, "Recall": recall,
        "F1_Score": f1, "True_Positives": int(tp), "True_Negatives": int(tn),
        "False_Positives": int(fp), "False_Negatives": int(fn),
        "Total_Samples": total_samples, "Correct_Predictions": correct,
    }]).to_csv(summary_file, index=False)

    # Save per-sample
    per_sample_file = os.path.join(results_dir, f"{exp_name}_per_sample_vulnerability_metrics.csv")
    pd.DataFrame(sample_metrics).to_csv(per_sample_file, index=False)

    # Save classification report
    report_dict = classification_report(
        ground_truth_labels, predictions,
        target_names=['Not Vulnerable', 'Vulnerable'],
        output_dict=True,
    )
    report_df = pd.DataFrame(report_dict).transpose()
    report_csv = os.path.join(results_dir, f"{exp_name}_classification_report.csv")
    report_df.to_csv(report_csv)

    report_txt = os.path.join(results_dir, f"{exp_name}_classification_report.txt")
    with open(report_txt, 'w') as f:
        f.write(classification_report(
            ground_truth_labels, predictions,
            target_names=['Not Vulnerable', 'Vulnerable'],
        ))


# ---------------------------------------------------------------------------
# Normalization functions
# ---------------------------------------------------------------------------

def normalize_basic(pred):
    if pred is None:
        return 1
    p = int(pred)
    return 1 if p == -1 else p

def normalize_conservative(pred):
    if pred is None or pred == "":
        return 1
    try:
        p = int(pred)
        return 1 if p == -1 else p  # Treat skipped as vulnerable (conservative)
    except (ValueError, TypeError):
        return 1

def normalize_strict(pred):
    if pred is None or pred == "":
        return 0
    try:
        p = int(pred)
        return 0 if p == -1 else p  # Treat skipped as not vulnerable (strict)
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Discovery (reuse same logic as fix script)
# ---------------------------------------------------------------------------

def discover_vuln_jsonl_files():
    """Find all vuln detection JSONL files."""
    results_dir = PROJECT_ROOT / "results"
    files = []

    for jsonl_path in sorted(results_dir.rglob("*_detailed_results.jsonl")):
        name = jsonl_path.name.lower()
        parent_name = jsonl_path.parent.name.lower()
        path_str = str(jsonl_path).lower()

        # Exclude codegen and log analysis
        if "codegen" in path_str or "_code_" in path_str or "log_analysis" in path_str:
            continue

        # Include vuln files
        is_vuln = False
        if "vuln" in name or "vuln" in parent_name:
            is_vuln = True
        if name.startswith(("sa-", "Sa-")):
            if "vuln" in parent_name or "thinking" in parent_name or "rerun" in parent_name.lower():
                is_vuln = True

        if not is_vuln:
            continue

        # Skip SOTA comparison
        if "sota_comparison" in path_str:
            continue

        files.append(str(jsonl_path))

    return files


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("Regenerate Vulnerability Detection Evaluation Metrics")
    print("=" * 72)

    # Load ground truth
    print(f"Loading ground truth from {VULN_DATASET}")
    gt_labels_list = load_ground_truth_list(VULN_DATASET)
    gt_dict = load_ground_truth_dict(VULN_DATASET)
    print(f"  Ground truth: {len(gt_labels_list)} samples\n")

    # Discover files
    jsonl_files = discover_vuln_jsonl_files()
    print(f"Found {len(jsonl_files)} vuln JSONL files\n")

    for fpath in jsonl_files:
        rel_path = os.path.relpath(fpath, PROJECT_ROOT)
        results_dir = os.path.dirname(fpath)

        # Derive exp_name from filename
        basename = os.path.basename(fpath)
        exp_name = basename.replace("_detailed_results.jsonl", "")

        # Load predictions from JSONL, keyed by idx
        pred_entries = []
        with open(fpath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if "vuln" in entry and "idx" in entry:
                        pred_entries.append(entry)
                    elif "vuln" in entry:
                        # Some entries use 'ground_truth' instead of 'target'
                        # and may lack 'idx' — use positional
                        pred_entries.append(entry)
                except json.JSONDecodeError:
                    continue

        if not pred_entries:
            print(f"SKIP {rel_path}: no predictions found")
            continue

        # Build aligned predictions and ground truth arrays
        # Use idx-based matching if available, else positional
        has_idx = all("idx" in e for e in pred_entries)
        if has_idx:
            preds = []
            gt = []
            for entry in pred_entries:
                idx = entry["idx"]
                if idx in gt_dict:
                    preds.append(entry["vuln"])
                    gt.append(gt_dict[idx])
                else:
                    # Use embedded ground_truth if available
                    g = entry.get("ground_truth", entry.get("target"))
                    if g is not None:
                        preds.append(entry["vuln"])
                        gt.append(g)
        else:
            preds = [e["vuln"] for e in pred_entries]
            gt = gt_labels_list[:len(preds)]

        print(f"Processing: {rel_path}")
        print(f"  Predictions: {len(preds)}  |  GT: {len(gt)}")

        # Evaluate with all three normalization strategies
        for norm_name, norm_fn in [("basic", normalize_basic),
                                    ("conservative", normalize_conservative),
                                    ("strict", normalize_strict)]:
            normalized = [norm_fn(p) for p in preds]
            if norm_name == "basic":
                prefix = exp_name
            else:
                prefix = f"{exp_name}_{norm_name}"

            evaluate_and_save(normalized, gt, prefix, results_dir)

        print(f"  Saved: basic, conservative, strict metrics\n")

    print("=" * 72)
    print(f"Regeneration complete for {len(jsonl_files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
