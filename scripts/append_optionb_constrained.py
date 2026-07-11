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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from consolidate_emissions import load_emissions_from_dir  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDIR = os.path.join(ROOT, "results", "runpod_vuln_870_constrained")
PERF_CSV = os.path.join(ROOT, "results", "consolidated_performance.csv")
PC_CSV = os.path.join(ROOT, "results", "rq3_baseline", "pairwise_correct_all_configs.csv")
EMISSIONS_CSV = os.path.join(ROOT, "results", "consolidated_emissions.csv")
EDIR = os.path.join(CDIR, "emissions")

# model display name -> (family, parameters_b)
MODEL_META = {
    "Nemotron-Super-49B": ("Nemotron", 49),
    "Qwen3-30B-A3B-Instruct": ("Qwen", 30),
    "Qwen3-30B-A3B-Thinking": ("Qwen", 30),
    "Qwen3-4B-Instruct": ("Qwen", 4),
    "Qwen3-4B-Thinking": ("Qwen", 4),
    "Nemotron-Nano-8B": ("Nemotron", 8),
}

# Energy is parse-independent -> these rows are variant=constrained / label_rule=any
# (sentinel). Join to consolidated_performance.csv on (model, design, mode,
# prompting, dataset, variant), NOT label_rule. Some cells sum multiple shard subdirs
# (Super-49B-thinking zero = 3 shards; Nano-8B-thinking few = 4 disjoint shards).
# Keyed by (model, mode, prompting).
EMISSIONS_SUBDIRS = {
    # --- zero-shot LARGE (original Option-B campaign) ---
    ("Nemotron-Super-49B", "instruct", "zero-shot"): ["super49b_instruct"],
    ("Nemotron-Super-49B", "thinking", "zero-shot"): ["super49b_thinking_shard1",
                                                      "super49b_thinking_shard2",
                                                      "super49b_thinking_shard3"],
    ("Qwen3-30B-A3B-Instruct", "instruct", "zero-shot"): ["qwen30b_instruct"],
    ("Qwen3-30B-A3B-Thinking", "thinking", "zero-shot"): ["qwen30b_thinking"],
    # --- few-shot (all 4 models) ---
    ("Nemotron-Super-49B", "instruct", "few-shot"): ["super49b_instruct_few"],
    ("Nemotron-Super-49B", "thinking", "few-shot"): ["super49b_thinking_few"],
    ("Qwen3-30B-A3B-Instruct", "instruct", "few-shot"): ["qwen30b_instruct_few"],
    ("Qwen3-30B-A3B-Thinking", "thinking", "few-shot"): ["qwen30b_thinking_few"],
    ("Qwen3-4B-Instruct", "instruct", "few-shot"): ["qwen4b_instruct_few"],
    ("Qwen3-4B-Thinking", "thinking", "few-shot"): ["qwen4b_thinking_few"],
    ("Nemotron-Nano-8B", "instruct", "few-shot"): ["nano8b_instruct_few"],
    ("Nemotron-Nano-8B", "thinking", "few-shot"): ["nano8b_thinking_few_front",
                                                   "nano8b_thinking_few_shardA",
                                                   "nano8b_thinking_few_shardB",
                                                   "nano8b_thinking_few_shardC"],
    # --- zero-shot SMALL ---
    ("Qwen3-4B-Instruct", "instruct", "zero-shot"): ["qwen4b_instruct_zero"],
    ("Qwen3-4B-Thinking", "thinking", "zero-shot"): ["qwen4b_thinking_zero"],
    ("Nemotron-Nano-8B", "instruct", "zero-shot"): ["nano8b_instruct_zero"],
    ("Nemotron-Nano-8B", "thinking", "zero-shot"): ["nano8b_thinking_zero"],
}

LABEL_RULE = "constrained_strict_optionB"
VARIANT = "constrained"

# The PrimeVul-Pair test split contains 2 inherent duplicate benign functions
# (both target=0), each appearing twice byte-identical. To report on the canonical
# VulTrial-870 (comparable to other PrimeVul-Pair work), we dedup by idx for
# reproducibility, then count these 2 idx twice in the flat confusion matrix
# (F1/accuracy) so n = 870. They sit in multi-vulnerability commit groups outside
# the clean pairs, so P-C is left untouched (see VulTrial_870_PROVENANCE.md).
DUP_IDX = {349259, 439495}

# (model, model_family, parameters_b, mode, prompting, filename)
CONFIGS = [
    # --- zero-shot LARGE (original Option-B campaign) ---
    ("Nemotron-Super-49B", "Nemotron", 49, "instruct", "zero-shot",
     "MA-vuln-four-zero_shot-constrained_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_detailed_results.jsonl"),
    ("Nemotron-Super-49B", "Nemotron", 49, "thinking", "zero-shot",
     "MA-vuln-four-zero_shot-constrained_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_thinking_detailed_results.jsonl"),
    ("Qwen3-30B-A3B-Instruct", "Qwen", 30, "instruct", "zero-shot",
     "MA-vuln-four-zero_shot-constrained_Qwen-Qwen3-30B-A3B-Instruct-2507_detailed_results.jsonl"),
    ("Qwen3-30B-A3B-Thinking", "Qwen", 30, "thinking", "zero-shot",
     "MA-vuln-four-zero_shot-constrained_Qwen-Qwen3-30B-A3B-Thinking-2507_thinking_detailed_results.jsonl"),
    # --- few-shot (all 4 models) ---
    ("Nemotron-Super-49B", "Nemotron", 49, "instruct", "few-shot",
     "MA-vuln-four-few_shot-constrained_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_detailed_results.jsonl"),
    ("Nemotron-Super-49B", "Nemotron", 49, "thinking", "few-shot",
     "MA-vuln-four-few_shot-constrained_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_thinking_detailed_results.jsonl"),
    ("Qwen3-30B-A3B-Instruct", "Qwen", 30, "instruct", "few-shot",
     "MA-vuln-four-few_shot-constrained_Qwen-Qwen3-30B-A3B-Instruct-2507_detailed_results.jsonl"),
    ("Qwen3-30B-A3B-Thinking", "Qwen", 30, "thinking", "few-shot",
     "MA-vuln-four-few_shot-constrained_Qwen-Qwen3-30B-A3B-Thinking-2507_thinking_detailed_results.jsonl"),
    ("Qwen3-4B-Instruct", "Qwen", 4, "instruct", "few-shot",
     "MA-vuln-four-few_shot-constrained_Qwen-Qwen3-4B-Instruct-2507_detailed_results.jsonl"),
    ("Qwen3-4B-Thinking", "Qwen", 4, "thinking", "few-shot",
     "MA-vuln-four-few_shot-constrained_Qwen-Qwen3-4B-Thinking-2507_thinking_detailed_results.jsonl"),
    ("Nemotron-Nano-8B", "Nemotron", 8, "instruct", "few-shot",
     "MA-vuln-four-few_shot-constrained_nvidia-Llama-3.1-Nemotron-Nano-8B-v1_detailed_results.jsonl"),
    ("Nemotron-Nano-8B", "Nemotron", 8, "thinking", "few-shot",
     "MA-vuln-four-few_shot-constrained_nvidia-Llama-3.1-Nemotron-Nano-8B-v1_thinking_detailed_results.jsonl"),
    # --- zero-shot SMALL ---
    ("Qwen3-4B-Instruct", "Qwen", 4, "instruct", "zero-shot",
     "MA-vuln-four-zero_shot-constrained_Qwen-Qwen3-4B-Instruct-2507_detailed_results.jsonl"),
    ("Qwen3-4B-Thinking", "Qwen", 4, "thinking", "zero-shot",
     "MA-vuln-four-zero_shot-constrained_Qwen-Qwen3-4B-Thinking-2507_thinking_detailed_results.jsonl"),
    ("Nemotron-Nano-8B", "Nemotron", 8, "instruct", "zero-shot",
     "MA-vuln-four-zero_shot-constrained_nvidia-Llama-3.1-Nemotron-Nano-8B-v1_detailed_results.jsonl"),
    ("Nemotron-Nano-8B", "Nemotron", 8, "thinking", "zero-shot",
     "MA-vuln-four-zero_shot-constrained_nvidia-Llama-3.1-Nemotron-Nano-8B-v1_thinking_detailed_results.jsonl"),
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
        # canonical-870: count the 2 inherent PrimeVul duplicates twice in the
        # flat confusion matrix (pairing below is left at weight 1).
        mult = 2 if idx in DUP_IDX else 1
        if skip:
            n_excluded += mult
        else:
            v = int(r.get("vuln"))
            for _ in range(mult):
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


def append_emissions():
    """Append the 4 constrained-MA emission rows (preserving the existing file).

    Existing rows are tagged variant=freeform / label_rule=any; constrained rows
    sum their per-config subdirs (Super-49B-thinking across 3 shards). Re-run safe.
    """
    # Build constrained emission records
    crows = []
    for (model, mode, prompting), subdirs in EMISSIONS_SUBDIRS.items():
        parts = [load_emissions_from_dir(os.path.join(EDIR, s)) for s in subdirs]
        parts = [p for p in parts if p]
        if not parts:
            print(f"  emissions MISSING for {model}/{mode}/{prompting}")
            continue
        dur = sum(p["duration_s"] for p in parts)
        fam, params = MODEL_META[model]
        wavg = lambda key: (sum(p[key] * p["duration_s"] for p in parts) / dur) if dur else 0
        crows.append({
            "model": model, "model_family": fam, "parameters_b": params,
            "design": "MA", "task": "vulnerability_detection", "dataset": "VulTrial-870",
            "mode": mode, "prompting": prompting, "thinking_enabled": mode == "thinking",
            "num_sessions": sum(p["num_sessions"] for p in parts),
            "total_duration_s": dur, "duration_hours": dur / 3600,
            "total_emissions_kg": sum(p["emissions_kg"] for p in parts),
            "emissions_g": sum(p["emissions_kg"] for p in parts) * 1000,
            "total_energy_kwh": sum(p["energy_kwh"] for p in parts),
            "total_cpu_energy_kwh": sum(p["cpu_energy_kwh"] for p in parts),
            "total_gpu_energy_kwh": sum(p["gpu_energy_kwh"] for p in parts),
            "total_ram_energy_kwh": sum(p["ram_energy_kwh"] for p in parts),
            "avg_cpu_power_w": wavg("cpu_power_w"), "avg_gpu_power_w": wavg("gpu_power_w"),
            "avg_ram_power_w": wavg("ram_power_w"),
            "gpu_model": parts[0]["gpu_model"], "gpu_count": parts[0]["gpu_count"],
            "cpu_model": parts[0]["cpu_model"], "country": parts[0]["country"],
            "source_note": "; ".join(os.path.join(EDIR, s) for s in subdirs),
            "variant": "constrained", "label_rule": "any",
        })

    with open(EMISSIONS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for col in ("variant", "label_rule"):
        if col not in fields:
            fields.append(col)
    kept = []
    for r in rows:
        if r.get("variant") == "constrained":
            continue  # re-run safe
        r.setdefault("variant", "freeform")
        r.setdefault("label_rule", "any")
        if not r.get("variant"):
            r["variant"] = "freeform"
        if not r.get("label_rule"):
            r["label_rule"] = "any"
        kept.append(r)
    with open(EMISSIONS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in kept:
            w.writerow({k: r.get(k, "") for k in fields})
        for r in crows:
            w.writerow({k: r.get(k, "") for k in fields})
    tot_kwh = sum(r["total_energy_kwh"] for r in crows)
    print(f"emissions: kept {len(kept)} + appended {len(crows)} constrained "
          f"({tot_kwh:.1f} kWh) -> {EMISSIONS_CSV}")


def main():
    perf_rows, pc_rows = [], []
    print(f"{'config':40s} {'n':>4} {'excl':>4}  F1    PPR   P-C")
    for model, fam, params, mode, prompting, fname in CONFIGS:
        path = os.path.join(CDIR, fname)
        if not os.path.exists(path):
            print(f"  MISSING: {fname}")
            continue
        m = perf_and_pc(load_dedup(path))
        ppr = (m["tp"] + m["fp"]) / m["n"] if m["n"] else 0
        print(f"  {model+'/'+mode+'/'+prompting:48s} {m['n']:>4} {m['n_excluded']:>4}  "
              f"{m['f1']:.3f} {ppr:.3f} {m['pc_pct']:.1f}%")
        perf_rows.append({
            "model": model, "model_family": fam, "parameters_b": params,
            "design": "MA", "task": "vulnerability_detection", "dataset": "VulTrial-870",
            "mode": mode, "prompting": prompting, "thinking_enabled": mode == "thinking",
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
            "design": "MA", "model": model, "mode": mode, "prompting": prompting,
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

    # --- append constrained emissions (preserve existing file) ---
    append_emissions()


if __name__ == "__main__":
    main()
