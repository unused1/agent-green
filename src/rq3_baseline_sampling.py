"""
RQ3 Baseline Sampling: Explanation Usefulness & Faithfulness from Existing Results

Produces a stratified random sample of correct predictions from SA thinking-model
results across all 3 SE tasks (code generation, vulnerability detection, log
analysis). Each sample includes the model's explanation text for subsequent human
rater review of usefulness and faithfulness.

Sampling design (20 strata, 200 samples):
  - Code Generation: All 4 thinking models × 2 prompting
    8 strata × 10 = 80 samples
    (Qwen codegen rerun 2026-02-07 recovered missing thinking content)
  - Vulnerability Detection: All 4 thinking models × 2 prompting
    8 strata × 10 = 80 samples
  - Log Analysis: Qwen 4B + 30B × 2 prompting
    4 strata × 10 = 40 samples  (4B strata have 10-11 available)

Output:
  - results/rq3_baseline/rq3_baseline_samples.csv
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
SAMPLES_PER_STRATUM = 10
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "results" / "rq3_baseline"
OUTPUT_CSV = OUTPUT_DIR / "rq3_baseline_samples.csv"
OUTPUT_SUMMARY = OUTPUT_DIR / "rq3_sampling_summary.txt"

# Ground truth for log analysis
LOG_GT_PATH = PROJECT_ROOT / "data" / "HDFS_anomaly_label_385_session_sampled.csv"

# Minimum explanation length (chars) to filter out non-responses like "No response from agent"
MIN_EXPLANATION_LENGTH = 100

# CSV columns for output
CSV_COLUMNS = [
    "sample_id",
    "task",
    "model",
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
    "usefulness_score",
    "faithfulness_score",
    "rater_notes",
]

# ---------------------------------------------------------------------------
# Stratum definitions
# ---------------------------------------------------------------------------

# Each stratum is a dict with keys:
#   task, model, parameters_b, prompting, results_jsonl, eval_json (codegen only)

def _find_single(pattern, label):
    """Glob for exactly one file matching pattern; raise if not found."""
    matches = sorted(glob.glob(str(PROJECT_ROOT / pattern)))
    if not matches:
        print(f"  WARNING: no file for {label} (pattern: {pattern})")
        return None
    return matches[0]


def build_strata():
    """Build the list of strata to sample from."""
    strata = []

    # ----- Code Generation -----
    # Qwen models (rerun 2026-02-07 with reasoning field)
    qwen_code_files = [
        ("results/runpod_codegen_rerun/SA-few_Qwen-Qwen3-4B-Thinking-2507_*_detailed_results.jsonl",
         "results/runpod_codegen_rerun/SA-few_Qwen-Qwen3-4B-Thinking-2507_*_detailed_results_evaluation.json",
         "Qwen3-4B-Thinking", 4, "few-shot"),
        ("results/runpod_codegen_rerun/SA-zero_Qwen-Qwen3-4B-Thinking-2507_*_detailed_results.jsonl",
         "results/runpod_codegen_rerun/SA-zero_Qwen-Qwen3-4B-Thinking-2507_*_detailed_results_evaluation.json",
         "Qwen3-4B-Thinking", 4, "zero-shot"),
        ("results/runpod_codegen_rerun/SA-few_Qwen-Qwen3-30B-A3B-Thinking-2507_*_detailed_results.jsonl",
         "results/runpod_codegen_rerun/SA-few_Qwen-Qwen3-30B-A3B-Thinking-2507_*_detailed_results_evaluation.json",
         "Qwen3-30B-A3B-Thinking", 30, "few-shot"),
        ("results/runpod_codegen_rerun/SA-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_*_detailed_results.jsonl",
         "results/runpod_codegen_rerun/SA-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_*_detailed_results_evaluation.json",
         "Qwen3-30B-A3B-Thinking", 30, "zero-shot"),
    ]
    for jsonl_pat, eval_pat, model, params, prompting in qwen_code_files:
        jsonl = _find_single(jsonl_pat, f"codegen {model} {prompting}")
        evaljson = _find_single(eval_pat, f"codegen eval {model} {prompting}")
        if jsonl and evaljson:
            strata.append(dict(
                task="code_generation", model=model, parameters_b=params,
                prompting=prompting, results_jsonl=jsonl, eval_json=evaljson,
            ))

    # Nemotron models
    nemotron_code_dirs = [
        ("nemotron_8b_code_SA-few_thinking", "Nemotron-Nano-8B", 8, "few-shot"),
        ("nemotron_8b_code_SA-zero_thinking", "Nemotron-Nano-8B", 8, "zero-shot"),
        ("nemotron_49b_code_SA-few_thinking", "Nemotron-Super-49B", 49, "few-shot"),
        ("nemotron_49b_code_SA-zero_thinking", "Nemotron-Super-49B", 49, "zero-shot"),
    ]
    for dirname, model, params, prompting in nemotron_code_dirs:
        base = f"results/rq2_cross_architecture/{dirname}"
        jsonl = _find_single(f"{base}/*_detailed_results.jsonl", f"codegen {dirname}")
        evaljson = _find_single(f"{base}/*_evaluation.json", f"codegen eval {dirname}")
        if jsonl and evaljson:
            strata.append(dict(
                task="code_generation", model=model, parameters_b=params,
                prompting=prompting, results_jsonl=jsonl, eval_json=evaljson,
            ))

    # ----- Vulnerability Detection -----
    # Qwen models (runpod_rerun for few-shot reruns, runpod for original zero-shot)
    qwen_vuln_files = [
        ("results/runpod_rerun/Sa-few_Qwen-Qwen3-4B-Thinking-2507_*_detailed_results.jsonl",
         "Qwen3-4B-Thinking", 4, "few-shot"),
        ("results/runpod_rerun/Sa-zero_Qwen-Qwen3-4B-Thinking-2507_*_detailed_results.jsonl",
         "Qwen3-4B-Thinking", 4, "zero-shot"),
        ("results/runpod_rerun/Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_*_detailed_results.jsonl",
         "Qwen3-30B-A3B-Thinking", 30, "few-shot"),
        # Qwen3-30B zero-shot is in the original runpod dir (rerun only covered few-shot)
        ("results/runpod/thinking_zero_20251020_215332/Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_*_detailed_results.jsonl",
         "Qwen3-30B-A3B-Thinking", 30, "zero-shot"),
    ]
    for pattern, model, params, prompting in qwen_vuln_files:
        jsonl = _find_single(pattern, f"vuln {model} {prompting}")
        if jsonl:
            strata.append(dict(
                task="vulnerability_detection", model=model, parameters_b=params,
                prompting=prompting, results_jsonl=jsonl,
            ))

    # Nemotron models (rq2_cross_architecture)
    nemotron_vuln_dirs = [
        ("nemotron_8b_vuln_SA-few_thinking", "Nemotron-Nano-8B", 8, "few-shot"),
        ("nemotron_8b_vuln_SA-zero_thinking", "Nemotron-Nano-8B", 8, "zero-shot"),
        ("nemotron_49b_vuln_SA-few_thinking", "Nemotron-Super-49B", 49, "few-shot"),
        ("nemotron_49b_vuln_SA-zero_thinking", "Nemotron-Super-49B", 49, "zero-shot"),
    ]
    for dirname, model, params, prompting in nemotron_vuln_dirs:
        base = f"results/rq2_cross_architecture/{dirname}"
        jsonl = _find_single(f"{base}/*_detailed_results.jsonl", f"vuln {dirname}")
        if jsonl:
            strata.append(dict(
                task="vulnerability_detection", model=model, parameters_b=params,
                prompting=prompting, results_jsonl=jsonl,
            ))

    # ----- Log Analysis (Qwen 4B + 30B only) -----
    log_dirs = [
        ("SA-zero_Qwen3-4B-Thinking", "Qwen3-4B-Thinking", 4, "zero-shot"),
        ("SA-few_Qwen3-4B-Thinking", "Qwen3-4B-Thinking", 4, "few-shot"),
        ("SA-zero_Qwen3-30B-Thinking", "Qwen3-30B-A3B-Thinking", 30, "zero-shot"),
        ("SA-few_Qwen3-30B-Thinking", "Qwen3-30B-A3B-Thinking", 30, "few-shot"),
    ]
    for dirname, model, params, prompting in log_dirs:
        base = f"results/runpod_log_analysis/{dirname}"
        jsonl = _find_single(f"{base}/*_detailed_results.jsonl", f"log {dirname}")
        metrics_csv = _find_single(f"{base}/*_per_session_metrics.csv", f"log metrics {dirname}")
        if jsonl and metrics_csv:
            strata.append(dict(
                task="log_analysis", model=model, parameters_b=params,
                prompting=prompting, results_jsonl=jsonl, metrics_csv=metrics_csv,
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
    """
    # Strip think block — parse only the response after </think>
    parse_text = reasoning.split("</think>", 1)[1].strip() if "</think>" in reasoning else reasoning
    response_lower = parse_text.lower()

    # Explicit YES answers (vulnerable = 1)
    if any(p in response_lower for p in [
        "final answer: yes", "final answer: (1) yes", "(1) yes",
        "answer: yes", "vulnerability detected", "yes, the code",
        "yes: vulnerability",
    ]):
        return 1

    # Explicit NO answers (not vulnerable = 0)
    if any(p in response_lower for p in [
        "final answer: no", "final answer: (2) no", "(2) no",
        "answer: no", "no vulnerability", "no security vulnerability",
        "no, the code",
    ]):
        return 0

    # Fallback keywords
    if any(k in response_lower for k in [
        "is vulnerable", "contains a vulnerability",
        "security vulnerability exists", "security risk",
        "can be exploited", "buffer overflow", "memory leak",
        "sql injection", "xss", "race condition",
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
# Loading and filtering functions
# ---------------------------------------------------------------------------

def load_codegen_correct(stratum):
    """Load correct code generation entries (passed test cases)."""
    # Load evaluation results to get pass/fail per task_id
    with open(stratum["eval_json"]) as f:
        eval_data = json.load(f)

    passed_ids = set()
    for r in eval_data["per_sample_results"]:
        if r["passed"]:
            passed_ids.add(r["task_id"])

    # Load detailed results to get reasoning text
    entries = []
    with open(stratum["results_jsonl"]) as f:
        for line in f:
            entry = json.loads(line)
            if entry["task_id"] in passed_ids:
                reasoning = entry.get("reasoning", "")
                explanation = extract_thinking_block(reasoning) if reasoning else ""
                if not explanation:
                    continue  # Skip entries with no explanation
                response = extract_response_block(reasoning)
                entries.append(dict(
                    entry_id=entry["task_id"],
                    ground_truth="passed",
                    prediction="passed",
                    is_correct=True,
                    explanation_text=explanation,
                    has_think_close_tag="</think>" in reasoning,
                    response_text=response,
                ))

    return entries


def load_vuln_correct(stratum):
    """Load correct vulnerability detection entries (prediction == ground_truth)."""
    entries = []
    with open(stratum["results_jsonl"]) as f:
        for line in f:
            entry = json.loads(line)
            gt = entry["ground_truth"]
            pred = parse_vuln_prediction(entry["reasoning"])
            if pred == gt:
                reasoning = entry["reasoning"]
                explanation = extract_thinking_block(reasoning)
                if len(explanation) < MIN_EXPLANATION_LENGTH:
                    continue  # Skip non-responses (e.g., "No response from agent")
                response = extract_response_block(reasoning)
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


def load_log_correct(stratum):
    """Load correct log analysis entries using pre-computed per_session_metrics."""
    # Load per-session metrics to identify TP and TN
    correct_blocks = {}
    with open(stratum["metrics_csv"]) as f:
        for row in csv.DictReader(f):
            if row["result"] in ("TP", "TN"):
                correct_blocks[row["block_id"]] = dict(
                    ground_truth=int(row["ground_truth"]),
                    prediction=int(row["prediction"]),
                )

    # Load detailed results to get raw_output
    entries = []
    with open(stratum["results_jsonl"]) as f:
        for line in f:
            entry = json.loads(line)
            block_id = entry["block_id"]
            if block_id in correct_blocks:
                raw_output = entry["raw_output"]
                # Skip entries with no actual model output (e.g., "NONE")
                if not raw_output or raw_output.strip().upper() == "NONE":
                    continue
                explanation = extract_thinking_block(raw_output)
                if not explanation:
                    continue
                response = extract_response_block(raw_output)
                entries.append(dict(
                    entry_id=block_id,
                    ground_truth=correct_blocks[block_id]["ground_truth"],
                    prediction=correct_blocks[block_id]["prediction"],
                    is_correct=True,
                    explanation_text=explanation,
                    has_think_close_tag="</think>" in raw_output,
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


def sample_stratum(stratum, rng):
    """Load correct entries for a stratum, sample, and return records."""
    task = stratum["task"]
    loaders = {
        "code_generation": load_codegen_correct,
        "vulnerability_detection": load_vuln_correct,
        "log_analysis": load_log_correct,
    }
    correct_entries = loaders[task](stratum)

    n_available = len(correct_entries)
    n_sample = min(SAMPLES_PER_STRATUM, n_available)

    if n_available == 0:
        label = f"{task}/{stratum['model']}/{stratum['prompting']}"
        print(f"  WARNING: 0 correct entries for {label}, skipping")
        return [], n_available

    sampled = rng.sample(correct_entries, n_sample)

    # Enrich with stratum metadata and explanation length
    for entry in sampled:
        entry["task"] = task
        entry["model"] = stratum["model"]
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
    lines.append("RQ3 Baseline Sampling Summary")
    lines.append("=" * 72)
    lines.append(f"Total samples: {len(all_samples)}")
    lines.append(f"Random seed: {RANDOM_SEED}")
    lines.append(f"Target per stratum: {SAMPLES_PER_STRATUM}")
    lines.append("")

    # Per-task summary
    by_task = defaultdict(list)
    for s in all_samples:
        by_task[s["task"]].append(s)

    for task in ["code_generation", "vulnerability_detection", "log_analysis"]:
        task_samples = by_task.get(task, [])
        lines.append(f"--- {task} ({len(task_samples)} samples) ---")

        # Per-stratum
        by_stratum = defaultdict(list)
        for s in task_samples:
            key = f"{s['model']} / {s['prompting']}"
            by_stratum[key].append(s)

        for key in sorted(by_stratum.keys()):
            samples = by_stratum[key]
            lengths = [s["explanation_length_chars"] for s in samples]
            trunc = sum(1 for s in samples if s.get("truncation_flag"))
            think_close = sum(1 for s in samples if s["has_think_close_tag"])

            # Find available count from stratum_info
            avail = "?"
            for si in stratum_info:
                si_key = f"{si['model']} / {si['prompting']}"
                if si_key == key and si["task"] == task:
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

    # Overall length distribution
    all_lengths = [s["explanation_length_chars"] for s in all_samples]
    lines.append("--- Overall explanation length distribution ---")
    lines.append(f"  min={min(all_lengths)}, max={max(all_lengths)}, "
                 f"mean={mean(all_lengths):.0f}, median={median(all_lengths):.0f}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    rng = random.Random(RANDOM_SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Building strata...")
    strata = build_strata()
    print(f"  Found {len(strata)} strata\n")

    all_samples = []
    stratum_info = []
    sample_id = 1

    for stratum in strata:
        label = f"{stratum['task']} / {stratum['model']} / {stratum['prompting']}"
        print(f"Sampling: {label}")
        sampled, n_available = sample_stratum(stratum, rng)
        print(f"  {len(sampled)} sampled from {n_available} correct entries")

        stratum_info.append(dict(
            task=stratum["task"], model=stratum["model"],
            prompting=stratum["prompting"], available=n_available,
            sampled=len(sampled),
        ))

        for entry in sampled:
            entry["sample_id"] = sample_id
            sample_id += 1

        all_samples.extend(sampled)

    # Compute truncation flags per task (10th percentile within each task)
    by_task = defaultdict(list)
    for s in all_samples:
        by_task[s["task"]].append(s)
    for task_samples in by_task.values():
        compute_truncation_flags(task_samples)

    # Write CSV
    print(f"\nWriting {len(all_samples)} samples to {OUTPUT_CSV}")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for s in all_samples:
            # Fill empty rater columns
            s.setdefault("usefulness_score", "")
            s.setdefault("faithfulness_score", "")
            s.setdefault("rater_notes", "")
            writer.writerow(s)

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

    # Check for duplicates within strata (same entry_id in same model/prompting is a bug)
    ids = [(s["task"], s["model"], s["prompting"], s["entry_id"]) for s in all_samples]
    dupes = len(ids) - len(set(ids))
    print(f"Duplicate entries (within strata): {dupes}")

    # Check for empty explanations
    empty = sum(1 for s in all_samples if not s["explanation_text"].strip())
    print(f"Empty explanations: {empty}")

    # Check all is_correct
    all_correct = all(s["is_correct"] for s in all_samples)
    print(f"All is_correct=True: {all_correct}")

    if dupes > 0 or empty > 0 or not all_correct:
        print("WARNING: Verification issues found!")
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
