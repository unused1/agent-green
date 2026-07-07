#!/usr/bin/env python3
"""Aggregate the paired-386 Item 5 (budget-SA) and Item 9 (VulAgent-lite) runs.

For each config it computes detection metrics (accuracy, precision, recall, F1,
FPR, positive-prediction-rate, and Pairwise-Correct) plus cost (mean calls per
sample, energy in kWh and kg CO2). Pairwise-Correct (P-C) pairs the vulnerable
and benign members of each commit (pairing key = commit_id; the VulTrial-386 set
is 193 balanced commit pairs) and credits a pair only when both members are
predicted correctly. Rows flagged skipped (vuln == -1) are excluded from the
detection counts and mark their pair incomplete.

Output: results/paired386_item5_9_consolidated.csv (one row per config).
"""
import csv, glob, json, os, re
from collections import defaultdict

DIRS = {
    "budget":   "results/runpod_vuln_386paired_budget",
    "vulagent": "results/runpod_vuln_386paired_vulagent",
}
OUT = "results/paired386_item5_9_consolidated.csv"


def parse_config(fname):
    """Return (method, model, family, mode) from a detailed_results filename."""
    stem = fname.replace("_detailed_results.jsonl", "")
    mode = "thinking" if stem.endswith("_thinking") else "instruct"
    stem_nm = stem[:-9] if mode == "thinking" else stem  # strip trailing _thinking
    # method = prefix up to the model token
    if stem_nm.startswith("VulAgentLite"):
        method = "VulAgentLite"; rest = stem_nm[len("VulAgentLite") + 1:]
    else:
        m = re.match(r"(SA-budget-[a-z0-9]+)_(.*)", stem_nm)
        method, rest = m.group(1), m.group(2)
    family = "Qwen" if rest.startswith("Qwen") else ("Nemotron" if "nvidia" in rest or "Nemotron" in rest else "?")
    return method, rest, family, mode


def energy_for(cfg_dir, stem):
    """Sum energy_consumed (kWh) and emissions (kg) over the config emissions CSV."""
    ef = os.path.join(cfg_dir, "emissions", f"emissions_{stem}.csv")
    if not os.path.exists(ef):
        return None, None
    kwh = kg = 0.0
    for r in csv.DictReader(open(ef)):
        try:
            kwh += float(r.get("energy_consumed", 0) or 0)
            kg += float(r.get("emissions", 0) or 0)
        except ValueError:
            pass
    return round(kwh, 3), round(kg, 4)


def metrics(rows):
    live = [r for r in rows if not r.get("skipped") and r.get("vuln") in (0, 1)]
    tp = sum(1 for r in live if r["vuln"] == 1 and r["ground_truth"] == 1)
    tn = sum(1 for r in live if r["vuln"] == 0 and r["ground_truth"] == 0)
    fp = sum(1 for r in live if r["vuln"] == 1 and r["ground_truth"] == 0)
    fn = sum(1 for r in live if r["vuln"] == 0 and r["ground_truth"] == 1)
    n = len(live)
    acc = (tp + tn) / n if n else 0
    prec = tp / (tp + fp) if (tp + fp) else 0
    rec = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
    fpr = fp / (fp + tn) if (fp + tn) else 0
    ppr = (tp + fp) / n if n else 0  # positive-prediction rate
    # Pairwise-Correct by commit_id
    pairs = defaultdict(list)
    for r in rows:
        pairs[r["commit_id"]].append(r)
    npairs = len(pairs)
    correct = 0; incomplete = 0
    for members in pairs.values():
        if any(m.get("skipped") or m.get("vuln") not in (0, 1) for m in members):
            incomplete += 1; continue
        if all(m["vuln"] == m["ground_truth"] for m in members):
            correct += 1
    pc = correct / npairs if npairs else 0
    return dict(accuracy=round(acc, 4), precision=round(prec, 4), recall=round(rec, 4),
                f1_score=round(f1, 4), fpr=round(fpr, 4), ppr=round(ppr, 4),
                tp=tp, tn=tn, fp=fp, fn=fn, pc=round(pc, 4), n_pairs=npairs,
                pairs_correct=correct, pairs_incomplete=incomplete)


def main():
    out_rows = []
    for kind, d in DIRS.items():
        for f in sorted(glob.glob(os.path.join(d, "*_detailed_results.jsonl"))):
            fname = os.path.basename(f)
            stem = fname.replace("_detailed_results.jsonl", "")
            method, model, family, mode = parse_config(fname)
            rows = [json.loads(l) for l in open(f) if l.strip()]
            m = metrics(rows)
            live = [r for r in rows if not r.get("skipped") and r.get("vuln") in (0, 1)]
            mean_calls = round(sum(r.get("n_calls", 0) or 0 for r in live) / len(live), 2) if live else 0
            kwh, kg = energy_for(d, stem)
            out_rows.append(dict(
                item=("Item5" if kind == "budget" else "Item9"),
                method=method, model=model, model_family=family, mode=mode,
                thinking_enabled=(mode == "thinking"),
                **m,
                mean_calls=mean_calls, energy_kwh=kwh, energy_kgco2=kg,
                n_total=len(rows), n_skipped=sum(1 for r in rows if r.get("skipped")),
                source_file=fname,
            ))
    cols = ["item", "method", "model", "model_family", "mode", "thinking_enabled",
            "accuracy", "precision", "recall", "f1_score", "fpr", "ppr", "pc",
            "tp", "tn", "fp", "fn", "n_pairs", "pairs_correct", "pairs_incomplete",
            "mean_calls", "energy_kwh", "energy_kgco2", "n_total", "n_skipped", "source_file"]
    with open(OUT, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=cols); w.writeheader()
        for r in out_rows: w.writerow(r)
    print(f"wrote {OUT}: {len(out_rows)} configs\n")
    # readable summary
    hdr = f'{"item":6}{"method":18}{"family":10}{"mode":9}{"F1":>6}{"P-C":>7}{"FPR":>6}{"PPR":>6}{"calls":>7}{"kWh":>8}'
    print(hdr); print("-" * len(hdr))
    for r in sorted(out_rows, key=lambda x: (x["item"], x["method"], x["model_family"], x["mode"])):
        print(f'{r["item"]:6}{r["method"]:18}{r["model_family"]:10}{r["mode"]:9}'
              f'{r["f1_score"]:6.3f}{r["pc"]:7.3f}{r["fpr"]:6.3f}{r["ppr"]:6.3f}'
              f'{r["mean_calls"]:7.1f}{(r["energy_kwh"] or 0):8.1f}')


if __name__ == "__main__":
    main()
