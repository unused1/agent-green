#!/usr/bin/env python3
"""
Merge incremental 100-sample vulnerability detection results with existing 386-sample results.

For each of the 48 vulnerability detection configurations:
1. Finds the existing 386-sample detailed_results.jsonl
2. Finds the matching 100-sample JSONL from results/runpod_vuln_incremental/
3. Concatenates into a 486-sample JSONL
4. Re-evaluates metrics on all 486 predictions using VulTrial_486 ground truth
5. Saves merged results to results/runpod_vuln_486/

Usage:
    python scripts/merge_vuln_incremental.py [--dry-run]
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
INCREMENTAL_DIR = RESULTS_DIR / "runpod_vuln_incremental"
MERGED_DIR = RESULTS_DIR / "runpod_vuln_486"
VULN_486 = PROJECT_ROOT / "vuln_database" / "VulTrial_486_samples_balanced.jsonl"
CONSOLIDATED_CSV = RESULTS_DIR / "consolidated_performance.csv"


# ---------------------------------------------------------------------------
# Config parsing (adapted from consolidate_performance.py)
# ---------------------------------------------------------------------------

def parse_config_key(filename: str) -> tuple:
    """
    Parse (model, design, mode, prompting) from a result filename.

    Returns a 4-tuple used as a matching key between old and new results.
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

    # Nemotron mode: check ENABLE_REASONING from the filename pattern
    # Nemotron-Nano-8B instruct vs thinking is encoded via parent dir or filename suffix
    if model and "Nemotron" in model:
        fn_lower = filename.lower()
        parent_lower = ""
        # Check for thinking indicators
        if "thinking" in fn_lower or "_think" in fn_lower:
            mode = "thinking"
        else:
            # Nemotron instruct is default
            mode = "instruct"

    return (model, design, mode, prompting)


def parse_config_from_path(path: str) -> tuple:
    """Parse config key from a full file path, using both filename and directory name."""
    p = Path(path)
    filename = p.name
    dirname = p.parent.name
    full_path = str(path)

    # Parse from filename first
    key = parse_config_key(filename)

    # If model not found in filename, try directory name
    if key[0] is None:
        key = parse_config_key(dirname)

    model, design, mode, prompting = key

    # For Nemotron: mode is often encoded in parent directory name, not filename
    # e.g., nemotron_8b_vuln_SA-few_thinking/Sa-few_nvidia-...
    if model and "Nemotron" in model and mode == "instruct":
        # Check the full path for thinking indicators
        path_lower = full_path.lower()
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
# Evaluation (reused from regenerate_vuln_evaluation.py)
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
# Discovery: find existing 386-sample results
# ---------------------------------------------------------------------------

def find_existing_vuln_jsonl_files() -> dict:
    """
    Find existing 386-sample vuln detection JSONL files.

    Uses consolidated_performance.csv source_file column to find the parent
    directory, then locates the detailed_results.jsonl in that directory.

    Returns dict mapping config_key → file_path.
    """
    existing = {}

    if not CONSOLIDATED_CSV.exists():
        print(f"WARNING: {CONSOLIDATED_CSV} not found, falling back to directory scan")
        return _find_existing_by_scan()

    df = pd.read_csv(CONSOLIDATED_CSV)
    vuln_df = df[df["task"] == "vulnerability_detection"]

    for _, row in vuln_df.iterrows():
        source_file = row["source_file"]
        source_dir = Path(source_file).parent

        # Find the detailed_results.jsonl in the same directory
        jsonl_files = list(source_dir.glob("*_detailed_results.jsonl"))
        if not jsonl_files:
            # Some source_file paths may point to a results/ subdirectory
            jsonl_files = list(source_dir.glob("results/*_detailed_results.jsonl"))

        for jf in jsonl_files:
            key = parse_config_from_path(str(jf))
            if key[0] is not None:
                existing[key] = str(jf)

    return existing


def _find_existing_by_scan() -> dict:
    """Fallback: scan results/ for vuln JSONL files."""
    existing = {}
    skip_dirs = {"runpod_vuln_incremental", "runpod_vuln_486", "sota_comparison",
                 "rq2_nm8b_ma_rerun_20260103", "context_overflow_test"}

    for jsonl_path in sorted(RESULTS_DIR.rglob("*_detailed_results.jsonl")):
        path_str = str(jsonl_path).lower()

        # Skip non-vuln files
        if "codegen" in path_str or "_code_" in path_str or "log_analysis" in path_str:
            continue
        if not ("vuln" in path_str or jsonl_path.name.lower().startswith(("sa-", "da-", "ma-"))):
            continue
        # Skip excluded dirs
        if any(sd in jsonl_path.parts for sd in skip_dirs):
            continue
        # Skip alternative normalization
        if "_conservative_" in jsonl_path.name or "_strict_" in jsonl_path.name:
            continue

        key = parse_config_from_path(str(jsonl_path))
        if key[0] is not None:
            # Keep the one from highest-priority source
            if key in existing:
                # Simple heuristic: prefer rerun > rq2 > original
                old_path = existing[key]
                if "rerun" in str(jsonl_path) and "rerun" not in old_path:
                    existing[key] = str(jsonl_path)
                elif "rq2" in str(jsonl_path) and "rq2" not in old_path and "rerun" not in old_path:
                    existing[key] = str(jsonl_path)
            else:
                existing[key] = str(jsonl_path)

    return existing


def find_incremental_jsonl_files() -> dict:
    """Find 100-sample incremental JSONL files in results/runpod_vuln_incremental/."""
    incremental = {}

    if not INCREMENTAL_DIR.exists():
        print(f"ERROR: Incremental results directory not found: {INCREMENTAL_DIR}")
        return incremental

    for jsonl_path in sorted(INCREMENTAL_DIR.rglob("*_detailed_results.jsonl")):
        # Skip alternative normalization files
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
    """
    Merge a single config's results and re-evaluate.

    Returns metrics dict or None on failure.
    """
    model, design, mode, prompting = key
    label = f"{model} {design} {mode} {prompting}"

    # Load entries
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

    # Build aligned predictions and ground truth using idx
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

    # Derive experiment name from the new JSONL filename
    new_basename = Path(new_path).name.replace("_detailed_results.jsonl", "")

    # Create output directory (flat structure under runpod_vuln_486/)
    config_dir = output_dir
    config_dir.mkdir(parents=True, exist_ok=True)

    # Save merged JSONL
    merged_jsonl = config_dir / f"{new_basename}_detailed_results.jsonl"
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
            prefix = new_basename
        else:
            prefix = f"{new_basename}_{norm_name}"

        metrics = evaluate_and_save(normalized, gt_labels, prefix, str(config_dir))
        if norm_name == "basic":
            results = metrics

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Merge incremental vuln detection results with existing 386-sample results"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be merged without writing files")
    args = parser.parse_args()

    print("=" * 72)
    print("Merge Incremental Vulnerability Detection Results")
    print("=" * 72)

    # Load ground truth
    if not VULN_486.exists():
        print(f"ERROR: Ground truth file not found: {VULN_486}")
        print("Run scripts/prepare_vuln_incremental.py first.")
        return 1

    gt_dict = load_ground_truth_dict(VULN_486)
    print(f"Ground truth: {len(gt_dict)} samples from {VULN_486.name}")

    # Find existing results
    print("\nFinding existing 386-sample results...")
    existing = find_existing_vuln_jsonl_files()
    print(f"  Found {len(existing)} existing configs")

    # Find incremental results
    print("\nFinding incremental 100-sample results...")
    incremental = find_incremental_jsonl_files()
    print(f"  Found {len(incremental)} incremental configs")

    if not incremental:
        print("\nNo incremental results found. Run the RunPod experiments first.")
        print(f"Expected directory: {INCREMENTAL_DIR}")
        return 1

    # Match configs
    common_keys = set(existing.keys()) & set(incremental.keys())
    only_existing = set(existing.keys()) - set(incremental.keys())
    only_incremental = set(incremental.keys()) - set(existing.keys())

    print(f"\nConfig matching:")
    print(f"  Matched: {len(common_keys)}")
    print(f"  Only in existing (no incremental): {len(only_existing)}")
    print(f"  Only in incremental (no existing): {len(only_incremental)}")

    if only_existing:
        print("\n  Missing incremental results for:")
        for key in sorted(only_existing, key=str):
            print(f"    {key}")

    if only_incremental:
        print("\n  Incremental results with no existing match:")
        for key in sorted(only_incremental, key=str):
            print(f"    {key}")

    if not common_keys:
        print("\nNo matching configs found. Check filename patterns.")
        return 1

    # Merge each config
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

    # Verification summary
    print(f"\n{'='*72}")
    print("Verification Summary")
    print(f"{'='*72}")
    print(f"  Configs merged:  {success}")
    print(f"  Configs failed:  {failed}")
    print(f"  Expected:        48")

    if not args.dry_run and all_metrics:
        # Check all have 486 samples
        sample_counts = Counter(m["metrics"]["total"] for m in all_metrics)
        print(f"\n  Sample counts: {dict(sample_counts)}")

        # Check confusion matrix sums
        for m in all_metrics:
            met = m["metrics"]
            cm_total = met["tp"] + met["tn"] + met["fp"] + met["fn"]
            if cm_total != met["total"]:
                print(f"  WARNING: CM total ({cm_total}) != total ({met['total']}) for {m['config']}")

        # F1 summary
        f1_scores = [m["metrics"]["f1_score"] for m in all_metrics]
        print(f"\n  F1 range: {min(f1_scores):.4f} - {max(f1_scores):.4f}")
        print(f"  F1 mean:  {sum(f1_scores)/len(f1_scores):.4f}")

    print(f"\nMerge {'(dry run) ' if args.dry_run else ''}complete.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
