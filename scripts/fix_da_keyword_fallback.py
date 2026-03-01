#!/usr/bin/env python3
"""
Fix DA vulnerability keyword fallback false positives in DA vuln JSONL files.

The DA vulnerability parser has a JSON primary path (reads vulnerability_detected
boolean) and a keyword fallback for free-text responses. The fallback used broad
substrings ("vulnerable", "unsafe", "security issue") that were never tightened
when SA's parser was fixed on 2026-02-22.

This script:
1. Discovers all DA vuln detection *_detailed_results.jsonl files
2. Re-parses predictions using the full tightened DA parser (JSON + tight keywords)
3. Updates the vuln field in each JSONL entry
4. Updates companion CSV files if present
5. Logs all changes with direction (1->0 vs 0->1)

Usage:
    python scripts/fix_da_keyword_fallback.py --dry-run                          # Preview changes
    python scripts/fix_da_keyword_fallback.py                                     # Apply fixes
    python scripts/fix_da_keyword_fallback.py --diff-report results/report.csv   # Apply + save change log
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
# Tightened DA prediction parser (JSON primary + tight keyword fallback)
# ---------------------------------------------------------------------------

def parse_da_prediction_fixed(response_text):
    """
    Full DA parser with tightened keyword fallback.
    Mirrors dual_agent_vuln.py extract_vulnerability_decision() after the fix.
    """
    try:
        text = response_text.strip()
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
            # NO-before-YES ordering to prevent substring false positives
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


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def discover_da_vuln_files():
    """Find all DA vuln detection JSONL files under results/.

    Identifies DA vuln files by:
    1. Filename starts with DA- or contains _DA-
    2. First entry has ground_truth/target and vuln fields
    3. Excludes codegen and log analysis files
    """
    results_dir = PROJECT_ROOT / "results"
    da_vuln_files = []

    for jsonl_path in sorted(results_dir.rglob("*_detailed_results.jsonl")):
        path_str = str(jsonl_path).lower()
        name = jsonl_path.name.lower()

        # Exclude codegen files
        if "codegen" in path_str or "_code_" in path_str:
            continue

        # Exclude log analysis files
        if "log_analysis" in path_str:
            continue

        # Must be DA file (DA-vuln prefix, not DA-code)
        if not (name.startswith("da-") or "_da-" in name):
            continue

        # Exclude codegen files by DA-code prefix
        if name.startswith("da-code"):
            continue

        # Verify it's a vuln file by checking first entry for expected fields
        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    has_gt = "ground_truth" in entry or "target" in entry
                    if has_gt and "vuln" in entry:
                        da_vuln_files.append(str(jsonl_path))
                    break
        except Exception:
            continue

    return da_vuln_files


# ---------------------------------------------------------------------------
# Fix a single JSONL file
# ---------------------------------------------------------------------------

def fix_jsonl_file(jsonl_path, dry_run=False):
    """
    Re-parse vuln predictions for all entries using the tightened DA parser.

    Returns dict with:
        changed: int — number of entries with changed prediction
        total: int — total data entries processed
        changes: list of (idx, old_pred, new_pred)
    """
    entries = []
    changes = []

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

            # Skip entries without vuln field (e.g., evaluation summaries)
            if "vuln" not in entry:
                entries.append(entry)
                continue

            reasoning = entry.get("reasoning", "")
            if not isinstance(reasoning, str) or not reasoning.strip():
                entries.append(entry)
                continue

            # Strip think block and re-parse with full tightened parser
            response_only = strip_think_block(reasoning)
            new_pred = parse_da_prediction_fixed(response_only)
            old_pred = entry.get("vuln")

            if old_pred != new_pred:
                changes.append((entry.get("idx", "?"), old_pred, new_pred))
                if not dry_run:
                    entry["vuln"] = new_pred

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
        "total": sum(1 for e in entries if isinstance(e, dict) and "vuln" in e),
        "changes": changes,
    }


def fix_companion_csv(jsonl_path, changes_by_idx):
    """
    Update the companion CSV file's vuln column to match corrected JSONL.
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

    # Find vuln and idx column indices
    vuln_col = None
    idx_col = None
    for i, h in enumerate(header):
        h_lower = h.strip().lower()
        if h_lower == "vuln":
            vuln_col = i
        if h_lower == "idx":
            idx_col = i

    if vuln_col is None or idx_col is None:
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
                old_val = row[vuln_col]
                row[vuln_col] = str(new_val)
                if old_val != row[vuln_col]:
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
        description="Fix DA vuln keyword fallback false positives (NO-before-YES + tight phrases)"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    parser.add_argument("--diff-report", type=str, default=None,
                        help="Save per-sample change log to this CSV path")
    args = parser.parse_args()

    print("=" * 72)
    print("Fix DA Vulnerability Keyword Fallback False Positives")
    print("=" * 72)
    if args.dry_run:
        print("MODE: DRY RUN (no files will be modified)\n")
    else:
        print("MODE: LIVE (files will be modified)\n")

    # Step 1: Discover DA vuln files
    print("Discovering DA vuln JSONL files...")
    da_vuln_files = discover_da_vuln_files()
    print(f"  Found {len(da_vuln_files)} DA vuln files\n")

    if not da_vuln_files:
        print("No DA vuln files found. Exiting.")
        return 0

    # Step 2: Process each file
    total_changes = 0
    total_to_0 = 0
    total_to_1 = 0
    summary = []
    all_changes = []  # For diff report

    for fpath in da_vuln_files:
        rel_path = os.path.relpath(fpath, PROJECT_ROOT)
        print(f"Processing: {rel_path}")

        result = fix_jsonl_file(fpath, dry_run=args.dry_run)

        # Build changes-by-idx for CSV update
        changes_by_idx = {}
        for idx, old_v, new_v in result["changes"]:
            changes_by_idx[idx] = new_v

        csv_updated = 0
        if not args.dry_run and result["changed"] > 0:
            csv_updated = fix_companion_csv(fpath, changes_by_idx)

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
            for idx, old_v, new_v in result["changes"]:
                print(f"    idx={idx}: {old_v} -> {new_v}")

        # Collect for diff report
        for idx, old_v, new_v in result["changes"]:
            all_changes.append({
                "file": rel_path,
                "idx": idx,
                "old_vuln": old_v,
                "new_vuln": new_v,
            })

        summary.append({
            "file": rel_path,
            "total": result["total"],
            "changed": result["changed"],
            "to_0": to_0,
            "to_1": to_1,
        })
        print()

    # Step 3: Save diff report if requested
    if args.diff_report and all_changes:
        os.makedirs(os.path.dirname(args.diff_report) or ".", exist_ok=True)
        with open(args.diff_report, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["file", "idx", "old_vuln", "new_vuln"])
            writer.writeheader()
            writer.writerows(all_changes)
        print(f"Diff report saved to: {args.diff_report}")

    # Step 4: Print summary
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Files processed: {len(da_vuln_files)}")
    print(f"Total predictions changed: {total_changes}")
    print(f"  1->0 (false positive removed): {total_to_0}")
    print(f"  0->1 (new positive added):     {total_to_1}")

    if args.dry_run:
        print(f"\nDRY RUN — no files were modified.")
        print("Run without --dry-run to apply changes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
