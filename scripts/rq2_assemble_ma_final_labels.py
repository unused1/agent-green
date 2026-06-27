"""Assemble final adjudicated MA labels and recompute RQ2 metrics (P0, MA).

Final MA label per entry:
  - cls == agree1  -> 1 (both keyword parsers agreed VULNERABLE; validated at
    100% judge agreement on the 80-case sample, so trusted without re-judging).
  - otherwise      -> the LLM judge verdict from rq2_ma_disagreement_judged.csv.

Outputs:
  results/rq3_baseline/ma_final_labels.csv  (per-entry sidecar)
  prints MA F1 (pooled) and P-C win-counts under stored / canonical / final.
"""

import ast
import csv
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from vuln_parser import classify  # noqa: E402

csv.field_size_limit(sys.maxsize)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSOLIDATED = os.path.join(ROOT, "results", "consolidated_performance.csv")
JUDGED = os.path.join(ROOT, "results", "rq3_baseline", "rq2_ma_disagreement_judged.csv")
OUT = os.path.join(ROOT, "results", "rq3_baseline", "ma_final_labels.csv")


def as_dict(v):
    if isinstance(v, dict):
        return v
    if isinstance(v, str) and v.strip():
        for ld in (json.loads, ast.literal_eval):
            try:
                o = ld(v)
                if isinstance(o, dict):
                    return o
            except (ValueError, SyntaxError, TypeError):
                pass
    return {}


def ma_board(rec):
    fd = as_dict(rec.get("full_discussion"))
    return str(fd.get("review_board") or fd.get("board") or rec.get("reasoning", ""))


def load_judge_map():
    m = {}
    with open(JUDGED) as f:
        for r in csv.DictReader(f):
            m[(r["model"], r["mode"], r["prompting"], int(r["idx"]))] = int(r["judge"])
    return m


def f1_from(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0
    r = tp / (tp + fn) if tp + fn else 0
    return 2 * p * r / (p + r) if p + r else 0


def main():
    judge = load_judge_map()
    configs = [r for r in csv.DictReader(open(CONSOLIDATED)) if r["dataset"] == "VulTrial-870"]
    ma_cfgs = [c for c in configs if c["design"] == "MA"]

    out_rows = []
    miss = 0
    # per-config confusion for stored/canon/final + per-config P-C
    for cfg in ma_cfgs:
        seen = set()
        for path in [p.strip() for p in cfg["source_file"].split(";") if p.strip()]:
            for line in open(path):
                if not line.strip():
                    continue
                rec = json.loads(line)
                idx = rec.get("idx")
                if idx is None or int(idx) in seen:
                    continue
                seen.add(int(idx))
                idx = int(idx)
                gt = int(rec.get("ground_truth", rec.get("target", -1)))
                stored = rec.get("vuln")
                try:
                    stored = int(stored)
                except (TypeError, ValueError):
                    stored = 0
                if stored == -1:
                    stored = 1
                canon, det = classify("MA", ma_board(rec))
                cls = "disagree" if canon != stored else ("agree1" if canon == 1
                       else ("agree0_det" if det else "agree0_undet"))
                if cls == "agree1":
                    final = 1
                    src = "trusted_agree1"
                else:
                    key = (cfg["model"], cfg["mode"], cfg["prompting"], idx)
                    if key in judge:
                        final = judge[key]
                        src = "judge"
                    else:
                        final = canon  # fallback (shouldn't happen)
                        src = "fallback_canon"
                        miss += 1
                out_rows.append({
                    "model": cfg["model"], "mode": cfg["mode"], "prompting": cfg["prompting"],
                    "idx": idx, "ground_truth": gt, "stored": stored, "canon": canon,
                    "cls": cls, "final": final, "source": src})

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "mode", "prompting", "idx",
                                          "ground_truth", "stored", "canon", "cls", "final", "source"])
        w.writeheader()
        w.writerows(out_rows)
    print(f"Wrote {OUT} ({len(out_rows)} MA entries; judge-missing fallbacks={miss})")

    # --- MA F1 (pooled) + PPR under each label set ---
    print("\nMA pooled metrics (GT balanced ~50/50):")
    for lab in ("stored", "canon", "final"):
        tp = fp = fn = pos = 0
        for r in out_rows:
            gt = r["ground_truth"]; pred = r[lab]
            if pred == 1 and gt == 1: tp += 1
            elif pred == 1 and gt == 0: fp += 1
            elif pred == 0 and gt == 1: fn += 1
            pos += (pred == 1)
        print(f"  {lab:6s}  F1={f1_from(tp,fp,fn):.3f}  PPR={pos/len(out_rows):.3f}")

    # --- P-C win-counts across SA/DA/MA (16 settings) under stored vs final ---
    # SA/DA labels: stored (clean). MA: stored vs final.
    def pc_for(records, label_key):
        pairs = defaultdict(lambda: {"gt": [], "pred": []})
        for r in records:
            pairs[r["_cid"]]["gt"].append(r["ground_truth"])
            pairs[r["_cid"]]["pred"].append(r[label_key])
        pc = tot = 0
        for cid, d in pairs.items():
            i = 0
            while i + 1 < len(d["gt"]):
                tot += 1
                if d["gt"][i] == d["pred"][i] and d["gt"][i+1] == d["pred"][i+1]:
                    pc += 1
                i += 2
        return (pc / tot * 100) if tot else 0

    # need commit_id for pairing -> reload MA with cid; and SA/DA stored P-C
    def load_design_pc(design, label="stored", final_map=None):
        """Return {(model,mode,prompting): pc_pct}."""
        res = {}
        for cfg in [c for c in configs if c["design"] == design]:
            recs = []
            seen = set()
            for path in [p.strip() for p in cfg["source_file"].split(";") if p.strip()]:
                for line in open(path):
                    if not line.strip(): continue
                    rec = json.loads(line); idx = rec.get("idx")
                    if idx is None or int(idx) in seen: continue
                    seen.add(int(idx)); idx = int(idx)
                    cid = rec.get("commit_id", "")
                    if not cid: continue
                    gt = int(rec.get("ground_truth", rec.get("target", -1)))
                    if label == "final" and final_map is not None:
                        pred = final_map.get((cfg["model"], cfg["mode"], cfg["prompting"], idx))
                        if pred is None:
                            ps = rec.get("vuln")
                            try: pred = int(ps)
                            except: pred = 0
                            if pred == -1: pred = 1
                    else:
                        ps = rec.get("vuln")
                        try: pred = int(ps)
                        except: pred = 0
                        if pred == -1: pred = 1
                    recs.append({"_cid": cid, "ground_truth": gt, "x": pred})
            res[(cfg["model"], cfg["mode"], cfg["prompting"])] = pc_for(
                [{"_cid": r["_cid"], "ground_truth": r["ground_truth"], "x": r["x"]} for r in recs], "x")
        return res

    final_map = {(r["model"], r["mode"], r["prompting"], r["idx"]): r["final"] for r in out_rows}
    sa = load_design_pc("SA")
    da = load_design_pc("DA")
    ma_stored = load_design_pc("MA", "stored")
    ma_final = load_design_pc("MA", "final", final_map)

    for world, ma_pc in (("STORED", ma_stored), ("FINAL(judge)", ma_final)):
        wins = defaultdict(int); ties = 0
        for key in sa:
            vals = {"SA": sa[key], "DA": da.get(key, 0), "MA": ma_pc.get(key, 0)}
            best = max(vals.values())
            winners = [d for d, v in vals.items() if abs(v - best) < 1e-9]
            if len(winners) == 1: wins[winners[0]] += 1
            else: ties += 1
        print(f"\nP-C win-counts ({world}) over {len(sa)} settings: "
              f"SA={wins['SA']} DA={wins['DA']} MA={wins['MA']} ties={ties}")
        mean_ma = sum(ma_pc.values())/len(ma_pc)
        print(f"  mean MA P-C% = {mean_ma:.1f}")


if __name__ == "__main__":
    main()
