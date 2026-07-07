#!/usr/bin/env python3
"""Combine submitted SA/DA/MA(+NoAgent) 870 baselines with the paired-386
Item 5 (budget-SA) and Item 9 (VulAgent-lite) runs into one discussion table,
showing the SUBMITTED vs CORRECTED parse side by side for the baselines.

Baseline detection metrics (corrected) and Pairwise-Correct are recomputed from
the raw detailed_results (the catalogue's source_file, which for the 870 set is
the VulTrial-486 and VulTrial-384-incremental files merged) so F1 and P-C come
from the same predictions. Alongside, `f1_submitted` / `fp_submitted` are the
as-submitted values pulled from consolidated_performance.csv (label_rule
`original_submitted`), and `f1_delta` = corrected - submitted. `corrected_parse`
names the corrected parse (canonical for SA/DA/NoAgent; Option A for MA freeform;
Option B for MA constrained). Item 5/9 are new (no submitted counterpart).

P-C on the 870 set is over clean balanced commit pairs (commit_id groups of size
2, one vulnerable + one benign). Baseline mean_calls is design nominal
(NoAgent/SA=1, DA=2, MA=4); Item 5/9 mean_calls are measured. Energy is
per-sample (Wh/sample) since the two sample sizes differ (868 vs 386).

Output: results/paired386_vs_870baseline_meeting.csv
"""
import csv, json, os
from collections import defaultdict
csv.field_size_limit(2**27)

PERF = "results/consolidated_performance.csv"
EM = "results/consolidated_emissions.csv"
P386 = "results/paired386_item5_9_consolidated.csv"
E386 = "results/paired386_item5_9_emissions.csv"
OUT = "results/paired386_vs_870baseline_meeting.csv"

TARGET = {"Nemotron-Super-49B", "Nemotron-Nano-8B",
          "Qwen3-30B-A3B-Instruct", "Qwen3-30B-A3B-Thinking",
          "Qwen3-4B-Instruct", "Qwen3-4B-Thinking"}
# (design, variant, corrected_label_rule, display, nominal_calls, corrected_parse_tag)
SLICES = [
    ("NoAgent", "freeform", "canonical", "NoAgent", 1, "canonical"),
    ("SA", "freeform", "canonical", "SA", 1, "canonical"),
    ("DA", "freeform", "canonical", "DA", 2, "canonical"),
    ("MA", "freeform", "affirm_optionA", "MA-A(freeform)", 4, "optionA"),
    ("MA", "constrained", "constrained_strict_optionB", "MA-B(constrained)", 4, "optionB"),
]


def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def load_raw(source_file):
    recs = {}
    for p in source_file.split(";"):
        p = p.strip()
        if p and os.path.exists(p):
            for line in open(p):
                if line.strip():
                    r = json.loads(line)
                    recs[str(r["idx"])] = r
    return list(recs.values())


def _gt(r):
    v = r.get("ground_truth", r.get("target"))
    return int(v) if v is not None else None


def raw_metrics(recs):
    live = [r for r in recs if r.get("vuln") in (0, 1) and not r.get("skipped")]
    tp = sum(1 for r in live if r["vuln"] == 1 and _gt(r) == 1)
    tn = sum(1 for r in live if r["vuln"] == 0 and _gt(r) == 0)
    fp = sum(1 for r in live if r["vuln"] == 1 and _gt(r) == 0)
    fn = sum(1 for r in live if r["vuln"] == 0 and _gt(r) == 1)
    n = len(live)
    prec = tp / (tp + fp) if (tp + fp) else 0
    rec = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
    fpr = fp / (fp + tn) if (fp + tn) else None
    ppr = (tp + fp) / n if n else None
    groups = defaultdict(list)
    for r in recs:
        groups[r["commit_id"]].append(r)
    clean = [m for m in groups.values() if len(m) == 2 and {_gt(m[0]), _gt(m[1])} == {0, 1}]
    correct = sum(1 for m in clean
                  if all((not x.get("skipped")) and x.get("vuln") in (0, 1)
                         and x["vuln"] == _gt(x) for x in m))
    pc = correct / len(clean) if clean else None
    return dict(f1=round(f1, 3), precision=round(prec, 3), recall=round(rec, 3),
                fpr=round(fpr, 3) if fpr is not None else "",
                ppr=round(ppr, 3) if ppr is not None else "",
                pc=round(pc, 3) if pc is not None else "", fp=fp,
                n_total=len(recs), n_pairs=len(clean),
                skipped=sum(1 for r in recs if r.get("skipped") or r.get("vuln") not in (0, 1)))


def main():
    perf = [r for r in csv.DictReader(open(PERF)) if r["dataset"] == "VulTrial-870"]
    # index by full key for corrected + submitted lookup
    by_key = {}
    for r in perf:
        by_key[(r["design"], r["variant"], r["model"], r["mode"], r["prompting"], r["label_rule"])] = r
    en = {}
    for r in csv.DictReader(open(EM)):
        if r["dataset"] == "VulTrial-870":
            en[(r["design"], r["variant"], r["model"], r["mode"], r["prompting"])] = r

    # paired-386 idx set, to subset baselines onto the same samples as Item 5/9
    paired386 = {str(json.loads(l)["idx"]) for l in open("vuln_database/VulTrial_386_paired.jsonl") if l.strip()}

    out = []
    cover_warn = set()
    for design, variant, corr_lr, disp, ncalls, parse_tag in SLICES:
        for model in TARGET:
            for mode in ("instruct", "thinking"):
                corr = by_key.get((design, variant, model, mode, "zero-shot", corr_lr))
                if not corr:  # fall back through the parse priority
                    for lr in ("canonical", "affirm_optionA", "constrained_strict_optionB", "original_submitted"):
                        corr = by_key.get((design, variant, model, mode, "zero-shot", lr))
                        if corr:
                            break
                if not corr:
                    continue
                sub = by_key.get((design, variant, model, mode, "zero-shot", "original_submitted"))
                recs = load_raw(corr["source_file"])
                f1_sub = round(f(sub["f1_score"]), 3) if sub else ""
                fp_sub = sub["false_positives"] if sub else ""
                ek = en.get((design, variant, model, mode, "zero-shot"))
                kwh = f(ek["total_energy_kwh"]) if ek else None
                kg = f(ek["total_emissions_kg"]) if ek else None
                gpuW = f(ek["avg_gpu_power_w"]) if ek else None
                hrs = f(ek["duration_hours"]) if ek else None
                nsess = ek["num_sessions"] if ek else ""
                # per-sample energy is intrinsic to (model, design) -> reused for the 386 subset
                wh_ps = (kwh * 1000 / len(recs)) if (kwh is not None and recs) else None
                wh_pc = (wh_ps / ncalls) if (wh_ps is not None and ncalls) else None

                # --- full 870 row (with submitted-vs-corrected) ---
                m = raw_metrics(recs)
                out.append(dict(
                    block="baseline-870", design=disp, model=model,
                    model_family=corr["model_family"], mode=mode, prompting="zero-shot",
                    sample_set="VulTrial-870", n_total=m["n_total"], n_pairs=m["n_pairs"],
                    f1_submitted=f1_sub, f1=m["f1"],
                    f1_delta=round(m["f1"] - f1_sub, 3) if f1_sub != "" else "",
                    corrected_parse=parse_tag, precision=m["precision"], recall=m["recall"],
                    fpr=m["fpr"], ppr=m["ppr"], pc=m["pc"],
                    fp_submitted=fp_sub, fp=m["fp"], mean_calls=ncalls,
                    total_energy_kwh=round(kwh, 2) if kwh is not None else "",
                    total_energy_kgco2=round(kg, 3) if kg is not None else "",
                    wh_per_sample=round(wh_ps, 1) if wh_ps is not None else "",
                    wh_per_call=round(wh_pc, 2) if wh_pc is not None else "",
                    avg_gpu_power_w=round(gpuW) if gpuW is not None else "",
                    duration_hours=round(hrs, 1) if hrs is not None else "",
                    num_sessions=nsess, skipped=m["skipped"]))

                # --- 386-matched row (same commits as Item 5/9; corrected parse only) ---
                sub386 = [r for r in recs if str(r["idx"]) in paired386]
                got = {str(r["idx"]) for r in sub386}
                if len(got) < len(paired386):
                    cover_warn.add(f"{disp} {model} {mode}: {len(got)}/{len(paired386)} paired idx present")
                m6 = raw_metrics(sub386)
                out.append(dict(
                    block="baseline-386", design=disp, model=model,
                    model_family=corr["model_family"], mode=mode, prompting="zero-shot",
                    sample_set="VulTrial-386-paired", n_total=m6["n_total"], n_pairs=m6["n_pairs"],
                    f1_submitted="", f1=m6["f1"], f1_delta="", corrected_parse=parse_tag,
                    precision=m6["precision"], recall=m6["recall"], fpr=m6["fpr"], ppr=m6["ppr"],
                    pc=m6["pc"], fp_submitted="", fp=m6["fp"], mean_calls=ncalls,
                    total_energy_kwh="",  # subset of the 870 run; see the baseline-870 row
                    total_energy_kgco2="",
                    wh_per_sample=round(wh_ps, 1) if wh_ps is not None else "",  # intrinsic per-sample
                    wh_per_call=round(wh_pc, 2) if wh_pc is not None else "",
                    avg_gpu_power_w=round(gpuW) if gpuW is not None else "",  # from the parent 870 run
                    duration_hours=round(hrs, 1) if hrs is not None else "",
                    num_sessions=nsess, skipped=m6["skipped"]))
    if cover_warn:
        print("-- paired-386 coverage notes --")
        for w in sorted(cover_warn):
            print("  ", w)

    # Item 5/9
    e386 = {(r["variant"], r["model"], r["mode"]): r for r in csv.DictReader(open(E386))}
    for r in csv.DictReader(open(P386)):
        model = ("Nemotron-Super-49B" if r["model_family"] == "Nemotron"
                 else "Qwen3-30B-A3B-" + ("Thinking" if r["mode"] == "thinking" else "Instruct"))
        evar = "vulagent-lite" if r["method"] == "VulAgentLite" else r["method"].replace("SA-budget-", "budget-")
        ek = e386.get((evar, model, r["mode"]))
        kwh = f(ek["total_energy_kwh"]) if ek else None
        kg = f(ek["total_emissions_kg"]) if ek else None
        gpuW = f(ek["avg_gpu_power_w"]) if ek else None
        hrs = f(ek["duration_hours"]) if ek else None
        nsess = ek["num_sessions"] if ek else ""
        n = int(f(r["n_total"]))
        mc = f(r["mean_calls"]) or 0
        wh_ps = (kwh * 1000 / n) if (kwh is not None and n) else None
        wh_pc = (wh_ps / mc) if (wh_ps is not None and mc) else None
        out.append(dict(
            block=r["item"], design=evar, model=model, model_family=r["model_family"],
            mode=r["mode"], prompting="zero-shot", sample_set="VulTrial-386-paired",
            n_total=n, n_pairs=int(f(r["n_pairs"])),
            f1_submitted="", f1=round(f(r["f1_score"]), 3), f1_delta="", corrected_parse="paired386(new)",
            precision=round(f(r["precision"]), 3), recall=round(f(r["recall"]), 3),
            fpr=round(f(r["fpr"]), 3), ppr=round(f(r["ppr"]), 3), pc=round(f(r["pc"]), 3),
            fp_submitted="", fp=int(f(r["fp"])), mean_calls=r["mean_calls"],
            total_energy_kwh=round(kwh, 2) if kwh is not None else "",
            total_energy_kgco2=round(kg, 3) if kg is not None else "",
            wh_per_sample=round(wh_ps, 1) if wh_ps is not None else "",
            wh_per_call=round(wh_pc, 2) if wh_pc is not None else "",
            avg_gpu_power_w=round(gpuW) if gpuW is not None else "",
            duration_hours=round(hrs, 1) if hrs is not None else "",
            num_sessions=nsess, skipped=r.get("n_skipped", "")))

    cols = ["block", "design", "model", "model_family", "mode", "prompting", "sample_set",
            "n_total", "n_pairs", "f1_submitted", "f1", "f1_delta", "corrected_parse",
            "precision", "recall", "fpr", "ppr", "pc", "fp_submitted", "fp",
            "mean_calls", "total_energy_kwh", "total_energy_kgco2", "wh_per_sample",
            "wh_per_call", "avg_gpu_power_w", "duration_hours", "num_sessions", "skipped"]
    with open(OUT, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=cols); w.writeheader()
        for r in out:
            w.writerow(r)
    print(f"wrote {OUT}: {len(out)} rows\n")

    order = {"baseline-870": 0, "baseline-386": 1, "Item5": 2, "Item9": 3}
    out.sort(key=lambda x: (order[x["block"]], x["design"], x["model_family"], x["model"], x["mode"]))
    hdr = f'{"block":14}{"design":18}{"model":24}{"mode":9}{"F1sub":>7}{"F1cor":>7}{"P-C":>6}{"smp":>6}'
    print(hdr); print("-" * len(hdr))
    last = None
    for r in out:
        if r["block"] != last:
            print(); last = r["block"]
        fs = f'{r["f1_submitted"]:.3f}' if r["f1_submitted"] != "" else "   -  "
        pc = f'{r["pc"]:.3f}' if r["pc"] not in ("", None) else "  -  "
        smp = "386" if "386" in r["sample_set"] else "870"
        print(f'{r["block"]:14}{r["design"]:18}{r["model"]:24}{r["mode"]:9}{fs:>7}{r["f1"]:7.3f}{pc:>6}{smp:>6}')


if __name__ == "__main__":
    main()
