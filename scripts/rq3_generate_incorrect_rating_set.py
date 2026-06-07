"""
Generate the incorrect-intersection rating set for RQ3 (Reviewer B5 follow-up).

Samples from a model's SA zero-shot **incorrect**-intersection pool (entries
where *both* thinking and instruct modes produced an incorrect prediction on
the same code snippet). Used to address Reviewer #2084C, point B5:

    "Why is the manual explanation evaluation limited to 30 correctly
     classified instances? What happens if incorrectly classified instances
     are included?"

The 15 snippets are stratified 8 FP / 7 FN (mirroring the 8 TP / 7 TN split
of the correct pilot) and drawn with seed=42. Each snippet yields two rows
(think + inst), giving 30 evaluation rows ready for the LLM judge.

Supported models (--model):
  super49b — Nemotron-Super-49B (single model with instruct/thinking modes)
  qwen30b  — Qwen3-30B-A3B (separate Instruct + Thinking model variants)

Outputs to results/rq3_baseline/{model}_zero_incorrect_rating_set.csv.

The output schema matches the eval_queue records used inside
`rq3_llm_judge.mode_evaluate`, so the `--mode evaluate-incorrect` mode
of the judge can consume this CSV directly.
"""

import argparse
import csv
import json
import os
import random
import sys
from collections import Counter

csv.field_size_limit(sys.maxsize)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSOLIDATED_CSV = os.path.join(PROJECT_ROOT, "results", "consolidated_performance.csv")
VULN_DATASETS = [
    os.path.join(PROJECT_ROOT, "vuln_database", "VulTrial_486_samples_balanced.jsonl"),
    os.path.join(PROJECT_ROOT, "vuln_database", "VulTrial_384_incremental.jsonl"),
]
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "results", "rq3_baseline")

# Model registry: maps CLI key -> consolidated_performance.csv model-name filter.
# Qwen3-30B ships as two separate model checkpoints (Instruct + Thinking),
# while Super-49B is a single checkpoint with mode toggling. The filter
# captures whichever rows together cover both thinking + instruct.
MODEL_REGISTRY = {
    "super49b": {
        "models": ("Nemotron-Super-49B",),  # one model, two modes
    },
    "qwen30b": {
        "models": ("Qwen3-30B-A3B-Instruct", "Qwen3-30B-A3B-Thinking"),
    },
}

TARGET_FP = 8   # gt=0, pred=1 in both modes (false alarm)
TARGET_FN = 7   # gt=1, pred=0 in both modes (missed vulnerability)
TOTAL_SNIPPETS = TARGET_FP + TARGET_FN  # 15
SEED = 42


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def find_source_files(consolidated_csv: str, model_key: str):
    """Locate <model> SA zero-shot thinking + instruct JSONL paths (VulTrial-870)."""
    model_names = MODEL_REGISTRY[model_key]["models"]
    think_paths, inst_paths = [], []
    with open(consolidated_csv) as f:
        for row in csv.DictReader(f):
            if not (row["dataset"] == "VulTrial-870"
                    and row["design"] == "SA"
                    and row["model"] in model_names
                    and row["prompting"] == "zero-shot"):
                continue
            paths = [p.strip() for p in row["source_file"].split(";") if p.strip()]
            if row["mode"] == "thinking":
                think_paths.extend(paths)
            elif row["mode"] == "instruct":
                inst_paths.extend(paths)
    if not think_paths or not inst_paths:
        sys.exit(f"ERROR: Could not find {model_key} SA zero-shot source files in "
                 f"consolidated_performance.csv (model_names={model_names})")
    return think_paths, inst_paths


def load_jsonl_records(paths):
    """Load + merge JSONL records keyed by idx. First occurrence wins on dup idx."""
    records = {}
    for p in paths:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if "idx" not in r:
                    continue
                eid = int(r["idx"])
                if eid not in records:
                    records[eid] = r
    return records


def load_vuln_datasets(paths):
    ds = {}
    for p in paths:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                ds[int(r["idx"])] = r
    return ds


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        choices=list(MODEL_REGISTRY.keys()),
        default="super49b",
        help="Which model's SA zero-shot incorrect-intersection pool to sample from. "
             "Default: super49b (backwards-compatible).",
    )
    args = parser.parse_args()

    output_csv = os.path.join(
        OUTPUT_DIR, f"{args.model}_zero_incorrect_rating_set.csv")

    print(f"=== Generating incorrect rating set for {args.model} ===\n")

    think_paths, inst_paths = find_source_files(CONSOLIDATED_CSV, args.model)
    print("Thinking JSONLs:")
    for p in think_paths:
        print(f"  {p}")
    print("Instruct JSONLs:")
    for p in inst_paths:
        print(f"  {p}")
    print()

    think_data = load_jsonl_records(think_paths)
    inst_data = load_jsonl_records(inst_paths)
    vuln_ds = load_vuln_datasets(VULN_DATASETS)

    print(f"Thinking records: {len(think_data)}")
    print(f"Instruct records: {len(inst_data)}")
    print(f"VulTrial-870 dataset records: {len(vuln_ds)}")
    print()

    # Build incorrect-intersection pool: both modes wrong on the same snippet.
    common = set(think_data) & set(inst_data)
    pool_fp = []  # gt=0, pred=1 in both modes
    pool_fn = []  # gt=1, pred=0 in both modes
    skipped_unparseable = 0
    for eid in sorted(common):
        t, i = think_data[eid], inst_data[eid]
        gt = int(t.get("ground_truth", t.get("target", -1)))
        t_pred = int(t.get("vuln", -2))
        i_pred = int(i.get("vuln", -2))
        if t_pred not in (0, 1) or i_pred not in (0, 1) or gt not in (0, 1):
            skipped_unparseable += 1
            continue
        if t_pred == gt or i_pred == gt:
            continue  # at least one correct → not in incorrect-intersection
        if gt == 0 and t_pred == 1 and i_pred == 1:
            pool_fp.append(eid)
        elif gt == 1 and t_pred == 0 and i_pred == 0:
            pool_fn.append(eid)

    print(f"Incorrect-intersection pool")
    print(f"  Both FP (gt=0, both predict 1): {len(pool_fp)}")
    print(f"  Both FN (gt=1, both predict 0): {len(pool_fn)}")
    print(f"  Skipped (unparseable vuln/gt) : {skipped_unparseable}")
    print()

    if len(pool_fp) < TARGET_FP:
        sys.exit(f"ERROR: pool_fp too small ({len(pool_fp)} < {TARGET_FP})")
    if len(pool_fn) < TARGET_FN:
        sys.exit(f"ERROR: pool_fn too small ({len(pool_fn)} < {TARGET_FN})")

    random.seed(SEED)
    sampled_fp = sorted(random.sample(pool_fp, TARGET_FP))
    sampled_fn = sorted(random.sample(pool_fn, TARGET_FN))
    final_all = sorted(sampled_fp + sampled_fn)

    print(f"Selected {TOTAL_SNIPPETS} snippets ({TARGET_FP} FP, {TARGET_FN} FN):")
    for snip, eid in enumerate(final_all, 1):
        label = "FP" if eid in sampled_fp else "FN"
        print(f"  snippet {snip:2d}: entry_id {eid} — {label}")
    print()

    # Build rows in the same schema as rq3_llm_judge.mode_evaluate's eval_queue
    rows = []
    for snippet_id, eid in enumerate(final_all, 1):
        gt = int(think_data[eid].get("ground_truth",
                                     think_data[eid].get("target", 0)))
        gt_label = "vulnerable" if gt == 1 else "safe"
        error_label = "FP" if eid in sampled_fp else "FN"

        vul_rec = vuln_ds.get(eid, {})
        source_code = vul_rec.get("func", "")
        cwe = think_data[eid].get("cwe", vul_rec.get("cwe", ""))
        cve_desc = think_data[eid].get("cve_desc", vul_rec.get("cve_desc", ""))

        for resp_id, data_dict in [("think", think_data), ("inst", inst_data)]:
            rec = data_dict[eid]
            response_text = rec.get("reasoning", "")
            rows.append({
                "snippet_id": snippet_id,
                "entry_id": eid,
                "response_id": resp_id,
                "ground_truth": gt,
                "ground_truth_label": gt_label,
                "stratum": f"{resp_id}-{error_label}",  # think-FP / think-FN / inst-FP / inst-FN
                "source_code": source_code,
                "response_text": response_text,
                "cwe": str(cwe),
                "cve_desc": str(cve_desc),
            })

    # Shuffle to break adjacent think/inst pairing
    random.seed(SEED)
    random.shuffle(rows)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fieldnames = [
        "snippet_id", "entry_id", "response_id", "ground_truth",
        "ground_truth_label", "stratum", "source_code", "response_text",
        "cwe", "cve_desc",
    ]
    with open(output_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote: {output_csv}")
    print(f"  Total rows: {len(rows)}")
    strata = Counter(r["stratum"] for r in rows)
    print("  Stratum distribution:")
    for s in sorted(strata):
        print(f"    {s}: {strata[s]}")


if __name__ == "__main__":
    main()
