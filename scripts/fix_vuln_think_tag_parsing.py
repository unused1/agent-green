#!/usr/bin/env python3
"""
Fix vulnerability detection predictions affected by think-tag parsing bug.

When thinking models produce output with <think>...</think> tags, the keyword-based
prediction parser was searching the entire output (think block + formal response)
instead of just the formal response after </think>. The think block often mentions
vulnerability keywords while exploring possibilities (e.g., "buffer overflow") even
when the model's final answer is "NO", causing incorrect vuln field values.

This script:
1. Discovers all vuln detection *_detailed_results.jsonl files with </think> tags
2. Re-parses the vuln field from the response-only text (after </think>)
3. Uses the same parsing logic per agent design (SA/DA/MA)
4. Overwrites the vuln field in each JSONL entry in-place
5. Updates companion CSV files if present
6. Logs all changes

Usage:
    python scripts/fix_vuln_think_tag_parsing.py --dry-run   # Preview changes
    python scripts/fix_vuln_think_tag_parsing.py              # Apply fixes
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
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
# Parsing functions per agent design (mirroring source scripts)
# ---------------------------------------------------------------------------

def parse_sa_prediction(response_text):
    """
    SA keyword parsing — mirrors single_agent_vuln_detection.py lines 326-345
    and single_agent_vuln_openrouter.py parse_vulnerability_response().

    Fixed 2026-02-22: Reorder NO before YES to prevent "no vulnerability detected"
    matching the YES substring "vulnerability detected". Removed broad fallback
    keywords that matched in negative contexts (e.g., "no buffer overflow detected").
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

    # Fallback keywords — only strong positive indicators
    if any(k in response_lower for k in [
        "is vulnerable", "contains a vulnerability",
        "security vulnerability exists", "can be exploited",
    ]):
        return 1

    return 0  # Default


def parse_da_prediction(response_text):
    """
    DA parsing — mirrors dual_agent_vuln.py extract_vulnerability_decision().
    JSON parse + keyword fallback (tightened 2026-03-01: NO-before-YES + tight phrases).
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


def parse_ma_prediction(response_text):
    """
    MA parsing — mirrors multi_agent_vuln_detection_four_agents.py
    extract_vulnerability_decision(). JSON array + signal counting.
    """
    try:
        # Strip markdown code blocks
        text = re.sub(r'```(?:json)?\s*', '', response_text)
        text = re.sub(r'```\s*', '', text)

        # Extract JSON array
        match = re.search(r'(\[[\s\S]*\])', text)
        if match:
            json_str = match.group(1)
        else:
            json_str = text.strip()

        verdicts = json.loads(json_str)

        vuln_signals = 0
        safe_signals = 0

        for v in verdicts:
            decision = v.get('decision', '').lower().strip()
            severity = v.get('severity', '').lower().strip()

            # SAFE signals
            if any(kw in decision for kw in ['no vulnerability', 'no_vulnerability', 'reject', 'invalid', 'safe', 'not exploitable']):
                safe_signals += 2
                continue
            if any(kw in decision for kw in ['mitigated', 'resolved', 'fixed', 'patched']):
                safe_signals += 2
                continue

            # VULNERABLE signals
            if any(kw in decision for kw in ['confirmed', 'vulnerable', 'exploitable']):
                vuln_signals += 2
                continue
            if decision in ['valid', 'partially valid']:
                vuln_signals += 2
                continue
            if 'accept' in decision:
                vuln_signals += 2
                continue
            if decision in ['critical', 'high', 'high severity', 'critical severity']:
                vuln_signals += 2
                continue
            if any(kw in decision for kw in ['fix required', 'action required', 'requires fix']):
                vuln_signals += 1
                continue
            if decision in ['medium', 'low', 'moderate', 'medium severity', 'low severity']:
                vuln_signals += 1
                continue

            # Ambiguous — use severity
            if severity in ['critical', 'high']:
                vuln_signals += 1
            elif severity in ['low', 'medium', 'moderate']:
                safe_signals += 1

        has_vulnerability = vuln_signals >= safe_signals and vuln_signals > 0
        return 1 if has_vulnerability else 0

    except Exception:
        # Fallback: keyword matching
        text = response_text.lower()
        if any(k in text for k in ['confirmed vulnerability', 'critical vulnerability', 'exploitable']):
            return 1
        if any(k in text for k in ['no vulnerability', 'not vulnerable', 'safe', 'mitigated', 'resolved']):
            return 0
        return 0


# ---------------------------------------------------------------------------
# Agent design detection from filename
# ---------------------------------------------------------------------------

def detect_design(filename):
    """Detect agent design from filename: SA, DA, or MA."""
    name = os.path.basename(filename)
    if name.startswith("DA-") or "_DA-" in name:
        return "DA"
    elif name.startswith("MA-") or "_MA-" in name:
        return "MA"
    elif name.startswith("Sa-") or name.startswith("SA-"):
        return "SA"
    # Fallback: check for vuln in path to distinguish
    return "SA"


PARSERS = {
    "SA": parse_sa_prediction,
    "DA": parse_da_prediction,
    "MA": parse_ma_prediction,
}


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def discover_affected_files():
    """Find all vuln detection JSONL files that contain </think> tags."""
    results_dir = PROJECT_ROOT / "results"
    affected = []

    # Search all *_detailed_results.jsonl under results/
    for jsonl_path in sorted(results_dir.rglob("*_detailed_results.jsonl")):
        # Skip non-vuln files (codegen, log analysis)
        name = jsonl_path.name.lower()
        parent_name = jsonl_path.parent.name.lower()

        # Exclude codegen and log analysis files
        path_str = str(jsonl_path).lower()
        if "codegen" in path_str or "_code_" in path_str or "log_analysis" in path_str:
            continue

        # Include SA vuln files (Sa-*, SA-*) and DA/MA vuln files
        is_vuln = False
        if "vuln" in name or "vuln" in parent_name:
            is_vuln = True
        # SA files may not have "vuln" in filename (e.g., Sa-few_Qwen...)
        if name.startswith(("sa-", "Sa-")):
            # Check if it's under a vuln directory or has vuln fields
            if "vuln" in parent_name or "thinking" in parent_name or "rerun" in parent_name.lower():
                is_vuln = True

        if not is_vuln:
            continue

        # Skip SOTA comparison files (Claude models, no think tags)
        if "sota_comparison" in path_str:
            continue

        # Skip Instruct models (no think tags)
        if "instruct" in name or "_instruct" in parent_name:
            continue

        # Check if any entry has </think> in reasoning
        has_think = False
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        reasoning = entry.get("reasoning", "")
                        if isinstance(reasoning, str) and "</think>" in reasoning:
                            has_think = True
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"  Warning: could not read {jsonl_path}: {e}")
            continue

        if has_think:
            affected.append(str(jsonl_path))

    return affected


# ---------------------------------------------------------------------------
# Fix a single JSONL file
# ---------------------------------------------------------------------------

def fix_jsonl_file(jsonl_path, dry_run=False):
    """
    Re-parse vuln predictions for entries with </think> tags.

    Returns dict with:
        changed: int — number of entries with changed vuln field
        total: int — total entries processed
        think_entries: int — entries with </think> tag
        changes: list of (idx, old_vuln, new_vuln)
    """
    design = detect_design(jsonl_path)
    parser = PARSERS[design]

    entries = []
    changes = []
    think_entries = 0

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                entries.append(line)  # Preserve non-JSON lines (e.g., summary)
                continue

            # Skip entries without vuln field (e.g., evaluation summaries)
            if "vuln" not in entry:
                entries.append(entry)
                continue

            reasoning = entry.get("reasoning", "")

            # Only fix entries with </think> tags
            if isinstance(reasoning, str) and "</think>" in reasoning:
                think_entries += 1
                response_only = strip_think_block(reasoning)
                new_vuln = parser(response_only)
                old_vuln = entry.get("vuln")

                if old_vuln != new_vuln:
                    changes.append((entry.get("idx", "?"), old_vuln, new_vuln))
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
        "total": len(entries),
        "think_entries": think_entries,
        "changes": changes,
    }


def fix_companion_csv(jsonl_path, changes_by_idx):
    """
    Update the companion CSV file's vuln column to match corrected JSONL.
    changes_by_idx: dict mapping idx -> new_vuln value
    """
    csv_path = jsonl_path.replace(".jsonl", ".csv")
    if not os.path.exists(csv_path):
        return 0

    csv.field_size_limit(sys.maxsize)

    # Read all rows
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    # Find vuln and idx column indices
    vuln_col = None
    idx_col = None
    for i, h in enumerate(header):
        if h.strip().lower() == "vuln":
            vuln_col = i
        if h.strip().lower() == "idx":
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

            if row_idx_num in changes_by_idx:
                old_val = row[vuln_col]
                row[vuln_col] = str(changes_by_idx[row_idx_num])
                if old_val != row[vuln_col]:
                    updated += 1
            elif row_idx in changes_by_idx:
                old_val = row[vuln_col]
                row[vuln_col] = str(changes_by_idx[row_idx])
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
    parser = argparse.ArgumentParser(description="Fix vuln detection think-tag parsing bug")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    args = parser.parse_args()

    print("=" * 72)
    print("Fix Vulnerability Detection Think-Tag Parsing Bug")
    print("=" * 72)
    if args.dry_run:
        print("MODE: DRY RUN (no files will be modified)\n")
    else:
        print("MODE: LIVE (files will be modified)\n")

    # Step 1: Discover affected files
    print("Discovering affected JSONL files...")
    affected_files = discover_affected_files()
    print(f"  Found {len(affected_files)} files with </think> tags\n")

    if not affected_files:
        print("No affected files found. Exiting.")
        return 0

    # Step 2: Process each file
    total_changes = 0
    summary = []

    for fpath in affected_files:
        rel_path = os.path.relpath(fpath, PROJECT_ROOT)
        design = detect_design(fpath)
        print(f"Processing [{design}]: {rel_path}")

        result = fix_jsonl_file(fpath, dry_run=args.dry_run)

        # Build changes-by-idx for CSV update
        changes_by_idx = {}
        for idx, old_v, new_v in result["changes"]:
            changes_by_idx[idx] = new_v

        csv_updated = 0
        if not args.dry_run and result["changed"] > 0:
            csv_updated = fix_companion_csv(fpath, changes_by_idx)

        mismatch_pct = (result["changed"] / result["think_entries"] * 100
                        if result["think_entries"] > 0 else 0)
        total_changes += result["changed"]

        print(f"  Entries: {result['total']}  |  With </think>: {result['think_entries']}  |  "
              f"Changed: {result['changed']} ({mismatch_pct:.1f}%)")
        if csv_updated:
            print(f"  CSV rows updated: {csv_updated}")

        if result["changes"]:
            # Show change breakdown
            to_0 = sum(1 for _, old, new in result["changes"] if new == 0)
            to_1 = sum(1 for _, old, new in result["changes"] if new == 1)
            print(f"  Direction: {to_0} changed 1→0, {to_1} changed 0→1")

        summary.append({
            "file": rel_path,
            "design": design,
            "total": result["total"],
            "think_entries": result["think_entries"],
            "changed": result["changed"],
            "mismatch_pct": mismatch_pct,
        })
        print()

    # Step 3: Print summary
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Files processed: {len(affected_files)}")
    print(f"Total predictions changed: {total_changes}")

    if args.dry_run:
        print(f"\nDRY RUN — no files were modified.")
        print("Run without --dry-run to apply changes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
