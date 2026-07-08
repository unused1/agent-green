#!/usr/bin/env python3
"""Grade the full FP/FN explanation-rating frame with the RQ3 LLM-as-judge.

Reuses the validated judge pipeline in scripts/rq3_llm_judge.py (rubric-only
zero-shot prompt, same parser) to score every row of
results/rq3_baseline/fpfn_rater_sheet.xlsx (480 rows: 120 each of TN/FP/FN/TP)
on completeness / clarity / actionability / informativeness.

The ANTHROPIC_API_KEY is loaded from .env. Output is appended incrementally so
the run is crash-recoverable and resumable.

Usage:
    python scripts/rq3_judge_fpfn.py --model claude-sonnet-4-6 --limit 2   # smoke test
    python scripts/rq3_judge_fpfn.py --model claude-opus-4-6               # full 480
"""
import argparse
import csv
import os
import sys
import time

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
csv.field_size_limit(2**27)


def load_dotenv(path):
    if not os.path.exists(path):
        return
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-4-6",
                    help="Anthropic judge model id (e.g. claude-opus-4-6)")
    ap.add_argument("--frame", default="results/rq3_baseline/fpfn_sample_frame.csv",
                    help="reconciled frame CSV (carries entry_id/family/mode for the IRR join)")
    ap.add_argument("--limit", type=int, default=0, help="0 = all rows (smoke-test with small N)")
    args = ap.parse_args()

    load_dotenv(os.path.join(ROOT, ".env"))
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: ANTHROPIC_API_KEY not found (checked .env)")

    import rq3_llm_judge as J
    J.JUDGE_BACKEND = "claude"
    J.JUDGE_MODEL = args.model
    J.ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

    system_prompt = J.build_system_prompt(J.load_rubric_text())
    print(f"Judge: claude/{args.model}  | system prompt {len(system_prompt)} chars")

    rows = list(csv.DictReader(open(os.path.join(ROOT, args.frame))))
    if args.limit:
        rows = rows[:args.limit]
    print(f"Rows to grade: {len(rows)} from {os.path.basename(args.frame)}")

    short = args.model.replace("claude-", "")
    out_path = os.path.join(ROOT, "results", "rq3_baseline", f"fpfn_llm_judged_{short}.csv")
    fields = (["sample_id", "family", "model", "mode", "stratum", "entry_id",
               "ground_truth_label", "prediction"]
              + [f"{d}_score" for d in J.DIMENSIONS]
              + [f"{d}_justification" for d in J.DIMENSIONS])

    done = set()
    if os.path.exists(out_path):
        for r in csv.DictReader(open(out_path)):
            done.add(str(r["sample_id"]))
        print(f"Resuming: {len(done)} already graded")
    else:
        with open(out_path, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=fields).writeheader()

    ok = fail = 0
    for i, r in enumerate(rows, 1):
        sid = str(r["sample_id"])
        if sid in done:
            continue
        user = J.build_evaluation_prompt(
            source_code=r.get("source_code", ""),
            response_text=r.get("response_text", ""),
            ground_truth_label=r.get("ground_truth_label", ""),
            cwe=r.get("cwe", ""),
            cve_desc=r.get("cve_desc", ""),
        )
        print(f"  [{i}/{len(rows)}] sid={sid} {r['family'].split('-')[0]}/{r['mode']}/{r['stratum']} "
              f"entry={r['entry_id']} ... ", end="", flush=True)
        resp = J.call_llm_judge(system_prompt, user)
        p = J.parse_judge_response(resp) if resp else None
        if p:
            row = {"sample_id": sid, "family": r["family"], "model": r["model"],
                   "mode": r["mode"], "stratum": r["stratum"], "entry_id": r["entry_id"],
                   "ground_truth_label": r["ground_truth_label"], "prediction": r["prediction"]}
            for d in J.DIMENSIONS:
                row[f"{d}_score"] = p[f"{d}_score"]
                row[f"{d}_justification"] = p[f"{d}_justification"]
            with open(out_path, "a", newline="") as f:
                csv.DictWriter(f, fieldnames=fields).writerow(row)
            print(f"scores={[p[f'{d}_score'] for d in J.DIMENSIONS]}")
            ok += 1
        else:
            print("FAILED")
            fail += 1
        time.sleep(J.REQUEST_DELAY_SECONDS)

    print(f"\nDone: {ok} ok, {fail} failed -> {out_path}")


if __name__ == "__main__":
    main()
