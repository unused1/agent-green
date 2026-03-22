#!/usr/bin/env python3
"""
Consolidate emissions.csv files from multiple experiments into a single aggregated file.

This script:
1. Finds all emissions.csv files across all experiment directories
2. Parses experiment configuration from directory structure and project_name
3. Aggregates multi-session experiments (due to interrupt/resume cycles)
4. Adds lineage columns for traceability
5. Outputs a consolidated CSV file

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
    python scripts/consolidate_emissions.py [--output results/consolidated_emissions.csv]
"""

import argparse
import os
import re
from pathlib import Path
from datetime import datetime

import pandas as pd


def parse_model_from_project_name(project_name: str) -> dict:
    """Parse model info from CodeCarbon project_name field."""
    info = {
        "model": None,
        "model_family": None,
        "parameters_b": None,
        "mode": None,
        "design": "SA",  # Default to single-agent
        "task": None,
        "prompting": None,
    }

    if not project_name:
        return info

    # Parse design type (NoAgent, SA, DA, MA)
    # Handle both direct prefix (NA-, DA-, MA-) and log-analysis prefix (log-analysis_DA-, etc.)
    if project_name.startswith("NA-") or "_NA-" in project_name:
        info["design"] = "NoAgent"
    elif project_name.startswith("DA-") or "_DA-" in project_name:
        info["design"] = "DA"
    elif project_name.startswith("MA-") or "_MA-" in project_name:
        info["design"] = "MA"
    elif project_name.startswith("SA-") or "_SA-" in project_name:
        info["design"] = "SA"
    else:
        info["design"] = "SA"

    # Parse task
    if "log-analysis" in project_name.lower():
        info["task"] = "log_analysis"
    elif "vuln" in project_name.lower():
        info["task"] = "vulnerability_detection"
    elif "code" in project_name.lower():
        info["task"] = "code_generation"

    # Parse prompting strategy
    if "zero" in project_name.lower() or "Sa-zero" in project_name or "SA-zero" in project_name:
        info["prompting"] = "zero-shot"
    elif "few" in project_name.lower() or "Sa-few" in project_name or "SA-few" in project_name:
        info["prompting"] = "few-shot"

    # Parse Nemotron models
    if "Nemotron-Super-49B" in project_name or "Nemotron-Super-49B-v1_5" in project_name:
        info["model"] = "Nemotron-Super-49B"
        info["model_family"] = "Nemotron"
        info["parameters_b"] = 49
    elif "Nemotron-Nano-8B" in project_name:
        info["model"] = "Nemotron-Nano-8B"
        info["model_family"] = "Nemotron"
        info["parameters_b"] = 8

    # Parse Qwen3 models
    elif "Qwen3-30B-A3B" in project_name:
        info["model_family"] = "Qwen"
        info["parameters_b"] = 30
        if "Thinking" in project_name:
            info["model"] = "Qwen3-30B-A3B-Thinking"
            info["mode"] = "thinking"
        elif "Instruct" in project_name:
            info["model"] = "Qwen3-30B-A3B-Instruct"
            info["mode"] = "instruct"
    elif "Qwen3-4B" in project_name:
        info["model_family"] = "Qwen"
        info["parameters_b"] = 4
        if "Thinking" in project_name:
            info["model"] = "Qwen3-4B-Thinking"
            info["mode"] = "thinking"
        elif "Instruct" in project_name:
            info["model"] = "Qwen3-4B-Instruct"
            info["mode"] = "instruct"

    # Infer mode from project_name if not set
    if info["mode"] is None:
        if "thinking" in project_name.lower():
            info["mode"] = "thinking"
        elif "instruct" in project_name.lower() or "baseline" in project_name.lower():
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

    # Task - check explicit markers first
    if "runpod_log_analysis" in path_str or "log-analysis" in path_str:
        info["task"] = "log_analysis"
    elif "_vuln_" in path_str or "vuln" in path_str:
        info["task"] = "vulnerability_detection"
    elif "_code_" in path_str or "codegen" in path_str:
        info["task"] = "code_generation"
    # Infer task from directory structure for runpod experiments
    elif "/runpod_codegen/" in file_path:
        info["task"] = "code_generation"
    elif "/runpod_rerun/" in file_path or "/runpod/" in file_path:
        # runpod and runpod_rerun contain vulnerability detection experiments
        info["task"] = "vulnerability_detection"

    # Mode
    if "_thinking" in path_str or "thinking" in path_str or "_think" in path_str:
        info["mode"] = "thinking"
    elif "_instruct" in path_str or "baseline" in path_str or "instruct" in path_str:
        info["mode"] = "instruct"

    # Prompting
    if "sa-zero" in path_str or "zero" in path_str:
        info["prompting"] = "zero-shot"
    elif "sa-few" in path_str or "few" in path_str:
        info["prompting"] = "few-shot"

    return info


def find_all_emissions_files(base_dir: str) -> list[dict]:
    """Find all emissions.csv files and extract metadata."""
    emissions_files = []
    base_path = Path(base_dir)
    results_dir = base_path / "results"

    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return emissions_files

    # Directories to exclude (reruns for verification, not primary results)
    exclude_dirs = {
        "rq2_nm8b_ma_rerun_20260103",  # Rerun to verify Nemotron 8B skip rates
        "context_overflow_test",        # 128K context test (not primary results)
    }

    # Find all emissions.csv files recursively
    for emissions_file in results_dir.rglob("emissions.csv"):
        # Skip excluded directories
        if any(excl in emissions_file.parts for excl in exclude_dirs):
            continue

        file_path = str(emissions_file)

        # Determine source directory type
        relative_path = emissions_file.relative_to(results_dir)
        parts = relative_path.parts

        source_type = "unknown"
        parts_str = str(relative_path)
        if "runpod_log_analysis" in parts:
            source_type = "runpod_log_analysis"
        elif any("runpod_870_batch" in p for p in parts):
            source_type = "runpod_870_batch"
        elif any("runpod_na486" in p for p in parts):
            source_type = "runpod_na486"
        elif any("runpod_vuln_incremental_pod" in p for p in parts):
            source_type = "runpod_vuln_incremental_pod_raw"
        elif "runpod_vuln_incremental" in parts:
            source_type = "runpod_vuln_incremental"
        elif "rq2_cross_architecture" in parts:
            source_type = "rq2_cross_architecture"
        elif "mars_rerun" in parts:
            source_type = "mars_rerun"
        elif "mars_codegen" in parts:
            source_type = "mars_codegen"
        elif "runpod_codegen_rerun" in parts:
            source_type = "runpod_codegen_rerun"
        elif "runpod_codegen" in parts:
            source_type = "runpod_codegen"
        elif "runpod_rerun" in parts:
            source_type = "runpod_rerun"
        elif any("runpod_rq2_pod" in p for p in parts):
            source_type = "runpod_rq2"
        elif "runpod" in parts and "runpod_" not in str(parts[0]):
            source_type = "runpod"

        emissions_files.append({
            "file_path": file_path,
            "source_type": source_type,
            "source_dir": str(emissions_file.parent),
        })

    return emissions_files


def load_and_process_emissions(file_info: dict) -> list[dict]:
    """Load emissions.csv and process each row with metadata."""
    file_path = file_info["file_path"]
    source_type = file_info["source_type"]
    source_dir = file_info["source_dir"]

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
        return []

    if df.empty:
        return []

    results = []
    for _, row in df.iterrows():
        # Parse config from project_name
        project_name = row.get("project_name", "")
        parsed_config = parse_model_from_project_name(project_name)

        # If parsing failed, try to infer from path
        path_config = infer_config_from_path(file_path)

        # Merge configs (project_name takes precedence)
        for key in parsed_config:
            if parsed_config[key] is None:
                parsed_config[key] = path_config.get(key)

        # Determine dataset from source type
        if "870_batch" in source_type or "384" in source_dir:
            dataset = "VulTrial-384-incr"
        elif "na486" in source_type:
            dataset = "VulTrial-486"
        elif "vuln_incremental" in source_type:
            dataset = "VulTrial-100-incr"
        elif "log_analysis" in source_type:
            dataset = "HDFS-385"
        elif "codegen" in source_type:
            dataset = "HumanEval"
        elif "vuln" in str(parsed_config.get("task", "")):
            dataset = "VulTrial-386"
        else:
            dataset = "unknown"

        # Build result record
        result = {
            # Lineage
            "source_file": file_path,
            "source_type": source_type,
            "source_dir": source_dir,
            "project_name": project_name,
            "dataset": dataset,

            # Experiment config
            "model": parsed_config["model"],
            "model_family": parsed_config["model_family"],
            "parameters_b": parsed_config["parameters_b"],
            "design": parsed_config["design"],
            "task": parsed_config["task"],
            "mode": parsed_config["mode"],
            "prompting": parsed_config["prompting"],
            "thinking_enabled": parsed_config["mode"] == "thinking",

            # Session info
            "timestamp": row.get("timestamp"),
            "run_id": row.get("run_id"),
            "experiment_id": row.get("experiment_id"),

            # Metrics
            "duration_s": row.get("duration"),
            "emissions_kg": row.get("emissions"),
            "emissions_rate": row.get("emissions_rate"),
            "energy_kwh": row.get("energy_consumed"),
            "cpu_energy_kwh": row.get("cpu_energy"),
            "gpu_energy_kwh": row.get("gpu_energy"),
            "ram_energy_kwh": row.get("ram_energy"),

            # Power
            "cpu_power_w": row.get("cpu_power"),
            "gpu_power_w": row.get("gpu_power"),
            "ram_power_w": row.get("ram_power"),

            # Hardware
            "cpu_model": row.get("cpu_model"),
            "cpu_count": row.get("cpu_count"),
            "gpu_model": row.get("gpu_model"),
            "gpu_count": row.get("gpu_count"),
            "ram_total_gb": row.get("ram_total_size", 0) / 1024 if row.get("ram_total_size") else None,

            # Location
            "country": row.get("country_name"),
            "country_iso": row.get("country_iso_code"),
        }

        results.append(result)

    return results


def aggregate_by_experiment(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate multiple sessions into single experiment records."""
    # Define grouping columns
    group_cols = [
        "model", "model_family", "parameters_b", "design",
        "task", "dataset", "mode", "prompting", "thinking_enabled"
    ]

    # Filter out rows with missing key columns
    df_valid = df.dropna(subset=["model", "task"])

    if df_valid.empty:
        return pd.DataFrame()

    # Aggregate
    aggregated = df_valid.groupby(group_cols, dropna=False).agg({
        # Count sessions
        "run_id": "count",
        "timestamp": ["min", "max"],

        # Sum metrics
        "duration_s": "sum",
        "emissions_kg": "sum",
        "energy_kwh": "sum",
        "cpu_energy_kwh": "sum",
        "gpu_energy_kwh": "sum",
        "ram_energy_kwh": "sum",

        # Average power
        "cpu_power_w": "mean",
        "gpu_power_w": "mean",
        "ram_power_w": "mean",
        "emissions_rate": "mean",

        # Keep first hardware info
        "cpu_model": "first",
        "cpu_count": "first",
        "gpu_model": "first",
        "gpu_count": "first",
        "ram_total_gb": "first",
        "country": "first",

        # Keep source info
        "source_type": lambda x: ", ".join(sorted(set(str(s) for s in x))),
        "source_file": lambda x: "; ".join(sorted(set(str(s) for s in x))),
    }).reset_index()

    # Flatten column names
    aggregated.columns = [
        "_".join(col).strip("_") if isinstance(col, tuple) else col
        for col in aggregated.columns
    ]

    # Rename columns
    aggregated = aggregated.rename(columns={
        "run_id_count": "num_sessions",
        "timestamp_min": "first_session",
        "timestamp_max": "last_session",
        "duration_s_sum": "total_duration_s",
        "emissions_kg_sum": "total_emissions_kg",
        "energy_kwh_sum": "total_energy_kwh",
        "cpu_energy_kwh_sum": "total_cpu_energy_kwh",
        "gpu_energy_kwh_sum": "total_gpu_energy_kwh",
        "ram_energy_kwh_sum": "total_ram_energy_kwh",
        "cpu_power_w_mean": "avg_cpu_power_w",
        "gpu_power_w_mean": "avg_gpu_power_w",
        "ram_power_w_mean": "avg_ram_power_w",
        "emissions_rate_mean": "avg_emissions_rate",
        "cpu_model_first": "cpu_model",
        "cpu_count_first": "cpu_count",
        "gpu_model_first": "gpu_model",
        "gpu_count_first": "gpu_count",
        "ram_total_gb_first": "ram_total_gb",
        "country_first": "country",
        "source_type_<lambda>": "source_types",
        "source_file_<lambda>": "source_files",
    })

    # Add derived metrics
    aggregated["duration_hours"] = aggregated["total_duration_s"] / 3600
    aggregated["emissions_g"] = aggregated["total_emissions_kg"] * 1000

    return aggregated


def deduplicate_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate emission records, preferring newer/rerun data over older.

    Priority order (higher = preferred):
    1. runpod_codegen_rerun (codegen reruns with reasoning)
    2. runpod_rerun (vuln detection reruns)
    3. runpod_codegen (code generation originals)
    4. rq2_cross_architecture (Nemotron experiments)
    5. runpod_rq2 (RQ2 DA/MA experiments)
    6. runpod (original, oldest)
    """
    # Define source priority (higher number = higher priority)
    source_priority = {
        "runpod": 1,
        "runpod_rq2": 2,
        "rq2_cross_architecture": 3,
        "runpod_codegen": 4,
        "runpod_rerun": 5,
        "runpod_log_analysis": 6,
        "runpod_codegen_rerun": 7,
        "runpod_vuln_incremental": 8,
        "runpod_vuln_incremental_pod_raw": 8,
        "runpod_870_batch": 9,
        "runpod_na486": 10,
    }

    # Add priority column
    df = df.copy()
    df["_source_priority"] = df["source_type"].map(lambda x: source_priority.get(x, 0))

    # Define deduplication key columns
    key_cols = ["model", "task", "dataset", "mode", "prompting", "design"]

    # Find duplicates
    df["_dedup_key"] = df[key_cols].apply(lambda x: tuple(x), axis=1)

    # Group by dedup key and find duplicates
    dup_counts = df.groupby("_dedup_key").size()
    duplicate_keys = dup_counts[dup_counts > 1].index.tolist()

    if not duplicate_keys:
        print("No duplicates found.")
        df = df.drop(columns=["_source_priority", "_dedup_key"])
        return df

    print(f"\nDeduplication: Found {len(duplicate_keys)} duplicate experiment groups")

    # For each duplicate group, keep only the highest priority source
    rows_to_drop = []
    for key in duplicate_keys:
        group = df[df["_dedup_key"] == key]

        # Get unique source types in this group
        sources = group[["source_type", "_source_priority"]].drop_duplicates()

        if len(sources) > 1:
            # Multiple sources - keep highest priority
            max_priority = sources["_source_priority"].max()
            preferred_source = sources[sources["_source_priority"] == max_priority]["source_type"].iloc[0]

            # Mark rows from lower priority sources for removal
            to_drop = group[group["_source_priority"] < max_priority].index.tolist()
            rows_to_drop.extend(to_drop)

            # Report
            dropped_sources = sources[sources["_source_priority"] < max_priority]["source_type"].tolist()
            model, task, dataset, mode, prompting, design = key
            print(f"  {model} {design} {task} {mode} {prompting}:")
            print(f"    Keeping: {preferred_source} ({len(group[group['source_type'] == preferred_source])} records)")
            print(f"    Dropping: {dropped_sources} ({len(to_drop)} records)")

    # Drop duplicate rows
    df_deduped = df.drop(index=rows_to_drop)
    print(f"\nRemoved {len(rows_to_drop)} duplicate records, {len(df_deduped)} remaining")

    # Clean up helper columns
    df_deduped = df_deduped.drop(columns=["_source_priority", "_dedup_key"])

    return df_deduped


def load_emissions_from_dir(emissions_dir: str, filter_project_prefix: str = None) -> dict | None:
    """Load and sum emissions from a directory's emissions.csv.

    Returns dict with summed energy/duration and averaged power, or None if not found.
    """
    emissions_path = os.path.join(emissions_dir, "emissions.csv")
    if not os.path.exists(emissions_path):
        # Check for merged emissions (e.g., from split runs)
        emissions_path = os.path.join(emissions_dir, "emissions_merged.csv")
        if not os.path.exists(emissions_path):
            return None

    try:
        df = pd.read_csv(emissions_path, on_bad_lines="skip")
    except Exception:
        return None

    if df.empty:
        return None

    # Filter by project_name prefix if specified
    if filter_project_prefix and "project_name" in df.columns:
        mask = df["project_name"].str.contains(filter_project_prefix, case=False, na=False)
        df = df[mask]
        if df.empty:
            return None

    # Sum cumulative, average instantaneous
    result = {
        "num_sessions": len(df),
        "duration_s": df["duration"].sum() if "duration" in df.columns else 0,
        "emissions_kg": df["emissions"].sum() if "emissions" in df.columns else 0,
        "energy_kwh": df["energy_consumed"].sum() if "energy_consumed" in df.columns else 0,
        "cpu_energy_kwh": df["cpu_energy"].sum() if "cpu_energy" in df.columns else 0,
        "gpu_energy_kwh": df["gpu_energy"].sum() if "gpu_energy" in df.columns else 0,
        "ram_energy_kwh": df["ram_energy"].sum() if "ram_energy" in df.columns else 0,
        "cpu_power_w": df["cpu_power"].mean() if "cpu_power" in df.columns else 0,
        "gpu_power_w": df["gpu_power"].mean() if "gpu_power" in df.columns else 0,
        "ram_power_w": df["ram_power"].mean() if "ram_power" in df.columns else 0,
        "gpu_model": df["gpu_model"].iloc[0] if "gpu_model" in df.columns else None,
        "gpu_count": df["gpu_count"].iloc[0] if "gpu_count" in df.columns else None,
        "cpu_model": df["cpu_model"].iloc[0] if "cpu_model" in df.columns else None,
        "country": df["country_name"].iloc[0] if "country_name" in df.columns else None,
    }
    return result


def weighted_avg(val1, dur1, val2, dur2):
    """Compute duration-weighted average of two values."""
    total_dur = dur1 + dur2
    if total_dur == 0:
        return 0
    return (val1 * dur1 + val2 * dur2) / total_dur


def load_all_emissions_from_manifest(base_dir: str) -> list[dict]:
    """Load all emissions using the expanded manifest file.

    Covers vulnerability detection, code generation, and log analysis.
    For VulTrial-486 SA/DA/MA: combines base 386 + incremental 100 emissions.
    For mixed dirs (codegen in vuln pods): uses filter_prefix to isolate rows.
    """
    import csv as csv_mod

    manifest_path = os.path.join(base_dir, "results", "emissions_source_manifest_expanded.csv")
    if not os.path.exists(manifest_path):
        print(f"  Manifest not found: {manifest_path}")
        return []

    # Map dataset to task
    dataset_task = {
        "VulTrial-486": "vulnerability_detection",
        "VulTrial-384-incr": "vulnerability_detection",
        "HumanEval": "code_generation",
        "HDFS-385": "log_analysis",
    }

    records = []
    with open(manifest_path, "r") as f:
        reader = csv_mod.DictReader(f)
        for row in reader:
            dataset = row["dataset"]
            design = row["design"]
            mode = row["mode"]
            prompting = row["prompting"]
            model_short = row["model"]
            raw_dir = row.get("raw_source_dir", "")
            base386_dir = row.get("base386_emissions_dir", "")
            emissions_found = row.get("emissions_csv", "")
            base386_found = row.get("base386_emissions_found", "")
            filter_prefix = row.get("filter_prefix", "")

            task = dataset_task.get(dataset, "unknown")

            # Map short model name to full name
            model_map = {
                "Qwen3-4B": ("Qwen3-4B-Thinking" if mode == "thinking" else "Qwen3-4B-Instruct", "Qwen", 4),
                "Qwen3-30B": ("Qwen3-30B-A3B-Thinking" if mode == "thinking" else "Qwen3-30B-A3B-Instruct", "Qwen", 30),
                "Nano-8B": ("Nemotron-Nano-8B", "Nemotron", 8),
                "Super-49B": ("Nemotron-Super-49B", "Nemotron", 49),
            }
            model_full, model_family, params = model_map.get(model_short, (model_short, "?", 0))

            # Load primary emissions (with optional filter for mixed dirs)
            primary = None
            if raw_dir and emissions_found == "YES":
                primary = load_emissions_from_dir(
                    raw_dir,
                    filter_project_prefix=filter_prefix if filter_prefix else None,
                )

            # Load base 386 emissions (only for VulTrial-486 SA/DA/MA)
            base = None
            if dataset == "VulTrial-486" and design != "NoAgent" and base386_dir and base386_found == "YES":
                base = load_emissions_from_dir(base386_dir)

            # Combine emissions
            if primary and base:
                dur1 = base["duration_s"]
                dur2 = primary["duration_s"]
                combined = {
                    "num_sessions": base["num_sessions"] + primary["num_sessions"],
                    "duration_s": dur1 + dur2,
                    "emissions_kg": base["emissions_kg"] + primary["emissions_kg"],
                    "energy_kwh": base["energy_kwh"] + primary["energy_kwh"],
                    "cpu_energy_kwh": base["cpu_energy_kwh"] + primary["cpu_energy_kwh"],
                    "gpu_energy_kwh": base["gpu_energy_kwh"] + primary["gpu_energy_kwh"],
                    "ram_energy_kwh": base["ram_energy_kwh"] + primary["ram_energy_kwh"],
                    "cpu_power_w": weighted_avg(base["cpu_power_w"], dur1, primary["cpu_power_w"], dur2),
                    "gpu_power_w": weighted_avg(base["gpu_power_w"], dur1, primary["gpu_power_w"], dur2),
                    "ram_power_w": weighted_avg(base["ram_power_w"], dur1, primary["ram_power_w"], dur2),
                    "gpu_model": primary["gpu_model"] or base["gpu_model"],
                    "gpu_count": primary["gpu_count"] or base["gpu_count"],
                    "cpu_model": primary["cpu_model"] or base["cpu_model"],
                    "country": primary["country"] or base["country"],
                    "source_note": f"386({base386_dir}) + 100({raw_dir})",
                }
            elif primary:
                combined = primary
                combined["source_note"] = raw_dir
            elif base:
                combined = base
                combined["source_note"] = base386_dir
            else:
                continue

            record = {
                "model": model_full,
                "model_family": model_family,
                "parameters_b": params,
                "design": design,
                "task": task,
                "dataset": dataset,
                "mode": mode,
                "prompting": prompting,
                "thinking_enabled": mode == "thinking",
                "num_sessions": combined["num_sessions"],
                "total_duration_s": combined["duration_s"],
                "duration_hours": combined["duration_s"] / 3600,
                "total_emissions_kg": combined["emissions_kg"],
                "emissions_g": combined["emissions_kg"] * 1000,
                "total_energy_kwh": combined["energy_kwh"],
                "total_cpu_energy_kwh": combined["cpu_energy_kwh"],
                "total_gpu_energy_kwh": combined["gpu_energy_kwh"],
                "total_ram_energy_kwh": combined["ram_energy_kwh"],
                "avg_cpu_power_w": combined["cpu_power_w"],
                "avg_gpu_power_w": combined["gpu_power_w"],
                "avg_ram_power_w": combined["ram_power_w"],
                "gpu_model": combined["gpu_model"],
                "gpu_count": combined["gpu_count"],
                "cpu_model": combined["cpu_model"],
                "country": combined["country"],
                "source_note": combined.get("source_note", ""),
            }
            records.append(record)

    return records


def consolidate_emissions(base_dir: str, output_file: str, **kwargs) -> pd.DataFrame:
    """Main function to consolidate all emissions data from the manifest."""
    print(f"Consolidating emissions from {base_dir}...")

    from collections import Counter

    records = load_all_emissions_from_manifest(base_dir)
    if not records:
        print("No emissions data found!")
        return None

    df = pd.DataFrame(records)

    # Print breakdown
    by_task = Counter(r["task"] for r in records)
    by_dataset = Counter(r["dataset"] for r in records)
    print(f"\nLoaded {len(records)} emission records from manifest")
    for task, count in sorted(by_task.items()):
        print(f"  {task}: {count}")
    for ds, count in sorted(by_dataset.items()):
        print(f"    {ds}: {count}")

    print(f"\nTotal consolidated records: {len(df)}")

    # Sort
    df = df.sort_values(
        by=["task", "dataset", "parameters_b", "design", "mode", "prompting"],
        ascending=True,
        na_position="last"
    ).reset_index(drop=True)

    # Save output
    df.to_csv(output_file, index=False)
    print(f"Consolidated emissions saved to: {output_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("CONSOLIDATION SUMMARY")
    print("=" * 80)
    print(f"Total experiment configs: {len(df)}")

    if "total_emissions_kg" in df.columns:
        print(f"\nBy task:")
        task_summary = df.groupby("task")[["total_emissions_kg", "total_energy_kwh"]].sum()
        print(task_summary.to_string())

        print(f"\nBy dataset:")
        ds_summary = df.groupby("dataset")[["total_emissions_kg", "total_energy_kwh"]].sum()
        print(ds_summary.to_string())

        print(f"\nBy design:")
        design_summary = df.groupby("design")[["total_emissions_kg", "total_energy_kwh"]].sum()
        print(design_summary.to_string())

        print(f"\nBy model:")
        model_summary = df.groupby("model")[["total_emissions_kg", "total_energy_kwh"]].sum()
        print(model_summary.to_string())

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Consolidate emissions.csv files from multiple experiments"
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Base directory of the agent-green project (default: current directory)"
    )
    parser.add_argument(
        "--output",
        default="results/consolidated_emissions.csv",
        help="Output file path (default: results/consolidated_emissions.csv)"
    )
    parser.add_argument(
        "--no-aggregate",
        action="store_true",
        help="Don't aggregate multi-session experiments (keep raw data)"
    )
    parser.add_argument(
        "--exclude-mars",
        action="store_true",
        help="Exclude MARS cluster results (only include RunPod results)"
    )
    parser.add_argument(
        "--no-deduplicate",
        action="store_true",
        help="Don't deduplicate experiments (keep all sources even if duplicated)"
    )

    args = parser.parse_args()

    # Resolve paths
    base_dir = Path(args.base_dir).resolve()
    output_file = base_dir / args.output

    df = consolidate_emissions(
        str(base_dir),
        str(output_file),
        aggregate=not args.no_aggregate,
        exclude_mars=args.exclude_mars,
        deduplicate=not args.no_deduplicate
    )

    if df is not None:
        print(f"\nConsolidation complete! {len(df)} records.")
        print(f"Output: {output_file}")


if __name__ == "__main__":
    main()
