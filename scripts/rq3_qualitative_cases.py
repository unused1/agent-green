"""
Stage qualitative FP/FN spot-checks for the rebuttal narrative (Axis D,
companion to scripts/rq3_compare_correct_vs_incorrect.py).

For each model (super49b, qwen30b) the script:
  1. Loads the model's incorrect-intersection rating set (source code +
     model responses per entry_id × {think, inst})
  2. Loads the LLM judge's per-row scores and justifications
  3. Joins them, computes a "plausibility-disconnect" score:
         actionability + clarity - (completeness + informativeness)
     A high value flags responses that *sound* actionable and clear but
     are *thin* on substance — the "plausibly worded yet causally
     disconnected" pattern the methodology section anticipates.
  4. Picks the top-N candidates per (model × error_type), keeping a balance
     across modes
  5. Writes a Markdown digest with quoted code, response excerpts, judge
     justifications, and analyst notes

Output: results/rq3_baseline/rq3_b5_qualitative_cases.md
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

csv.field_size_limit(sys.maxsize)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "results" / "rq3_baseline"
DIMENSIONS = ["completeness", "clarity", "actionability", "informativeness"]

MODEL_REGISTRY = {
    "super49b": {
        "display_name": "Nemotron-Super-49B",
        "rating_set": "super49b_zero_incorrect_rating_set.csv",
        "judged":     "super49b_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv",
    },
    "qwen30b": {
        "display_name": "Qwen3-30B-A3B",
        "rating_set": "qwen30b_zero_incorrect_rating_set.csv",
        "judged":     "qwen30b_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv",
    },
}


def load_rating_set(path: Path) -> dict:
    """Return {(entry_id, response_id): rating-set row dict}."""
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            out[(int(row["entry_id"]), row["response_id"])] = row
    return out


def load_judged(path: Path) -> dict:
    """Return {(entry_id, response_id): judged row dict (with int scores)}."""
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            key = (int(row["entry_id"]), row["response_id"])
            scores = {}
            for d in DIMENSIONS:
                v = row.get(f"{d}_score", "")
                scores[d] = int(v) if v not in ("", None) else None
            out[key] = {"scores": scores, "justifications": row}
    return out


def plausibility_disconnect(scores: dict) -> int:
    """Higher = sounds clear/actionable but thin on substance."""
    s = lambda d: scores.get(d, 0) or 0
    return (s("actionability") + s("clarity")) - (s("completeness") + s("informativeness"))


def truncate(text: str, max_chars: int, marker: str = " […]") -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + marker


def format_case(case: dict, model_display: str, lines: list):
    rs = case["rating_set_row"]
    sc = case["scores"]
    just = case["justifications"]
    eid = case["entry_id"]
    rid = case["response_id"]
    err = "FP" if rs["stratum"].endswith("FP") else "FN"
    mode_lbl = "thinking" if rid == "think" else "instruct"
    gt_lbl = rs["ground_truth_label"]
    cwe = rs.get("cwe", "")
    cve_desc = rs.get("cve_desc", "")

    lines.append(f"\n### Case: {model_display} · {mode_lbl} · {err} · entry_id={eid}\n")
    lines.append(f"**Ground truth**: {gt_lbl} (model predicted {'safe' if err == 'FN' else 'vulnerable'})  \n")
    if cwe:
        lines.append(f"**CWE**: {cwe}  \n")
    if cve_desc and cve_desc.strip() not in ("None", ""):
        lines.append(f"**CVE description**: {truncate(cve_desc, 220)}  \n")
    lines.append(f"**Plausibility-disconnect score**: {case['disconnect']:+d}  \n")
    lines.append(f"**Judge scores** — completeness {sc['completeness']}, clarity {sc['clarity']}, "
                 f"actionability {sc['actionability']}, informativeness {sc['informativeness']}\n")

    # Source code (truncated to ~30 LOC)
    func = (rs.get("source_code") or "").rstrip()
    func_lines = func.splitlines()
    if len(func_lines) > 30:
        func_excerpt = "\n".join(func_lines[:30]) + "\n// […]"
    else:
        func_excerpt = "\n".join(func_lines)
    lines.append("\n**Source code (excerpt)**:\n")
    lines.append("```c\n" + func_excerpt + "\n```\n")

    # Model response (excerpt)
    resp = rs.get("response_text", "")
    lines.append("\n**Model response (excerpt)**:\n")
    lines.append("> " + truncate(resp.replace("\n", " "), 600) + "\n")

    # Judge justifications for the two weakest dimensions
    sorted_dims = sorted(DIMENSIONS, key=lambda d: sc[d] or 0)
    lines.append("\n**Judge justifications (lowest-scoring dimensions)**:\n")
    for d in sorted_dims[:2]:
        j = (just.get(f"{d}_justification") or "").strip()
        lines.append(f"- *{d}* (score {sc[d]}): {truncate(j, 320)}\n")

    # Analyst note (heuristic auto-generated)
    note_parts = []
    if (sc["completeness"] or 0) <= 2:
        note_parts.append("treats one surface concern as the full picture, "
                          "missing the actual mechanism")
    if (sc["informativeness"] or 0) <= 2:
        note_parts.append("substance is thin (recommendation rather than analysis)")
    if (sc["clarity"] or 0) >= 4:
        note_parts.append("written confidently and cleanly despite being wrong")
    if (sc["actionability"] or 0) >= 3:
        note_parts.append("still proposes remediation, just for the wrong underlying claim")
    if not note_parts:
        note_parts.append("uniformly weak across the four dimensions")
    lines.append(f"\n**Analyst note**: " + "; ".join(note_parts) + ".\n")
    lines.append("\n---\n")


def select_cases(rating_set: dict, judged: dict, per_error: int) -> list:
    """Pick representative cases. Returns list of dicts ordered by selection."""
    keys = set(rating_set) & set(judged)
    cases = []
    for (eid, rid) in keys:
        rs = rating_set[(eid, rid)]
        j = judged[(eid, rid)]
        sc = j["scores"]
        if any(sc[d] is None for d in DIMENSIONS):
            continue
        disconnect = plausibility_disconnect(sc)
        cases.append({
            "entry_id": eid,
            "response_id": rid,
            "rating_set_row": rs,
            "scores": sc,
            "justifications": j["justifications"],
            "disconnect": disconnect,
        })

    # Stratify by (error_type, response_id), pick highest-disconnect per stratum
    by_strat = defaultdict(list)
    for c in cases:
        err = "FP" if c["rating_set_row"]["stratum"].endswith("FP") else "FN"
        by_strat[(err, c["response_id"])].append(c)

    selected = []
    # Sort within stratum by disconnect descending (most plausible-but-disconnected first)
    for k in sorted(by_strat.keys()):
        by_strat[k].sort(key=lambda c: -c["disconnect"])
        selected.extend(by_strat[k][:per_error])
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--per-stratum",
        type=int,
        default=1,
        help="Cases per (error_type × response_id) stratum per model. "
             "Default 1 → 4 cases per model → 8 total across both models.",
    )
    args = parser.parse_args()

    lines = []
    lines.append("# RQ3 — Qualitative FP/FN cases (rebuttal narrative)\n")
    lines.append("Companion to `rq3_b5_cross_model_summary.md`. Selected to illustrate "
                 "the *plausibly-worded but causally-disconnected* pattern that drives "
                 "the statistical correct-vs-incorrect gap.\n")
    lines.append("Selection: highest *plausibility-disconnect* score "
                 "(`actionability + clarity − completeness − informativeness`) "
                 "within each (model × error_type × response_mode) stratum, "
                 f"top {args.per_stratum} per stratum.\n")
    lines.append("Each case shows the source code, the model's response, the LLM "
                 "judge's justification for the two lowest-scoring dimensions, and a "
                 "short analyst note. All cases are from the Super-49B or Qwen3-30B "
                 "SA zero-shot incorrect-intersection pool.\n")

    for model_key, cfg in MODEL_REGISTRY.items():
        rs_path = OUT_DIR / cfg["rating_set"]
        j_path = OUT_DIR / cfg["judged"]
        if not rs_path.exists() or not j_path.exists():
            print(f"[{model_key}] SKIP: missing inputs", file=sys.stderr)
            continue
        rating_set = load_rating_set(rs_path)
        judged = load_judged(j_path)
        print(f"[{model_key}] loaded {len(rating_set)} rating rows, {len(judged)} judged rows")

        cases = select_cases(rating_set, judged, per_error=args.per_stratum)
        print(f"[{model_key}] selected {len(cases)} cases")

        lines.append(f"\n## {cfg['display_name']}\n")
        for c in cases:
            format_case(c, cfg["display_name"], lines)

    out_md = OUT_DIR / "rq3_b5_qualitative_cases.md"
    with open(out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"\nWrote {out_md}")


if __name__ == "__main__":
    main()
