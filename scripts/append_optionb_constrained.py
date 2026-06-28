#!/usr/bin/env python3
"""Append the Option-B (VulTrial-constrained, strict) MA rows to the catalog.

The 4 constrained MA configs (Super-49B + Qwen-30B, instruct/thinking, zero-shot)
were re-inferred with the full VulTrial prompt set and labelled by
parse_ma_constrained(strict) — already stored in the `vuln` field of the
detailed_results JSONLs under results/runpod_vuln_870_constrained/.

This computes perf (F1/precision/recall/confusion) + P-C for each and appends
rows tagged variant=constrained / label_rule=constrained_strict_optionB to:
    results/consolidated_performance.csv
    results/rq3_baseline/pairwise_correct_all_configs.csv

Re-run safe: existing constrained_strict_optionB rows are removed first.
Dedup by idx (the merged Super-49B-thinking file has 2 dup idx); skipped
samples (skipped:true / vuln not in {0,1}) are EXCLUDED.

Usage:
    python scripts/append_optionb_constrained.py
"""

import csv
import json
import os
import sys
from collections import defaultdict

from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix)

csv.field_size_limit(sys.maxsize)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDIR = os.path.join(ROOT, "results", "runpod_vuln_870_constrained")
PERF_CSV = os.path.join(ROOT, "results", "consolidated_performance.csv")
PC_CSV = os.path.join(ROOT, "results", "rq3_baseline", "pairwise_correct_all_configs.csv")

LABEL_RULE = "constrained_strict_optionB"
VARIANT = "constrained"

# (model, model_family, parameters_b, mode, filename)
CONFIGS = [
    ("Nemotron-Super-49B", "Nemotron", 49, "instruct",
     "MA-vuln-four-zero_shot-constrained_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_detailed_results.jsonl"),
    ("Nemotron-Super-49B", "Nemotron", 49, "thinking",
     "MA-vuln-four-zero_shot-constrained_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_thinking_detailed_results.jsonl"),
    ("Qwen3-30B-A3B-Instruct", "Qwen", 30, "instruct",
     "MA-vuln-four-zero_shot-constrained_Qwen-Qwen3-30B-A3B-Instruct-2507_detailed_results.jsonl"),
    ("Qwen3-30B-A3B-Thinking", "Qwen", 30, "thinking",
     "MA-vuln-four-zero_shot-constrained_Qwen-Qwen3-30B-A3B-Thinking-2507_thinking_detailed_results.jsonl"),
]


def load_dedup(path):
    """Load JSONL, dedup by idx (first occurrence)."""
    recs = {}
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            idx = r.get("idx")
            if idx is None:
                continue
            idx = int(idx)
            if idx not in recs:
                recs[idx] = r
    return recs


def is_skipped(r):
    if r.get("skipped"):
        return True
    try:
        return int(r.get("vuln")) not in (0, 1)
    except (TypeError, ValueError):
        return True


def perf_and_pc(recs):
    preds, gts = [], []
    pairs = defaultdict(lambda: {"gt": [], "pred": [], "skip": []})
    n_excluded = 0
    for idx, r in recs.items():
        gt = int(r.get("ground_truth", r.get("target", -1)))
        skip = is_skipped(r)
        if skip:
            n_excluded += 1
        else:
            v = int(r.get("vuln"))
            preds.append(v); gts.append(gt)
        cid = r.get("commit_id", "")
        if cid:
            pairs[cid]["gt"].append(gt)
            pairs[cid]["pred"].append(-1 if skip else int(r.get("vuln")))
            pairs[cid]["skip"].append(skip)

    acc = accuracy_score(gts, preds)
    prec = precision_score(gts, preds, zero_division=0)
    rec = recall_score(gts, preds, zero_division=0)
    f1 = f1_score(gts, preds, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(gts, preds, labels=[0, 1]).ravel()

    res = {"pc": 0, "pv": 0, "pb": 0, "pr": 0}
    pair_count = excl_pairs = 0
    for cid, d in pairs.items():
        i = 0
        while i + 1 < len(d["gt"]):
            if d["skip"][i] or d["skip"][i + 1]:
                excl_pairs += 1; i += 2; continue
            pair_count += 1
            if d["gt"][i] == d["pred"][i] and d["gt"][i + 1] == d["pred"][i + 1]:
                res["pc"] += 1
            elif d["pred"][i] == 1 and d["pred"][i + 1] == 1:
                res["pv"] += 1
            elif d["pred"][i] == 0 and d["pred"][i + 1] == 0:
                res["pb"] += 1
            else:
                res["pr"] += 1
            i += 2
    tot = sum(res.values())
    pc = {k: round(v / tot * 100, 2) if tot else 0 for k, v in res.items()}
    return {
        "n": len(preds), "n_excluded": n_excluded,
        "acc": acc, "prec": prec, "rec": rec, "f1": f1,
        "tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn),
        "correct": int(tp + tn),
        "pairs": pair_count, "excluded_pairs": excl_pairs,
        "pc_pct": pc["pc"], "pv_pct": pc["pv"], "pb_pct": pc["pb"], "pr_pct": pc["pr"],
    }


def main():
    perf_rows, pc_rows = [], []
    print(f"{'config':40s} {'n':>4} {'excl':>4}  F1    PPR   P-C")
    for model, fam, params, mode, fname in CONFIGS:
        path = os.path.join(CDIR, fname)
        if not os.path.exists(path):
            print(f"  MISSING: {fname}")
            continue
        m = perf_and_pc(load_dedup(path))
        ppr = (m["tp"] + m["fp"]) / m["n"] if m["n"] else 0
        print(f"  {model+'/'+mode:38s} {m['n']:>4} {m['n_excluded']:>4}  "
              f"{m['f1']:.3f} {ppr:.3f} {m['pc_pct']:.1f}%")
        perf_rows.append({
            "model": model, "model_family": fam, "parameters_b": params,
            "design": "MA", "task": "vulnerability_detection", "dataset": "VulTrial-870",
            "mode": mode, "prompting": "zero-shot", "thinking_enabled": mode == "thinking",
            "accuracy": round(m["acc"], 6), "precision": round(m["prec"], 6),
            "recall": round(m["rec"], 6), "f1_score": round(m["f1"], 6),
            "true_positives": m["tp"], "true_negatives": m["tn"],
            "false_positives": m["fp"], "false_negatives": m["fn"],
            "pass_at_1": "", "passed_samples": "", "failed_samples": "",
            "total_samples": m["n"], "correct_predictions": m["correct"],
            "skipped_samples": m["n_excluded"],
            "source_type": "runpod_vuln_870_constrained", "source_file": path,
            "variant": VARIANT, "label_rule": LABEL_RULE,
        })
        pc_rows.append({
            "design": "MA", "model": model, "mode": mode, "prompting": "zero-shot",
            "pairs": m["pairs"], "pc_pct": m["pc_pct"], "pv_pct": m["pv_pct"],
            "pb_pct": m["pb_pct"], "pr_pct": m["pr_pct"],
            "variant": VARIANT, "label_rule": LABEL_RULE,
        })

    # --- append to perf CSV (re-run safe) ---
    with open(PERF_CSV, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        kept = [r for r in reader if r.get("label_rule") != LABEL_RULE]
    with open(PERF_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in kept:
            w.writerow({k: r.get(k, "") for k in fields})
        for r in perf_rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print(f"\nperf: kept {len(kept)} + appended {len(perf_rows)} constrained -> {PERF_CSV}")

    # --- append to P-C CSV (re-run safe) ---
    with open(PC_CSV, newline="") as f:
        reader = csv.DictReader(f)
        pc_fields = list(reader.fieldnames)
        pc_kept = [r for r in reader if r.get("label_rule") != LABEL_RULE]
    for col in ("variant", "label_rule"):
        if col not in pc_fields:
            pc_fields.append(col)
    with open(PC_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pc_fields)
        w.writeheader()
        for r in pc_kept:
            w.writerow({k: r.get(k, "") for k in pc_fields})
        for r in pc_rows:
            w.writerow({k: r.get(k, "") for k in pc_fields})
    print(f"P-C:  kept {len(pc_kept)} + appended {len(pc_rows)} constrained -> {PC_CSV}")


if __name__ == "__main__":
    main()
