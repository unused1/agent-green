#!/usr/bin/env python3
"""Add the paired-386 Item 5/9 configs to the master catalogue so everything is in
one place. Detection metrics -> results/consolidated_performance.csv; energy ->
results/consolidated_emissions.csv. Idempotent: any prior VulTrial-386-paired rows
are removed and re-added. Pairwise-Correct/PPR/FPR are not in the master schema —
they remain in results/paired386_item5_9_consolidated.csv (the sidecar)."""
import csv, os
csv.field_size_limit(2**27)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "results")
PERF = os.path.join(R, "consolidated_performance.csv")
EM = os.path.join(R, "consolidated_emissions.csv")
P386 = os.path.join(R, "paired386_item5_9_consolidated.csv")
E386 = os.path.join(R, "paired386_item5_9_emissions.csv")
DS = "VulTrial-386-paired"


def model_name(family, mode):
    if family == "Nemotron":
        return "Nemotron-Super-49B", "49"
    return "Qwen3-30B-A3B-" + ("Thinking" if mode == "thinking" else "Instruct"), "30"


def main():
    perf = list(csv.DictReader(open(PERF)))
    perf_cols = perf[0].keys()
    perf = [r for r in perf if r["dataset"] != DS]  # idempotent

    new = []
    for r in csv.DictReader(open(P386)):
        model, pb = model_name(r["model_family"], r["mode"])
        design = "SA" if r["method"].startswith("SA-budget") else "MA"
        variant = r["method"].replace("SA-budget-", "budget-") if design == "SA" else "vulagent-lite"
        tp, tn, fp, fn = int(float(r["tp"])), int(float(r["tn"])), int(float(r["fp"])), int(float(r["fn"]))
        row = {c: "" for c in perf_cols}
        row.update(model=model, model_family=r["model_family"], parameters_b=pb,
                   design=design, task="vulnerability_detection", dataset=DS,
                   mode=r["mode"], prompting="zero-shot", thinking_enabled=r["thinking_enabled"],
                   accuracy=r["accuracy"], precision=r["precision"], recall=r["recall"],
                   f1_score=r["f1_score"], true_positives=tp, true_negatives=tn,
                   false_positives=fp, false_negatives=fn, total_samples=r["n_total"],
                   correct_predictions=tp + tn, skipped_samples=r["n_skipped"],
                   source_type="runpod_vuln_386paired", source_file=r["source_file"],
                   variant=variant, label_rule="paired386")
        new.append(row)
    with open(PERF, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(perf_cols)); w.writeheader()
        w.writerows(perf); w.writerows(new)
    print(f"consolidated_performance.csv: +{len(new)} paired-386 rows -> {len(perf) + len(new)} total")

    # emissions: paired386_emissions already matches the master emissions schema
    em = list(csv.DictReader(open(EM)))
    em_cols = list(em[0].keys())
    em = [r for r in em if r["dataset"] != DS]
    e_new = []
    for r in csv.DictReader(open(E386)):
        model, pb = model_name(r["model_family"], r["mode"])
        design = "SA" if r["variant"].startswith("budget") else "MA"
        row = {c: r.get(c, "") for c in em_cols}
        row.update(model=model, parameters_b=pb, design=design)
        e_new.append(row)
    with open(EM, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=em_cols); w.writeheader()
        w.writerows(em); w.writerows(e_new)
    print(f"consolidated_emissions.csv: +{len(e_new)} paired-386 rows -> {len(em) + len(e_new)} total")


if __name__ == "__main__":
    main()
