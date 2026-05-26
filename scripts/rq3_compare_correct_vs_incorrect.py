"""
Compare LLM-judged explanation quality between correct and incorrect predictions
for Super-49B SA zero-shot (Reviewer #2084C, point B5).

Inputs (under results/rq3_baseline/):
  - super49b_870_llm_judged_opus-4-6_zeroshot.csv          (correct intersection, n=462)
  - super49b_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv (incorrect intersection, n=30)

For each of the four metrics (completeness, clarity, actionability, informativeness)
compute, overall and split by response_id (think / inst):
  - mean ± std per group
  - Mann-Whitney U statistic + p-value (two-sided)
  - Cohen's d effect size (pooled SD)
  - Common-language effect size (probability that a random correct sample
    scores above a random incorrect sample)

Outputs:
  - results/rq3_baseline/rq3_b5_correct_vs_incorrect_summary.csv
  - results/rq3_baseline/rq3_b5_correct_vs_incorrect_summary.md
"""

import csv
import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "results" / "rq3_baseline"
CORRECT_CSV = OUT_DIR / "super49b_870_llm_judged_opus-4-6_zeroshot.csv"
INCORRECT_CSV = OUT_DIR / "super49b_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv"
SUMMARY_CSV = OUT_DIR / "rq3_b5_correct_vs_incorrect_summary.csv"
SUMMARY_MD = OUT_DIR / "rq3_b5_correct_vs_incorrect_summary.md"

DIMENSIONS = ["completeness", "clarity", "actionability", "informativeness"]


def load_scores(path: Path) -> list:
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            entry = {"response_id": row["response_id"]}
            for dim in DIMENSIONS:
                v = row.get(f"{dim}_score", "")
                entry[dim] = int(v) if v not in ("", None) else None
            rows.append(entry)
    return rows


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's d with pooled standard deviation (a vs b)."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    va, vb = a.var(ddof=1), b.var(ddof=1)
    s_pool = math.sqrt(((na - 1) * va + (nb - 1) * vb) / (na + nb - 2))
    if s_pool == 0:
        return float("nan")
    return (a.mean() - b.mean()) / s_pool


def common_language_es(a: np.ndarray, b: np.ndarray) -> float:
    """P(X > Y) + 0.5 P(X = Y) for X drawn from a and Y from b."""
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    wins = 0
    ties = 0
    for x in a:
        wins += int((b < x).sum())
        ties += int((b == x).sum())
    total = len(a) * len(b)
    return (wins + 0.5 * ties) / total


def compare(correct_vals: list, incorrect_vals: list) -> dict:
    a = np.array([v for v in correct_vals if v is not None], dtype=float)
    b = np.array([v for v in incorrect_vals if v is not None], dtype=float)
    out = {
        "n_correct": len(a),
        "n_incorrect": len(b),
        "mean_correct": a.mean() if len(a) else float("nan"),
        "std_correct": a.std(ddof=1) if len(a) > 1 else float("nan"),
        "mean_incorrect": b.mean() if len(b) else float("nan"),
        "std_incorrect": b.std(ddof=1) if len(b) > 1 else float("nan"),
        "mean_diff": (a.mean() - b.mean()) if (len(a) and len(b)) else float("nan"),
        "cohens_d": cohens_d(a, b),
        "cles_correct_over_incorrect": common_language_es(a, b),
    }
    if len(a) > 0 and len(b) > 0:
        u, p = mannwhitneyu(a, b, alternative="two-sided")
        out["mannwhitney_u"] = float(u)
        out["mannwhitney_p"] = float(p)
    else:
        out["mannwhitney_u"] = float("nan")
        out["mannwhitney_p"] = float("nan")
    return out


def main():
    if not CORRECT_CSV.exists():
        sys.exit(f"ERROR: correct CSV not found: {CORRECT_CSV}")
    if not INCORRECT_CSV.exists():
        sys.exit(f"ERROR: incorrect CSV not found: {INCORRECT_CSV}")

    correct = load_scores(CORRECT_CSV)
    incorrect = load_scores(INCORRECT_CSV)
    print(f"Loaded {len(correct)} correct rows from {CORRECT_CSV.name}")
    print(f"Loaded {len(incorrect)} incorrect rows from {INCORRECT_CSV.name}")
    print()

    rows = []
    for split_label, c_filter, i_filter in [
        ("overall", lambda r: True,                  lambda r: True),
        ("think",   lambda r: r["response_id"] == "think", lambda r: r["response_id"] == "think"),
        ("inst",    lambda r: r["response_id"] == "inst",  lambda r: r["response_id"] == "inst"),
    ]:
        c_sub = [r for r in correct if c_filter(r)]
        i_sub = [r for r in incorrect if i_filter(r)]
        for dim in DIMENSIONS:
            stats = compare([r[dim] for r in c_sub], [r[dim] for r in i_sub])
            rows.append({"split": split_label, "dimension": dim, **stats})

    # Write CSV
    fieldnames = ["split", "dimension", "n_correct", "n_incorrect",
                  "mean_correct", "std_correct", "mean_incorrect", "std_incorrect",
                  "mean_diff", "cohens_d", "cles_correct_over_incorrect",
                  "mannwhitney_u", "mannwhitney_p"]
    with open(SUMMARY_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            r2 = {k: (f"{v:.4f}" if isinstance(v, float) and not math.isnan(v) else
                      ("" if (isinstance(v, float) and math.isnan(v)) else v))
                  for k, v in r.items()}
            w.writerow(r2)
    print(f"Wrote {SUMMARY_CSV}")

    # Write markdown
    lines = []
    lines.append("# RQ3 — Correct vs Incorrect Explanation Quality (Reviewer B5)\n")
    lines.append(f"Source: {CORRECT_CSV.name} ({len(correct)} rows), "
                 f"{INCORRECT_CSV.name} ({len(incorrect)} rows)\n")
    lines.append("Judge: Claude Opus 4.6 zero-shot. Group split shown overall and per response mode.\n")
    for split_label in ["overall", "think", "inst"]:
        lines.append(f"\n## {split_label}\n")
        lines.append("| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            if r["split"] != split_label:
                continue
            def fmt(v):
                if isinstance(v, float):
                    return "—" if math.isnan(v) else f"{v:.3f}"
                return str(v)
            lines.append(
                f"| {r['dimension']} | {r['n_correct']} | {r['n_incorrect']} | "
                f"{fmt(r['mean_correct'])} ± {fmt(r['std_correct'])} | "
                f"{fmt(r['mean_incorrect'])} ± {fmt(r['std_incorrect'])} | "
                f"{fmt(r['mean_diff'])} | {fmt(r['cohens_d'])} | "
                f"{fmt(r['cles_correct_over_incorrect'])} | "
                f"{fmt(r['mannwhitney_u'])} | "
                f"{fmt(r['mannwhitney_p'])} |"
            )
    lines.append("\n")
    lines.append("**Effect size interpretation (Cohen's d, absolute):** ≈0.2 small, ≈0.5 medium, ≈0.8 large.\n")
    lines.append("**CLES** is the probability that a randomly drawn correct-sample score exceeds a randomly drawn incorrect-sample score (0.5 = no preference).\n")

    with open(SUMMARY_MD, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {SUMMARY_MD}")

    # Echo to stdout for quick reading
    print("\n--- summary.md ---")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
