"""
Compare LLM-judged explanation quality between correct and incorrect predictions
for SA zero-shot (Reviewer #2084C, point B5; and the cross-model extension
addressing Reviewer C #7 / model-specific RQ3 concern).

Supported models (--model):
  super49b — Nemotron-Super-49B (the original B5 pilot)
  qwen30b  — Qwen3-30B-A3B (Axis A: cross-model FP/FN extension)
  both     — Run both per-model summaries, then write a combined cross-model
             comparison table.

Inputs (under results/rq3_baseline/) per model:
  {model}_870_llm_judged_opus-4-6_zeroshot.csv          (correct intersection)
  {model}_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv (incorrect intersection)

For each of the four metrics (completeness, clarity, actionability,
informativeness) compute, overall and split by response_id (think / inst):
  - mean ± std per group
  - Mann-Whitney U statistic + p-value (two-sided)
  - Cohen's d effect size (pooled SD)
  - Common-language effect size (probability that a random correct sample
    scores above a random incorrect sample)

Outputs (per model + combined if --model both):
  results/rq3_baseline/rq3_b5_{model}_correct_vs_incorrect_summary.csv
  results/rq3_baseline/rq3_b5_{model}_correct_vs_incorrect_summary.md
  results/rq3_baseline/rq3_b5_cross_model_summary.md  (only with --model both)
"""

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "results" / "rq3_baseline"
DIMENSIONS = ["completeness", "clarity", "actionability", "informativeness"]

MODEL_REGISTRY = {
    "super49b": {
        "display_name": "Nemotron-Super-49B",
        "correct_csv": "super49b_870_llm_judged_opus-4-6_zeroshot.csv",
        "incorrect_csv": "super49b_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv",
    },
    "qwen30b": {
        "display_name": "Qwen3-30B-A3B",
        "correct_csv": "qwen30b_870_llm_judged_opus-4-6_zeroshot.csv",
        "incorrect_csv": "qwen30b_zero_incorrect_llm_judged_opus-4-6_zeroshot.csv",
    },
}


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
    wins = ties = 0
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


def fmt(v):
    if isinstance(v, float):
        return "—" if math.isnan(v) else f"{v:.3f}"
    return str(v)


def run_one_model(model_key: str) -> dict:
    """Run the correct-vs-incorrect comparison for one model.

    Returns a dict with: model_key, correct (rows), incorrect (rows),
    summary (list of per-(split, dim) stats dicts), out_csv (Path), out_md (Path).
    """
    cfg = MODEL_REGISTRY[model_key]
    correct_csv = OUT_DIR / cfg["correct_csv"]
    incorrect_csv = OUT_DIR / cfg["incorrect_csv"]

    if not correct_csv.exists():
        sys.exit(f"ERROR: correct CSV not found for {model_key}: {correct_csv}")
    if not incorrect_csv.exists():
        sys.exit(f"ERROR: incorrect CSV not found for {model_key}: {incorrect_csv}")

    correct = load_scores(correct_csv)
    incorrect = load_scores(incorrect_csv)
    print(f"[{model_key}] Loaded {len(correct)} correct rows from {correct_csv.name}")
    print(f"[{model_key}] Loaded {len(incorrect)} incorrect rows from {incorrect_csv.name}")

    rows = []
    for split_label, c_filter, i_filter in [
        ("overall", lambda r: True,                          lambda r: True),
        ("think",   lambda r: r["response_id"] == "think",   lambda r: r["response_id"] == "think"),
        ("inst",    lambda r: r["response_id"] == "inst",    lambda r: r["response_id"] == "inst"),
    ]:
        c_sub = [r for r in correct if c_filter(r)]
        i_sub = [r for r in incorrect if i_filter(r)]
        for dim in DIMENSIONS:
            stats = compare([r[dim] for r in c_sub], [r[dim] for r in i_sub])
            rows.append({"split": split_label, "dimension": dim, **stats})

    # Per-model CSV
    out_csv = OUT_DIR / f"rq3_b5_{model_key}_correct_vs_incorrect_summary.csv"
    fieldnames = ["split", "dimension", "n_correct", "n_incorrect",
                  "mean_correct", "std_correct", "mean_incorrect", "std_incorrect",
                  "mean_diff", "cohens_d", "cles_correct_over_incorrect",
                  "mannwhitney_u", "mannwhitney_p"]
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            r2 = {k: (f"{v:.4f}" if isinstance(v, float) and not math.isnan(v) else
                      ("" if (isinstance(v, float) and math.isnan(v)) else v))
                  for k, v in r.items()}
            w.writerow(r2)
    print(f"[{model_key}] Wrote {out_csv}")

    # Per-model Markdown
    out_md = OUT_DIR / f"rq3_b5_{model_key}_correct_vs_incorrect_summary.md"
    lines = []
    lines.append(f"# RQ3 — Correct vs Incorrect Explanation Quality — {cfg['display_name']}\n")
    lines.append(f"Source: {correct_csv.name} ({len(correct)} rows), "
                 f"{incorrect_csv.name} ({len(incorrect)} rows)\n")
    lines.append("Judge: Claude Opus 4.6 zero-shot. Group split shown overall and per response mode.\n")
    for split_label in ["overall", "think", "inst"]:
        lines.append(f"\n## {split_label}\n")
        lines.append("| Metric | n_correct | n_incorrect | mean_correct | mean_incorrect | mean_diff | Cohen's d | CLES (P(corr>incorr)) | U | p |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            if r["split"] != split_label:
                continue
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
    with open(out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"[{model_key}] Wrote {out_md}")

    return {
        "model_key": model_key,
        "display_name": cfg["display_name"],
        "correct": correct,
        "incorrect": incorrect,
        "summary": rows,
        "out_csv": out_csv,
        "out_md": out_md,
    }


def write_cross_model_summary(per_model: list):
    """Combine per-model summaries into a single cross-model comparison table.

    Format: for each metric in the overall split, side-by-side d / p / CLES
    across both models. This is the rebuttal-ready view addressing the
    'RQ3 is model-specific' concern.
    """
    out_md = OUT_DIR / "rq3_b5_cross_model_summary.md"
    lines = []
    lines.append("# RQ3 — Cross-model Correct-vs-Incorrect Explanation Quality\n")
    lines.append("Cross-model summary addressing Reviewer C #7 (RQ3 generalisability beyond "
                 "Nemotron-Super-49B). Each row reports the correct-vs-incorrect comparison "
                 "for one metric, side-by-side across the two models.\n")
    lines.append("Judge: Claude Opus 4.6 zero-shot. Same incorrect-intersection methodology "
                 "(15 snippets stratified 8 FP + 7 FN × {think, inst}, seed=42) applied to "
                 "both models.\n")

    # Sample-size summary first
    lines.append("\n## Sample sizes\n")
    lines.append("| Model | n_correct | n_incorrect |")
    lines.append("|---|---|---|")
    for pm in per_model:
        lines.append(f"| {pm['display_name']} | {len(pm['correct'])} | {len(pm['incorrect'])} |")

    # Overall split, side-by-side
    lines.append("\n## Overall (both modes pooled)\n")
    header = "| Metric "
    sep    = "|---"
    for pm in per_model:
        nm = pm["display_name"]
        header += f"| {nm} mean_corr | {nm} mean_incorr | {nm} Cohen's d | {nm} p "
        sep    += "|---|---|---|---"
    header += "|"
    sep    += "|"
    lines.append(header)
    lines.append(sep)
    for dim in DIMENSIONS:
        row = f"| {dim} "
        for pm in per_model:
            stats = [r for r in pm["summary"] if r["split"] == "overall" and r["dimension"] == dim][0]
            row += (f"| {fmt(stats['mean_correct'])} | {fmt(stats['mean_incorrect'])} "
                    f"| {fmt(stats['cohens_d'])} | {fmt(stats['mannwhitney_p'])} ")
        row += "|"
        lines.append(row)

    # Thinking-mode split
    lines.append("\n## Thinking mode only\n")
    lines.append(header)
    lines.append(sep)
    for dim in DIMENSIONS:
        row = f"| {dim} "
        for pm in per_model:
            stats = [r for r in pm["summary"] if r["split"] == "think" and r["dimension"] == dim][0]
            row += (f"| {fmt(stats['mean_correct'])} | {fmt(stats['mean_incorrect'])} "
                    f"| {fmt(stats['cohens_d'])} | {fmt(stats['mannwhitney_p'])} ")
        row += "|"
        lines.append(row)

    # Instruct-mode split
    lines.append("\n## Instruct mode only\n")
    lines.append(header)
    lines.append(sep)
    for dim in DIMENSIONS:
        row = f"| {dim} "
        for pm in per_model:
            stats = [r for r in pm["summary"] if r["split"] == "inst" and r["dimension"] == dim][0]
            row += (f"| {fmt(stats['mean_correct'])} | {fmt(stats['mean_incorrect'])} "
                    f"| {fmt(stats['cohens_d'])} | {fmt(stats['mannwhitney_p'])} ")
        row += "|"
        lines.append(row)

    # Interpretation hints
    lines.append("\n## Interpretation\n")
    lines.append("- Consistent direction across models on a metric (same sign of Cohen's d, "
                 "both p<0.05) means the finding *generalises* beyond Super-49B.\n")
    lines.append("- Divergent direction or magnitude on a metric is informative on its own — "
                 "it bounds which conclusions are model-specific.\n")
    lines.append("- Effect size interpretation: |d| ≈ 0.2 small, 0.5 medium, 0.8 large.\n")

    with open(out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote cross-model summary: {out_md}")

    # Echo to stdout
    print("\n--- cross-model summary ---")
    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        choices=list(MODEL_REGISTRY.keys()) + ["both"],
        default="super49b",
        help="Which model's pool to compare. 'both' runs each per-model summary then writes "
             "a combined cross-model table. Default: super49b (backwards-compatible).",
    )
    args = parser.parse_args()

    if args.model == "both":
        per_model = [run_one_model(k) for k in MODEL_REGISTRY.keys()]
        write_cross_model_summary(per_model)
    else:
        run_one_model(args.model)


if __name__ == "__main__":
    main()
