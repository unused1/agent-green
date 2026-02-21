#!/usr/bin/env python3
"""
Fix vulnerability keyword parser false positives in SA vuln JSONL files.

Two bugs in the SA vuln prediction parser:
1. YES patterns checked before NO — "no vulnerability detected" matched
   the YES substring "vulnerability detected" first
2. Broad fallback keywords ("buffer overflow", "memory leak", "race condition",
   etc.) matched in negative contexts (e.g., "no buffer overflow detected")

This script:
1. Discovers all SA vuln detection *_detailed_results.jsonl files
2. Re-parses predictions using the fixed parser (NO before YES, reduced fallback)
3. Updates the vuln/prediction field in each JSONL entry
4. Updates companion CSV files if present
5. Logs all changes with direction (1→0 vs 0→1)

Usage:
    python scripts/fix_vuln_keyword_parsing.py --dry-run   # Preview changes
    python scripts/fix_vuln_keyword_parsing.py              # Apply fixes
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Think-tag stripping helper
# ---------------------------------------------------------------------------

def strip_think_block(text):
    """Return only the response portion after </think>, or full text if no tag."""
    if "</think>" in text:
        return text.split("</think>", 1)[1].strip()
    return text


# ---------------------------------------------------------------------------
# Fixed SA prediction parser
# ---------------------------------------------------------------------------

def parse_sa_prediction_fixed(response_text):
    """
    Fixed SA keyword parsing — NO checked before YES to prevent substring
    false positives (e.g., "no vulnerability detected" matching "vulnerability
    detected"). Broad fallback keywords removed.
    """
    response_lower = response_text.lower()

    # Explicit NO — checked FIRST to avoid substring false positives
    if any(p in response_lower for p in [
        "final answer: no", "final answer: (2) no", "(2) no",
        "answer: no", "no vulnerability", "no security vulnerability",
        "no, the code",
        "no:",  # from single_agent_vuln_detection.py
    ]):
        return 0

    # Explicit YES
    if any(p in response_lower for p in [
        "final answer: yes", "final answer: (1) yes", "(1) yes",
        "answer: yes", "vulnerability detected", "yes, the code",
        "yes: vulnerability",
        "yes:",  # from single_agent_vuln_detection.py
    ]):
        return 1

    # Fallback — only strong positive indicators
    if any(k in response_lower for k in [
        "is vulnerable", "contains a vulnerability",
        "security vulnerability exists", "can be exploited",
    ]):
        return 1

    return 0  # Default


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def discover_sa_vuln_files():
    """Find all SA vuln detection JSONL files under results/.

    Identifies SA vuln files by:
    1. Filename starts with Sa-, SA-, or vuln_SA- (SA agent design)
    2. First entry has ground_truth and (vuln or prediction) fields
    3. Excludes codegen and log analysis files
    """
    results_dir = PROJECT_ROOT / "results"
    sa_vuln_files = []

    for jsonl_path in sorted(results_dir.rglob("*_detailed_results.jsonl")):
        path_str = str(jsonl_path).lower()
        name = jsonl_path.name.lower()

        # Exclude codegen files
        if "codegen" in path_str or "_code_" in path_str:
            continue

        # Exclude log analysis files
        if "log_analysis" in path_str:
            continue

        # Must be SA file (Sa-, SA-, or vuln_SA-)
        if not (name.startswith("sa-") or name.startswith("vuln_sa-")):
            continue

        # Verify it's a vuln file by checking first entry for expected fields
        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    if "ground_truth" in entry and ("vuln" in entry or "prediction" in entry):
                        sa_vuln_files.append(str(jsonl_path))
                    break
        except Exception:
            continue

    return sa_vuln_files


# ---------------------------------------------------------------------------
# Fix a single JSONL file
# ---------------------------------------------------------------------------

def fix_jsonl_file(jsonl_path, dry_run=False):
    """
    Re-parse vuln predictions for all entries using the fixed parser.

    Returns dict with:
        changed: int — number of entries with changed prediction
        total: int — total entries processed
        changes: list of (idx, old_pred, new_pred)
        pred_field: str — field name used (vuln or prediction)
    """
    entries = []
    changes = []
    pred_field_used = None

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                entries.append(line)  # Preserve non-JSON lines
                continue

            # Detect prediction field name
            pred_field = None
            if "vuln" in entry:
                pred_field = "vuln"
            elif "prediction" in entry and "ground_truth" in entry:
                pred_field = "prediction"

            if pred_field is None:
                entries.append(entry)
                continue

            if pred_field_used is None:
                pred_field_used = pred_field

            reasoning = entry.get("reasoning", "")
            if not isinstance(reasoning, str) or not reasoning.strip():
                entries.append(entry)
                continue

            # Strip think block and re-parse
            response_only = strip_think_block(reasoning)
            new_pred = parse_sa_prediction_fixed(response_only)
            old_pred = entry.get(pred_field)

            if old_pred != new_pred:
                changes.append((entry.get("idx", "?"), old_pred, new_pred))
                if not dry_run:
                    entry[pred_field] = new_pred

            entries.append(entry)

    # Write back
    if not dry_run and changes:
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for entry in entries:
                if isinstance(entry, str):
                    f.write(entry + "\n")
                else:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {
        "changed": len(changes),
        "total": len(entries),
        "changes": changes,
        "pred_field": pred_field_used or "vuln",
    }


def fix_companion_csv(jsonl_path, changes_by_idx, pred_field="vuln"):
    """
    Update the companion CSV file's prediction column to match corrected JSONL.
    changes_by_idx: dict mapping idx -> new_pred value
    """
    csv_path = jsonl_path.replace(".jsonl", ".csv")
    if not os.path.exists(csv_path):
        return 0

    csv.field_size_limit(sys.maxsize)

    # Read all rows
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    # Find prediction and idx column indices
    pred_col = None
    idx_col = None
    for i, h in enumerate(header):
        h_lower = h.strip().lower()
        if h_lower == pred_field:
            pred_col = i
        if h_lower == "idx":
            idx_col = i

    if pred_col is None or idx_col is None:
        return 0

    updated = 0
    for row in rows:
        try:
            row_idx = row[idx_col].strip()
            # Try numeric comparison
            try:
                row_idx_num = int(row_idx)
            except (ValueError, TypeError):
                row_idx_num = row_idx

            new_val = None
            if row_idx_num in changes_by_idx:
                new_val = changes_by_idx[row_idx_num]
            elif row_idx in changes_by_idx:
                new_val = changes_by_idx[row_idx]

            if new_val is not None:
                old_val = row[pred_col]
                row[pred_col] = str(new_val)
                if old_val != row[pred_col]:
                    updated += 1
        except (IndexError, ValueError):
            continue

    if updated > 0:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    return updated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fix SA vuln keyword parser false positives (NO-before-YES reorder + fallback reduction)"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    args = parser.parse_args()

    print("=" * 72)
    print("Fix Vulnerability Keyword Parser False Positives")
    print("=" * 72)
    if args.dry_run:
        print("MODE: DRY RUN (no files will be modified)\n")
    else:
        print("MODE: LIVE (files will be modified)\n")

    # Step 1: Discover SA vuln files
    print("Discovering SA vuln JSONL files...")
    sa_vuln_files = discover_sa_vuln_files()
    print(f"  Found {len(sa_vuln_files)} SA vuln files\n")

    if not sa_vuln_files:
        print("No SA vuln files found. Exiting.")
        return 0

    # Step 2: Process each file
    total_changes = 0
    total_to_0 = 0
    total_to_1 = 0
    summary = []

    for fpath in sa_vuln_files:
        rel_path = os.path.relpath(fpath, PROJECT_ROOT)
        print(f"Processing: {rel_path}")

        result = fix_jsonl_file(fpath, dry_run=args.dry_run)

        # Build changes-by-idx for CSV update
        changes_by_idx = {}
        for idx, old_v, new_v in result["changes"]:
            changes_by_idx[idx] = new_v

        csv_updated = 0
        if not args.dry_run and result["changed"] > 0:
            csv_updated = fix_companion_csv(fpath, changes_by_idx, result["pred_field"])

        total_changes += result["changed"]
        to_0 = sum(1 for _, old, new in result["changes"] if new == 0)
        to_1 = sum(1 for _, old, new in result["changes"] if new == 1)
        total_to_0 += to_0
        total_to_1 += to_1

        print(f"  Entries: {result['total']}  |  Changed: {result['changed']}")
        if csv_updated:
            print(f"  CSV rows updated: {csv_updated}")

        if result["changes"]:
            print(f"  Direction: {to_0} changed 1->0, {to_1} changed 0->1")
            # Show affected sample indices
            for idx, old_v, new_v in result["changes"]:
                print(f"    idx={idx}: {old_v} -> {new_v}")

        summary.append({
            "file": rel_path,
            "total": result["total"],
            "changed": result["changed"],
            "to_0": to_0,
            "to_1": to_1,
        })
        print()

    # Step 3: Print summary
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Files processed: {len(sa_vuln_files)}")
    print(f"Total predictions changed: {total_changes}")
    print(f"  1->0 (false positive removed): {total_to_0}")
    print(f"  0->1 (new positive added):     {total_to_1}")

    if args.dry_run:
        print(f"\nDRY RUN — no files were modified.")
        print("Run without --dry-run to apply changes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
