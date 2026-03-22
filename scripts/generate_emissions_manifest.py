#!/usr/bin/env python3
"""Generate expanded emissions_source_manifest.csv covering all tasks.

Reads the existing vuln manifest, then adds codegen and log analysis entries
by scanning emissions.csv files and selecting the preferred source for each config.
"""

import csv
import glob
import os
import re
from collections import defaultdict

import pandas as pd

PROJECT_ROOT = "/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green"
os.chdir(PROJECT_ROOT)

EXCLUDE_DIRS = {"rq2_nm8b_ma_rerun_20260103", "context_overflow_test"}


def parse_project_name(pn):
    """Parse CodeCarbon project_name -> (task, design, mode, prompting, model_short) or None."""
    if not pn or pd.isna(pn):
        return None
    pn = str(pn)

    # Task
    if "log-analysis" in pn.lower() or "log_analysis" in pn.lower():
        task = "log_analysis"
    elif "vuln" in pn.lower():
        task = "vulnerability_detection"
    elif "code" in pn.lower() or (pn.startswith("Sa-") or pn.startswith("SA-")):
        task = "code_generation"
    else:
        return None

    # Design
    if pn.startswith("NA-") or "_NA-" in pn:
        design = "NoAgent"
    elif pn.startswith("DA-") or "_DA-" in pn:
        design = "DA"
    elif pn.startswith("MA-") or "_MA-" in pn:
        design = "MA"
    else:
        design = "SA"

    # Prompting
    if "zero" in pn.lower():
        prompting = "zero-shot"
    elif "few" in pn.lower():
        prompting = "few-shot"
    else:
        prompting = None

    # Model
    if "Nemotron-Super-49B" in pn or "Nemotron-Super-49B-v1" in pn:
        model_short = "Super-49B"
    elif "Nemotron-Nano-8B" in pn:
        model_short = "Nano-8B"
    elif "Qwen3-30B" in pn or "Qwen-Qwen3-30B" in pn:
        model_short = "Qwen3-30B"
    elif "Qwen3-4B" in pn or "Qwen-Qwen3-4B" in pn:
        model_short = "Qwen3-4B"
    else:
        model_short = None

    # Mode
    if "Thinking" in pn or "_thinking" in pn.lower():
        mode = "thinking"
    elif "Instruct" in pn or "_instruct" in pn.lower() or "baseline" in pn.lower():
        mode = "instruct"
    else:
        mode = None  # Will be inferred from dir path

    if not all([task, design, prompting, model_short]):
        return None

    return (task, design, mode, prompting, model_short)


def infer_mode_from_path(dir_path):
    lp = dir_path.lower()
    if "thinking" in lp or "_think" in lp:
        return "thinking"
    elif "instruct" in lp or "baseline" in lp:
        return "instruct"
    return None


# Source priority for dedup (higher = preferred)
SOURCE_PRIORITY = {
    "runpod_codegen_rerun": 10,
    "runpod_codegen": 8,
    "rq2_cross_architecture": 7,
    "runpod_rq2": 6,
    "runpod_rerun": 5,
    "runpod_log_analysis": 9,
    "mars_codegen": 2,
    "mars_rerun": 2,
    "mars": 1,
}


def classify_source(dir_path):
    """Classify source directory type."""
    for key in ["runpod_codegen_rerun", "runpod_codegen", "rq2_cross_architecture",
                "runpod_log_analysis", "mars_codegen", "mars_rerun", "runpod_rerun"]:
        if key in dir_path:
            return key
    for key in ["runpod_rq2"]:
        if key in dir_path:
            return key
    if "runpod_870_batch" in dir_path:
        return "runpod_870_batch"
    if "runpod_na486" in dir_path:
        return "runpod_na486"
    if "runpod_vuln_incremental" in dir_path:
        return "runpod_vuln_incremental"
    if "/mars/" in dir_path:
        return "mars"
    return "unknown"


# Scan all emissions files
emissions_files = glob.glob("results/**/emissions.csv", recursive=True)
emissions_files += glob.glob("results/**/emissions_merged.csv", recursive=True)
emissions_files = [f for f in emissions_files if not any(e in f for e in EXCLUDE_DIRS)]

# Build config -> [(source_dir, source_type, project_name_prefix, num_rows, total_emissions)]
config_sources = defaultdict(list)

for ef in sorted(emissions_files):
    try:
        df = pd.read_csv(ef, on_bad_lines="skip")
    except Exception:
        continue
    if df.empty or "project_name" not in df.columns:
        continue

    dir_path = os.path.dirname(ef)
    source_type = classify_source(dir_path)

    # Group rows by parsed config
    dir_configs = defaultdict(list)
    for _, row in df.iterrows():
        parsed = parse_project_name(row.get("project_name"))
        if parsed is None:
            continue
        task, design, mode, prompting, model_short = parsed
        if mode is None:
            mode = infer_mode_from_path(dir_path)
        if mode is None:
            continue
        key = (task, design, mode, prompting, model_short)
        dir_configs[key].append(row)

    for key, rows in dir_configs.items():
        config_sources[key].append({
            "dir": dir_path,
            "source_type": source_type,
            "num_rows": len(rows),
            "total_emissions": sum(r.get("emissions", 0) for r in rows),
            "total_duration": sum(r.get("duration", 0) for r in rows),
        })

# Now select preferred source for each config (codegen + log analysis only)
# For vuln, keep existing manifest
codegen_log_manifest = []

for key in sorted(config_sources.keys(), key=lambda x: tuple(str(v) for v in x)):
    task, design, mode, prompting, model_short = key
    if task == "vulnerability_detection":
        continue  # Handled by existing manifest

    sources = config_sources[key]

    # Select preferred source: highest priority source type
    best = max(sources, key=lambda s: SOURCE_PRIORITY.get(s["source_type"], 0))

    # Determine if we need a filter_prefix to isolate this config's rows
    # Mixed dirs: multiple experiments in same emissions.csv
    needs_filter = best["source_type"] in ("rq2_cross_architecture", "runpod_rq2")

    # Also need filter if SA codegen dir has both 4B and 30B
    if (task == "code_generation" and design == "SA" and
            best["source_type"] in ("runpod_codegen", "runpod_codegen_rerun")):
        needs_filter = True

    # Build filter prefix
    filter_prefix = ""
    if needs_filter:
        shot = "zero" if prompting == "zero-shot" else "few"
        if task == "code_generation":
            if design == "SA":
                # SA project names include model: Sa-zero_Qwen-Qwen3-30B or Sa-zero_nvidia-Llama
                model_prefix_map = {
                    "Qwen3-4B": "Qwen3-4B",
                    "Qwen3-30B": "Qwen3-30B",
                    "Nano-8B": "Nemotron-Nano",
                    "Super-49B": "Nemotron-Super",
                }
                mp = model_prefix_map.get(model_short, model_short)
                filter_prefix = f"Sa-{shot}.*{mp}" if model_short.startswith("Qwen") else f"SA-{shot}.*{mp}"
            elif design == "DA":
                filter_prefix = f"DA-code-{shot}"
            elif design == "MA":
                filter_prefix = f"MA-code-{shot}"
        elif task == "log_analysis":
            filter_prefix = f"log-analysis_{design}-{shot}"

    codegen_log_manifest.append({
        "dataset": "HumanEval" if task == "code_generation" else "HDFS-385",
        "design": design,
        "mode": mode,
        "prompting": prompting,
        "model": model_short,
        "raw_source_dir": best["dir"],
        "emissions_csv": "YES",
        "filter_prefix": filter_prefix,
        "num_sessions": best["num_rows"],
        "source_type": best["source_type"],
    })

print(f"Codegen + log analysis entries: {len(codegen_log_manifest)}")
print(f"  Codegen: {sum(1 for r in codegen_log_manifest if r['dataset'] == 'HumanEval')}")
print(f"  Log analysis: {sum(1 for r in codegen_log_manifest if r['dataset'] == 'HDFS-385')}")

# Print table
for r in codegen_log_manifest:
    filt = f" filter={r['filter_prefix']}" if r['filter_prefix'] else ""
    print(f"  {r['dataset']:12s} {r['design']:8s} {r['mode']:10s} {r['prompting']:10s} "
          f"{r['model']:12s} -> {r['raw_source_dir']}{filt}")

# Now read existing vuln manifest and merge
print("\n\nReading existing vuln manifest...")
existing_rows = []
with open("results/emissions_source_manifest.csv") as f:
    reader = csv.DictReader(f)
    existing_fields = reader.fieldnames
    for row in reader:
        existing_rows.append(row)

print(f"Existing vuln entries: {len(existing_rows)}")

# Write expanded manifest
# New columns: dataset, design, mode, prompting, model, raw_source_dir, emissions_csv, filter_prefix,
#              base386_emissions_dir, base386_emissions_found
# (drop staging_file, energy_tracking_json from old format — not needed for emissions)
new_fields = [
    "dataset", "design", "mode", "prompting", "model",
    "raw_source_dir", "emissions_csv", "filter_prefix",
    "base386_emissions_dir", "base386_emissions_found",
]

output_path = "results/emissions_source_manifest_expanded.csv"
with open(output_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=new_fields)
    writer.writeheader()

    # Write vuln entries (preserve from existing)
    for row in existing_rows:
        new_row = {
            "dataset": row["dataset"],
            "design": row["design"],
            "mode": row["mode"],
            "prompting": row["prompting"],
            "model": row["model"],
            "raw_source_dir": row.get("raw_source_dir", ""),
            "emissions_csv": row.get("emissions_csv", ""),
            "filter_prefix": "",  # Vuln dirs are not mixed
            "base386_emissions_dir": row.get("base386_emissions_dir", ""),
            "base386_emissions_found": row.get("base386_emissions_found", ""),
        }
        writer.writerow(new_row)

    # Write codegen + log analysis entries
    for r in codegen_log_manifest:
        new_row = {
            "dataset": r["dataset"],
            "design": r["design"],
            "mode": r["mode"],
            "prompting": r["prompting"],
            "model": r["model"],
            "raw_source_dir": r["raw_source_dir"],
            "emissions_csv": "YES",
            "filter_prefix": "",  # We'll set this below
            "base386_emissions_dir": "",
            "base386_emissions_found": "",
        }
        if r["filter_prefix"]:
            new_row["filter_prefix"] = r["filter_prefix"]
        writer.writerow(new_row)

print(f"\nExpanded manifest written to: {output_path}")
print(f"Total entries: {len(existing_rows) + len(codegen_log_manifest)}")
