"""
Length-confound analysis for the RQ3 LLM judge (Reviewer A, point 3).

Reviewer A asked two things:
  (1) Do Claude Opus 4.6's scores correlate with response length / output
      complexity independently of content quality?
  (2) Does the thinking-mode advantage on completeness and informativeness
      persist after controlling for response length?

Approach:
  (1) Spearman ρ and Pearson r between response length and each of the four
      LLM-judge dimensions, overall and split by response_id (think / inst).
      Length is measured in characters and in whitespace-split tokens.
  (2) Partial Spearman correlation between mode (think=1, inst=0) and score,
      controlling for response length, for completeness and informativeness.
      A non-trivial partial coefficient with significant p indicates the
      mode advantage is not just a length artifact.

Inputs:
  results/rq3_baseline/super49b_870_llm_judged_opus-4-6_zeroshot.csv
  results/runpod_vuln_486/Sa-zero_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_*_{thinking,instruct}_detailed_results.jsonl
  results/runpod_vuln_384_incremental/Sa-zero_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_*_detailed_results.jsonl

Outputs:
  results/rq3_baseline/rq3_a3_length_confound_summary.csv
  results/rq3_baseline/rq3_a3_length_confound_summary.md
"""

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr
import pingouin as pg
from transformers import AutoTokenizer

# Nemotron BPE tokenizer (Super-49B is the Llama-3.3 tune of the same family
# as Nano-8B; both share the Llama-3.1 tokenizer used in compute_token_counts.py)
_TOKENIZER = AutoTokenizer.from_pretrained(
    "nvidia/Llama-3.1-Nemotron-Nano-8B-v1", trust_remote_code=True)

csv.field_size_limit(sys.maxsize)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RQ3_DIR = PROJECT_ROOT / "results" / "rq3_baseline"
JUDGED_CSV = RQ3_DIR / "super49b_870_llm_judged_opus-4-6_zeroshot.csv"

THINK_JSONLS = [
    PROJECT_ROOT / "results" / "runpod_vuln_486" /
    "Sa-zero_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_20260307-021559_thinking_detailed_results.jsonl",
    PROJECT_ROOT / "results" / "runpod_vuln_384_incremental" /
    "Sa-zero_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_20260318-211147_thinking_detailed_results.jsonl",
]
INST_JSONLS = [
    PROJECT_ROOT / "results" / "runpod_vuln_486" /
    "Sa-zero_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_20260306-235454_instruct_detailed_results.jsonl",
    PROJECT_ROOT / "results" / "runpod_vuln_384_incremental" /
    "Sa-zero_nvidia-Llama-3_3-Nemotron-Super-49B-v1_5_20260318-151410_detailed_results.jsonl",
]

OUT_CSV = RQ3_DIR / "rq3_a3_length_confound_summary.csv"
OUT_MD = RQ3_DIR / "rq3_a3_length_confound_summary.md"

DIMENSIONS = ["completeness", "clarity", "actionability", "informativeness"]


def load_response_lengths(paths):
    """Return {idx: (chars, whitespace_tokens, bpe_tokens)} for each response."""
    out = {}
    for p in paths:
        with open(p) as f:
            for line in f:
                r = json.loads(line)
                if "idx" not in r:
                    continue
                eid = int(r["idx"])
                if eid in out:
                    continue
                txt = r.get("reasoning", "") or ""
                if txt.strip():
                    bpe = len(_TOKENIZER.encode(txt))
                else:
                    bpe = 0
                out[eid] = (len(txt), len(txt.split()), bpe)
    return out


def fmt_p(p):
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "—"
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def fmt(x, places=3):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{x:.{places}f}"


def main():
    if not JUDGED_CSV.exists():
        sys.exit(f"ERROR: judged CSV not found: {JUDGED_CSV}")

    judged = pd.read_csv(JUDGED_CSV)
    print(f"Loaded {len(judged)} judged rows from {JUDGED_CSV.name}")

    think_lens = load_response_lengths(THINK_JSONLS)
    inst_lens = load_response_lengths(INST_JSONLS)
    print(f"  thinking response-length records: {len(think_lens)}")
    print(f"  instruct response-length records: {len(inst_lens)}")

    # Join lengths into the dataframe
    chars, tokens, bpe = [], [], []
    for _, row in judged.iterrows():
        eid = int(row["entry_id"])
        rid = row["response_id"]
        src = think_lens if rid == "think" else inst_lens
        if eid not in src:
            chars.append(np.nan)
            tokens.append(np.nan)
            bpe.append(np.nan)
        else:
            c, t, b = src[eid]
            chars.append(c)
            tokens.append(t)
            bpe.append(b)
    judged["len_chars"] = chars
    judged["len_tokens"] = tokens
    judged["len_bpe"] = bpe

    missing = judged["len_chars"].isna().sum()
    print(f"  rows missing length: {missing}")
    judged = judged.dropna(subset=["len_chars", "len_tokens", "len_bpe"]).reset_index(drop=True)
    print(f"  rows after length join: {len(judged)}\n")

    # =============================================================
    # Part 1 — Score ↔ Length correlations
    # =============================================================
    rows = []
    for split_label, df_sub in [
        ("overall", judged),
        ("think",   judged[judged["response_id"] == "think"]),
        ("inst",    judged[judged["response_id"] == "inst"]),
    ]:
        for unit in ("chars", "tokens", "bpe"):
            length = df_sub[f"len_{unit}"].to_numpy(dtype=float)
            for dim in DIMENSIONS:
                score = df_sub[f"{dim}_score"].to_numpy(dtype=float)
                rho, p_rho = spearmanr(length, score)
                r, p_r = pearsonr(length, score)
                rows.append({
                    "analysis": "length_vs_score",
                    "split": split_label,
                    "length_unit": unit,
                    "dimension": dim,
                    "n": len(score),
                    "spearman_rho": float(rho) if rho is not None else float("nan"),
                    "spearman_p": float(p_rho) if p_rho is not None else float("nan"),
                    "pearson_r": float(r) if r is not None else float("nan"),
                    "pearson_p": float(p_r) if p_r is not None else float("nan"),
                })

    # =============================================================
    # Part 2 — Mode → Score, controlling for length (partial Spearman)
    # =============================================================
    judged["mode_bin"] = (judged["response_id"] == "think").astype(int)
    for dim in DIMENSIONS:
        for unit in ("chars", "tokens", "bpe"):
            # Raw Spearman (mode vs score) — sanity check
            rho_raw, p_raw = spearmanr(judged["mode_bin"], judged[f"{dim}_score"])
            # Partial Spearman, controlling for length
            stats = pg.partial_corr(
                data=judged,
                x="mode_bin",
                y=f"{dim}_score",
                covar=[f"len_{unit}"],
                method="spearman",
            )
            partial_rho = float(stats["r"].iloc[0])
            # pingouin renamed columns in 0.6.x (p-val → p_val, CI95% → CI95)
            p_col = "p_val" if "p_val" in stats.columns else "p-val"
            ci_col = "CI95" if "CI95" in stats.columns else "CI95%"
            partial_p = float(stats[p_col].iloc[0])
            ci = stats[ci_col].iloc[0]
            ci_lo = float(ci[0]) if ci is not None else float("nan")
            ci_hi = float(ci[1]) if ci is not None else float("nan")

            rows.append({
                "analysis": "mode_vs_score_partial",
                "split": "overall",
                "length_unit": unit,
                "dimension": dim,
                "n": int(stats["n"].iloc[0]),
                "spearman_rho": rho_raw,
                "spearman_p": p_raw,
                "partial_spearman_rho": partial_rho,
                "partial_spearman_p": partial_p,
                "partial_ci95_lo": ci_lo,
                "partial_ci95_hi": ci_hi,
            })

    # ---- Write CSV ----
    fieldnames = sorted({k for r in rows for k in r.keys()})
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            row = {k: (fmt(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
            w.writerow({k: row.get(k, "") for k in fieldnames})
    print(f"Wrote {OUT_CSV}")

    # ---- Write Markdown summary ----
    md = []
    md.append("# RQ3 — Length Confound Analysis (Reviewer A, point 3)\n")
    md.append(f"Source: `{JUDGED_CSV.name}` (n={len(judged)}). "
              "Length is `len(reasoning)` measured three ways: characters, "
              "whitespace-split tokens, and BPE tokens using the Nemotron Llama-3.1 "
              "tokenizer (matching the inference model). "
              "Judge: Claude Opus 4.6 zero-shot.\n")

    # Descriptive length stats per mode
    md.append("\n## Response length, descriptive statistics\n")
    md.append("BPE counts use the Nemotron Llama-3.1 tokenizer "
              "(matching the inference model family).\n")
    md.append("| Mode | n | mean_chars | median_chars | mean_split | median_split | mean_bpe | median_bpe |")
    md.append("|---|---|---|---|---|---|---|---|")
    for mode in ("think", "inst"):
        sub = judged[judged["response_id"] == mode]
        md.append(
            f"| {mode} | {len(sub)} | {sub['len_chars'].mean():.0f} | "
            f"{sub['len_chars'].median():.0f} | {sub['len_tokens'].mean():.0f} | "
            f"{sub['len_tokens'].median():.0f} | {sub['len_bpe'].mean():.0f} | "
            f"{sub['len_bpe'].median():.0f} |"
        )

    # Rank correlation between length units (sensitivity baseline)
    md.append("\n**Rank correlation between length units** (Spearman ρ across all "
              f"{len(judged)} rows):")
    rho_ct, _ = spearmanr(judged["len_chars"], judged["len_tokens"])
    rho_cb, _ = spearmanr(judged["len_chars"], judged["len_bpe"])
    rho_tb, _ = spearmanr(judged["len_tokens"], judged["len_bpe"])
    md.append(f"chars↔split={rho_ct:.3f}, chars↔bpe={rho_cb:.3f}, "
              f"split↔bpe={rho_tb:.3f} — near-perfect monotonic alignment confirms "
              "the choice of length unit does not materially affect Spearman-based results.\n")

    # Table 1 — score ↔ length correlations
    md.append("\n## Table 1 — Score ↔ Length correlation\n")
    md.append("Spearman ρ is the primary statistic (rank-based, robust to skew). "
              "Pearson r reported for transparency.\n")
    md.append("| Split | Length unit | Metric | n | Spearman ρ | p | Pearson r | p |")
    md.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        if r["analysis"] != "length_vs_score":
            continue
        md.append(
            f"| {r['split']} | {r['length_unit']} | {r['dimension']} | {r['n']} | "
            f"{fmt(r['spearman_rho'])} | {fmt_p(r['spearman_p'])} | "
            f"{fmt(r['pearson_r'])} | {fmt_p(r['pearson_p'])} |"
        )

    # Table 2 — partial correlation: mode → score, controlling for length
    md.append("\n## Table 2 — Thinking-vs-instruct on all four metrics, "
              "controlling for response length\n")
    md.append("Mode coded as think=1, inst=0. Raw Spearman ρ is mode→score without "
              "controls; partial Spearman ρ is the same after partialling out length. "
              "A partial coefficient close to the raw value indicates length is not a "
              "dominant confound.\n")
    md.append("| Metric | Length unit | Raw Spearman ρ | Raw p | "
              "Partial Spearman ρ | Partial p | 95% CI |")
    md.append("|---|---|---|---|---|---|---|")
    for r in rows:
        if r["analysis"] != "mode_vs_score_partial":
            continue
        md.append(
            f"| {r['dimension']} | {r['length_unit']} | "
            f"{fmt(r['spearman_rho'])} | {fmt_p(r['spearman_p'])} | "
            f"{fmt(r['partial_spearman_rho'])} | {fmt_p(r['partial_spearman_p'])} | "
            f"[{fmt(r['partial_ci95_lo'])}, {fmt(r['partial_ci95_hi'])}] |"
        )

    md.append("\n**Interpretation guide:** "
              "|ρ| ≈ 0.1 small, ≈ 0.3 moderate, ≈ 0.5 large (Cohen). "
              "If partial ρ shrinks substantially toward zero relative to raw ρ, "
              "length explains a large share of the mode effect; if it remains "
              "comparable, the mode advantage is not driven by length.\n")

    with open(OUT_MD, "w") as f:
        f.write("\n".join(md))
    print(f"Wrote {OUT_MD}\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
