"""Build the paired 120-explanation human-rating frame for RQ3 (revision, Item 8).

Design (extends the EMSE pilot to all four strata, per RA4/RB5/RC4):
  - Nemotron-Super-49B (strongest model in RQ1), SA zero-shot.
  - Paired thinking<->instruct on the SAME snippet (the core RQ3 unit + paired
    Wilcoxon), so each snippet contributes 2 rows.
  - 15 snippets per stratum x {TP,TN,FP,FN} x 2 modes = 120 explanations (60 snippets).
  - Correct-case strata (TP/TN) prefer the 15 snippets already rated in the prior
    3-annotator study (super49b_zero_rater_sheet.csv), which are verified still
    correctly classified and whose responses match the current run exactly -> their
    ratings are reused; only the remaining 45 snippets (90 explanations) are new.

Output: results/rq3_baseline/fpfn_human_frame_120.csv  (master key + LLM-judge input)
"""

import csv, json, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from vuln_parser import strip_think_block  # noqa: E402
from sa_noresp_overlay import load_overlay_full  # noqa: E402
csv.field_size_limit(sys.maxsize)

MODEL = "Nemotron-Super-49B"
SEED = 42
PER_STRATUM = 15  # snippets per stratum (x2 modes = 30 explanations/stratum)
STRATA = {"TP": (1, 1), "TN": (0, 0), "FP": (0, 1), "FN": (1, 0)}  # (gt, pred)
OUT = os.path.join(ROOT, "results/rq3_baseline/fpfn_human_frame_120.csv")
PRIOR = os.path.join(ROOT, "results/rq3_baseline/super49b_zero_rater_sheet.csv")
DS = os.path.join(ROOT, "vuln_database/VulTrial_870_samples_balanced.jsonl")
import glob


def load_ds():
    func, gt, meta = {}, {}, {}
    for line in open(DS):
        if line.strip():
            r = json.loads(line); i = int(r["idx"])
            func[r.get("func", "").strip()] = i
            gt[i] = int(r.get("ground_truth", r.get("target", -1)))
            meta[i] = r
    return func, gt, meta


def load_sa(mode, overlay):
    """{idx: (pred, response)} for SA-zero Super-49B, corrected + overlaid."""
    out = {}
    for d in ["runpod_vuln_486", "runpod_vuln_384_incremental"]:
        for f in glob.glob(os.path.join(ROOT, f"results/{d}/Sa-zero_nvidia-Llama-3_3-Nemotron-Super-49B*detailed_results.jsonl")):
            is_think = "_thinking_" in os.path.basename(f)
            if (mode == "thinking") != is_think:
                continue
            for line in open(f):
                if not line.strip():
                    continue
                rec = json.loads(line); i = int(rec["idx"])
                ov = overlay.get((MODEL, mode, i))
                if ov is not None:
                    out[i] = (ov[0], ov[1])
                else:
                    try:
                        v = int(rec["vuln"])
                    except (TypeError, ValueError, KeyError):
                        continue
                    out[i] = (v, strip_think_block(rec.get("reasoning", "") or ""))
    return out


def main():
    func, gt, meta = load_ds()
    overlay = load_overlay_full()
    inst, think = load_sa("instruct", overlay), load_sa("thinking", overlay)

    # prior human-rated idx (still-valid correct cases)
    prior_idx = set()
    for r in csv.DictReader(open(PRIOR)):
        i = func.get(r["source_code"].strip())
        if i is not None:
            prior_idx.add(i)

    # intersection pools (both modes present + agree) per stratum
    common = set(inst) & set(think)
    rng = random.Random(SEED)
    rows = []
    print(f"prior idx: {len(prior_idx)}")
    for st, (g, p) in STRATA.items():
        pool = [i for i in common
                if gt.get(i) == g and inst[i][0] == p and think[i][0] == p]
        pool.sort(); rng.shuffle(pool)
        pref = [i for i in pool if i in prior_idx]
        rest = [i for i in pool if i not in prior_idx]
        take = (pref + rest)[:PER_STRATUM]
        reused = sum(1 for i in take if i in prior_idx)
        print(f"  {st}: pool={len(pool)} take={len(take)} reused_prior={reused} new={len(take)-reused}")
        for i in take:
            for mode, src in (("thinking", think), ("instruct", inst)):
                rows.append({
                    "family": MODEL, "model": MODEL, "mode": mode, "stratum": st,
                    "entry_id": i, "ground_truth": g, "prediction": p,
                    "ground_truth_label": "vulnerable" if g == 1 else "safe",
                    "reused_prior": int(i in prior_idx),
                    "cwe": str(meta[i].get("cwe", "")), "cve_desc": str(meta[i].get("cve_desc", "")),
                    "source_code": meta[i].get("func", ""),
                    "response_text": strip_think_block(src[i][1]),
                })
    # global shuffle + sample_id (so a snippet's 2 modes aren't adjacent)
    rng2 = random.Random(SEED); rng2.shuffle(rows)
    for sid, r in enumerate(rows, 1):
        r["sample_id"] = sid
    fields = ["sample_id", "family", "model", "mode", "stratum", "entry_id",
              "ground_truth", "prediction", "ground_truth_label", "reused_prior",
              "cwe", "cve_desc", "source_code", "response_text"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    reused = sum(r["reused_prior"] for r in rows)
    print(f"\nWrote {OUT}: {len(rows)} rows ({reused} reused / {len(rows)-reused} new to rate)")


if __name__ == "__main__":
    main()
