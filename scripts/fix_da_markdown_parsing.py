#!/usr/bin/env python3
"""
Fix DA vulnerability parser: strip markdown code blocks before JSON parsing.

The DA parser (`extract_vulnerability_decision` in `dual_agent_vuln.py`) checks
if the response starts with `{` or `[` to detect JSON. However, some models
(especially Qwen3 Instruct) wrap their JSON output in markdown code blocks:

    ```json
    {"vulnerability_detected": true, ...}
    ```

This caused the parser to skip the JSON path and fall through to keyword matching,
which often defaulted to vuln=0 (safe). This script re-parses the `reasoning` or
`analyst_feedback` field in all DA JSONL files and updates the `vuln` field where
the fixed parser produces a different result.

Only the `vuln` field is modified. Model responses are never changed.

Usage:
    python scripts/fix_da_markdown_parsing.py [--dry-run]
"""

import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

csv.field_size_limit(sys.maxsize)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def extract_vulnerability_decision_fixed(response):
    """Fixed DA parser with markdown code block stripping."""
    try:
        text = response.split("</think>", 1)[1].strip() if "</think>" in response else response.strip()
        # Strip markdown code blocks
        text = re.sub(r'```(?:json)?\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()

        if text.startswith("{") or text.startswith("["):
            data = json.loads(text)
            if isinstance(data, dict):
                decision = data.get("vulnerability_detected", False)
            elif isinstance(data, list):
                decision = any(d.get("vulnerability_detected", False) for d in data)
            else:
                decision = False
        else:
            lowered = text.lower()
            if any(p in lowered for p in [
                "final answer: no", "final answer: (2) no", "(2) no",
                "answer: no", "no vulnerability", "no security vulnerability",
                "no, the code", "no:",
            ]):
                decision = False
            elif any(p in lowered for p in [
                "final answer: yes", "final answer: (1) yes", "(1) yes",
                "answer: yes", "vulnerability detected", "yes, the code",
                "yes: vulnerability", "yes:",
            ]):
                decision = True
            elif any(k in lowered for k in [
                "is vulnerable", "contains a vulnerability",
                "security vulnerability exists", "can be exploited",
            ]):
                decision = True
            else:
                decision = False

        return 1 if decision else 0
    except Exception:
        return 0


def find_da_jsonl_files():
    """Find all DA vulnerability detection JSONL files across all result directories."""
    patterns = [
        "results/runpod_rq2_pod*/DA-vuln*_detailed_results.jsonl",
        "results/runpod_rq2_pod*/results/DA-vuln*_detailed_results.jsonl",
        "results/rq2_cross_architecture/*/DA-vuln*_detailed_results.jsonl",
        "results/rq2_nm8b_ma_rerun_20260103/DA-vuln*_detailed_results.jsonl",
        "results/runpod_vuln_incremental/DA-vuln*_detailed_results.jsonl",
        "results/runpod_vuln_486/DA-vuln*_detailed_results.jsonl",
        "results/runpod_vuln_384_incremental/DA-vuln*_detailed_results.jsonl",
        "results/runpod_870_batch3_raw/*/results/DA-vuln*_detailed_results.jsonl",
        "results/runpod_870_batch4_raw/*/results/DA-vuln*_detailed_results.jsonl",
        "results/runpod_vuln_incremental_pod*_raw/*/DA-vuln*_detailed_results.jsonl",
    ]

    all_files = []
    for pattern in patterns:
        full_pattern = str(PROJECT_ROOT / pattern)
        all_files.extend(glob.glob(full_pattern))

    # Filter out stray/alternative normalization files
    all_files = [
        f for f in all_files
        if "_stray" not in f and "_conservative" not in f and "_strict" not in f
    ]
    return sorted(set(all_files))


def process_file(filepath, dry_run=False):
    """Re-parse a single JSONL file and update vuln field where changed.

    Returns (total_entries, changed_entries, changes_detail).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = []
    changed = 0
    changes = []

    for line in lines:
        line = line.strip()
        if not line:
            entries.append("")
            continue

        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            entries.append(line)
            continue

        # Get the analyst's raw response — DA stores it in discussion.analyst_feedback
        # The 'reasoning' field may contain different content (e.g., code author's text)
        discussion = entry.get("discussion", {})
        if isinstance(discussion, dict):
            analyst_feedback = discussion.get("analyst_feedback", "")
        else:
            analyst_feedback = ""
        # Fallback: if no discussion field, try reasoning directly
        if not analyst_feedback:
            analyst_feedback = entry.get("analyst_feedback", entry.get("reasoning", ""))
        if not analyst_feedback:
            entries.append(json.dumps(entry, ensure_ascii=False))
            continue

        old_vuln = entry.get("vuln")
        new_vuln = extract_vulnerability_decision_fixed(analyst_feedback)

        if old_vuln is not None and int(old_vuln) != new_vuln:
            changes.append({
                "idx": entry.get("idx", "?"),
                "old": int(old_vuln),
                "new": new_vuln,
                "gt": entry.get("ground_truth", entry.get("target", "?")),
            })
            entry["vuln"] = new_vuln
            changed += 1

        entries.append(json.dumps(entry, ensure_ascii=False))

    # Write back
    if not dry_run and changed > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            for e in entries:
                if e:
                    f.write(e + "\n")

    return len([e for e in entries if e]), changed, changes


def main():
    parser = argparse.ArgumentParser(
        description="Fix DA vulnerability parser: strip markdown code blocks before JSON parsing"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show changes without modifying files",
    )
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)

    print("=" * 72)
    print("Fix DA Markdown Code Block Parsing")
    print("=" * 72)
    if args.dry_run:
        print("DRY RUN — no files will be modified\n")

    files = find_da_jsonl_files()
    print(f"Found {len(files)} DA JSONL files\n")

    total_entries = 0
    total_changed = 0
    changes_0to1 = 0
    changes_1to0 = 0
    all_changes = []

    for filepath in files:
        relpath = os.path.relpath(filepath, PROJECT_ROOT)
        n_entries, n_changed, changes = process_file(filepath, dry_run=args.dry_run)
        total_entries += n_entries
        total_changed += n_changed

        for c in changes:
            c["file"] = relpath
            all_changes.append(c)
            if c["old"] == 0 and c["new"] == 1:
                changes_0to1 += 1
            else:
                changes_1to0 += 1

        if n_changed > 0:
            print(f"  {n_changed:4d} changes in {relpath}")

    # Summary
    print()
    print("=" * 72)
    print("Summary")
    print("=" * 72)
    print(f"  Files scanned:       {len(files)}")
    print(f"  Total entries:       {total_entries}")
    print(f"  Predictions changed: {total_changed}")
    print(f"    0→1 (safe→vuln):   {changes_0to1}")
    print(f"    1→0 (vuln→safe):   {changes_1to0}")

    if args.dry_run:
        print("\n  DRY RUN — no files were modified.")
    else:
        print(f"\n  {total_changed} entries updated across {len(files)} files.")

    # Save change log
    if all_changes:
        log_path = PROJECT_ROOT / "results" / "da_markdown_fix_changes.csv"
        with open(log_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["file", "idx", "old", "new", "gt"])
            writer.writeheader()
            writer.writerows(all_changes)
        print(f"  Change log saved to: {log_path}")


if __name__ == "__main__":
    sys.exit(main() or 0)
