#!/usr/bin/env python3
"""
Consolidate performance metrics from multiple experiments into a single aggregated file.

This script:
1. Finds all *_summary_vulnerability_metrics.csv files (vulnerability detection)
2. Finds all *_evaluation.json files (code generation)
3. Finds all *_summary_metrics.csv files in runpod_log_analysis/ (log analysis)
4. Parses experiment configuration from directory structure and filenames
5. Handles deduplication preferring newer/rerun data
6. Outputs a consolidated CSV file

Supported experiment sources:
- results/rq2_cross_architecture/nemotron_* (Nemotron 8B and 49B)
- results/mars_rerun/ (Qwen3 4B vuln detection on MARS)
- results/mars_codegen/ (Qwen3 4B code generation on MARS)
- results/runpod/ (Qwen3 4B vuln detection on RunPod)
- results/runpod_codegen/ (Qwen3 4B/30B code generation on RunPod)
- results/runpod_codegen_rerun/ (Qwen3 4B/30B code generation reruns with reasoning on RunPod)
- results/runpod_rerun/ (Qwen3 4B/30B vuln detection reruns on RunPod)
- results/runpod_rq2_pod1-8/ (Qwen3 DA/MA experiments on RunPod)
- results/runpod_log_analysis/ (Log analysis SA/DA/MA experiments on RunPod)

Usage:
    python scripts/consolidate_performance.py [--output results/consolidated_performance.csv]
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from collections import Counter

csv.field_size_limit(sys.maxsize)

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


def parse_config_from_filename(filename: str) -> dict:
    """Parse experiment config from result filename."""
    info = {
        "model": None,
        "model_family": None,
        "parameters_b": None,
        "mode": None,
        "design": "SA",  # Default to single-agent
        "task": None,
        "prompting": None,
    }

    if not filename:
        return info

    # Parse design type (NoAgent, SA, DA, MA)
    if filename.startswith("NA-") or "_NA-" in filename:
        info["design"] = "NoAgent"
    elif filename.startswith("DA-") or "_DA-" in filename:
        info["design"] = "DA"
    elif filename.startswith("MA-") or "_MA-" in filename:
        info["design"] = "MA"
    elif filename.startswith("Sa-") or filename.startswith("SA-"):
        info["design"] = "SA"

    # Parse prompting strategy
    if "zero" in filename.lower():
        info["prompting"] = "zero-shot"
    elif "few" in filename.lower():
        info["prompting"] = "few-shot"

    # Parse Nemotron models
    if "Nemotron-Super-49B" in filename or "Nemotron-Super-49B-v1_5" in filename:
        info["model"] = "Nemotron-Super-49B"
        info["model_family"] = "Nemotron"
        info["parameters_b"] = 49
    elif "Nemotron-Nano-8B" in filename:
        info["model"] = "Nemotron-Nano-8B"
        info["model_family"] = "Nemotron"
        info["parameters_b"] = 8

    # Parse Qwen3 models
    elif "Qwen3-30B-A3B" in filename:
        info["model_family"] = "Qwen"
        info["parameters_b"] = 30
        if "Thinking" in filename:
            info["model"] = "Qwen3-30B-A3B-Thinking"
            info["mode"] = "thinking"
        elif "Instruct" in filename:
            info["model"] = "Qwen3-30B-A3B-Instruct"
            info["mode"] = "instruct"
    elif "Qwen3-4B" in filename:
        info["model_family"] = "Qwen"
        info["parameters_b"] = 4
        if "Thinking" in filename:
            info["model"] = "Qwen3-4B-Thinking"
            info["mode"] = "thinking"
        elif "Instruct" in filename:
            info["model"] = "Qwen3-4B-Instruct"
            info["mode"] = "instruct"

    return info


def infer_config_from_path(file_path: str) -> dict:
    """Infer experiment config from file path."""
    info = {
        "model": None,
        "model_family": None,
        "parameters_b": None,
        "mode": None,
        "design": "SA",
        "task": None,
        "prompting": None,
    }

    path_str = str(file_path).lower()

    # Nemotron from rq2_cross_architecture
    if "nemotron_49b" in path_str:
        info["model"] = "Nemotron-Super-49B"
        info["model_family"] = "Nemotron"
        info["parameters_b"] = 49
    elif "nemotron_8b" in path_str:
        info["model"] = "Nemotron-Nano-8B"
        info["model_family"] = "Nemotron"
        info["parameters_b"] = 8

    # Task detection
    if "runpod_log_analysis" in path_str or "log-analysis" in path_str:
        info["task"] = "log_analysis"
    elif "_vuln_" in path_str or "/vuln" in path_str:
        info["task"] = "vulnerability_detection"
    elif "_code_" in path_str or "codegen" in path_str:
        info["task"] = "code_generation"
    # Infer from filename pattern
    elif "vuln" in path_str:
        info["task"] = "vulnerability_detection"
    elif "code" in path_str:
        info["task"] = "code_generation"
    # Infer from directory structure
    elif "/runpod_codegen/" in file_path or "/mars_codegen/" in file_path:
        info["task"] = "code_generation"
    elif "/runpod_rerun/" in file_path or "/runpod/" in file_path or "/mars_rerun/" in file_path or "/mars/" in file_path:
        info["task"] = "vulnerability_detection"

    # Design detection
    if "_na-" in path_str or "/na-" in path_str or "na-vuln" in path_str:
        info["design"] = "NoAgent"
    elif "_da-" in path_str or "/da-" in path_str:
        info["design"] = "DA"
    elif "_ma-" in path_str or "/ma-" in path_str:
        info["design"] = "MA"
    elif "_sa-" in path_str or "/sa-" in path_str:
        info["design"] = "SA"

    # Mode
    if "_thinking" in path_str or "thinking" in path_str or "_think" in path_str:
        info["mode"] = "thinking"
    elif "_instruct" in path_str or "baseline" in path_str or "instruct" in path_str:
        info["mode"] = "instruct"

    # Prompting
    if "zero" in path_str:
        info["prompting"] = "zero-shot"
    elif "few" in path_str:
        info["prompting"] = "few-shot"

    return info


def get_source_type(file_path: str) -> str:
    """Determine source type from file path."""
    path_str = str(file_path)

    if "runpod_log_analysis" in path_str:
        return "runpod_log_analysis"
    elif "runpod_vuln_486" in path_str:
        return "runpod_vuln_486"
    elif "runpod_vuln_incremental" in path_str:
        return "runpod_vuln_incremental"
    elif "rq2_cross_architecture" in path_str:
        return "rq2_cross_architecture"
    elif "mars_rerun" in path_str:
        return "mars_rerun"
    elif "mars_codegen" in path_str:
        return "mars_codegen"
    elif "mars" in path_str and "rerun" not in path_str:
        return "mars"
    elif "runpod_codegen_rerun" in path_str:
        return "runpod_codegen_rerun"
    elif "runpod_codegen" in path_str:
        return "runpod_codegen"
    elif "runpod_rerun" in path_str:
        return "runpod_rerun"
    elif "runpod_rq2_pod" in path_str:
        return "runpod_rq2"
    elif "runpod" in path_str:
        return "runpod"
    return "unknown"


def find_vuln_summary_files(base_dir: str) -> list[dict]:
    """Find all vulnerability detection summary files."""
    results_dir = Path(base_dir) / "results"
    files = []

    # Directories to exclude
    exclude_dirs = {
        "rq2_nm8b_ma_rerun_20260103",
        "context_overflow_test",
        "runpod_vuln_incremental",  # Partial 100-sample results (merged into runpod_vuln_486)
    }

    # Skip files with _conservative_ or _strict_ in the name (use basic normalization only)
    skip_patterns = ["_conservative_", "_strict_"]

    for csv_file in results_dir.rglob("*_summary_vulnerability_metrics.csv"):
        # Skip excluded directories
        if any(excl in csv_file.parts for excl in exclude_dirs):
            continue

        # Skip alternative normalization files
        if any(pat in csv_file.name for pat in skip_patterns):
            continue

        # Skip _orig backup files
        if "_orig" in csv_file.name:
            continue

        files.append({
            "file_path": str(csv_file),
            "source_type": get_source_type(str(csv_file)),
            "source_dir": str(csv_file.parent),
            "task": "vulnerability_detection",
        })

    return files


def find_code_eval_files(base_dir: str) -> list[dict]:
    """Find all code generation evaluation files."""
    results_dir = Path(base_dir) / "results"
    files = []

    # Directories to exclude
    exclude_dirs = {
        "rq2_nm8b_ma_rerun_20260103",
        "context_overflow_test",
    }

    for json_file in results_dir.rglob("*_evaluation.json"):
        # Skip excluded directories
        if any(excl in json_file.parts for excl in exclude_dirs):
            continue

        files.append({
            "file_path": str(json_file),
            "source_type": get_source_type(str(json_file)),
            "source_dir": str(json_file.parent),
            "task": "code_generation",
        })

    return files


def find_log_analysis_files(base_dir: str) -> list[dict]:
    """Find all log analysis summary files."""
    results_dir = Path(base_dir) / "results" / "runpod_log_analysis"
    files = []

    if not results_dir.exists():
        return files

    # Find summary_metrics.csv files (not vulnerability_metrics.csv)
    for csv_file in results_dir.rglob("*_summary_metrics.csv"):
        # Skip vulnerability metrics files
        if "_vulnerability_metrics" in csv_file.name:
            continue

        files.append({
            "file_path": str(csv_file),
            "source_type": "runpod_log_analysis",
            "source_dir": str(csv_file.parent),
            "task": "log_analysis",
        })

    return files


def parse_log_analysis_dir_name(dir_name: str) -> dict:
    """Parse experiment config from log analysis directory name like 'SA-zero_Qwen3-4B-Instruct'."""
    info = {
        "model": None,
        "model_family": None,
        "parameters_b": None,
        "mode": None,
        "design": "SA",
        "prompting": None,
    }

    # Parse design type
    if dir_name.startswith("DA-") or "_DA-" in dir_name:
        info["design"] = "DA"
    elif dir_name.startswith("MA-") or "_MA-" in dir_name:
        info["design"] = "MA"
    elif dir_name.startswith("SA-") or "_SA-" in dir_name:
        info["design"] = "SA"

    # Parse prompting strategy
    if "zero" in dir_name.lower():
        info["prompting"] = "zero-shot"
    elif "few" in dir_name.lower():
        info["prompting"] = "few-shot"

    # Parse model
    if "Qwen3-30B" in dir_name:
        info["model_family"] = "Qwen"
        info["parameters_b"] = 30
        if "Thinking" in dir_name:
            info["model"] = "Qwen3-30B-A3B-Thinking"
            info["mode"] = "thinking"
        elif "Instruct" in dir_name:
            info["model"] = "Qwen3-30B-A3B-Instruct"
            info["mode"] = "instruct"
    elif "Qwen3-4B" in dir_name:
        info["model_family"] = "Qwen"
        info["parameters_b"] = 4
        if "Thinking" in dir_name:
            info["model"] = "Qwen3-4B-Thinking"
            info["mode"] = "thinking"
        elif "Instruct" in dir_name:
            info["model"] = "Qwen3-4B-Instruct"
            info["mode"] = "instruct"

    return info


def load_vuln_metrics(file_info: dict) -> dict | None:
    """Load vulnerability detection metrics from CSV."""
    file_path = file_info["file_path"]
    filename = Path(file_path).name

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            return None

        row = df.iloc[0]

        # Parse config from filename
        parsed_config = parse_config_from_filename(filename)
        path_config = infer_config_from_path(file_path)

        # Merge configs (filename takes precedence, then path)
        for key in parsed_config:
            if parsed_config[key] is None:
                parsed_config[key] = path_config.get(key)

        result = {
            # Lineage
            "source_file": file_path,
            "source_type": file_info["source_type"],

            # Experiment config
            "model": parsed_config["model"],
            "model_family": parsed_config["model_family"],
            "parameters_b": parsed_config["parameters_b"],
            "design": parsed_config["design"],
            "task": "vulnerability_detection",
            "mode": parsed_config["mode"],
            "prompting": parsed_config["prompting"],
            "thinking_enabled": parsed_config["mode"] == "thinking",

            # Vulnerability metrics
            "accuracy": row.get("Accuracy"),
            "precision": row.get("Precision"),
            "recall": row.get("Recall"),
            "f1_score": row.get("F1_Score"),
            "true_positives": row.get("True_Positives"),
            "true_negatives": row.get("True_Negatives"),
            "false_positives": row.get("False_Positives"),
            "false_negatives": row.get("False_Negatives"),
            "total_samples": row.get("Total_Samples"),
            "correct_predictions": row.get("Correct_Predictions"),
            "skipped_samples": row.get("Skipped_Samples", 0),

            # Code generation metrics (not applicable)
            "pass_at_1": None,
            "passed_samples": None,
            "failed_samples": None,
        }

        return result

    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
        return None


def load_code_metrics(file_info: dict) -> dict | None:
    """Load code generation metrics from JSON."""
    file_path = file_info["file_path"]
    filename = Path(file_path).name

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        metrics = data.get("metrics", {})

        # Parse config from filename
        parsed_config = parse_config_from_filename(filename)
        path_config = infer_config_from_path(file_path)

        # Merge configs
        for key in parsed_config:
            if parsed_config[key] is None:
                parsed_config[key] = path_config.get(key)

        result = {
            # Lineage
            "source_file": file_path,
            "source_type": file_info["source_type"],
            "dataset": "HumanEval",

            # Experiment config
            "model": parsed_config["model"],
            "model_family": parsed_config["model_family"],
            "parameters_b": parsed_config["parameters_b"],
            "design": parsed_config["design"],
            "task": "code_generation",
            "mode": parsed_config["mode"],
            "prompting": parsed_config["prompting"],
            "thinking_enabled": parsed_config["mode"] == "thinking",

            # Vulnerability metrics (not applicable)
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "true_positives": None,
            "true_negatives": None,
            "false_positives": None,
            "false_negatives": None,

            # Code generation metrics
            "pass_at_1": metrics.get("pass@1"),
            "total_samples": metrics.get("total_samples"),
            "passed_samples": metrics.get("passed_samples"),
            "failed_samples": metrics.get("failed_samples"),
            "correct_predictions": metrics.get("passed_samples"),  # Alias for uniformity
            "skipped_samples": 0,
        }

        return result

    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
        return None


def load_log_analysis_metrics(file_info: dict) -> dict | None:
    """Load log analysis metrics from CSV."""
    file_path = file_info["file_path"]
    source_dir = Path(file_path).parent

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            return None

        row = df.iloc[0]

        # Parse config from directory name (e.g., "SA-zero_Qwen3-4B-Instruct")
        dir_name = source_dir.name
        parsed_config = parse_log_analysis_dir_name(dir_name)

        # Calculate correct predictions
        tp = row.get("TP", 0)
        tn = row.get("TN", 0)
        fp = row.get("FP", 0)
        fn = row.get("FN", 0)
        correct = tp + tn

        result = {
            # Lineage
            "source_file": file_path,
            "source_type": file_info["source_type"],
            "dataset": "HDFS-385",

            # Experiment config
            "model": parsed_config["model"],
            "model_family": parsed_config["model_family"],
            "parameters_b": parsed_config["parameters_b"],
            "design": parsed_config["design"],
            "task": "log_analysis",
            "mode": parsed_config["mode"],
            "prompting": parsed_config["prompting"],
            "thinking_enabled": parsed_config["mode"] == "thinking",

            # Log analysis metrics (same format as vulnerability detection)
            "accuracy": row.get("Accuracy"),
            "precision": row.get("Precision"),
            "recall": row.get("Recall"),
            "f1_score": row.get("F1"),
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "total_samples": row.get("Total"),
            "correct_predictions": correct,
            "skipped_samples": 0,

            # Code generation metrics (not applicable)
            "pass_at_1": None,
            "passed_samples": None,
            "failed_samples": None,
        }

        return result

    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
        return None


def deduplicate_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate performance records in two stages:
    1. Cross-source: prefer newer/rerun data over older sources
    2. Within-source: keep record with best performance (F1 for vuln, pass@1 for code)

    Priority order (higher = preferred):
    1. runpod_codegen_rerun (codegen reruns with reasoning)
    2. runpod_rerun (vuln detection reruns)
    3. runpod_codegen (code generation originals)
    4. rq2_cross_architecture (Nemotron experiments)
    5. runpod_rq2 (RQ2 DA/MA experiments)
    6. mars_rerun (MARS reruns)
    7. mars_codegen (MARS code gen)
    8. runpod (original)
    9. mars (original, oldest)
    """
    source_priority = {
        "mars": 1,
        "runpod": 2,
        "mars_codegen": 3,
        "mars_rerun": 4,
        "runpod_rq2": 5,
        "rq2_cross_architecture": 6,
        "runpod_codegen": 7,
        "runpod_rerun": 8,
        "runpod_codegen_rerun": 9,
        "runpod_vuln_486": 10,
    }

    df = df.copy()
    df["_source_priority"] = df["source_type"].map(lambda x: source_priority.get(x, 0))

    # Define deduplication key columns
    key_cols = ["model", "task", "mode", "prompting", "design", "dataset"]

    # Create dedup key
    df["_dedup_key"] = df[key_cols].apply(lambda x: tuple(x), axis=1)

    # Find duplicates
    dup_counts = df.groupby("_dedup_key").size()
    duplicate_keys = dup_counts[dup_counts > 1].index.tolist()

    if not duplicate_keys:
        print("No duplicates found.")
        df = df.drop(columns=["_source_priority", "_dedup_key"])
        return df

    print(f"\nDeduplication: Found {len(duplicate_keys)} duplicate experiment groups")

    # For each duplicate group, apply deduplication logic
    rows_to_drop = []
    for key in duplicate_keys:
        group = df[df["_dedup_key"] == key]
        sources = group[["source_type", "_source_priority"]].drop_duplicates()

        # Stage 1: Cross-source deduplication
        if len(sources) > 1:
            max_priority = sources["_source_priority"].max()
            preferred_source = sources[sources["_source_priority"] == max_priority]["source_type"].iloc[0]

            to_drop = group[group["_source_priority"] < max_priority].index.tolist()
            rows_to_drop.extend(to_drop)

            dropped_sources = sources[sources["_source_priority"] < max_priority]["source_type"].tolist()
            model, task, mode, prompting, design, dataset = key
            print(f"  {model} {design} {task} {mode} {prompting}:")
            print(f"    Cross-source: Keeping {preferred_source}, dropping {dropped_sources}")

            # Update group to only include preferred source for stage 2
            group = group[group["source_type"] == preferred_source]

        # Stage 2: Within-source deduplication (multiple runs of same experiment)
        if len(group) > 1:
            model, task, mode, prompting, design, dataset = key

            # Keep the record with best performance
            if task == "vulnerability_detection":
                # Keep highest F1 score
                best_idx = group["f1_score"].idxmax()
                best_f1 = group.loc[best_idx, "f1_score"]
                to_drop_within = [idx for idx in group.index if idx != best_idx]
                rows_to_drop.extend(to_drop_within)
                print(f"  {model} {design} {task} {mode} {prompting}:")
                print(f"    Within-source: Keeping best F1={best_f1:.4f}, dropping {len(to_drop_within)} other run(s)")
            else:
                # Keep highest pass@1
                best_idx = group["pass_at_1"].idxmax()
                best_pass = group.loc[best_idx, "pass_at_1"]
                to_drop_within = [idx for idx in group.index if idx != best_idx]
                rows_to_drop.extend(to_drop_within)
                print(f"  {model} {design} {task} {mode} {prompting}:")
                print(f"    Within-source: Keeping best pass@1={best_pass:.4f}, dropping {len(to_drop_within)} other run(s)")

    df_deduped = df.drop(index=rows_to_drop)
    print(f"\nRemoved {len(rows_to_drop)} duplicate records, {len(df_deduped)} remaining")

    df_deduped = df_deduped.drop(columns=["_source_priority", "_dedup_key"])

    return df_deduped


def normalize_vuln_basic(pred):
    """Basic normalization: None/-1 → 1 (conservative: assume vulnerable)."""
    if pred is None:
        return 1
    p = int(pred)
    return 1 if p == -1 else p


def find_and_evaluate_vuln_from_jsonl(base_dir: str, vuln_dirs: list[str] = None) -> list[dict]:
    """Find JSONL files in staging directories and compute metrics directly.

    This bypasses stale summary CSVs by reading the corrected vuln field
    from JSONL files and re-evaluating against ground truth.

    Args:
        base_dir: Project root directory.
        vuln_dirs: List of directories to scan for JSONL files.
                   Defaults to runpod_vuln_486 and runpod_vuln_384_incremental.

    Returns:
        List of performance records ready for consolidation.
    """
    results_dir = Path(base_dir) / "results"

    if vuln_dirs is None:
        vuln_dirs = [
            results_dir / "runpod_vuln_486",
            results_dir / "runpod_vuln_384_incremental",
        ]
    else:
        vuln_dirs = [Path(d) for d in vuln_dirs]

    records = []

    for vuln_dir in vuln_dirs:
        if not vuln_dir.exists():
            print(f"  Warning: {vuln_dir} not found, skipping")
            continue

        source_type = vuln_dir.name
        # Determine dataset label from directory name
        if "486" in vuln_dir.name:
            dataset = "VulTrial-486"
        elif "384" in vuln_dir.name:
            dataset = "VulTrial-384-incr"
        else:
            dataset = vuln_dir.name
        jsonl_files = sorted(vuln_dir.glob("*_detailed_results.jsonl"))

        # Filter out alternative normalization and stray files
        jsonl_files = [
            f for f in jsonl_files
            if "_conservative_" not in f.name
            and "_strict_" not in f.name
            and "_stray" not in str(f)
        ]

        print(f"\n  Scanning {vuln_dir.name}: {len(jsonl_files)} JSONL files")

        for jsonl_path in jsonl_files:
            filename = jsonl_path.name

            # Parse config from filename
            parsed = parse_config_from_filename(filename)
            path_cfg = infer_config_from_path(str(jsonl_path))

            # Merge (filename takes precedence)
            for key in parsed:
                if parsed[key] is None:
                    parsed[key] = path_cfg.get(key)

            # Handle Nemotron thinking via _thinking suffix
            if parsed.get("model_family") == "Nemotron" or (
                parsed.get("model") and "Nemotron" in parsed["model"]
            ):
                if "_thinking_" in filename or filename.endswith("_thinking_detailed_results.jsonl"):
                    parsed["mode"] = "thinking"
                elif parsed["mode"] is None:
                    parsed["mode"] = "instruct"

            # Ensure task is set
            if parsed.get("task") is None:
                parsed["task"] = "vulnerability_detection"

            # Skip if essential config is missing
            if not parsed.get("model") or not parsed.get("prompting"):
                print(f"    Skipping {filename}: missing model or prompting config")
                continue

            # Load JSONL and compute metrics
            try:
                predictions = []
                ground_truths = []
                skipped = 0

                with open(jsonl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        entry = json.loads(line)
                        pred = entry.get("vuln")
                        gt = entry.get("ground_truth", entry.get("target"))

                        if gt is None:
                            continue

                        pred_norm = normalize_vuln_basic(pred)
                        predictions.append(pred_norm)
                        ground_truths.append(int(gt))

                        if pred is not None and int(pred) == -1:
                            skipped += 1

                if len(predictions) == 0:
                    print(f"    Skipping {filename}: no valid entries")
                    continue

                # Compute metrics
                acc = accuracy_score(ground_truths, predictions)
                prec = precision_score(ground_truths, predictions, zero_division=0)
                rec = recall_score(ground_truths, predictions, zero_division=0)
                f1 = f1_score(ground_truths, predictions, zero_division=0)
                tn, fp, fn, tp = confusion_matrix(
                    ground_truths, predictions, labels=[0, 1]
                ).ravel()
                correct = sum(p == g for p, g in zip(predictions, ground_truths))

                record = {
                    "source_file": str(jsonl_path),
                    "source_type": source_type,
                    "dataset": dataset,
                    "model": parsed["model"],
                    "model_family": parsed.get("model_family"),
                    "parameters_b": parsed.get("parameters_b"),
                    "design": parsed.get("design", "SA"),
                    "task": "vulnerability_detection",
                    "mode": parsed.get("mode"),
                    "prompting": parsed.get("prompting"),
                    "thinking_enabled": parsed.get("mode") == "thinking",
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1_score": f1,
                    "true_positives": int(tp),
                    "true_negatives": int(tn),
                    "false_positives": int(fp),
                    "false_negatives": int(fn),
                    "total_samples": len(predictions),
                    "correct_predictions": correct,
                    "skipped_samples": skipped,
                    "pass_at_1": None,
                    "passed_samples": None,
                    "failed_samples": None,
                }

                records.append(record)

            except Exception as e:
                print(f"    Error processing {filename}: {e}")

    return records


def consolidate_performance(base_dir: str, output_file: str, deduplicate: bool = True, exclude_mars: bool = False) -> pd.DataFrame:
    """Main function to consolidate all performance data."""
    print(f"Searching for performance files in {base_dir}...")

    # --- Vulnerability detection: evaluate directly from JSONL files ---
    # This reads corrected vuln predictions from JSONL (post parser fixes)
    # instead of stale summary CSVs generated during the original experiment runs.
    print("\n--- Vulnerability Detection (from JSONL) ---")
    vuln_records = find_and_evaluate_vuln_from_jsonl(base_dir)
    print(f"  Evaluated {len(vuln_records)} vuln detection configs from JSONL")

    # Report vuln by source
    vuln_by_source = Counter(r["source_type"] for r in vuln_records)
    for src, count in sorted(vuln_by_source.items()):
        print(f"    {src}: {count}")

    # --- Code generation and log analysis: keep existing CSV/JSON approach ---
    code_files = find_code_eval_files(base_dir)
    log_files = find_log_analysis_files(base_dir)

    print(f"\n--- Code Generation ---")
    print(f"  Found {len(code_files)} code generation evaluation files")
    print(f"\n--- Log Analysis ---")
    print(f"  Found {len(log_files)} log analysis summary files")

    # Filter out MARS if requested
    if exclude_mars:
        mars_sources = {"mars", "mars_rerun", "mars_codegen"}
        code_files = [f for f in code_files if f["source_type"] not in mars_sources]
        print(f"  After excluding MARS: {len(code_files)} code files")

    # Load all metrics
    all_records = list(vuln_records)

    print("\nLoading code generation metrics...")
    for file_info in code_files:
        record = load_code_metrics(file_info)
        if record:
            all_records.append(record)

    print("\nLoading log analysis metrics...")
    for file_info in log_files:
        record = load_log_analysis_metrics(file_info)
        if record:
            all_records.append(record)

    if not all_records:
        print("No performance data found!")
        return None

    # Create DataFrame
    df = pd.DataFrame(all_records)
    print(f"\nLoaded {len(df)} performance records")

    # Deduplicate if requested
    if deduplicate:
        df = deduplicate_records(df)

    # Sort by parameters, design, task, mode, prompting
    df = df.sort_values(
        by=["parameters_b", "design", "task", "mode", "prompting"],
        ascending=[True, True, True, True, True]
    )

    # Reorder columns for readability
    column_order = [
        # Experiment config
        "model", "model_family", "parameters_b", "design", "task", "dataset", "mode", "prompting", "thinking_enabled",
        # Vulnerability metrics
        "accuracy", "precision", "recall", "f1_score",
        "true_positives", "true_negatives", "false_positives", "false_negatives",
        # Code generation metrics
        "pass_at_1", "passed_samples", "failed_samples",
        # Sample info
        "total_samples", "correct_predictions", "skipped_samples",
        # Lineage
        "source_type", "source_file",
    ]
    # Only include columns that exist
    df = df[[c for c in column_order if c in df.columns]]

    # Save to CSV — keep_default_na=False prevents "NA" design from being read as NaN
    df.to_csv(output_file, index=False)
    print(f"\nConsolidated performance data saved to: {output_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("CONSOLIDATION SUMMARY")
    print("=" * 80)
    print(f"Total experiments: {len(df)}")

    print(f"\nBy model:")
    model_counts = df.groupby("model").size()
    print(model_counts.to_string())

    print(f"\nBy design:")
    design_counts = df.groupby("design").size()
    print(design_counts.to_string())

    print(f"\nBy task:")
    task_counts = df.groupby("task").size()
    print(task_counts.to_string())

    # Summary metrics by task
    vuln_df = df[df["task"] == "vulnerability_detection"]
    code_df = df[df["task"] == "code_generation"]
    log_df = df[df["task"] == "log_analysis"]

    if not vuln_df.empty:
        print(f"\nVulnerability Detection Summary:")
        print(f"  Mean Accuracy: {vuln_df['accuracy'].mean():.4f}")
        print(f"  Mean F1 Score: {vuln_df['f1_score'].mean():.4f}")
        print(f"  Total Skipped Samples: {vuln_df['skipped_samples'].sum():.0f}")

    if not code_df.empty:
        print(f"\nCode Generation Summary:")
        print(f"  Mean Pass@1: {code_df['pass_at_1'].mean():.4f}")
        print(f"  Total Passed: {code_df['passed_samples'].sum():.0f}")
        print(f"  Total Failed: {code_df['failed_samples'].sum():.0f}")

    if not log_df.empty:
        print(f"\nLog Analysis Summary:")
        print(f"  Mean Accuracy: {log_df['accuracy'].mean():.4f}")
        print(f"  Mean F1 Score: {log_df['f1_score'].mean():.4f}")
        print(f"  Experiments: {len(log_df)}")

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Consolidate performance metrics from multiple experiments"
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Base directory of the agent-green project (default: current directory)"
    )
    parser.add_argument(
        "--output",
        default="results/consolidated_performance.csv",
        help="Output file path (default: results/consolidated_performance.csv)"
    )
    parser.add_argument(
        "--no-deduplicate",
        action="store_true",
        help="Don't deduplicate experiments (keep all sources even if duplicated)"
    )
    parser.add_argument(
        "--exclude-mars",
        action="store_true",
        help="Exclude MARS cluster results (only include RunPod results)"
    )

    args = parser.parse_args()

    # Resolve paths
    base_dir = Path(args.base_dir).resolve()
    output_file = base_dir / args.output

    df = consolidate_performance(
        str(base_dir),
        str(output_file),
        deduplicate=not args.no_deduplicate,
        exclude_mars=args.exclude_mars
    )

    if df is not None:
        print(f"\nConsolidation complete! {len(df)} records.")
        print(f"Output: {output_file}")


if __name__ == "__main__":
    main()
