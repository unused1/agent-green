"""Patch the `vuln` label IN-PLACE in the VulTrial-870 result JSONLs (P0.6).

Corrects only the derived `vuln` field using the canonical parser; the raw model
output (`reasoning` / `discussion` / `full_discussion`) is never touched. After
patching, run scripts/generate_vuln_870_performance.py to recompute
consolidated_performance.csv from the corrected labels.

Field map (same as the reparser):
    NoAgent / SA : reasoning                       -> classify
    DA           : discussion.analyst_feedback     -> classify
    MA           : full_discussion.review_board     -> parse_ma_affirm (Option A)

Safeguards:
  - Skipped samples (vuln == -1, no model output) are preserved as -1.
  - Records whose verdict field is empty are left unchanged.
  - Atomic write (temp file + os.replace) so an interrupt cannot corrupt a file.
  - p0_corrected_labels.csv already records old->new per entry (audit + revert);
    a local tar/zip backup of the two dirs is the second revert path.

Usage:
    python scripts/patch_vuln_labels_inplace.py --dry-run   # report, no writes
    python scripts/patch_vuln_labels_inplace.py             # patch in place
"""

import argparse
import ast
import csv
import json
import os
import sys
import tempfile
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from vuln_parser import classify, parse_ma_affirm  # noqa: E402

csv.field_size_limit(sys.maxsize)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSOLIDATED = os.path.join(ROOT, "results", "consolidated_performance.csv")


def _as_dict(v):
    if isinstance(v, dict):
        return v
    if isinstance(v, str) and v.strip():
        for ld in (json.loads, ast.literal_eval):
            try:
                o = ld(v)
                if isinstance(o, dict):
                    return o
            except (ValueError, SyntaxError, TypeError):
                pass
    return {}


def raw_verdict_field(design, rec):
    d = design.upper()
    if d == "DA":
        disc = _as_dict(rec.get("discussion"))
        for k in ("analyst_feedback", "final_decision"):
            if disc.get(k):
                return disc[k]
        return rec.get("reasoning", "")
    if d == "MA":
        fd = _as_dict(rec.get("full_discussion"))
        for k in ("review_board", "board"):
            if fd.get(k):
                return fd[k]
        return rec.get("reasoning", "")
    return rec.get("reasoning", "")


def new_label(design, rec):
    """Return (new_vuln_or_None). None => leave unchanged (skip/empty)."""
    old = rec.get("vuln")
    try:
        old_int = int(old)
    except (TypeError, ValueError):
        old_int = None
    if old_int == -1:
        return None  # preserve explicit skip
    raw = raw_verdict_field(design, rec)
    if not str(raw).strip():
        return None  # no output to parse -> leave as-is
    if design.upper() == "MA":
        v, _ = parse_ma_affirm(raw)
    else:
        v, _ = classify(design, raw)
    return v


def file_design_map():
    """Map each VulTrial-870 source JSONL path -> design."""
    m = {}
    for r in csv.DictReader(open(CONSOLIDATED)):
        if r.get("dataset") != "VulTrial-870":
            continue
        for p in r["source_file"].split(";"):
            p = p.strip()
            if p:
                m[p] = r["design"]
    return m


def patch_file(path, design, dry_run):
    changed = 0
    total = 0
    out_lines = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s:
                out_lines.append(line)
                continue
            rec = json.loads(s)
            total += 1
            nv = new_label(design, rec)
            if nv is not None:
                try:
                    old = int(rec.get("vuln"))
                except (TypeError, ValueError):
                    old = None
                if old != nv:
                    changed += 1
                rec["vuln"] = nv
            out_lines.append(json.dumps(rec, ensure_ascii=False) + "\n")
    if not dry_run and changed:
        d = os.path.dirname(path)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w") as tf:
            tf.writelines(out_lines)
        os.replace(tmp, path)  # atomic
    return total, changed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fdm = file_design_map()
    print(f"VulTrial-870 source files to patch: {len(fdm)}")
    by_design = defaultdict(lambda: [0, 0, 0])  # files, total, changed
    for path, design in sorted(fdm.items()):
        if not os.path.exists(path):
            print(f"  MISSING: {path}")
            continue
        total, changed = patch_file(path, design, args.dry_run)
        bd = by_design[design]
        bd[0] += 1; bd[1] += total; bd[2] += changed

    print(f"\n{'design':8s} {'files':>6} {'rows':>7} {'changed':>8} {'pct':>6}")
    tf = tt = tc = 0
    for d in ("NoAgent", "SA", "DA", "MA"):
        if d not in by_design:
            continue
        files, total, changed = by_design[d]
        tf += files; tt += total; tc += changed
        pct = 100.0 * changed / total if total else 0
        print(f"{d:8s} {files:>6} {total:>7} {changed:>8} {pct:>5.1f}%")
    print(f"{'TOTAL':8s} {tf:>6} {tt:>7} {tc:>8} {100.0*tc/tt if tt else 0:>5.1f}%")
    if args.dry_run:
        print("\n[dry-run] no files written.")
    else:
        print("\nPatched in place. Next: python scripts/generate_vuln_870_performance.py")


if __name__ == "__main__":
    main()
