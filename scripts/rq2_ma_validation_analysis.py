"""Analyze the MA judge validation sample (step c).

Compares the LLM judge's verdict against the stored keyword label and the
canonical keyword label, per entry class. The key questions:
  1. On 'agree0_det' (both parsers said SAFE, dominated by "accepted and
     mitigated/resolved") — does the judge say VULNERABLE? If yes, it confirms
     the shared polarity blind spot and justifies the full-MA judge.
  2. On 'disagree' — does the judge side with canonical or stored?
  3. On 'agree1' (clean control) — does the judge agree it's vulnerable?

Usage:
    python scripts/rq2_ma_validation_analysis.py [--csv <path>]
"""

import argparse
import csv
import sys
from collections import defaultdict

csv.field_size_limit(sys.maxsize)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/rq3_baseline/rq2_ma_validation_sample_opus.csv")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.csv)))
    print(f"Loaded {len(rows)} judged rows from {args.csv}\n")

    by_cls = defaultdict(list)
    for r in rows:
        by_cls[r["cls"]].append(r)

    print(f"{'class':14s} {'n':>4} {'judge=1':>8} {'judge=stored':>13} {'judge=canon':>12} "
          f"{'judge=gt':>9}")
    tot = defaultdict(int)
    for cls in ("agree1", "agree0_det", "agree0_undet", "disagree"):
        rs = by_cls.get(cls, [])
        if not rs:
            continue
        n = len(rs)
        j1 = sum(1 for r in rs if int(r["judge"]) == 1)
        js = sum(1 for r in rs if int(r["judge"]) == int(r["stored"]))
        jc = sum(1 for r in rs if int(r["judge"]) == int(r["canon"]))
        jg = sum(1 for r in rs if int(r["judge"]) == int(r["ground_truth"]))
        print(f"{cls:14s} {n:>4} {j1:>8} {js:>11}({100*js//n:>3d}%) "
              f"{jc:>9}({100*jc//n:>3d}%) {jg:>6}({100*jg//n:>3d}%)")
        tot["n"] += n; tot["js"] += js; tot["jc"] += jc; tot["jg"] += jg

    n = tot["n"]
    print(f"\n{'OVERALL':14s} {n:>4} {'':>8} "
          f"{tot['js']:>11}({100*tot['js']//n:>3d}%) "
          f"{tot['jc']:>9}({100*tot['jc']//n:>3d}%) "
          f"{tot['jg']:>6}({100*tot['jg']//n:>3d}%)")

    # Focused read on the suspect class
    det = by_cls.get("agree0_det", [])
    if det:
        j1 = sum(1 for r in det if int(r["judge"]) == 1)
        print(f"\nKEY: of {len(det)} 'agree0_det' (both parsers SAFE) cases, "
              f"judge says VULNERABLE on {j1} ({100*j1//len(det)}%).")
        print("     -> high % confirms the shared polarity blind spot; the full-MA")
        print("        judge is warranted (keyword agreement is NOT trustworthy here).")

    # Interpretation hint
    print("\nDecision rule:")
    print("  - If judge tracks CANONICAL >> STORED on disagree, and flags many")
    print("    agree0_det as vulnerable -> proceed to full-MA judge (step a).")
    print("  - If judge tracks STORED -> stored labels were fine; reconsider.")


if __name__ == "__main__":
    main()
