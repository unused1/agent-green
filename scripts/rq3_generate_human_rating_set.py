"""
Generate the Phase A human rating set for RQ3.

This script samples 15 code snippets from the Nemotron-Super-49B SA zero-shot
think-intersect-instruct pool (VulTrial-486 dataset) and produces a shuffled
CSV of 30 evaluation rows (each snippet x {thinking, instruct}).

Two snippets are force-included from prior Phase A preliminary ratings. The
remaining 13 are drawn via stratified random sampling (8 TP, 7 TN total).
Rows are shuffled (seed=42) so the rater cannot easily pair think/inst
responses for the same snippet, reducing bias.

Output:  results/rq3_baseline/super49b_zero_human_rating_set.csv
"""

import csv
import json
import os
import random
import sys

csv.field_size_limit(sys.maxsize)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSOLIDATED_CSV = os.path.join(PROJECT_ROOT, "results", "consolidated_performance.csv")
VULN_DATASET = os.path.join(PROJECT_ROOT, "vuln_database", "VulTrial_486_samples_balanced.jsonl")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "results", "rq3_baseline")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "super49b_zero_human_rating_set.csv")

# Force-included entry_ids: all 15 human-rated entries are locked so that
# expanding the pool from VulTrial-486 → VulTrial-870 doesn't change the
# sampled snippets via random.sample(seed=42).
# The original 2 forced entries (197517, 222737) retain their prior scores;
# the remaining 13 were originally drawn by stratified random sampling.
FORCED_ENTRIES = {
    # --- Original forced includes (with prior Phase A scores) ---
    197517: {"label": "TP", "ground_truth": 1,
             "prior_scores": {"completeness": 3, "clarity": 4,
                              "actionability": 3, "informativeness": 3}},
    222737: {"label": "TN", "ground_truth": 0,
             "prior_scores": {"completeness": 3, "clarity": 5,
                              "actionability": 3, "informativeness": 4}},
    # --- Previously sampled TP entries (now locked) ---
    195029: {"label": "TP", "ground_truth": 1, "prior_scores": {}},
    195040: {"label": "TP", "ground_truth": 1, "prior_scores": {}},
    195399: {"label": "TP", "ground_truth": 1, "prior_scores": {}},
    195409: {"label": "TP", "ground_truth": 1, "prior_scores": {}},
    195800: {"label": "TP", "ground_truth": 1, "prior_scores": {}},
    197095: {"label": "TP", "ground_truth": 1, "prior_scores": {}},
    198013: {"label": "TP", "ground_truth": 1, "prior_scores": {}},
    # --- Previously sampled TN entries (now locked) ---
    224153: {"label": "TN", "ground_truth": 0, "prior_scores": {}},
    325821: {"label": "TN", "ground_truth": 0, "prior_scores": {}},
    379334: {"label": "TN", "ground_truth": 0, "prior_scores": {}},
    421378: {"label": "TN", "ground_truth": 0, "prior_scores": {}},
    442587: {"label": "TN", "ground_truth": 0, "prior_scores": {}},
    504608: {"label": "TN", "ground_truth": 0, "prior_scores": {}},
}

# Entries excluded due to text-parser mismatches: the response text conclusion
# contradicts the parser's vuln field (e.g., model concludes "NO" but parser set
# vuln=1, or model concludes "YES" but parser set vuln=0). These entries should
# not appear in the intersection pool because the response text shown to raters
# would contradict the ground truth label.
# - 197518, 204017: gt=1 but instruct response concludes NO (parser FP)
# - 206676: gt=1 but instruct response concludes NO (parser FP)
# - 270922: gt=0 but thinking response concludes YES (model FP on safe code)
# - 387593: gt=0 but instruct response concludes YES (model FP on safe code)
EXCLUDE_PARSER_MISMATCH = {197518, 204017, 206676, 270922, 387593}

# Sampling targets
TARGET_TP = 8
TARGET_TN = 7
TOTAL_SNIPPETS = TARGET_TP + TARGET_TN  # 15


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def find_source_files(consolidated_csv: str):
    """Return (thinking_jsonl, instruct_jsonl) paths for Super-49B SA zero-shot vuln."""
    think_path = None
    inst_path = None
    with open(consolidated_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row["model"] == "Nemotron-Super-49B"
                    and row["design"] == "SA"
                    and row["task"] == "vulnerability_detection"
                    and row["prompting"] == "zero-shot"):
                summary = row["source_file"]
                jsonl = summary.replace(
                    "_summary_vulnerability_metrics.csv",
                    "_detailed_results.jsonl",
                )
                if row["mode"] == "thinking":
                    think_path = jsonl
                elif row["mode"] == "instruct":
                    inst_path = jsonl
    if not think_path or not inst_path:
        sys.exit("ERROR: Could not find both thinking and instruct JSONL paths "
                 "in consolidated_performance.csv")
    return think_path, inst_path


def load_jsonl(path: str) -> dict:
    """Load JSONL, returning {idx: record} for lines that have an idx field."""
    records = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "idx" not in rec:
                continue
            records[int(rec["idx"])] = rec
    return records


def load_vuln_dataset(path: str) -> dict:
    """Load VulTrial dataset, returning {idx: record}."""
    records = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            records[int(rec["idx"])] = rec
    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Step 1 — locate JSONL files
    think_jsonl, inst_jsonl = find_source_files(CONSOLIDATED_CSV)
    print(f"Thinking JSONL : {think_jsonl}")
    print(f"Instruct JSONL : {inst_jsonl}")
    print()

    # Step 2 — load data
    think_data = load_jsonl(think_jsonl)
    inst_data = load_jsonl(inst_jsonl)
    vuln_ds = load_vuln_dataset(VULN_DATASET)

    print(f"Thinking records loaded : {len(think_data)}")
    print(f"Instruct records loaded : {len(inst_data)}")
    print(f"VulTrial-486 records    : {len(vuln_ds)}")
    print()

    # Step 3 — build intersection pool (correct in BOTH modes)
    common_ids = set(think_data.keys()) & set(inst_data.keys())
    pool_tp = []
    pool_tn = []
    excluded_count = 0
    for eid in sorted(common_ids):
        if eid in EXCLUDE_PARSER_MISMATCH:
            excluded_count += 1
            continue
        t = think_data[eid]
        i = inst_data[eid]
        gt = int(t["ground_truth"])
        t_pred = int(t["vuln"])
        i_pred = int(i["vuln"])
        # Correct in both modes
        if t_pred == gt and i_pred == gt:
            if gt == 1:
                pool_tp.append(eid)
            elif gt == 0:
                pool_tn.append(eid)

    pool_all = sorted(pool_tp + pool_tn)
    print(f"Intersection pool size  : {len(pool_all)}")
    print(f"  TP (vulnerable, both correct) : {len(pool_tp)}")
    print(f"  TN (safe, both correct)       : {len(pool_tn)}")
    print(f"  Excluded (parser mismatch)    : {excluded_count}")
    print()

    # Step 4 — verify forced includes
    for eid, info in FORCED_ENTRIES.items():
        expected_list = pool_tp if info["label"] == "TP" else pool_tn
        if eid not in expected_list:
            sys.exit(f"ERROR: Forced entry_id {eid} ({info['label']}) "
                     f"not found in intersection pool")
    print("Forced includes verified in pool:")
    for eid, info in FORCED_ENTRIES.items():
        print(f"  entry_id {eid} — {info['label']}")
    print()

    # Step 5 — stratified random sample remaining 13
    forced_tp = [e for e, i in FORCED_ENTRIES.items() if i["label"] == "TP"]
    forced_tn = [e for e, i in FORCED_ENTRIES.items() if i["label"] == "TN"]
    need_tp = TARGET_TP - len(forced_tp)  # 7
    need_tn = TARGET_TN - len(forced_tn)  # 6

    remaining_tp = [e for e in pool_tp if e not in FORCED_ENTRIES]
    remaining_tn = [e for e in pool_tn if e not in FORCED_ENTRIES]

    if len(remaining_tp) < need_tp:
        sys.exit(f"ERROR: Not enough TP in pool ({len(remaining_tp)}) "
                 f"to sample {need_tp}")
    if len(remaining_tn) < need_tn:
        sys.exit(f"ERROR: Not enough TN in pool ({len(remaining_tn)}) "
                 f"to sample {need_tn}")

    random.seed(42)
    sampled_tp = sorted(random.sample(remaining_tp, need_tp))
    sampled_tn = sorted(random.sample(remaining_tn, need_tn))

    final_tp = sorted(forced_tp + sampled_tp)
    final_tn = sorted(forced_tn + sampled_tn)
    final_all = sorted(final_tp + final_tn)

    print(f"Final 15 snippets (8 TP, 7 TN):")
    for i, eid in enumerate(final_all, 1):
        label = "TP" if eid in final_tp else "TN"
        forced = " [forced]" if eid in FORCED_ENTRIES else ""
        print(f"  snippet {i:2d}: entry_id {eid} — {label}{forced}")
    print()

    # Step 6 — build output rows
    # Prior scores apply only to thinking-mode responses for the original
    # forced entries that had prior Phase A ratings.
    PRIOR_SCORES = {
        eid: info["prior_scores"]
        for eid, info in FORCED_ENTRIES.items()
        if info["prior_scores"]  # non-empty dict
    }

    rows = []
    for snippet_id, eid in enumerate(final_all, 1):
        gt = int(think_data[eid]["ground_truth"])
        gt_label = "vulnerable" if gt == 1 else "safe"

        # Source code from VulTrial dataset
        vul_rec = vuln_ds.get(eid, {})
        source_code = vul_rec.get("func", "")
        cwe = think_data[eid].get("cwe", vul_rec.get("cwe", ""))
        cve_desc = think_data[eid].get("cve_desc", vul_rec.get("cve_desc", ""))

        is_forced = eid in FORCED_ENTRIES

        for resp_id, data_dict in [("think", think_data), ("inst", inst_data)]:
            rec = data_dict[eid]
            response_text = rec.get("reasoning", "")

            # Prior scores only for thinking-mode of entries with prior ratings
            prior = {}
            if resp_id == "think" and eid in PRIOR_SCORES:
                prior = PRIOR_SCORES[eid]

            rows.append({
                "snippet_id": snippet_id,
                "entry_id": eid,
                "ground_truth": gt,
                "ground_truth_label": gt_label,
                "cwe": cwe,
                "cve_desc": cve_desc,
                "source_code": source_code,
                "response_id": resp_id,
                "response_text": response_text,
                "is_forced_include": is_forced,
                "prior_completeness_score": prior.get("completeness", ""),
                "prior_clarity_score": prior.get("clarity", ""),
                "prior_actionability_score": prior.get("actionability", ""),
                "prior_informativeness_score": prior.get("informativeness", ""),
                "completeness_score": "",
                "clarity_score": "",
                "actionability_score": "",
                "informativeness_score": "",
                "rater_notes": "",
            })

    # Shuffle rows (seed=42) to prevent paired think/inst from being adjacent
    random.seed(42)
    random.shuffle(rows)

    # Step 7 — write CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fieldnames = [
        "snippet_id", "entry_id", "ground_truth", "ground_truth_label",
        "cwe", "cve_desc", "source_code", "response_id", "response_text",
        "is_forced_include",
        "prior_completeness_score", "prior_clarity_score",
        "prior_actionability_score", "prior_informativeness_score",
        "completeness_score", "clarity_score",
        "actionability_score", "informativeness_score",
        "rater_notes",
    ]
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Output written to: {OUTPUT_CSV}")
    print(f"  Total rows: {len(rows)}")

    # Summary of prior ratings
    rows_with_prior = sum(1 for r in rows if r["prior_completeness_score"] != "")
    rows_needing_new = len(rows) - rows_with_prior
    print(f"  Rows with prior ratings : {rows_with_prior}")
    print(f"  Rows needing new ratings: {rows_needing_new}")


if __name__ == "__main__":
    main()
