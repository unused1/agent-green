#!/usr/bin/env python3
"""Compute Pairwise Correct (P-C) metric for all VulTrial-870 configs.

P-C is the percentage of vulnerable-benign pairs where BOTH functions
are classified correctly. Based on PrimeVul Pair's commit_id grouping.

Outputs results to consolidated_performance.csv (adds pc_pct column)
and prints tables for RQ1 (NA) and RQ2 (SA/DA/MA).
"""

import json
import glob
import sys
import csv
import os
from collections import defaultdict

import pandas as pd

csv.field_size_limit(sys.maxsize)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sa_noresp_overlay import load_overlay, is_noresp  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(PROJECT_ROOT, "results")


def compute_pc(jsonl_paths: list, model: str = None, mode: str = None) -> dict:
    """Compute pairwise metrics from one or more JSONL files.

    Applies the SA no-response gap-fill overlay (by model,mode,idx) and excludes
    any pair containing a remaining no-output member (a non-prediction cannot be
    scored). Returns dict with pc, pv, pb, pr counts/percentages + excluded pairs.
    """
    overlay = load_overlay()

    # Load all predictions, dedup by idx
    preds = {}
    for path in jsonl_paths:
        with open(path) as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                idx = rec.get("idx")
                if idx is None:
                    continue
                idx = int(idx)
                if idx not in preds:
                    preds[idx] = rec

    # Group by commit_id, resolving overlay + no-output flag per member
    pairs = {}
    for idx, rec in preds.items():
        cid = rec.get("commit_id", "")
        if not cid:
            continue
        if cid not in pairs:
            pairs[cid] = {"ground_truth": [], "prediction": [], "noresp": [], "idx": []}
        gt = int(rec.get("ground_truth", rec.get("target", -1)))
        ov = overlay.get((model, mode, idx)) if model else None
        if ov is not None:
            pred, noresp = ov, False
        else:
            pred, noresp = int(rec.get("vuln", -1)), is_noresp(rec)
        pairs[cid]["ground_truth"].append(gt)
        pairs[cid]["prediction"].append(pred)
        pairs[cid]["noresp"].append(noresp)
        pairs[cid]["idx"].append(idx)

    # Compute pairwise metrics
    results = {"pc": 0, "pv": 0, "pb": 0, "pr": 0}
    pair_count = 0
    excluded_pairs = 0

    for cid, data in pairs.items():
        i = 0
        while i + 1 < len(data["ground_truth"]):
            if data["noresp"][i] or data["noresp"][i + 1]:
                excluded_pairs += 1  # non-prediction member -> drop the pair
                i += 2
                continue
            pair_count += 1
            gt1 = data["ground_truth"][i]
            gt2 = data["ground_truth"][i + 1]
            p1 = data["prediction"][i]
            p2 = data["prediction"][i + 1]

            if gt1 == p1 and gt2 == p2:
                results["pc"] += 1
            elif p1 == 1 and p2 == 1:
                results["pv"] += 1
            elif p1 == 0 and p2 == 0:
                results["pb"] += 1
            else:
                results["pr"] += 1

            i += 2

    total = sum(results.values())
    pct = {}
    for k, v in results.items():
        pct[k] = (v / total * 100) if total > 0 else 0

    return {
        "pairs": pair_count,
        "pc": results["pc"],
        "pc_pct": round(pct["pc"], 2),
        "pv_pct": round(pct["pv"], 2),
        "pb_pct": round(pct["pb"], 2),
        "pr_pct": round(pct["pr"], 2),
        "excluded_pairs": excluded_pairs,
    }


def find_jsonl_files(design, model_name, mode, prompting):
    """Find matching JSONL files across 486 and 384-incr directories."""
    shot = "zero_shot" if prompting == "zero-shot" else "few_shot"

    # Model name to possible filename substrings
    model_file_patterns = {
        "Nemotron-Nano-8B": ["Nemotron-Nano-8B"],
        "Nemotron-Super-49B": ["Nemotron-Super-49B"],
        "Qwen3-4B-Instruct": ["Qwen3-4B-Instruct"],
        "Qwen3-4B-Thinking": ["Qwen3-4B-Thinking"],
        "Qwen3-30B-A3B-Instruct": ["Qwen3-30B-A3B-Instruct"],
        "Qwen3-30B-A3B-Thinking": ["Qwen3-30B-A3B-Thinking"],
    }
    model_substrings = model_file_patterns.get(model_name, [model_name])

    # Design to filename prefix patterns
    design_prefixes = {
        "NoAgent": ["NA-vuln"],
        "SA": ["Sa-zero", "Sa-few"],
        "DA": ["DA-vuln-two"],
        "MA": ["MA-vuln-four"],
    }
    prefixes = design_prefixes.get(design, [design])

    files = []
    for dir_name in ["runpod_vuln_486", "runpod_vuln_384_incremental"]:
        dir_path = os.path.join(BASE, dir_name)
        if not os.path.exists(dir_path):
            continue

        for f in sorted(glob.glob(os.path.join(dir_path, "*_detailed_results.jsonl"))):
            fname = os.path.basename(f)

            if "_conservative_" in fname or "_strict_" in fname:
                continue

            # Check design prefix
            if not any(fname.startswith(p) for p in prefixes):
                continue

            # Check prompting
            # SA uses Sa-zero_ / Sa-few_ (no _shot suffix)
            # NA/DA/MA use zero_shot / few_shot
            if design == "SA":
                if prompting == "zero-shot" and "Sa-zero" not in fname:
                    continue
                if prompting == "few-shot" and "Sa-few" not in fname:
                    continue
            else:
                if shot not in fname:
                    continue

            # Check model (any substring match)
            if not any(ms in fname for ms in model_substrings):
                continue

            # Check mode
            # For Qwen: model name already encodes mode (Instruct vs Thinking)
            # For Nemotron: mode is in _thinking_ suffix or _instruct_ suffix
            if "Nemotron" in model_name:
                is_thinking_file = "_thinking_" in fname
                if mode == "thinking" and not is_thinking_file:
                    continue
                if mode == "instruct" and is_thinking_file:
                    continue
            # For Qwen, model name already matches the right mode

            files.append(f)

    return files


SUBMITTED_COMMIT = "c829127"  # pre-P0 pairwise_correct_all_configs.csv = as-submitted P-C


def load_submitted_pairwise():
    """Submitted (pre-P0) P-C rows from git, tagged freeform/original_submitted."""
    import subprocess
    import io
    try:
        blob = subprocess.run(
            ["git", "show", f"{SUBMITTED_COMMIT}:results/rq3_baseline/pairwise_correct_all_configs.csv"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except Exception as e:  # noqa: BLE001
        print(f"  WARN: could not load submitted P-C from git {SUBMITTED_COMMIT}: {e}")
        return None
    sub = pd.read_csv(io.StringIO(blob))
    sub["variant"] = "freeform"
    sub["label_rule"] = "original_submitted"
    return sub


def main():
    # Load consolidated performance to get all configs
    perf_path = os.path.join(PROJECT_ROOT, "results", "consolidated_performance.csv")
    perf = pd.read_csv(perf_path)
    v870 = perf[perf["dataset"] == "VulTrial-870"].copy()
    # consolidated now holds multiple variant rows per config (submitted + corrected);
    # P-C is computed once per config from the current JSONLs, so dedupe the config list.
    v870 = v870.drop_duplicates(subset=["design", "model", "mode", "prompting"])

    print(f"VulTrial-870 configs: {len(v870)}")

    # Model name to filename pattern (partial match on JSONL filenames)
    model_patterns = {
        "Nemotron-Nano-8B": "Nemotron-Nano-8B",
        "Nemotron-Super-49B": "Nemotron-Super-49B",
        "Qwen3-4B-Instruct": "Qwen3-4B-Instruct",
        "Qwen3-4B-Thinking": "Qwen3-4B-Thinking",
        "Qwen3-30B-A3B-Instruct": "Qwen3-30B-A3B-Instruct",
        "Qwen3-30B-A3B-Thinking": "Qwen3-30B-A3B-Thinking",
    }
    # For Nemotron, filenames use nvidia-Llama prefix, not our short name
    # Override to match the actual filenames
    model_patterns["Nemotron-Nano-8B"] = "Nemotron-Nano-8B"
    model_patterns["Nemotron-Super-49B"] = "Nemotron-Super-49B"

    results = []
    for _, row in v870.iterrows():
        design = row["design"]
        model = row["model"]
        mode = row["mode"]
        prompting = row["prompting"]

        pattern = model_patterns.get(model, model)
        files = find_jsonl_files(design, pattern, mode, prompting)

        if not files:
            print(f"  WARNING: No files for {design} {model} {mode} {prompting}")
            results.append({
                "design": design, "model": model, "mode": mode,
                "prompting": prompting, "pc_pct": None,
                "variant": "freeform",
                "label_rule": "affirm_optionA" if design == "MA" else "canonical",
            })
            continue

        pc = compute_pc(files, model=model, mode=mode)
        results.append({
            "design": design, "model": model, "mode": mode,
            "prompting": prompting, "pairs": pc["pairs"],
            "pc_pct": pc["pc_pct"], "pv_pct": pc["pv_pct"],
            "pb_pct": pc["pb_pct"], "pr_pct": pc["pr_pct"],
            # Cataloging: these are the corrected free-form labels (patched JSONLs).
            "variant": "freeform",
            "label_rule": "affirm_optionA" if design == "MA" else "canonical",
        })

    df = pd.DataFrame(results)

    # Interleave submitted (pre-P0) P-C from git for provenance.
    sub = load_submitted_pairwise()
    if sub is not None and len(sub):
        df = pd.concat([sub, df], ignore_index=True)

    # Print RQ1 table (NA)
    print("\n" + "=" * 70)
    print("RQ1: Non-Agentic (NA) — P-C (%)")
    print("=" * 70)
    # Console tables use the corrected free-form rows only (submitted rows are in
    # the saved CSV for provenance but would confuse the pivot).
    dfc = df[df["label_rule"] != "original_submitted"]
    na = dfc[dfc["design"] == "NoAgent"].sort_values(["model", "mode", "prompting"])
    for _, r in na.iterrows():
        print(f"  {r['model']:30s} {r['mode']:10s} {r['prompting']:10s} "
              f"P-C={r['pc_pct']:5.1f}%  (pairs={r['pairs']})")

    # Print RQ2 table (SA/DA/MA)
    print("\n" + "=" * 70)
    print("RQ2: SA / DA / MA — P-C (%)")
    print("=" * 70)
    rq2 = dfc[dfc["design"].isin(["SA", "DA", "MA"])]
    pivot = rq2.pivot_table(values="pc_pct",
                            index=["model", "mode", "prompting"],
                            columns="design")[["SA", "DA", "MA"]]
    print(pivot.round(1).to_string())

    # Save full results
    out_path = os.path.join(PROJECT_ROOT, "results", "rq3_baseline",
                            "pairwise_correct_all_configs.csv")
    df.to_csv(out_path, index=False)
    print(f"\nFull results saved: {out_path}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: Mean P-C by Design")
    print("=" * 70)
    for design in ["NoAgent", "SA", "DA", "MA"]:
        sub = dfc[dfc["design"] == design]
        print(f"  {design:8s}: mean P-C = {sub['pc_pct'].mean():.1f}%")


if __name__ == "__main__":
    main()
