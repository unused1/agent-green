#!/usr/bin/env python3
"""
Find and classify canonical experiment result files.

This script mirrors the logic from consolidate_emissions.py to:
1. Find all experiment result files (detailed_results.jsonl)
2. Classify by source type and parse metadata
3. Apply deduplication logic to identify canonical results
4. Output a clear list for review

Supported experiment sources (same as consolidate_emissions.py):
- results/rq2_cross_architecture/nemotron_* (Nemotron 8B and 49B)
- results/runpod_rq2_pod1-8/ (Qwen3 DA/MA experiments on RunPod)
- results/runpod_rerun/ (Qwen3 reruns - highest priority)
- results/runpod_codegen/ (Qwen3 code generation)
- results/runpod/ (original, lowest priority)
- results/mars_* (EXCLUDED by default)

Usage:
    python scripts/find_canonical_results.py [--task vuln|code] [--design SA|DA|MA] [--include-mars]

Examples:
    python scripts/find_canonical_results.py --task vuln --design MA
    python scripts/find_canonical_results.py --task vuln --design MA --output results/canonical_ma_vuln.json
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# Source type priority (higher = preferred when deduplicating)
SOURCE_PRIORITY = {
    "unknown": 0,
    "runpod": 1,
    "runpod_rq2": 2,
    "rq2_cross_architecture": 3,
    "runpod_codegen": 4,
    "runpod_rerun": 5,
}

# Sources to exclude by default
EXCLUDED_SOURCES = {"mars_rerun", "mars_codegen", "mars"}


def classify_source_type(file_path: Path, results_dir: Path) -> str:
    """Classify file into source type based on path."""
    try:
        relative_path = file_path.relative_to(results_dir)
        parts = relative_path.parts
    except ValueError:
        parts = file_path.parts

    path_str = str(file_path).lower()

    if "rq2_cross_architecture" in parts or "rq2_cross_architecture" in path_str:
        return "rq2_cross_architecture"
    elif "mars_rerun" in parts or "mars_rerun" in path_str:
        return "mars_rerun"
    elif "mars_codegen" in parts or "mars_codegen" in path_str:
        return "mars_codegen"
    elif "mars" in path_str:
        return "mars"
    elif "runpod_codegen" in parts or "runpod_codegen" in path_str:
        return "runpod_codegen"
    elif "runpod_rerun" in parts or "runpod_rerun" in path_str:
        return "runpod_rerun"
    elif any("runpod_rq2_pod" in p for p in parts) or "runpod_rq2_pod" in path_str:
        return "runpod_rq2"
    elif "runpod" in path_str:
        return "runpod"

    return "unknown"


def parse_experiment_metadata(file_path: Path, project_name: str = None) -> dict:
    """Parse experiment metadata from file path and optional project_name."""
    info = {
        "model": None,
        "model_family": None,
        "parameters_b": None,
        "mode": None,  # instruct or thinking
        "design": None,  # SA, DA, MA
        "task": None,  # vulnerability_detection or code_generation
        "prompting": None,  # zero-shot or few-shot
    }

    path_str = str(file_path).lower()
    filename = file_path.name.lower()

    # Parse design type
    if "ma-vuln" in filename or "ma-code" in filename or "_ma-" in path_str:
        info["design"] = "MA"
    elif "da-vuln" in filename or "da-code" in filename or "_da-" in path_str:
        info["design"] = "DA"
    elif "sa-" in filename or "sa_" in path_str:
        info["design"] = "SA"

    # Parse task
    if "vuln" in path_str:
        info["task"] = "vulnerability_detection"
    elif "code" in path_str:
        info["task"] = "code_generation"

    # Parse prompting
    if "zero" in path_str:
        info["prompting"] = "zero-shot"
    elif "few" in path_str:
        info["prompting"] = "few-shot"

    # Parse model - Nemotron
    if "nemotron-super-49b" in path_str or "nemotron_49b" in path_str:
        info["model"] = "Nemotron-Super-49B"
        info["model_family"] = "Nemotron"
        info["parameters_b"] = 49
    elif "nemotron-nano-8b" in path_str or "nemotron_8b" in path_str:
        info["model"] = "Nemotron-Nano-8B"
        info["model_family"] = "Nemotron"
        info["parameters_b"] = 8

    # Parse model - Qwen3
    elif "qwen3-30b" in path_str or "qwen-qwen3-30b" in path_str:
        info["model_family"] = "Qwen"
        info["parameters_b"] = 30
        if "thinking" in path_str:
            info["model"] = "Qwen3-30B-A3B-Thinking"
        else:
            info["model"] = "Qwen3-30B-A3B-Instruct"
    elif "qwen3-4b" in path_str or "qwen-qwen3-4b" in path_str:
        info["model_family"] = "Qwen"
        info["parameters_b"] = 4
        if "thinking" in path_str:
            info["model"] = "Qwen3-4B-Thinking"
        else:
            info["model"] = "Qwen3-4B-Instruct"

    # Parse mode (instruct vs thinking)
    if "thinking" in path_str or "_think" in path_str:
        info["mode"] = "thinking"
    elif "instruct" in path_str:
        info["mode"] = "instruct"

    return info


def get_sample_count(file_path: Path) -> dict:
    """Get sample count and basic stats from result file."""
    stats = {
        "total_samples": 0,
        "vuln_predictions": 0,
        "safe_predictions": 0,
        "ground_truth_vuln": 0,
        "ground_truth_safe": 0,
        "has_review_board": 0,
        "errors": 0,
    }

    try:
        with open(file_path) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)

                    # Skip evaluation summary lines
                    if "evaluation_summary" in data:
                        continue

                    stats["total_samples"] += 1

                    # Count predictions
                    vuln = data.get("vuln", -1)
                    if vuln == 1:
                        stats["vuln_predictions"] += 1
                    elif vuln == 0:
                        stats["safe_predictions"] += 1

                    # Count ground truth
                    gt = data.get("ground_truth", data.get("target", -1))
                    if gt == 1:
                        stats["ground_truth_vuln"] += 1
                    elif gt == 0:
                        stats["ground_truth_safe"] += 1

                    # Check for review_board response (for MA re-evaluation)
                    fd = data.get("full_discussion", {})
                    if fd.get("review_board"):
                        stats["has_review_board"] += 1

                    # Count errors
                    if data.get("skipped") or "ERROR" in str(data.get("reasoning", "")):
                        stats["errors"] += 1

                except json.JSONDecodeError:
                    continue
    except Exception as e:
        stats["read_error"] = str(e)

    return stats


def find_result_files(results_dir: Path, task_filter: str = None, design_filter: str = None) -> list[dict]:
    """Find all detailed result files matching criteria."""
    files = []

    # Find all detailed result files
    for jsonl_file in results_dir.rglob("*detailed_results.jsonl"):
        # Skip corrected files from previous runs
        if "_corrected" in jsonl_file.name:
            continue

        # Classify source
        source_type = classify_source_type(jsonl_file, results_dir)

        # Parse metadata
        metadata = parse_experiment_metadata(jsonl_file)

        # Apply filters
        if task_filter:
            if task_filter == "vuln" and metadata["task"] != "vulnerability_detection":
                continue
            elif task_filter == "code" and metadata["task"] != "code_generation":
                continue

        if design_filter and metadata["design"] != design_filter:
            continue

        files.append({
            "file_path": str(jsonl_file),
            "file_name": jsonl_file.name,
            "source_type": source_type,
            "priority": SOURCE_PRIORITY.get(source_type, 0),
            **metadata,
        })

    return files


def deduplicate_results(files: list[dict], exclude_mars: bool = True) -> tuple[list[dict], list[dict]]:
    """
    Deduplicate results, returning (canonical, excluded) lists.

    Deduplication key: (model, design, task, mode, prompting)
    """
    # Filter out excluded sources
    if exclude_mars:
        excluded_mars = [f for f in files if f["source_type"] in EXCLUDED_SOURCES]
        files = [f for f in files if f["source_type"] not in EXCLUDED_SOURCES]
    else:
        excluded_mars = []

    # Group by deduplication key
    groups = defaultdict(list)
    for f in files:
        key = (f["model"], f["design"], f["task"], f["mode"], f["prompting"])
        groups[key].append(f)

    canonical = []
    excluded_dups = []

    for key, group in groups.items():
        if len(group) == 1:
            canonical.append(group[0])
        else:
            # Sort by priority (descending) then by file path (for consistency)
            group.sort(key=lambda x: (-x["priority"], x["file_path"]))

            # Keep highest priority
            canonical.append(group[0])

            # Mark others as excluded
            for f in group[1:]:
                f["excluded_reason"] = f"superseded by {group[0]['source_type']}"
                excluded_dups.append(f)

    # Combine excluded lists
    for f in excluded_mars:
        f["excluded_reason"] = "mars source excluded"
    excluded = excluded_mars + excluded_dups

    return canonical, excluded


def format_experiment_id(f: dict) -> str:
    """Create a readable experiment ID."""
    parts = []
    if f.get("model_family"):
        parts.append(f["model_family"])
    if f.get("parameters_b"):
        parts.append(f"{f['parameters_b']}B")
    if f.get("design"):
        parts.append(f["design"])
    if f.get("prompting"):
        parts.append(f["prompting"].replace("-shot", ""))
    if f.get("mode"):
        parts.append(f["mode"][:3])  # inst or thi
    return "-".join(parts) if parts else "unknown"


def main():
    parser = argparse.ArgumentParser(description="Find canonical experiment result files")
    parser.add_argument("--task", choices=["vuln", "code"], help="Filter by task type")
    parser.add_argument("--design", choices=["SA", "DA", "MA"], help="Filter by design type")
    parser.add_argument("--include-mars", action="store_true", help="Include MARS results")
    parser.add_argument("--output", type=str, help="Output JSON file for canonical list")
    parser.add_argument("--results-dir", default="results", help="Results directory")

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return

    print("=" * 80)
    print("FIND CANONICAL RESULTS")
    print("=" * 80)

    filters = []
    if args.task:
        filters.append(f"task={args.task}")
    if args.design:
        filters.append(f"design={args.design}")
    print(f"Filters: {', '.join(filters) if filters else 'none'}")
    print(f"Include MARS: {args.include_mars}")
    print()

    # Find all matching files
    files = find_result_files(results_dir, args.task, args.design)
    print(f"Found {len(files)} result files matching criteria")

    # Group by source type
    by_source = defaultdict(list)
    for f in files:
        by_source[f["source_type"]].append(f)

    print("\nBy source type:")
    for source, source_files in sorted(by_source.items()):
        priority = SOURCE_PRIORITY.get(source, 0)
        print(f"  {source} (priority={priority}): {len(source_files)} files")

    # Deduplicate
    canonical, excluded = deduplicate_results(files, exclude_mars=not args.include_mars)

    print(f"\nAfter deduplication:")
    print(f"  Canonical: {len(canonical)}")
    print(f"  Excluded: {len(excluded)}")

    # Get sample counts for canonical files
    print("\n" + "=" * 80)
    print("CANONICAL RESULTS")
    print("=" * 80)

    canonical_with_stats = []
    for f in sorted(canonical, key=lambda x: (x.get("model_family", ""), x.get("parameters_b", 0), x.get("prompting", ""), x.get("mode", ""))):
        stats = get_sample_count(Path(f["file_path"]))
        f["stats"] = stats
        canonical_with_stats.append(f)

        exp_id = format_experiment_id(f)
        accuracy = "N/A"
        if stats["total_samples"] > 0:
            correct = (stats["vuln_predictions"] if stats["ground_truth_vuln"] else 0) + \
                      (stats["safe_predictions"] if stats["ground_truth_safe"] else 0)
            # Simple accuracy calc
            gt_total = stats["ground_truth_vuln"] + stats["ground_truth_safe"]
            if gt_total > 0:
                tp = min(stats["vuln_predictions"], stats["ground_truth_vuln"])
                tn = min(stats["safe_predictions"], stats["ground_truth_safe"])
                # This is approximate - just for display
                vuln_pct = stats["vuln_predictions"] / stats["total_samples"] * 100 if stats["total_samples"] > 0 else 0

        print(f"\n[{exp_id}]")
        print(f"  Source: {f['source_type']}")
        print(f"  File: {f['file_name']}")
        print(f"  Path: {f['file_path']}")
        print(f"  Samples: {stats['total_samples']} (GT: {stats['ground_truth_vuln']} vuln, {stats['ground_truth_safe']} safe)")
        print(f"  Predictions: {stats['vuln_predictions']} vuln ({stats['vuln_predictions']/stats['total_samples']*100:.1f}%), {stats['safe_predictions']} safe")
        if stats.get("has_review_board"):
            print(f"  Has review_board: {stats['has_review_board']}/{stats['total_samples']}")
        if stats.get("errors"):
            print(f"  Errors/Skipped: {stats['errors']}")

    # Show excluded files
    if excluded:
        print("\n" + "=" * 80)
        print("EXCLUDED RESULTS")
        print("=" * 80)

        for f in sorted(excluded, key=lambda x: (x.get("excluded_reason", ""), x.get("file_path", ""))):
            exp_id = format_experiment_id(f)
            print(f"\n[{exp_id}] - {f.get('excluded_reason', 'unknown')}")
            print(f"  Source: {f['source_type']}")
            print(f"  File: {f['file_name']}")

    # Save to JSON if requested
    if args.output:
        output_data = {
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "task": args.task,
                "design": args.design,
                "include_mars": args.include_mars,
            },
            "summary": {
                "total_found": len(files),
                "canonical": len(canonical),
                "excluded": len(excluded),
            },
            "canonical": canonical_with_stats,
            "excluded": excluded,
        }

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\nSaved canonical list to: {args.output}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Canonical experiments: {len(canonical)}")
    print(f"Excluded experiments: {len(excluded)}")

    if canonical:
        print("\nCanonical experiment IDs:")
        for f in sorted(canonical, key=lambda x: format_experiment_id(x)):
            print(f"  - {format_experiment_id(f)}")


if __name__ == "__main__":
    main()
