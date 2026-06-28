"""Re-parse all 64 VulTrial-870 configurations with the canonical parser (P0.4).

Reads the raw model outputs already stored in the result JSONLs and re-derives
the `vuln` label using src/vuln_parser.py — the single source of truth shared
with the live inference scripts. This corrects the ~3-6% label-parser errors
(e.g. "(1) YES" misread as safe) that propagate into every downstream metric.

Design -> raw-field -> parser mapping (verified against the data):
    NoAgent / SA : record["reasoning"]                 -> parse text verdict
    DA           : record["reasoning"]                 -> JSON vuln_detected / text
    MA           : record["full_discussion"]["review_board"]  (fallback: reasoning)
                                                       -> JSON decision / text
Ground truth: record["ground_truth"] or record["target"].

Output is written to a SIDECAR file, leaving raw JSONLs pristine and the
correction fully reversible:
    results/rq3_baseline/p0_corrected_labels.csv

Usage:
    python scripts/reparse_vuln_870.py --dry-run    # report only, no writes
    python scripts/reparse_vuln_870.py              # write the sidecar CSV
"""

import argparse
import ast
import csv
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from vuln_parser import classify, parse_ma_affirm  # noqa: E402

csv.field_size_limit(sys.maxsize)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSOLIDATED_CSV = os.path.join(PROJECT_ROOT, "results", "consolidated_performance.csv")
OUT_CSV = os.path.join(PROJECT_ROOT, "results", "rq3_baseline", "p0_corrected_labels.csv")


def _as_dict(val):
    """Return a dict from val whether it's already a dict, a JSON string, or a
    stringified Python dict (single-quoted). Returns {} on failure."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val.strip():
        for loader in (json.loads, ast.literal_eval):
            try:
                out = loader(val)
                if isinstance(out, dict):
                    return out
            except (ValueError, SyntaxError, TypeError):
                continue
    return {}


def get_raw_field(design: str, rec: dict):
    """Return the design-appropriate RAW verdict-bearing output for parsing.

    Critically, the `reasoning` field is the raw model output only for NA/SA.
    For DA/MA it is a derived summary; the actual verdict lives in the
    multi-turn discussion structures:
        DA -> discussion.analyst_feedback  (analyst JSON with vulnerability_detected)
        MA -> full_discussion.review_board (review-board JSON with decision)
    """
    d = design.upper()
    if d == "DA":
        disc = _as_dict(rec.get("discussion"))
        # analyst_feedback is the final decision; fall back through known keys.
        for key in ("analyst_feedback", "final_decision", "analyst", "security_analyst"):
            if disc.get(key):
                return disc[key]
        return rec.get("reasoning", "")  # last resort
    if d == "MA":
        fd = _as_dict(rec.get("full_discussion"))
        for key in ("review_board", "board"):
            if fd.get(key):
                return fd[key]
        return rec.get("reasoning", "")  # last resort
    # NA / SA: reasoning is the raw model output
    return rec.get("reasoning", "")


def get_ground_truth(rec: dict):
    gt = rec.get("ground_truth", rec.get("target"))
    try:
        return int(gt)
    except (TypeError, ValueError):
        return None


def load_jsonl(path: str):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="Report changes without writing the sidecar CSV.")
    ap.add_argument("--samples", type=int, default=3,
                    help="Flipped-entry samples to print per design (dry-run).")
    args = ap.parse_args()

    # consolidated now carries multiple variant rows per config (submitted +
    # corrected); dedupe by config so each source file is parsed once.
    _seen_cfg = set()
    configs = []
    for r in csv.DictReader(open(CONSOLIDATED_CSV)):
        if r["dataset"] != "VulTrial-870":
            continue
        key = (r["design"], r["model"], r["mode"], r["prompting"])
        if key in _seen_cfg:
            continue
        _seen_cfg.add(key)
        configs.append(r)
    print(f"VulTrial-870 configs: {len(configs)}\n")

    out_rows = []
    # tallies
    per_design = defaultdict(lambda: {"n": 0, "unchanged": 0, "0to1": 0, "1to0": 0,
                                       "undetermined": 0})
    sample_flips = defaultdict(list)
    config_changes = []  # (label, n, changed, undetermined)

    for cfg in configs:
        design = cfg["design"]
        files = [p.strip() for p in cfg["source_file"].split(";") if p.strip()]
        seen = set()
        c_n = c_changed = c_undet = 0
        for path in files:
            for rec in load_jsonl(path):
                idx = rec.get("idx")
                if idx is None:
                    continue
                idx = int(idx)
                if idx in seen:
                    continue
                seen.add(idx)

                gt = get_ground_truth(rec)
                old = rec.get("vuln")
                try:
                    old = int(old)
                except (TypeError, ValueError):
                    old = None
                raw = get_raw_field(design, rec)
                # MA uses the deterministic affirm-unless-rejected rule (Option A);
                # NA/SA/DA use the canonical design parsers.
                if design.upper() == "MA":
                    new, determined = parse_ma_affirm(raw)
                else:
                    new, determined = classify(design, raw)

                d = per_design[design]
                d["n"] += 1
                c_n += 1
                if not determined:
                    d["undetermined"] += 1
                    c_undet += 1
                if old is None or new != old:
                    if old == 0 and new == 1:
                        d["0to1"] += 1
                    elif old == 1 and new == 0:
                        d["1to0"] += 1
                    c_changed += 1
                    if len(sample_flips[design]) < args.samples:
                        sample_flips[design].append(
                            (idx, cfg["model"], cfg["mode"], cfg["prompting"],
                             gt, old, new, determined))
                else:
                    d["unchanged"] += 1

                out_rows.append({
                    "design": design, "model": cfg["model"], "mode": cfg["mode"],
                    "prompting": cfg["prompting"], "idx": idx,
                    "ground_truth": gt, "old_vuln": old, "new_vuln": new,
                    "determined": int(determined), "changed": int(old != new),
                })
        config_changes.append(
            (f"{design}/{cfg['model']}/{cfg['mode']}/{cfg['prompting']}", c_n, c_changed, c_undet))

    # ---- Report ----
    print("=" * 78)
    print("PER-DESIGN SUMMARY")
    print("=" * 78)
    tot_n = tot_chg = tot_undet = 0
    for design in ("NoAgent", "SA", "DA", "MA"):
        if design not in per_design:
            continue
        d = per_design[design]
        chg = d["0to1"] + d["1to0"]
        tot_n += d["n"]; tot_chg += chg; tot_undet += d["undetermined"]
        pct = 100.0 * chg / d["n"] if d["n"] else 0.0
        print(f"  {design:8s} n={d['n']:5d}  changed={chg:4d} ({pct:4.1f}%)  "
              f"[0->1={d['0to1']:4d}  1->0={d['1to0']:4d}]  undetermined={d['undetermined']:4d}")
    pct_all = 100.0 * tot_chg / tot_n if tot_n else 0.0
    print(f"  {'TOTAL':8s} n={tot_n:5d}  changed={tot_chg:4d} ({pct_all:4.1f}%)  "
          f"undetermined={tot_undet}")

    print("\n" + "=" * 78)
    print(f"SAMPLE FLIPS (up to {args.samples} per design)")
    print("=" * 78)
    for design in ("NoAgent", "SA", "DA", "MA"):
        for (idx, model, mode, prom, gt, old, new, det) in sample_flips.get(design, []):
            print(f"  {design:8s} idx={idx:7d} {model} {mode}/{prom}  "
                  f"gt={gt} old={old} new={new} determined={det}")

    print("\n" + "=" * 78)
    print("TOP 10 CONFIGS BY CHANGE COUNT")
    print("=" * 78)
    for label, n, chg, undet in sorted(config_changes, key=lambda x: -x[2])[:10]:
        print(f"  {chg:3d}/{n:3d} changed  undet={undet:3d}  {label}")

    if args.dry_run:
        print(f"\n[dry-run] No file written. Would write {len(out_rows)} rows to {OUT_CSV}")
        return

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "design", "model", "mode", "prompting", "idx",
            "ground_truth", "old_vuln", "new_vuln", "determined", "changed"])
        w.writeheader()
        w.writerows(out_rows)
    print(f"\nWrote {len(out_rows)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()
