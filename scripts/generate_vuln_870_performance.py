#!/usr/bin/env python3
"""Generate VulTrial-870 performance metrics by combining 486 + 384-incr predictions.

For each config (model × design × mode × prompting), merges predictions from
VulTrial-486 and VulTrial-384-incr JONLs and computes metrics on the combined
870 samples. Outputs rows suitable for appending to consolidated_performance.csv.

Usage:
    python scripts/generate_vuln_870_performance.py
"""

import csv
import json
import os
import sys
from pathlib import Path

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DIR_486 = RESULTS_DIR / "runpod_vuln_486"
DIR_384 = RESULTS_DIR / "runpod_vuln_384_incremental"
OUTPUT_CSV = RESULTS_DIR / "consolidated_performance.csv"

csv.field_size_limit(sys.maxsize)


def normalize_vuln_basic(pred):
    """Basic normalization: None/-1 → 1 (conservative: assume vulnerable)."""
    if pred is None:
        return 1
    p = int(pred)
    return 1 if p == -1 else p


def parse_config_from_filename(filename: str) -> dict:
    """Extract (design, prompting, model, mode) from JSONL filename."""
    # Import the parser from consolidate_performance
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from consolidate_performance import parse_config_from_filename as _parse
    from consolidate_performance import infer_config_from_path as _infer_path

    parsed = _parse(filename)

    # Handle Nemotron thinking via _thinking suffix
    if parsed.get("model_family") == "Nemotron" or (
        parsed.get("model") and "Nemotron" in str(parsed["model"])
    ):
        if "_thinking_" in filename or filename.endswith("_thinking_detailed_results.jsonl"):
            parsed["mode"] = "thinking"
        elif parsed["mode"] is None:
            parsed["mode"] = "instruct"

    if parsed.get("task") is None:
        parsed["task"] = "vulnerability_detection"

    return parsed


def load_predictions(jsonl_path: Path) -> dict:
    """Load JSONL, return {idx: (pred_norm, gt)} dict."""
    preds = {}
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            idx = entry.get("idx")
            pred = entry.get("vuln")
            gt = entry.get("ground_truth", entry.get("target"))
            if idx is None or gt is None:
                continue
            pred_norm = normalize_vuln_basic(pred)
            preds[int(idx)] = (pred_norm, int(gt))
    return preds


def config_key(parsed: dict) -> tuple:
    """Create a hashable config key."""
    return (
        parsed.get("model"),
        parsed.get("design"),
        parsed.get("mode"),
        parsed.get("prompting"),
    )


SUBMITTED_COMMIT = "c829127"  # pre-P0 consolidated_performance.csv = as-submitted metrics


def load_submitted_870_records(fieldnames):
    """Load the submitted (pre-P0) VulTrial-870 rows from git, for provenance.

    Tagged variant=freeform / label_rule=original_submitted so the live catalog is
    self-contained (submitted + corrected + constrained all queryable in one file).
    """
    import subprocess
    try:
        blob = subprocess.run(
            ["git", "show", f"{SUBMITTED_COMMIT}:results/consolidated_performance.csv"],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, check=True,
        ).stdout
    except Exception as e:  # noqa: BLE001
        print(f"  WARN: could not load submitted rows from git {SUBMITTED_COMMIT}: {e}")
        return []
    out = []
    for row in csv.DictReader(blob.splitlines()):
        if row.get("dataset") != "VulTrial-870":
            continue
        row["variant"] = "freeform"
        row["label_rule"] = "original_submitted"
        out.append({k: row.get(k, "") for k in fieldnames})
    return out


def main():
    print("Generating VulTrial-870 performance metrics...")
    print(f"  486 dir: {DIR_486}")
    print(f"  384 dir: {DIR_384}")

    # Index all JONLs by config
    configs_486 = {}
    configs_384 = {}

    for dir_path, configs_dict, label in [
        (DIR_486, configs_486, "486"),
        (DIR_384, configs_384, "384-incr"),
    ]:
        jsonl_files = sorted(dir_path.glob("*_detailed_results.jsonl"))
        jsonl_files = [
            f for f in jsonl_files
            if "_conservative_" not in f.name
            and "_strict_" not in f.name
        ]
        print(f"\n  {label}: {len(jsonl_files)} JSONL files")

        for jsonl_path in jsonl_files:
            parsed = parse_config_from_filename(jsonl_path.name)
            if not parsed.get("model") or not parsed.get("prompting"):
                print(f"    Skipping {jsonl_path.name}: missing config")
                continue
            key = config_key(parsed)
            configs_dict[key] = {
                "path": jsonl_path,
                "parsed": parsed,
            }

    # Match configs
    all_keys = set(configs_486.keys()) | set(configs_384.keys())
    matched = set(configs_486.keys()) & set(configs_384.keys())
    only_486 = set(configs_486.keys()) - set(configs_384.keys())
    only_384 = set(configs_384.keys()) - set(configs_486.keys())

    print(f"\n  Matched configs: {len(matched)}")
    if only_486:
        print(f"  Only in 486: {len(only_486)}")
        for k in sorted(only_486):
            print(f"    {k}")
    if only_384:
        print(f"  Only in 384: {len(only_384)}")
        for k in sorted(only_384):
            print(f"    {k}")

    # Combine and evaluate
    records_870 = []
    for key in sorted(matched):
        model, design, mode, prompting = key
        info_486 = configs_486[key]
        info_384 = configs_384[key]
        parsed = info_486["parsed"]

        preds_486 = load_predictions(info_486["path"])
        preds_384 = load_predictions(info_384["path"])

        # Check for idx overlap (should be none)
        overlap = set(preds_486.keys()) & set(preds_384.keys())
        if overlap:
            print(f"  WARNING: {len(overlap)} overlapping idx in {key}")

        # Combine
        all_preds = {}
        all_preds.update(preds_486)
        all_preds.update(preds_384)

        predictions = [v[0] for v in all_preds.values()]
        ground_truths = [v[1] for v in all_preds.values()]
        skipped = sum(1 for v in all_preds.values() if v[0] == 1 and v[1] is not None)

        if len(predictions) == 0:
            print(f"  Skipping {key}: no predictions")
            continue

        acc = accuracy_score(ground_truths, predictions)
        prec = precision_score(ground_truths, predictions, zero_division=0)
        rec = recall_score(ground_truths, predictions, zero_division=0)
        f1 = f1_score(ground_truths, predictions, zero_division=0)
        tn, fp, fn, tp = confusion_matrix(ground_truths, predictions, labels=[0, 1]).ravel()
        correct = sum(p == g for p, g in zip(predictions, ground_truths))

        record = {
            "model": parsed["model"],
            "model_family": parsed.get("model_family"),
            "parameters_b": parsed.get("parameters_b"),
            "design": parsed.get("design", "SA"),
            "task": "vulnerability_detection",
            "dataset": "VulTrial-870",
            "mode": mode,
            "prompting": prompting,
            "thinking_enabled": mode == "thinking",
            "accuracy": round(acc, 6),
            "precision": round(prec, 6),
            "recall": round(rec, 6),
            "f1_score": round(f1, 6),
            "true_positives": int(tp),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "pass_at_1": "",
            "passed_samples": "",
            "failed_samples": "",
            "total_samples": len(predictions),
            "correct_predictions": correct,
            "skipped_samples": 0,
            "source_type": "runpod_vuln_870_combined",
            "source_file": f"{info_486['path']}; {info_384['path']}",
            # Cataloging dimensions (see docs/scratch memos):
            #   variant     = prompt scheme (freeform submitted prompts here)
            #   label_rule  = binarisation/parser used for these labels
            "variant": "freeform",
            "label_rule": "affirm_optionA" if parsed.get("design") == "MA" else "canonical",
        }
        records_870.append(record)

        print(f"  {design:8s} {model:30s} {mode:10s} {prompting:10s} "
              f"n={len(predictions)} F1={f1:.3f} Acc={acc:.3f}")

    print(f"\nGenerated {len(records_870)} VulTrial-870 records")

    # Load existing consolidated_performance.csv and append
    existing = []
    with open(OUTPUT_CSV, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        for row in reader:
            # Remove any existing VulTrial-870 rows (re-run safe)
            if row.get("dataset") == "VulTrial-870":
                continue
            existing.append(row)

    # Ensure cataloging columns exist; default non-870 rows to single-state.
    for col in ("variant", "label_rule"):
        if col not in fieldnames:
            fieldnames.append(col)
    for row in existing:
        row.setdefault("variant", "freeform")
        row.setdefault("label_rule", "original")
        if not row.get("variant"):
            row["variant"] = "freeform"
        if not row.get("label_rule"):
            row["label_rule"] = "original"

    # Interleave the submitted (pre-P0) VulTrial-870 rows from git for provenance.
    submitted_870 = load_submitted_870_records(fieldnames)
    print(f"Existing records (non-870): {len(existing)}  | submitted-870 from git: {len(submitted_870)}")

    # Write back
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
        for rec in submitted_870 + records_870:
            writer.writerow({k: rec.get(k, "") for k in fieldnames})

    total = len(existing) + len(submitted_870) + len(records_870)
    print(f"Written {total} records to {OUTPUT_CSV} "
          f"({len(existing)} non-870 + {len(submitted_870)} submitted-870 + {len(records_870)} freeform-870)")
    print(f"  ({len(existing)} existing + {len(records_870)} VulTrial-870)")

    # Summary
    print(f"\n{'='*60}")
    print("VulTrial-870 SUMMARY")
    print(f"{'='*60}")
    import pandas as pd
    df = pd.DataFrame(records_870)
    print(f"\nBy design:")
    print(df.groupby("design")["f1_score"].agg(["mean", "min", "max"]).round(3).to_string())
    print(f"\nBy model:")
    print(df.groupby("model")["f1_score"].agg(["mean", "min", "max"]).round(3).to_string())
    print(f"\nBest config:")
    best = df.loc[df["f1_score"].idxmax()]
    print(f"  {best['design']} {best['model']} {best['mode']} {best['prompting']} "
          f"F1={best['f1_score']:.3f} Acc={best['accuracy']:.3f}")


if __name__ == "__main__":
    main()
