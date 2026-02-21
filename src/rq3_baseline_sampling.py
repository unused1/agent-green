"""
RQ3 Phase A Baseline Sampling: Vulnerability Detection Explanation Quality

Produces a stratified random sample of correct vulnerability-detection predictions
from SA results across both Thinking and Instruct model modes. Each sample includes
the model's explanation/response text for subsequent human rater evaluation of
completeness, clarity, actionability, and informativeness.

Sampling design (16 strata, 48 samples):
  - 4 models × 2 modes (Thinking / Instruct) × 2 prompting (zero / few-shot)
  - 3 samples per stratum

Models:
  - Qwen3-4B, Qwen3-30B-A3B, Nemotron-Nano-8B, Nemotron-Super-49B

Output:
  - results/rq3_baseline/rq3_baseline_samples.csv  (full metadata, for analysis)
  - results/rq3_baseline/rq3_baseline_samples_vulnerability_detection.csv  (same)
  - results/rq3_baseline/rq3_phase_a_rater_sheet.csv  (blinded, randomized, for raters)
  - results/rq3_baseline/rq3_sampling_summary.txt

See docs/RQ3_Baseline_Sampling.md for full methodology documentation.
"""

import csv
import json
import glob
import os
import random
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RANDOM_SEED = 42
SAMPLES_PER_STRATUM = 3
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "results" / "rq3_baseline"
OUTPUT_CSV = OUTPUT_DIR / "rq3_baseline_samples.csv"
OUTPUT_VULN_CSV = OUTPUT_DIR / "rq3_baseline_samples_vulnerability_detection.csv"
OUTPUT_RATER_CSV = OUTPUT_DIR / "rq3_phase_a_rater_sheet.csv"
OUTPUT_SUMMARY = OUTPUT_DIR / "rq3_sampling_summary.txt"

# Ground truth dataset (for source code lookup)
VULN_GT_PATH = PROJECT_ROOT / "vuln_database" / "VulTrial_386_samples_balanced.jsonl"

# CSV columns for output
CSV_COLUMNS = [
    "sample_id",
    "task",
    "model",
    "mode",
    "parameters_b",
    "prompting",
    "entry_id",
    "ground_truth",
    "prediction",
    "is_correct",
    "explanation_text",
    "explanation_length_chars",
    "has_think_close_tag",
    "response_text",
    "truncation_flag",
    # Human rater columns (empty for now)
    "completeness_score",
    "clarity_score",
    "actionability_score",
    "informativeness_score",
    "rater_notes",
]

# Rater-facing CSV columns (blinded — no model/mode/prompting)
RATER_COLUMNS = [
    "sample_id",
    "source_code",
    "ground_truth_label",
    "cwe",
    "cve_desc",
    "response_text",
    # Rater fills these in
    "completeness_score",
    "clarity_score",
    "actionability_score",
    "informativeness_score",
    "rater_notes",
]

# ---------------------------------------------------------------------------
# Stratum definitions
# ---------------------------------------------------------------------------

# Each stratum is a dict with keys:
#   task, model, mode, parameters_b, prompting, results_jsonl

def _find_single(pattern, label):
    """Glob for exactly one file matching pattern; raise if not found."""
    matches = sorted(glob.glob(str(PROJECT_ROOT / pattern)))
    if not matches:
        print(f"  WARNING: no file for {label} (pattern: {pattern})")
        return None
    return matches[0]


def build_strata():
    """Build the list of 16 vulnerability-detection strata (4 models × 2 modes × 2 prompting)."""
    strata = []

    # ----- Vulnerability Detection: Thinking mode -----
    # Qwen Thinking models
    qwen_vuln_thinking = [
        ("results/runpod_rerun/Sa-few_Qwen-Qwen3-4B-Thinking-2507_*_detailed_results.jsonl",
         "Qwen3-4B", 4, "few-shot"),
        ("results/runpod_rerun/Sa-zero_Qwen-Qwen3-4B-Thinking-2507_*_detailed_results.jsonl",
         "Qwen3-4B", 4, "zero-shot"),
        ("results/runpod_rerun/Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_*_detailed_results.jsonl",
         "Qwen3-30B-A3B", 30, "few-shot"),
        # Qwen3-30B zero-shot is in the original runpod dir (rerun only covered few-shot)
        ("results/runpod/thinking_zero_20251020_215332/Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_*_detailed_results.jsonl",
         "Qwen3-30B-A3B", 30, "zero-shot"),
    ]
    for pattern, model, params, prompting in qwen_vuln_thinking:
        jsonl = _find_single(pattern, f"vuln thinking {model} {prompting}")
        if jsonl:
            strata.append(dict(
                task="vulnerability_detection", model=model, mode="thinking",
                parameters_b=params, prompting=prompting, results_jsonl=jsonl,
            ))

    # Nemotron Thinking models
    nemotron_vuln_thinking = [
        ("nemotron_8b_vuln_SA-few_thinking", "Nemotron-Nano-8B", 8, "few-shot"),
        ("nemotron_8b_vuln_SA-zero_thinking", "Nemotron-Nano-8B", 8, "zero-shot"),
        ("nemotron_49b_vuln_SA-few_thinking", "Nemotron-Super-49B", 49, "few-shot"),
        ("nemotron_49b_vuln_SA-zero_thinking", "Nemotron-Super-49B", 49, "zero-shot"),
    ]
    for dirname, model, params, prompting in nemotron_vuln_thinking:
        base = f"results/rq2_cross_architecture/{dirname}"
        jsonl = _find_single(f"{base}/*_detailed_results.jsonl", f"vuln thinking {dirname}")
        if jsonl:
            strata.append(dict(
                task="vulnerability_detection", model=model, mode="thinking",
                parameters_b=params, prompting=prompting, results_jsonl=jsonl,
            ))

    # ----- Vulnerability Detection: Instruct mode -----
    # Qwen Instruct models
    qwen_vuln_instruct = [
        ("results/runpod_rerun/Sa-zero_Qwen-Qwen3-4B-Instruct-2507_*_detailed_results.jsonl",
         "Qwen3-4B", 4, "zero-shot"),
        ("results/runpod_rerun/Sa-few_Qwen-Qwen3-4B-Instruct-2507_*_detailed_results.jsonl",
         "Qwen3-4B", 4, "few-shot"),
        # Qwen3-30B Instruct zero-shot is in the original runpod dir
        ("results/runpod/instruct_zero_20251020_194844/Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_*_detailed_results.jsonl",
         "Qwen3-30B-A3B", 30, "zero-shot"),
        ("results/runpod_rerun/Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_*_detailed_results.jsonl",
         "Qwen3-30B-A3B", 30, "few-shot"),
    ]
    for pattern, model, params, prompting in qwen_vuln_instruct:
        jsonl = _find_single(pattern, f"vuln instruct {model} {prompting}")
        if jsonl:
            strata.append(dict(
                task="vulnerability_detection", model=model, mode="instruct",
                parameters_b=params, prompting=prompting, results_jsonl=jsonl,
            ))

    # Nemotron Instruct models
    nemotron_vuln_instruct = [
        ("nemotron_8b_vuln_SA-zero_instruct", "Nemotron-Nano-8B", 8, "zero-shot"),
        ("nemotron_8b_vuln_SA-few_instruct", "Nemotron-Nano-8B", 8, "few-shot"),
        ("nemotron_49b_vuln_SA-zero_instruct", "Nemotron-Super-49B", 49, "zero-shot"),
        ("nemotron_49b_vuln_SA-few_instruct", "Nemotron-Super-49B", 49, "few-shot"),
    ]
    for dirname, model, params, prompting in nemotron_vuln_instruct:
        base = f"results/rq2_cross_architecture/{dirname}"
        jsonl = _find_single(f"{base}/*_detailed_results.jsonl", f"vuln instruct {dirname}")
        if jsonl:
            strata.append(dict(
                task="vulnerability_detection", model=model, mode="instruct",
                parameters_b=params, prompting=prompting, results_jsonl=jsonl,
            ))

    return strata


# ---------------------------------------------------------------------------
# Prediction extraction
# ---------------------------------------------------------------------------

def parse_vuln_prediction(reasoning):
    """
    Extract vulnerability prediction from reasoning text.
    Mirrors parse_vulnerability_response() in single_agent_vuln_openrouter.py.
    Returns: 1 (vulnerable) or 0 (not vulnerable)

    Fixed 2026-02-22: Reorder NO before YES to prevent "no vulnerability detected"
    matching the YES substring "vulnerability detected". Removed broad fallback
    keywords that matched in negative contexts (e.g., "no buffer overflow detected").
    """
    # Strip think block — parse only the response after </think>
    parse_text = reasoning.split("</think>", 1)[1].strip() if "</think>" in reasoning else reasoning
    response_lower = parse_text.lower()

    # Explicit NO answers (not vulnerable = 0) — checked FIRST to avoid
    # "no vulnerability detected" matching the YES substring "vulnerability detected"
    if any(p in response_lower for p in [
        "final answer: no", "final answer: (2) no", "(2) no",
        "answer: no", "no vulnerability", "no security vulnerability",
        "no, the code",
    ]):
        return 0

    # Explicit YES answers (vulnerable = 1)
    if any(p in response_lower for p in [
        "final answer: yes", "final answer: (1) yes", "(1) yes",
        "answer: yes", "vulnerability detected", "yes, the code",
        "yes: vulnerability",
    ]):
        return 1

    # Fallback keywords — only strong positive indicators
    if any(k in response_lower for k in [
        "is vulnerable", "contains a vulnerability",
        "security vulnerability exists", "can be exploited",
    ]):
        return 1

    return 0  # Default


def extract_thinking_block(text):
    """
    Extract the <think>...</think> block from model output.
    Returns the thinking content (with tags preserved) if present, else the full text.
    """
    # Try to find content between <think> and </think>
    match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
    if match:
        return match.group(0).strip()

    # Some outputs have </think> but no <think> (opening tag stripped)
    match = re.search(r"^(.*?)</think>", text, re.DOTALL)
    if match:
        return match.group(0).strip()

    # No think tags — return full text as the explanation
    return text.strip()


def extract_response_block(text):
    """
    Extract the model's final response after the </think> tag.
    Returns the content after </think> if present, else empty string.
    """
    if "</think>" in text:
        return text.split("</think>", 1)[1].strip()
    return ""


# ---------------------------------------------------------------------------
# Loading and filtering
# ---------------------------------------------------------------------------

def load_vuln_correct(stratum):
    """Load correct vulnerability detection entries (prediction == ground_truth).

    For Thinking mode: explanation_text = thinking block, response_text = post-think response.
    For Instruct mode: explanation_text = "" (no think block), response_text = full reasoning.
    """
    mode = stratum["mode"]
    entries = []
    with open(stratum["results_jsonl"]) as f:
        for line in f:
            entry = json.loads(line)
            gt = entry["ground_truth"]
            pred = parse_vuln_prediction(entry["reasoning"])
            if pred == gt:
                reasoning = entry["reasoning"]
                if mode == "thinking":
                    explanation = extract_thinking_block(reasoning)
                    response = extract_response_block(reasoning)
                    # Some thinking models (e.g. Nemotron-Nano-8B) emit no
                    # <think> tags — the full output is the response.
                    if not response:
                        response = reasoning.strip()
                else:
                    # Instruct mode: no think block; full output is the response
                    explanation = ""
                    response = reasoning.strip()

                entries.append(dict(
                    entry_id=str(entry["idx"]),
                    ground_truth=gt,
                    prediction=pred,
                    is_correct=True,
                    explanation_text=explanation,
                    has_think_close_tag="</think>" in reasoning,
                    response_text=response,
                ))

    return entries


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def compute_truncation_flags(entries):
    """Flag entries below 10th percentile explanation length as potentially truncated."""
    if not entries:
        return
    lengths = [e["explanation_length_chars"] for e in entries]
    lengths_sorted = sorted(lengths)
    p10_idx = max(0, int(len(lengths_sorted) * 0.10) - 1)
    p10_threshold = lengths_sorted[p10_idx]

    for e in entries:
        e["truncation_flag"] = e["explanation_length_chars"] <= p10_threshold


def sample_stratum(stratum, rng, preserve_entry_ids=None):
    """Load correct entries for a stratum, sample, and return records.

    If preserve_entry_ids is given (set of entry_id strings), keep any preserved
    entries that are still in the correct pool and only draw replacements for the
    remaining slots. This avoids disrupting existing human ratings.
    """
    correct_entries = load_vuln_correct(stratum)

    n_available = len(correct_entries)

    if n_available == 0:
        label = f"{stratum['model']}/{stratum['mode']}/{stratum['prompting']}"
        print(f"  WARNING: 0 correct entries for {label}, skipping")
        return [], n_available

    if preserve_entry_ids:
        # Build lookup from entry_id -> correct_entry (deduplicated)
        correct_by_id = {}
        for e in correct_entries:
            if e["entry_id"] not in correct_by_id:
                correct_by_id[e["entry_id"]] = e

        # Rebuild preserved list in ORIGINAL order (from preserve_entry_ids list)
        # so that sample_id assignment matches the original CSV positions
        preserve_set = set(preserve_entry_ids)  # for O(1) membership
        preserved = []
        seen_ids = set()
        for eid in preserve_entry_ids:  # iterate in original sample order
            if eid in correct_by_id and eid not in seen_ids:
                preserved.append(correct_by_id[eid])
                seen_ids.add(eid)

        # Pool for replacements excludes all preserved and duplicate entry_ids
        remaining_pool = [e for e in correct_entries
                          if e["entry_id"] not in preserve_set and e["entry_id"] not in seen_ids]
        # Deduplicate remaining pool by entry_id
        seen_remaining = set()
        deduped_pool = []
        for e in remaining_pool:
            if e["entry_id"] not in seen_remaining:
                deduped_pool.append(e)
                seen_remaining.add(e["entry_id"])
        remaining_pool = deduped_pool

        n_needed = max(0, SAMPLES_PER_STRATUM - len(preserved))
        if n_needed > 0 and remaining_pool:
            new_draws = rng.sample(remaining_pool, min(n_needed, len(remaining_pool)))
            # Insert replacements at the positions of the removed entries
            # Build output: preserved entries stay in their positions, gaps filled by new draws
            sampled = []
            draw_idx = 0
            for eid in preserve_entry_ids:
                if eid in correct_by_id and eid in seen_ids:
                    sampled.append(correct_by_id[eid])
                elif draw_idx < len(new_draws):
                    sampled.append(new_draws[draw_idx])
                    draw_idx += 1
            # Add any remaining draws (shouldn't happen if counts match)
            while draw_idx < len(new_draws):
                sampled.append(new_draws[draw_idx])
                draw_idx += 1
        else:
            sampled = preserved[:SAMPLES_PER_STRATUM]

        n_preserved = min(len(preserved), SAMPLES_PER_STRATUM)
        n_replaced = len(sampled) - n_preserved
        if n_replaced > 0:
            print(f"  Preserved {n_preserved}, drew {n_replaced} replacement(s)")
        else:
            print(f"  All {n_preserved} preserved")
    else:
        n_sample = min(SAMPLES_PER_STRATUM, n_available)
        sampled = rng.sample(correct_entries, n_sample)

    # Enrich with stratum metadata and explanation length
    for entry in sampled:
        entry["task"] = stratum["task"]
        entry["model"] = stratum["model"]
        entry["mode"] = stratum["mode"]
        entry["parameters_b"] = stratum["parameters_b"]
        entry["prompting"] = stratum["prompting"]
        entry["explanation_length_chars"] = len(entry["explanation_text"])

    return sampled, n_available


# ---------------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------------

def generate_summary(all_samples, stratum_info):
    """Generate a text summary of sampling statistics."""
    lines = []
    lines.append("=" * 72)
    lines.append("RQ3 Phase A Baseline Sampling Summary")
    lines.append("=" * 72)
    lines.append(f"Total samples: {len(all_samples)}")
    lines.append(f"Random seed: {RANDOM_SEED}")
    lines.append(f"Target per stratum: {SAMPLES_PER_STRATUM}")
    lines.append("")

    task_samples = all_samples  # All are vulnerability_detection
    lines.append(f"--- vulnerability_detection ({len(task_samples)} samples) ---")

    # Per-stratum
    by_stratum = defaultdict(list)
    for s in task_samples:
        key = f"{s['model']} / {s['mode']} / {s['prompting']}"
        by_stratum[key].append(s)

    for key in sorted(by_stratum.keys()):
        samples = by_stratum[key]
        lengths = [s["explanation_length_chars"] for s in samples]
        trunc = sum(1 for s in samples if s.get("truncation_flag"))
        think_close = sum(1 for s in samples if s["has_think_close_tag"])

        # Find available count from stratum_info
        avail = "?"
        for si in stratum_info:
            si_key = f"{si['model']} / {si['mode']} / {si['prompting']}"
            if si_key == key:
                avail = si["available"]
                break

        lines.append(f"  {key}:")
        lines.append(f"    Sampled: {len(samples)} / {avail} available")
        lines.append(f"    Explanation length (chars): "
                     f"min={min(lengths)}, max={max(lengths)}, "
                     f"mean={mean(lengths):.0f}, median={median(lengths):.0f}")
        lines.append(f"    Has </think> tag: {think_close}/{len(samples)}")
        lines.append(f"    Truncation flags: {trunc}/{len(samples)}")

    lines.append("")

    # Overall length distribution (only meaningful for Thinking strata)
    thinking_samples = [s for s in all_samples if s["mode"] == "thinking"]
    if thinking_samples:
        thinking_lengths = [s["explanation_length_chars"] for s in thinking_samples]
        lines.append("--- Thinking mode explanation length distribution ---")
        lines.append(f"  min={min(thinking_lengths)}, max={max(thinking_lengths)}, "
                     f"mean={mean(thinking_lengths):.0f}, median={median(thinking_lengths):.0f}")
    lines.append("")

    # Response text length distribution (all modes)
    resp_lengths = [len(s["response_text"]) for s in all_samples]
    lines.append("--- Overall response_text length distribution ---")
    lines.append(f"  min={min(resp_lengths)}, max={max(resp_lengths)}, "
                 f"mean={mean(resp_lengths):.0f}, median={median(resp_lengths):.0f}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rater CSV generation
# ---------------------------------------------------------------------------

def load_vuln_ground_truth():
    """Load vulnerability ground truth dataset to get source code and metadata by idx."""
    gt_by_idx = {}
    with open(VULN_GT_PATH) as f:
        for line in f:
            entry = json.loads(line)
            gt_by_idx[str(entry["idx"])] = dict(
                func=entry["func"],
                cwe=", ".join(entry["cwe"]) if isinstance(entry["cwe"], list) else str(entry["cwe"]),
                cve_desc=entry.get("cve_desc", ""),
            )
    return gt_by_idx


def generate_rater_csv(all_samples, rng):
    """Generate a blinded, randomized CSV for human raters.

    Includes source code and vulnerability metadata for context.
    Excludes model identity, mode, prompting, and other internal metadata.
    """
    gt_data = load_vuln_ground_truth()

    # Build rater rows with source code enrichment
    rater_rows = []
    for s in all_samples:
        gt_entry = gt_data.get(s["entry_id"], {})
        gt_label = "vulnerable" if s["ground_truth"] == 1 else "safe"
        rater_rows.append(dict(
            sample_id=s["sample_id"],
            source_code=gt_entry.get("func", ""),
            ground_truth_label=gt_label,
            cwe=gt_entry.get("cwe", "") if s["ground_truth"] == 1 else "",
            cve_desc=gt_entry.get("cve_desc", "") if s["ground_truth"] == 1 else "",
            response_text=s["response_text"],
            completeness_score="",
            clarity_score="",
            actionability_score="",
            informativeness_score="",
            rater_notes="",
        ))

    # Randomize row order (deterministic with seeded RNG)
    rng.shuffle(rater_rows)

    print(f"Writing {len(rater_rows)} rater samples to {OUTPUT_RATER_CSV}")
    with open(OUTPUT_RATER_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RATER_COLUMNS, extrasaction="ignore",
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rater_rows:
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_preserve_entry_ids(preserve_csv):
    """Load entry_ids from an existing samples CSV, grouped by stratum.

    Returns dict mapping (model, mode, prompting) -> list of entry_id strings
    (in original sample_id order, so preserved entries keep their positions).
    """
    csv.field_size_limit(sys.maxsize)
    preserve = defaultdict(list)
    with open(preserve_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["model"], row["mode"], row["prompting"])
            preserve[key].append(row["entry_id"])
    total = sum(len(v) for v in preserve.values())
    print(f"  Loaded {total} entry_ids to preserve from {preserve_csv}\n")
    return preserve


def main():
    import argparse
    parser = argparse.ArgumentParser(description="RQ3 Phase A Baseline Sampling")
    parser.add_argument("--preserve", type=str, default=None,
                        help="Path to previous rq3_baseline_samples.csv to preserve valid samples")
    args = parser.parse_args()

    rng = random.Random(RANDOM_SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load entry_ids to preserve (if requested)
    preserve_map = None
    if args.preserve:
        print(f"Preserve mode: keeping valid samples from {args.preserve}")
        preserve_map = load_preserve_entry_ids(args.preserve)

    print("Building strata...")
    strata = build_strata()
    print(f"  Found {len(strata)} strata\n")

    all_samples = []
    stratum_info = []
    sample_id = 1

    for stratum in strata:
        label = f"{stratum['task']} / {stratum['model']} / {stratum['mode']} / {stratum['prompting']}"
        print(f"Sampling: {label}")

        # Get preserved entry_ids for this stratum (if preserving)
        stratum_key = (stratum["model"], stratum["mode"], stratum["prompting"])
        preserve_ids = preserve_map.get(stratum_key) if preserve_map else None

        sampled, n_available = sample_stratum(stratum, rng, preserve_entry_ids=preserve_ids)
        print(f"  {len(sampled)} sampled from {n_available} correct entries")

        stratum_info.append(dict(
            task=stratum["task"], model=stratum["model"],
            mode=stratum["mode"], prompting=stratum["prompting"],
            available=n_available, sampled=len(sampled),
        ))

        for entry in sampled:
            entry["sample_id"] = sample_id
            sample_id += 1

        all_samples.extend(sampled)

    # Compute truncation flags (10th percentile across all samples)
    compute_truncation_flags(all_samples)

    # Write main CSV (RFC 4180 — Google Sheets handles multi-line quoted fields natively)
    print(f"\nWriting {len(all_samples)} samples to {OUTPUT_CSV}")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore",
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for s in all_samples:
            # Fill empty rater columns
            s.setdefault("completeness_score", "")
            s.setdefault("clarity_score", "")
            s.setdefault("actionability_score", "")
            s.setdefault("informativeness_score", "")
            s.setdefault("rater_notes", "")
            writer.writerow(s)

    # Write task-specific CSV (identical content — vuln only)
    print(f"Writing {len(all_samples)} samples to {OUTPUT_VULN_CSV}")
    with open(OUTPUT_VULN_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore",
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for s in all_samples:
            writer.writerow(s)

    # Write rater-facing CSV (blinded, randomized, with source code)
    rater_rng = random.Random(RANDOM_SEED + 1)  # Separate seed for shuffle
    generate_rater_csv(all_samples, rater_rng)

    # Write summary
    summary = generate_summary(all_samples, stratum_info)
    print(f"Writing summary to {OUTPUT_SUMMARY}")
    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
        f.write(summary)

    print("\n" + summary)

    # Verification checks
    print("\n" + "=" * 72)
    print("VERIFICATION CHECKS")
    print("=" * 72)

    # Check for duplicates within strata (same entry_id in same model/mode/prompting is a bug)
    ids = [(s["model"], s["mode"], s["prompting"], s["entry_id"]) for s in all_samples]
    dupes = len(ids) - len(set(ids))
    print(f"Duplicate entries (within strata): {dupes}")

    # Check for empty response_text (this is what raters evaluate)
    empty_resp = sum(1 for s in all_samples if not s["response_text"].strip())
    print(f"Empty response_text: {empty_resp}")

    # Check all is_correct
    all_correct = all(s["is_correct"] for s in all_samples)
    print(f"All is_correct=True: {all_correct}")

    # Check strata count
    strata_keys = set((s["model"], s["mode"], s["prompting"]) for s in all_samples)
    print(f"Strata represented: {len(strata_keys)} / 16")

    # Check total sample count
    print(f"Total samples: {len(all_samples)} (expected 48)")

    # Check mode column present
    has_mode = all("mode" in s for s in all_samples)
    print(f"All samples have 'mode' field: {has_mode}")

    # Check explanation_text empty for Instruct, populated for Thinking
    instruct_empty = all(s["explanation_text"] == "" for s in all_samples if s["mode"] == "instruct")
    thinking_populated = all(s["explanation_text"] != "" for s in all_samples if s["mode"] == "thinking")
    print(f"Instruct explanation_text all empty: {instruct_empty}")
    print(f"Thinking explanation_text all populated: {thinking_populated}")

    if dupes > 0 or empty_resp > 0 or not all_correct:
        print("WARNING: Verification issues found!")
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
