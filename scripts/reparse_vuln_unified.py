#!/usr/bin/env python3
"""
Unified vulnerability detection re-parsing with the bug-fixed SA parser.

The 48 vulnerability detection experiments originally used three different parsers
(SA, DA, MA) to convert raw model output into binary predictions. This parser
variance is a threat to cross-design comparison reliability. This script applies
the bug-fixed SA parser uniformly to all experiments, replacing the original
per-design parsers.

The unified parser (bug-fixed SA):
1. Strip think-tags: text after </think> only
2. Check NO patterns FIRST (7 patterns)
3. Check YES patterns (9 patterns)
4. Fallback (4 strict keywords)
5. Default: 0 (not vulnerable)

For all three designs, the JSONL `reasoning` field contains the raw model output
text to parse (SA: direct LLM response; DA: discussion.analyst_feedback;
MA: full_discussion.review_board — same string stored in `reasoning`).

Usage:
    python scripts/reparse_vuln_unified.py --dry-run
    python scripts/reparse_vuln_unified.py --diff-report results/reparse_unified_changes.csv
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
# Unified parser (bug-fixed SA parser applied to all designs)
# ---------------------------------------------------------------------------

def parse_sa_prediction(response_text):
    """
    Unified keyword parser — the bug-fixed SA parser from fix_vuln_keyword_parsing.py.

    Applied uniformly to SA, DA, and MA experiments to eliminate parser variance.

    Fixed 2026-02-22: NO checked before YES to prevent "no vulnerability detected"
    matching the YES substring "vulnerability detected". Broad fallback keywords
    removed (matched in negative contexts).
    """
    response_lower = response_text.lower()

    # Explicit NO — checked FIRST to avoid substring false positives
    if any(p in response_lower for p in [
        "final answer: no", "final answer: (2) no", "(2) no",
        "answer: no", "no vulnerability", "no security vulnerability",
        "no, the code",
        "no:",
    ]):
        return 0

    # Explicit YES
    if any(p in response_lower for p in [
        "final answer: yes", "final answer: (1) yes", "(1) yes",
        "answer: yes", "vulnerability detected", "yes, the code",
        "yes: vulnerability",
        "yes:",
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
# Agent design detection from filename
# ---------------------------------------------------------------------------

def detect_design(filename):
    """Detect agent design from filename: SA, DA, or MA."""
    name = os.path.basename(filename).lower()
    if name.startswith("da-") or "_da-" in name:
        return "DA"
    elif name.startswith("ma-") or "_ma-" in name:
        return "MA"
    return "SA"


# ---------------------------------------------------------------------------
# File discovery (from regenerate_vuln_evaluation.py — finds ALL vuln files)
# ---------------------------------------------------------------------------

def discover_vuln_jsonl_files():
    """Find all vuln detection JSONL files (SA, DA, MA; instruct and thinking)."""
    results_dir = PROJECT_ROOT / "results"
    files = []

    for jsonl_path in sorted(results_dir.rglob("*_detailed_results.jsonl")):
        name = jsonl_path.name.lower()
        parent_name = jsonl_path.parent.name.lower()
        path_str = str(jsonl_path).lower()

        # Exclude codegen and log analysis
        if "codegen" in path_str or "_code_" in path_str or "log_analysis" in path_str:
            continue

        # Include vuln files
        is_vuln = False
        if "vuln" in name or "vuln" in parent_name:
            is_vuln = True
        if name.startswith(("sa-", "Sa-")):
            if "vuln" in parent_name or "thinking" in parent_name or "rerun" in parent_name:
                is_vuln = True

        if not is_vuln:
            continue

        # Skip SOTA comparison
        if "sota_comparison" in path_str:
            continue

        files.append(str(jsonl_path))

    return files


# ---------------------------------------------------------------------------
# Process a single JSONL file
# ---------------------------------------------------------------------------

def process_jsonl_file(jsonl_path, dry_run=False):
    """
    Re-parse vuln predictions for all entries using the unified SA parser.

    Returns dict with:
        changed: int — number of entries with changed vuln field
        total: int — total prediction entries processed
        think_entries: int — entries with </think> tag
        changes: list of (idx, old_vuln, new_vuln, ground_truth)
    """
    entries = []
    changes = []
    total_preds = 0
    think_entries = 0

    with open(jsonl_path, 'r', encoding='utf-8') as f:
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

            total_preds += 1
            reasoning = entry.get("reasoning", "")

            if not isinstance(reasoning, str) or not reasoning.strip():
                entries.append(entry)
                continue

            # Track think-tag presence
            if "</think>" in reasoning:
                think_entries += 1

            # Strip think block and re-parse with unified parser
            response_only = strip_think_block(reasoning)
            new_vuln = parse_sa_prediction(response_only)
            old_vuln = entry.get("vuln")

            if old_vuln != new_vuln:
                ground_truth = entry.get("ground_truth", "?")
                changes.append((entry.get("idx", "?"), old_vuln, new_vuln, ground_truth))
                if not dry_run:
                    entry["vuln"] = new_vuln

            entries.append(entry)

    # Write back
    if not dry_run and changes:
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                if isinstance(entry, str):
                    f.write(entry + "\n")
                else:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {
        "changed": len(changes),
        "total": total_preds,
        "think_entries": think_entries,
        "changes": changes,
    }


def fix_companion_csv(jsonl_path, changes_by_idx):
    """Update the companion CSV file's vuln column to match re-parsed JSONL."""
    csv_path = jsonl_path.replace(".jsonl", ".csv")
    if not os.path.exists(csv_path):
        return 0

    csv.field_size_limit(sys.maxsize)

    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

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
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    return updated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Unified vulnerability detection re-parsing with bug-fixed SA parser"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    parser.add_argument("--diff-report", type=str, default=None,
                        help="Path to save CSV diff report of all changed predictions")
    args = parser.parse_args()

    print("=" * 72)
    print("Unified Vulnerability Detection Re-parsing")
    print("=" * 72)
    if args.dry_run:
        print("MODE: DRY RUN (no files will be modified)\n")
    else:
        print("MODE: LIVE (files will be modified)\n")

    # Step 1: Discover all vuln JSONL files
    print("Discovering vuln JSONL files...")
    vuln_files = discover_vuln_jsonl_files()
    print(f"  Found {len(vuln_files)} vuln JSONL files\n")

    if not vuln_files:
        print("No vuln files found. Exiting.")
        return 0

    # Step 2: Process each file
    total_changes = 0
    total_to_0 = 0
    total_to_1 = 0
    all_diff_rows = []
    summary = []

    for fpath in vuln_files:
        rel_path = os.path.relpath(fpath, PROJECT_ROOT)
        design = detect_design(fpath)
        print(f"Processing [{design}]: {rel_path}")

        result = process_jsonl_file(fpath, dry_run=args.dry_run)

        # Build changes-by-idx for CSV update
        changes_by_idx = {}
        for idx, old_v, new_v, gt in result["changes"]:
            changes_by_idx[idx] = new_v

        csv_updated = 0
        if not args.dry_run and result["changed"] > 0:
            csv_updated = fix_companion_csv(fpath, changes_by_idx)

        to_0 = sum(1 for _, old, new, _ in result["changes"] if new == 0)
        to_1 = sum(1 for _, old, new, _ in result["changes"] if new == 1)
        total_changes += result["changed"]
        total_to_0 += to_0
        total_to_1 += to_1

        print(f"  Entries: {result['total']}  |  With </think>: {result['think_entries']}  |  "
              f"Changed: {result['changed']}")
        if csv_updated:
            print(f"  CSV rows updated: {csv_updated}")

        if result["changes"]:
            print(f"  Direction: {to_0} changed 1->0, {to_1} changed 0->1")

            # Collect diff rows for report
            for idx, old_v, new_v, gt in result["changes"]:
                old_correct = (1 if old_v == gt else 0) if gt != "?" else "?"
                new_correct = (1 if new_v == gt else 0) if gt != "?" else "?"
                all_diff_rows.append({
                    "file": rel_path,
                    "design": design,
                    "idx": idx,
                    "old_vuln": old_v,
                    "new_vuln": new_v,
                    "ground_truth": gt,
                    "old_correct": old_correct,
                    "new_correct": new_correct,
                })

        summary.append({
            "file": rel_path,
            "design": design,
            "total": result["total"],
            "think_entries": result["think_entries"],
            "changed": result["changed"],
            "to_0": to_0,
            "to_1": to_1,
        })
        print()

    # Step 3: Print summary
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Files processed:           {len(vuln_files)}")
    print(f"Total predictions changed: {total_changes}")
    print(f"  1->0 (positive removed): {total_to_0}")
    print(f"  0->1 (positive added):   {total_to_1}")

    # Per-design breakdown
    for d in ["SA", "DA", "MA"]:
        d_files = [s for s in summary if s["design"] == d]
        d_changed = sum(s["changed"] for s in d_files)
        print(f"  {d}: {len(d_files)} files, {d_changed} predictions changed")

    # Accuracy impact
    if all_diff_rows:
        improvements = sum(1 for r in all_diff_rows if r["old_correct"] == 0 and r["new_correct"] == 1)
        regressions = sum(1 for r in all_diff_rows if r["old_correct"] == 1 and r["new_correct"] == 0)
        print(f"\nAccuracy impact of changes:")
        print(f"  Improvements (wrong->right): {improvements}")
        print(f"  Regressions  (right->wrong): {regressions}")
        print(f"  Net improvement:             {improvements - regressions}")

    # Step 4: Save diff report if requested
    if args.diff_report and all_diff_rows:
        report_path = os.path.join(PROJECT_ROOT, args.diff_report) if not os.path.isabs(args.diff_report) else args.diff_report
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "file", "design", "idx", "old_vuln", "new_vuln",
                "ground_truth", "old_correct", "new_correct",
            ])
            writer.writeheader()
            writer.writerows(all_diff_rows)
        print(f"\nDiff report saved to: {report_path}")
        print(f"  Total rows: {len(all_diff_rows)}")

    if args.dry_run:
        print(f"\nDRY RUN — no files were modified.")
        print("Run without --dry-run to apply changes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
