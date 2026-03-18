#!/usr/bin/env python3
"""
Merge 384-sample incremental results with existing 486-sample results → 870.

For each vulnerability detection configuration:
1. Finds the existing 486-sample detailed_results.jsonl (in results/runpod_vuln_486/)
2. Finds the matching 384-sample JSONL from results/runpod_vuln_384_incremental/
3. Concatenates into an 870-sample JSONL
4. Re-evaluates metrics on all 870 predictions using VulTrial_870 ground truth
5. Saves merged results to results/runpod_vuln_870/

Usage:
    python scripts/merge_vuln_870.py [--dry-run] [--batch1-only]
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
# Existing 486-sample results (from prior merge)
EXISTING_DIR = RESULTS_DIR / "runpod_vuln_486"
# New 384-sample incremental results (from Batch 1+)
INCREMENTAL_DIR = RESULTS_DIR / "runpod_vuln_384_incremental"
# Output: merged 870-sample results
MERGED_DIR = RESULTS_DIR / "runpod_vuln_870"
# Ground truth for the full 870-sample dataset
VULN_870 = PROJECT_ROOT / "vuln_database" / "VulTrial_870_samples_balanced.jsonl"
CONSOLIDATED_CSV = RESULTS_DIR / "consolidated_performance.csv"


# ---------------------------------------------------------------------------
# Config parsing (reused from merge_vuln_incremental.py)
# ---------------------------------------------------------------------------

def parse_config_key(filename: str) -> tuple:
    """
    Parse (model, design, mode, prompting) from a result filename.
    Returns a 4-tuple used as a matching key.
    """
    design = "SA"
    if filename.startswith("DA-") or "_DA-" in filename:
        design = "DA"
    elif filename.startswith("MA-") or "_MA-" in filename:
        design = "MA"

    prompting = None
    if "zero" in filename.lower():
        prompting = "zero-shot"
    elif "few" in filename.lower():
        prompting = "few-shot"

    model = None
    mode = None
    if "Nemotron-Super-49B" in filename:
        model = "Nemotron-Super-49B"
        mode = "thinking" if any(x in filename for x in ["Thinking", "_think"]) else "instruct"
    elif "Nemotron-Nano-8B" in filename:
        model = "Nemotron-Nano-8B"
        mode = "thinking" if any(x in filename for x in ["Thinking", "_think"]) else "instruct"
    elif "Qwen3-30B" in filename:
        if "Thinking" in filename:
            model = "Qwen3-30B-A3B-Thinking"
            mode = "thinking"
        elif "Instruct" in filename:
            model = "Qwen3-30B-A3B-Instruct"
            mode = "instruct"
    elif "Qwen3-4B" in filename:
        if "Thinking" in filename:
            model = "Qwen3-4B-Thinking"
            mode = "thinking"
        elif "Instruct" in filename:
            model = "Qwen3-4B-Instruct"
            mode = "instruct"

    if model and "Nemotron" in model:
        fn_lower = filename.lower()
        if "thinking" in fn_lower or "_think" in fn_lower:
            mode = "thinking"
        else:
            mode = "instruct"

    return (model, design, mode, prompting)


def parse_config_from_path(path: str) -> tuple:
    """Parse config key from a full file path."""
    p = Path(path)
    filename = p.name
    dirname = p.parent.name

    key = parse_config_key(filename)
    if key[0] is None:
        key = parse_config_key(dirname)

    model, design, mode, prompting = key

    if model and "Nemotron" in model and mode == "instruct":
        path_lower = str(path).lower()
        if "_thinking" in path_lower or "_think" in path_lower:
            mode = "thinking"

    return (model, design, mode, prompting)


# ---------------------------------------------------------------------------
# Ground truth loading
# ---------------------------------------------------------------------------

def load_ground_truth_dict(file_path: Path) -> dict:
    """Load ground truth labels as dict keyed by idx."""
    gt = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line.strip())
                if "idx" in data and "target" in data:
                    gt[data["idx"]] = data["target"]
    return gt


# ---------------------------------------------------------------------------
# Normalization (reused)
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
        return 1 if p == -1 else p
    except (ValueError, TypeError):
        return 1


def normalize_strict(pred):
    if pred is None or pred == "":
        return 0
    try:
        p = int(pred)
        return 0 if p == -1 else p
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

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
            "Sample Number": idx,
            "Predicted": pred,
            "Ground Truth": truth,
            "Prediction Type": ptype,
            "Is Correct": is_correct,
        })

    # Save summary
    summary_file = os.path.join(results_dir, f"{exp_name}_summary_vulnerability_metrics.csv")
    pd.DataFrame([{
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1_Score": f1,
        "True_Positives": int(tp),
        "True_Negatives": int(tn),
        "False_Positives": int(fp),
        "False_Negatives": int(fn),
        "Total_Samples": total_samples,
        "Correct_Predictions": correct,
    }]).to_csv(summary_file, index=False)

    # Save per-sample
    per_sample_file = os.path.join(results_dir, f"{exp_name}_per_sample_vulnerability_metrics.csv")
    pd.DataFrame(sample_metrics).to_csv(per_sample_file, index=False)

    # Save classification report
    report_dict = classification_report(
        ground_truth_labels,
        predictions,
        target_names=["Not Vulnerable", "Vulnerable"],
        output_dict=True,
    )
    report_df = pd.DataFrame(report_dict).transpose()
    report_csv = os.path.join(results_dir, f"{exp_name}_classification_report.csv")
    report_df.to_csv(report_csv)

    report_txt = os.path.join(results_dir, f"{exp_name}_classification_report.txt")
    with open(report_txt, "w") as f:
        f.write(classification_report(
            ground_truth_labels,
            predictions,
            target_names=["Not Vulnerable", "Vulnerable"],
        ))

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "total": total_samples,
        "correct": correct,
    }


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_existing_486_jsonl_files() -> dict:
    """Find existing 486-sample JSONL files in runpod_vuln_486/."""
    existing = {}
    if not EXISTING_DIR.exists():
        print(f"WARNING: {EXISTING_DIR} not found")
        return existing

    for jsonl_path in sorted(EXISTING_DIR.glob("*_detailed_results.jsonl")):
        if "_conservative_" in jsonl_path.name or "_strict_" in jsonl_path.name:
            continue
        key = parse_config_from_path(str(jsonl_path))
        if key[0] is not None:
            existing[key] = str(jsonl_path)

    return existing


def find_incremental_384_jsonl_files() -> dict:
    """Find 384-sample incremental JSONL files."""
    incremental = {}
    if not INCREMENTAL_DIR.exists():
        print(f"ERROR: Incremental directory not found: {INCREMENTAL_DIR}")
        return incremental

    for jsonl_path in sorted(INCREMENTAL_DIR.rglob("*_detailed_results.jsonl")):
        if "_conservative_" in jsonl_path.name or "_strict_" in jsonl_path.name:
            continue
        key = parse_config_from_path(str(jsonl_path))
        if key[0] is not None:
            incremental[key] = str(jsonl_path)

    return incremental


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------

def load_jsonl_entries(path: str) -> list:
    """Load all entries from a JSONL file."""
    csv.field_size_limit(sys.maxsize)
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def merge_one_config(
    key: tuple,
    old_path: str,
    new_path: str,
    gt_dict: dict,
    output_dir: Path,
    dry_run: bool = False,
) -> dict | None:
    """Merge a single config's results and re-evaluate."""
    model, design, mode, prompting = key
    label = f"{model} {design} {mode} {prompting}"

    old_entries = load_jsonl_entries(old_path)
    new_entries = load_jsonl_entries(new_path)

    # Verify no idx overlap
    old_idx = set(e.get("idx") for e in old_entries if "idx" in e)
    new_idx = set(e.get("idx") for e in new_entries if "idx" in e)
    overlap = old_idx & new_idx
    if overlap:
        print(f"  ERROR {label}: {len(overlap)} overlapping idx values!")
        return None

    # Merge
    merged = old_entries + new_entries
    merged.sort(key=lambda e: e.get("idx", 0))

    # Build aligned predictions and ground truth
    preds_raw = []
    gt_labels = []
    missing_gt = 0
    for entry in merged:
        idx = entry.get("idx")
        if idx is None:
            continue
        pred = entry.get("vuln")
        if idx in gt_dict:
            preds_raw.append(pred)
            gt_labels.append(gt_dict[idx])
        else:
            missing_gt += 1

    if missing_gt > 0:
        print(f"  WARNING {label}: {missing_gt} entries missing from ground truth")

    print(f"  {label}: {len(old_entries)} + {len(new_entries)} = {len(merged)} merged, "
          f"{len(preds_raw)} matched to GT")

    if dry_run:
        return {"merged_count": len(merged), "matched_gt": len(preds_raw)}

    # Derive experiment name from the old (486) JSONL filename
    old_basename = Path(old_path).name.replace("_detailed_results.jsonl", "")

    config_dir = output_dir
    config_dir.mkdir(parents=True, exist_ok=True)

    # Save merged JSONL
    merged_jsonl = config_dir / f"{old_basename}_detailed_results.jsonl"
    with open(merged_jsonl, "w", encoding="utf-8") as f:
        for entry in merged:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Evaluate with all three normalization strategies
    results = {}
    for norm_name, norm_fn in [("basic", normalize_basic),
                                ("conservative", normalize_conservative),
                                ("strict", normalize_strict)]:
        normalized = [norm_fn(p) for p in preds_raw]
        if norm_name == "basic":
            prefix = old_basename
        else:
            prefix = f"{old_basename}_{norm_name}"

        metrics = evaluate_and_save(normalized, gt_labels, prefix, str(config_dir))
        if norm_name == "basic":
            results = metrics

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Merge 384-sample incremental results with 486-sample results → 870"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be merged without writing files")
    parser.add_argument("--batch1-only", action="store_true",
                        help="Only merge SA instruct configs (Batch 1)")
    args = parser.parse_args()

    print("=" * 72)
    print("Merge Vulnerability Detection Results: 486 + 384 → 870")
    print("=" * 72)

    # Load ground truth
    if not VULN_870.exists():
        print(f"ERROR: Ground truth file not found: {VULN_870}")
        return 1

    gt_dict = load_ground_truth_dict(VULN_870)
    print(f"Ground truth: {len(gt_dict)} samples from {VULN_870.name}")

    # Find existing 486 results
    print("\nFinding existing 486-sample results...")
    existing = find_existing_486_jsonl_files()
    print(f"  Found {len(existing)} existing configs")

    # Find incremental 384 results
    print("\nFinding 384-sample incremental results...")
    incremental = find_incremental_384_jsonl_files()
    print(f"  Found {len(incremental)} incremental configs")

    if not incremental:
        print("\nNo incremental results found.")
        print(f"Expected directory: {INCREMENTAL_DIR}")
        return 1

    # Optional: filter to Batch 1 only (SA instruct)
    if args.batch1_only:
        incremental = {k: v for k, v in incremental.items()
                       if k[1] == "SA" and k[2] == "instruct"}
        print(f"  Filtered to Batch 1 (SA instruct): {len(incremental)} configs")

    # Match configs
    common_keys = set(existing.keys()) & set(incremental.keys())
    only_existing = set(existing.keys()) - set(incremental.keys())
    only_incremental = set(incremental.keys()) - set(existing.keys())

    print(f"\nConfig matching:")
    print(f"  Matched: {len(common_keys)}")
    print(f"  Only in existing (no incremental): {len(only_existing)}")
    print(f"  Only in incremental (no existing): {len(only_incremental)}")

    if only_incremental:
        print("\n  Incremental results with no existing match:")
        for key in sorted(only_incremental, key=str):
            print(f"    {key}")

    if not common_keys:
        print("\nNo matching configs found. Check filename patterns.")
        return 1

    # Merge
    print(f"\n{'='*72}")
    print(f"Merging {len(common_keys)} configurations...")
    print(f"Output: {MERGED_DIR}")
    print(f"{'='*72}\n")

    success = 0
    failed = 0
    all_metrics = []

    for key in sorted(common_keys, key=str):
        metrics = merge_one_config(
            key=key,
            old_path=existing[key],
            new_path=incremental[key],
            gt_dict=gt_dict,
            output_dir=MERGED_DIR,
            dry_run=args.dry_run,
        )
        if metrics:
            success += 1
            all_metrics.append({"config": key, "metrics": metrics})
        else:
            failed += 1

    # Summary
    print(f"\n{'='*72}")
    print("Summary")
    print(f"{'='*72}")
    print(f"  Configs merged:  {success}")
    print(f"  Configs failed:  {failed}")

    if not args.dry_run and all_metrics:
        sample_counts = Counter(m["metrics"]["total"] for m in all_metrics)
        print(f"\n  Sample counts: {dict(sample_counts)}")

        for m in all_metrics:
            met = m["metrics"]
            cm_total = met["tp"] + met["tn"] + met["fp"] + met["fn"]
            if cm_total != met["total"]:
                print(f"  WARNING: CM total ({cm_total}) != total ({met['total']}) for {m['config']}")

        f1_scores = [m["metrics"]["f1_score"] for m in all_metrics]
        print(f"\n  F1 range: {min(f1_scores):.4f} - {max(f1_scores):.4f}")
        print(f"  F1 mean:  {sum(f1_scores)/len(f1_scores):.4f}")

    print(f"\nMerge {'(dry run) ' if args.dry_run else ''}complete.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
