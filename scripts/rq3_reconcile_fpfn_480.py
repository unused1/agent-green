#!/usr/bin/env python3
"""Reconcile the 480-row FP/FN frame so the human-rated paired-120 nests inside it.

The paired-120 human frame (`fpfn_human_frame_120.csv`, Nemotron-only, 15
snippets/stratum) and the 480 frame (`fpfn_sample_frame.csv`, Nemotron+Qwen, 30
snippets/stratum) were sampled independently and were later patched only on the
120 side, so the 120 was NOT a subset of the 480. This rebuilds the 480's
Nemotron half so each stratum's 30 snippets force-include the 120's 15 (using the
120's human-rated content), topped up with the existing 480 snippets. The Qwen
half is untouched. Net effect: N stays 480 and the paired-120 is a clean subset
by (entry_id, mode), enabling human-vs-LLM inter-rater agreement.

Outputs (old versions backed up to *_preA.*):
  results/rq3_baseline/fpfn_sample_frame.csv   (reconciled, LLM-judge input + key)
  results/rq3_baseline/fpfn_rater_sheet.xlsx   (reconciled blank human sheet)
"""
import csv, os, shutil, sys
from collections import defaultdict

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "results", "rq3_baseline")
csv.field_size_limit(sys.maxsize)

FRAME480 = os.path.join(BASE, "fpfn_sample_frame.csv")
FRAME120 = os.path.join(BASE, "fpfn_human_frame_120.csv")
RATER_XLSX = os.path.join(BASE, "fpfn_rater_sheet.xlsx")
STRATA = ["TP", "TN", "FP", "FN"]
FRAME_COLS = ["sample_id", "family", "model", "mode", "stratum", "entry_id",
              "snippet_pair_id", "ground_truth", "prediction", "ground_truth_label",
              "cwe", "cve_desc", "source_code", "response_text"]


def is_nemo(r):
    return "Nemotron" in r["model"]


def frame120_to_480row(r):
    """Map a fpfn_human_frame_120 row to the 480-frame schema."""
    return {
        "family": r["family"], "model": r["model"], "mode": r["mode"],
        "stratum": r["stratum"], "entry_id": r["entry_id"],
        "snippet_pair_id": f"{r['model']}:{r['stratum']}:{r['entry_id']}",
        "ground_truth": r["ground_truth"], "prediction": r["prediction"],
        "ground_truth_label": r["ground_truth_label"], "cwe": r["cwe"],
        "cve_desc": r["cve_desc"], "source_code": r["source_code"],
        "response_text": r["response_text"],
    }


def main():
    f480 = list(csv.DictReader(open(FRAME480)))
    f120 = list(csv.DictReader(open(FRAME120)))

    nemo480 = [r for r in f480 if is_nemo(r)]
    qwen480 = [r for r in f480 if not is_nemo(r)]

    # index by (stratum, entry_id) -> {mode: row}
    def by_snip(rows):
        d = defaultdict(dict)
        for r in rows:
            d[(r["stratum"], r["entry_id"])][r["mode"]] = r
        return d

    snip120 = by_snip(f120)
    snip480n = by_snip(nemo480)

    new_nemo = []
    report = []
    for stratum in STRATA:
        mand = sorted({e for (s, e) in snip120 if s == stratum})  # 120's 15 snippets
        exist = sorted({e for (s, e) in snip480n if s == stratum})  # 480's 30
        topup_pool = [e for e in exist if e not in set(mand)]
        need = 30 - len(mand)
        topup = topup_pool[:need]
        final = list(mand) + topup
        assert len(final) == 30, f"{stratum}: got {len(final)} snippets"
        dropped = [e for e in exist if e not in set(final)]
        added = [e for e in mand if e not in set(exist)]
        report.append((stratum, len(mand), len(set(mand) & set(exist)), len(added), len(dropped)))

        for e in final:
            src = "120" if e in set(mand) else "480"
            for mode in ("thinking", "instruct"):
                if src == "120":
                    row = frame120_to_480row(snip120[(stratum, e)][mode])
                else:
                    row = {k: snip480n[(stratum, e)][mode].get(k, "") for k in FRAME_COLS if k != "sample_id"}
                new_nemo.append(row)

    combined = new_nemo + [{k: r.get(k, "") for k in FRAME_COLS if k != "sample_id"} for r in qwen480]
    for i, r in enumerate(combined, 1):
        r["sample_id"] = i

    # --- backups ---
    shutil.copyfile(FRAME480, FRAME480.replace(".csv", "_preA.csv"))
    if os.path.exists(RATER_XLSX):
        shutil.copyfile(RATER_XLSX, RATER_XLSX.replace(".xlsx", "_preA.xlsx"))

    # --- write reconciled frame ---
    with open(FRAME480, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FRAME_COLS)
        w.writeheader()
        for r in combined:
            w.writerow({k: r.get(k, "") for k in FRAME_COLS})

    # --- regenerate blank rater sheet (same schema as before) ---
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "FP-FN rater sheet"
    cols = ["sample_id", "source_code", "ground_truth_label", "cwe", "cve_desc",
            "response_text", "parsed_label (TEMP)", "completeness_score",
            "clarity_score", "actionability_score", "informativeness_score", "rater_notes"]
    ws.append(cols)
    for r in combined:
        parsed = "vulnerable" if str(r["prediction"]) == "1" else "safe"
        ws.append([r["sample_id"], r["source_code"], r["ground_truth_label"], r["cwe"],
                   r["cve_desc"], r["response_text"], parsed, "", "", "", "", ""])
    wb.save(RATER_XLSX)

    # --- verify nesting ---
    new480 = list(csv.DictReader(open(FRAME480)))
    k480 = {(r["entry_id"], r["mode"]) for r in new480}
    k120 = {(r["entry_id"], r["mode"]) for r in f120}
    subset = k120 <= k480
    # content check on the 120
    b480 = {(r["entry_id"], r["mode"]): r for r in new480}
    def nz(x): return " ".join(str(x or "").split())
    content_ok = all(nz(b480[(r["entry_id"], r["mode"])]["response_text"])[:1500]
                     == nz(r["response_text"])[:1500] for r in f120)

    print("=== reconciliation report (per stratum: mand, overlap, added, dropped) ===")
    for s, m, ov, ad, dr in report:
        print(f"  {s}: mandatory={m} overlap_with_480={ov} added={ad} dropped_from_480={dr}")
    print(f"\nnew frame rows: {len(new480)} (Nemotron {len(new_nemo)} + Qwen {len(qwen480)})")
    print(f"paired-120 is a subset by (entry_id,mode): {subset}")
    print(f"120 content matches reconciled frame: {content_ok}")
    print(f"backups: fpfn_sample_frame_preA.csv, fpfn_rater_sheet_preA.xlsx")


if __name__ == "__main__":
    main()
