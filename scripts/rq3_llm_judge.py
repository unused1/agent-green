"""
LLM-as-Judge pipeline for RQ3 explanation quality evaluation.

Modes:
    --mode calibrate  Select 8 calibration + 22 validation samples, build prompt
    --mode validate   Run judge on 22 held-out, check Spearman >= 0.7, MAE <= 1.0
    --mode evaluate   Run judge on full pool (~487 Super-49B or ~534 Qwen3-30B)
    --mode spot-check Generate 10% stratified sample for human verification

Usage:
    export OPENROUTER_API_KEY=<key>
    python scripts/rq3_llm_judge.py --mode calibrate
    python scripts/rq3_llm_judge.py --mode validate [--iteration N]
    python scripts/rq3_llm_judge.py --mode evaluate --model super49b
    python scripts/rq3_llm_judge.py --mode spot-check --model super49b
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

csv.field_size_limit(sys.maxsize)

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "results", "rq3_baseline")
CONSENSUS_CSV = os.path.join(OUTPUT_DIR, "super49b_zero_consensus_scores.csv")
CONSOLIDATED_CSV = os.path.join(PROJECT_ROOT, "results", "consolidated_performance.csv")
RATER_INSTRUCTIONS_MD = os.path.join(PROJECT_ROOT, "docs", "RQ3_Rater_Instructions.md")
RATER_SHEET_CSV = os.path.join(OUTPUT_DIR, "super49b_zero_rater_sheet.csv")
MASTER_CSV = os.path.join(OUTPUT_DIR, "super49b_zero_human_rating_set.csv")

DIMENSIONS = ["completeness", "clarity", "actionability", "informativeness"]
STRATA = ["think-TP", "think-TN", "inst-TP", "inst-TN"]

# Judge model — independent family from study models (Qwen/Nemotron)
DEFAULT_JUDGE_MODEL = "anthropic/claude-sonnet-4"
JUDGE_MODEL = os.getenv("RQ3_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")

# Validation thresholds
MIN_SPEARMAN = 0.7
MAX_MAE = 1.0
MAX_BIAS = 0.5
MAX_ITERATIONS = 3

# Rate limiting
REQUEST_DELAY_SECONDS = 1.0


# ---------------------------------------------------------------------------
# Rubric text (extracted from docs/RQ3_Rater_Instructions.md Sections 4-5)
# ---------------------------------------------------------------------------
def load_rubric_text() -> str:
    """Load rubric sections 4 and 5 from the rater instructions markdown."""
    with open(RATER_INSTRUCTIONS_MD) as f:
        content = f.read()

    # Extract Section 4 (Scoring Rubric) through Section 5 (Evaluation Indicators)
    # up to Section 6 (General Guidelines)
    match = re.search(
        r"(## 4\. Scoring Rubric.*?)(?=## 6\. General Guidelines)",
        content,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    # Fallback: return sections 4-5
    match = re.search(r"(## 4\. Scoring Rubric.*)", content, re.DOTALL)
    return match.group(1).strip() if match else ""


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------
def load_consensus_scores() -> pd.DataFrame:
    """Load consensus scores with metadata."""
    return pd.read_csv(CONSENSUS_CSV)


def find_source_files(model_key: str) -> tuple:
    """Find thinking and instruct JSONL paths for a model from consolidated CSV.

    Args:
        model_key: 'super49b' or 'qwen30b'

    Returns:
        (thinking_jsonl_path, instruct_jsonl_path)
    """
    model_map = {
        "super49b": "Nemotron-Super-49B",
        "qwen30b": "Qwen3-30B-A3B",
    }
    model_name = model_map.get(model_key)
    if not model_name:
        sys.exit(f"ERROR: Unknown model key '{model_key}'. Use 'super49b' or 'qwen30b'.")

    think_path = None
    inst_path = None
    with open(CONSOLIDATED_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row["model"] == model_name
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
        sys.exit(f"ERROR: Could not find JSONL paths for {model_name}")
    return think_path, inst_path


def load_jsonl(path: str) -> dict:
    """Load JSONL, returning {idx: record}."""
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


def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> block from response text."""
    # Handle full tags
    text = re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL)
    # Handle opening-tag-stripped format (content</think>)
    if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()
    return text


def prepare_rater_response_text(response_text: str, response_id: str) -> str:
    """Prepare the response text as shown to raters.

    For thinking mode: strip <think> blocks.
    For instruct mode: use as-is.
    """
    if response_id == "think":
        return strip_think_tags(response_text)
    return response_text


# ---------------------------------------------------------------------------
# OpenRouter API
# ---------------------------------------------------------------------------
def call_llm_judge(
    system_prompt: str,
    user_prompt: str,
    model: str = None,
    temperature: float = 0.0,
    max_retries: int = 3,
) -> Optional[str]:
    """Call the LLM judge via OpenRouter API.

    Returns the assistant's response text, or None on failure.
    """
    try:
        import openai
    except ImportError:
        sys.exit("ERROR: openai package required. Install with: pip install openai")

    if not OPENROUTER_API_KEY:
        sys.exit("ERROR: OPENROUTER_API_KEY environment variable not set")

    model = model or JUDGE_MODEL
    client = openai.OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_API_BASE,
    )

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  API error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
    return None


def parse_judge_response(response_text: str) -> Optional[dict]:
    """Parse LLM judge response to extract scores and justifications.

    Expected JSON format:
    {
        "completeness_score": N,
        "completeness_justification": "...",
        "clarity_score": N,
        "clarity_justification": "...",
        "actionability_score": N,
        "actionability_justification": "...",
        "informativeness_score": N,
        "informativeness_justification": "..."
    }
    """
    if not response_text:
        return None

    # Try to extract JSON from response (may be wrapped in markdown code blocks)
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        # Try to find raw JSON object
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if json_match:
            json_str = json_match.group(0)
        else:
            return None

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return None

    # Validate all required fields
    result = {}
    for dim in DIMENSIONS:
        score_key = f"{dim}_score"
        just_key = f"{dim}_justification"
        score = data.get(score_key)
        if score is None:
            # Try alternative key formats
            score = data.get(dim)
        if score is None or not isinstance(score, (int, float)):
            return None
        score = int(round(score))
        if score < 1 or score > 5:
            return None
        result[score_key] = score
        result[just_key] = data.get(just_key, data.get(f"{dim}_reasoning", ""))
    return result


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------
def build_system_prompt(rubric_text: str) -> str:
    """Build the system prompt for the LLM judge."""
    return f"""You are an expert evaluator assessing the quality of AI-generated vulnerability analyses. Your task is to score each analysis on four dimensions using a 1-5 Likert scale, following the rubric below.

IMPORTANT GUIDELINES:
- Score each dimension independently. A response can score high on one dimension and low on another.
- Use the full 1-5 range. Do not cluster all scores around 3-4.
- Do not adjust scores based on response length alone.
- For safe code samples, low actionability (1-2) is expected — this is not a deficiency.
- Focus on substance and technical accuracy, not formatting.

{rubric_text}

OUTPUT FORMAT:
Respond with a JSON object containing scores and justifications for each dimension:
```json
{{
    "completeness_score": <1-5>,
    "completeness_justification": "<brief justification>",
    "clarity_score": <1-5>,
    "clarity_justification": "<brief justification>",
    "actionability_score": <1-5>,
    "actionability_justification": "<brief justification>",
    "informativeness_score": <1-5>,
    "informativeness_justification": "<brief justification>"
}}
```

Provide ONLY the JSON object. Do not include any other text."""


def build_few_shot_block(calibration_samples: pd.DataFrame) -> str:
    """Build few-shot examples block from calibration samples."""
    blocks = []
    for i, (_, row) in enumerate(calibration_samples.iterrows(), 1):
        # Load the response text from the rater sheet
        source_code = row.get("source_code", "[source code not available]")
        response_text = row.get("response_text", "[response text not available]")
        gt_label = row["ground_truth_label"]

        scores = {}
        for dim in DIMENSIONS:
            scores[dim] = row[f"{dim}_consensus"]

        block = f"""--- Example {i} ---
Ground truth: {gt_label}
Stratum: {row['stratum']}

Source code:
```
{source_code[:3000]}
```

AI response to evaluate:
\"\"\"
{response_text[:5000]}
\"\"\"

Correct scores:
{{
    "completeness_score": {scores['completeness']},
    "clarity_score": {scores['clarity']},
    "actionability_score": {scores['actionability']},
    "informativeness_score": {scores['informativeness']}
}}
"""
        blocks.append(block)

    return "\n".join(blocks)


def build_evaluation_prompt(
    source_code: str,
    response_text: str,
    ground_truth_label: str,
    cwe: str = "",
    cve_desc: str = "",
) -> str:
    """Build the user prompt for evaluating a single response."""
    context = f"Ground truth: {ground_truth_label}"
    if cwe and ground_truth_label == "vulnerable":
        context += f"\nCWE: {cwe}"
    if cve_desc and ground_truth_label == "vulnerable":
        context += f"\nCVE description: {cve_desc}"

    return f"""{context}

Source code:
```
{source_code}
```

AI response to evaluate:
\"\"\"
{response_text}
\"\"\"

Score this response on the four dimensions. Respond with JSON only."""


# ---------------------------------------------------------------------------
# Mode: calibrate
# ---------------------------------------------------------------------------
def mode_calibrate(iteration: int = 1):
    """Select calibration/validation split and build prompt template."""
    print(f"=== CALIBRATION (iteration {iteration}) ===\n")

    consensus_df = load_consensus_scores()
    print(f"Loaded {len(consensus_df)} consensus scores")

    if "stratum" not in consensus_df.columns:
        sys.exit("ERROR: consensus scores missing 'stratum' column. Run IRR script first.")

    # Load response text from rater sheet for few-shot examples
    rater_sheet = pd.read_csv(RATER_SHEET_CSV)
    # Join response text and source code to consensus by sample_id
    consensus_df = consensus_df.merge(
        rater_sheet[["sample_id", "source_code", "response_text"]],
        on="sample_id",
        how="left",
    )

    # Select 2 calibration samples per stratum (highest + lowest mean consensus)
    consensus_df["mean_consensus"] = consensus_df[
        [f"{d}_consensus" for d in DIMENSIONS]
    ].mean(axis=1)

    calibration_ids = []
    for stratum in STRATA:
        sub = consensus_df[consensus_df["stratum"] == stratum].copy()
        if len(sub) < 2:
            print(f"  WARNING: stratum {stratum} has only {len(sub)} samples")
            calibration_ids.extend(sub["sample_id"].tolist())
            continue
        # Pick highest and lowest mean consensus
        sorted_sub = sub.sort_values("mean_consensus")
        calibration_ids.append(sorted_sub.iloc[0]["sample_id"])  # lowest
        calibration_ids.append(sorted_sub.iloc[-1]["sample_id"])  # highest

    calibration_df = consensus_df[consensus_df["sample_id"].isin(calibration_ids)].copy()
    validation_df = consensus_df[~consensus_df["sample_id"].isin(calibration_ids)].copy()

    print(f"\nCalibration set: {len(calibration_df)} samples")
    for _, row in calibration_df.iterrows():
        mean_score = row["mean_consensus"]
        print(f"  sample_id={int(row['sample_id']):2d} stratum={row['stratum']:10s} "
              f"mean_consensus={mean_score:.2f}")

    print(f"\nValidation set: {len(validation_df)} samples")

    # Build prompt
    rubric_text = load_rubric_text()
    system_prompt = build_system_prompt(rubric_text)
    few_shot_block = build_few_shot_block(calibration_df)

    # Full prompt = system + few-shot
    full_prompt = f"{system_prompt}\n\n## CALIBRATION EXAMPLES\n\n{few_shot_block}"

    # Save prompt
    prompt_path = os.path.join(OUTPUT_DIR, f"llm_judge_prompt_v{iteration}.txt")
    with open(prompt_path, "w") as f:
        f.write(full_prompt)
    print(f"\nPrompt saved: {prompt_path}")
    print(f"Prompt length: {len(full_prompt)} chars")

    # Save calibration/validation split
    split_path = os.path.join(OUTPUT_DIR, f"llm_judge_split_v{iteration}.csv")
    split_data = []
    for _, row in consensus_df.iterrows():
        split_data.append({
            "sample_id": int(row["sample_id"]),
            "entry_id": int(row["entry_id"]) if pd.notna(row["entry_id"]) else "",
            "response_id": row["response_id"],
            "stratum": row["stratum"],
            "set": "calibration" if row["sample_id"] in calibration_ids else "validation",
            "mean_consensus": round(row["mean_consensus"], 2),
        })
    pd.DataFrame(split_data).to_csv(split_path, index=False)
    print(f"Split saved: {split_path}")

    return calibration_ids


# ---------------------------------------------------------------------------
# Mode: validate
# ---------------------------------------------------------------------------
def mode_validate(iteration: int = 1):
    """Run judge on validation set and check agreement metrics."""
    print(f"=== VALIDATION (iteration {iteration}) ===\n")

    # Load split
    split_path = os.path.join(OUTPUT_DIR, f"llm_judge_split_v{iteration}.csv")
    if not os.path.exists(split_path):
        sys.exit(f"ERROR: Split file not found: {split_path}\n"
                 f"Run --mode calibrate --iteration {iteration} first.")
    split_df = pd.read_csv(split_path)
    validation_ids = split_df[split_df["set"] == "validation"]["sample_id"].tolist()

    # Load prompt
    prompt_path = os.path.join(OUTPUT_DIR, f"llm_judge_prompt_v{iteration}.txt")
    if not os.path.exists(prompt_path):
        sys.exit(f"ERROR: Prompt file not found: {prompt_path}")
    with open(prompt_path) as f:
        system_prompt = f.read()

    # Load consensus scores and rater sheet
    consensus_df = load_consensus_scores()
    rater_sheet = pd.read_csv(RATER_SHEET_CSV)
    consensus_df = consensus_df.merge(
        rater_sheet[["sample_id", "source_code", "response_text", "cwe", "cve_desc",
                      "ground_truth_label"]],
        on="sample_id",
        how="left",
    )

    validation_df = consensus_df[consensus_df["sample_id"].isin(validation_ids)].copy()
    print(f"Validation samples: {len(validation_df)}")
    print(f"Judge model: {JUDGE_MODEL}")
    print()

    # Run judge on each validation sample
    results = []
    for i, (_, row) in enumerate(validation_df.iterrows(), 1):
        sid = int(row["sample_id"])
        print(f"  [{i}/{len(validation_df)}] sample_id={sid} "
              f"stratum={row['stratum']} ... ", end="", flush=True)

        user_prompt = build_evaluation_prompt(
            source_code=row["source_code"],
            response_text=row["response_text"],
            ground_truth_label=row["ground_truth_label"],
            cwe=str(row.get("cwe", "")),
            cve_desc=str(row.get("cve_desc", "")),
        )

        response = call_llm_judge(system_prompt, user_prompt)
        parsed = parse_judge_response(response) if response else None

        if parsed:
            result = {"sample_id": sid, "stratum": row["stratum"]}
            for dim in DIMENSIONS:
                result[f"{dim}_human"] = row[f"{dim}_consensus"]
                result[f"{dim}_llm"] = parsed[f"{dim}_score"]
                result[f"{dim}_justification"] = parsed[f"{dim}_justification"]
            results.append(result)
            llm_scores = [parsed[f"{d}_score"] for d in DIMENSIONS]
            print(f"scores={llm_scores}")
        else:
            print("FAILED to parse response")
            if response:
                print(f"    Raw response: {response[:200]}...")

        time.sleep(REQUEST_DELAY_SECONDS)

    if not results:
        sys.exit("ERROR: No valid results from validation run")

    results_df = pd.DataFrame(results)

    # Compute validation metrics
    print(f"\n{'=' * 60}")
    print("VALIDATION METRICS")
    print(f"{'=' * 60}")

    metrics = {}
    all_pass = True
    for dim in DIMENSIONS:
        human = results_df[f"{dim}_human"].values
        llm = results_df[f"{dim}_llm"].values

        rho, rho_p = spearmanr(human, llm)
        mae = np.mean(np.abs(human - llm))
        bias = np.mean(llm - human)  # positive = LLM scores higher

        pass_rho = rho >= MIN_SPEARMAN
        pass_mae = mae <= MAX_MAE
        pass_bias = abs(bias) <= MAX_BIAS
        dim_pass = pass_rho and pass_mae and pass_bias

        if not dim_pass:
            all_pass = False

        status = "PASS" if dim_pass else "FAIL"
        print(f"\n  {dim.upper()} [{status}]")
        print(f"    Spearman rho:  {rho:.4f} (p={rho_p:.4f}) "
              f"{'✓' if pass_rho else '✗'} (>= {MIN_SPEARMAN})")
        print(f"    MAE:           {mae:.3f} "
              f"{'✓' if pass_mae else '✗'} (<= {MAX_MAE})")
        print(f"    Bias:          {bias:+.3f} "
              f"{'✓' if pass_bias else '✗'} (|bias| <= {MAX_BIAS})")

        metrics[dim] = {
            "spearman_rho": round(rho, 4),
            "spearman_p": round(rho_p, 6),
            "mae": round(mae, 3),
            "bias": round(bias, 3),
            "pass": dim_pass,
        }

    # Save validation results
    val_results_path = os.path.join(OUTPUT_DIR, f"llm_judge_validation_v{iteration}.csv")
    results_df.to_csv(val_results_path, index=False)
    print(f"\nDetailed results: {val_results_path}")

    # Save validation metrics summary
    val_metrics_path = os.path.join(
        OUTPUT_DIR, f"llm_judge_validation_metrics_v{iteration}.csv"
    )
    metrics_rows = []
    for dim, m in metrics.items():
        metrics_rows.append({"dimension": dim, **m})
    pd.DataFrame(metrics_rows).to_csv(val_metrics_path, index=False)
    print(f"Metrics summary: {val_metrics_path}")

    if all_pass:
        print(f"\n*** ALL DIMENSIONS PASSED — judge is calibrated (iteration {iteration}) ***")
        print("Proceed to: --mode evaluate")
    else:
        if iteration < MAX_ITERATIONS:
            print(f"\n*** VALIDATION FAILED — adjust calibration and re-run "
                  f"(iteration {iteration + 1}/{MAX_ITERATIONS}) ***")
        else:
            print(f"\n*** VALIDATION FAILED after {MAX_ITERATIONS} iterations ***")
            print("Consider expanding the human-rated set.")

    return all_pass


# ---------------------------------------------------------------------------
# Mode: evaluate
# ---------------------------------------------------------------------------
def mode_evaluate(model_key: str, iteration: int = 1):
    """Run judge on the full evaluation pool for a model."""
    print(f"=== FULL EVALUATION: {model_key} (prompt v{iteration}) ===\n")

    # Load prompt
    prompt_path = os.path.join(OUTPUT_DIR, f"llm_judge_prompt_v{iteration}.txt")
    if not os.path.exists(prompt_path):
        sys.exit(f"ERROR: Prompt file not found: {prompt_path}")
    with open(prompt_path) as f:
        system_prompt = f.read()

    # Load source JSONL files
    think_jsonl, inst_jsonl = find_source_files(model_key)
    print(f"Thinking JSONL: {think_jsonl}")
    print(f"Instruct JSONL: {inst_jsonl}")

    think_data = load_jsonl(think_jsonl)
    inst_data = load_jsonl(inst_jsonl)
    print(f"Thinking records: {len(think_data)}")
    print(f"Instruct records: {len(inst_data)}")

    # For Super-49B, exclude already human-rated samples
    human_rated_ids = set()
    if model_key == "super49b":
        consensus_df = load_consensus_scores()
        for _, row in consensus_df.iterrows():
            eid = int(row["entry_id"])
            rid = row["response_id"]
            human_rated_ids.add((eid, rid))
        print(f"Human-rated samples to skip: {len(human_rated_ids)}")

    # Load VulTrial dataset for source code and metadata
    vuln_dataset_path = os.path.join(
        PROJECT_ROOT, "vuln_database", "VulTrial_486_samples_balanced.jsonl"
    )
    vuln_ds = {}
    with open(vuln_dataset_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            vuln_ds[int(rec["idx"])] = rec

    # Build evaluation queue
    eval_queue = []
    for mode_label, data_dict, resp_id in [
        ("thinking", think_data, "think"),
        ("instruct", inst_data, "inst"),
    ]:
        for eid, rec in sorted(data_dict.items()):
            if (eid, resp_id) in human_rated_ids:
                continue
            gt = int(rec["ground_truth"])
            pred = int(rec["vuln"])
            # Only evaluate correct predictions
            if pred != gt:
                continue

            response_text = rec.get("reasoning", "")
            rater_text = prepare_rater_response_text(response_text, resp_id)

            vul_rec = vuln_ds.get(eid, {})
            source_code = vul_rec.get("func", "")
            gt_label = "vulnerable" if gt == 1 else "safe"
            label = "TP" if gt == 1 else "TN"

            eval_queue.append({
                "entry_id": eid,
                "response_id": resp_id,
                "ground_truth": gt,
                "ground_truth_label": gt_label,
                "stratum": f"{resp_id}-{label}",
                "source_code": source_code,
                "response_text": rater_text,
                "cwe": str(vul_rec.get("cwe", "")),
                "cve_desc": str(vul_rec.get("cve_desc", "")),
            })

    print(f"\nEvaluation queue: {len(eval_queue)} samples")
    # Breakdown by stratum
    from collections import Counter
    strat_counts = Counter(e["stratum"] for e in eval_queue)
    for s in sorted(strat_counts):
        print(f"  {s}: {strat_counts[s]}")

    # Output file (incremental)
    output_path = os.path.join(OUTPUT_DIR, f"{model_key}_zero_llm_judged.csv")
    fieldnames = [
        "entry_id", "response_id", "ground_truth", "ground_truth_label", "stratum",
    ] + [f"{d}_score" for d in DIMENSIONS] + [f"{d}_justification" for d in DIMENSIONS]

    # Check for existing partial results (crash recovery)
    completed_keys = set()
    if os.path.exists(output_path):
        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                completed_keys.add((int(row["entry_id"]), row["response_id"]))
        print(f"\nResuming: {len(completed_keys)} already completed")
    else:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    remaining = [e for e in eval_queue
                 if (e["entry_id"], e["response_id"]) not in completed_keys]
    print(f"Remaining to evaluate: {len(remaining)}")

    if not remaining:
        print("All samples already evaluated.")
        return

    # Evaluate
    success = 0
    failed = 0
    for i, sample in enumerate(remaining, 1):
        eid = sample["entry_id"]
        rid = sample["response_id"]
        print(f"  [{i}/{len(remaining)}] entry={eid} resp={rid} "
              f"stratum={sample['stratum']} ... ", end="", flush=True)

        user_prompt = build_evaluation_prompt(
            source_code=sample["source_code"],
            response_text=sample["response_text"],
            ground_truth_label=sample["ground_truth_label"],
            cwe=sample["cwe"],
            cve_desc=sample["cve_desc"],
        )

        response = call_llm_judge(system_prompt, user_prompt)
        parsed = parse_judge_response(response) if response else None

        if parsed:
            row = {
                "entry_id": eid,
                "response_id": rid,
                "ground_truth": sample["ground_truth"],
                "ground_truth_label": sample["ground_truth_label"],
                "stratum": sample["stratum"],
            }
            for dim in DIMENSIONS:
                row[f"{dim}_score"] = parsed[f"{dim}_score"]
                row[f"{dim}_justification"] = parsed[f"{dim}_justification"]

            # Append to CSV
            with open(output_path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(row)

            scores = [parsed[f"{d}_score"] for d in DIMENSIONS]
            print(f"scores={scores}")
            success += 1
        else:
            print("FAILED")
            failed += 1

        time.sleep(REQUEST_DELAY_SECONDS)

    print(f"\nCompleted: {success} success, {failed} failed")
    print(f"Results: {output_path}")


# ---------------------------------------------------------------------------
# Mode: spot-check
# ---------------------------------------------------------------------------
def mode_spot_check(model_key: str):
    """Generate 10% stratified sample for human spot-checking."""
    print(f"=== SPOT-CHECK SAMPLE: {model_key} ===\n")

    output_path = os.path.join(OUTPUT_DIR, f"{model_key}_zero_llm_judged.csv")
    if not os.path.exists(output_path):
        sys.exit(f"ERROR: LLM-judged results not found: {output_path}")

    judged_df = pd.read_csv(output_path)
    print(f"LLM-judged samples: {len(judged_df)}")

    # 10% stratified sample
    np.random.seed(42)
    spot_samples = []
    for stratum in sorted(judged_df["stratum"].unique()):
        sub = judged_df[judged_df["stratum"] == stratum]
        n_sample = max(1, round(len(sub) * 0.10))
        sampled = sub.sample(n=n_sample, random_state=42)
        spot_samples.append(sampled)
        print(f"  {stratum}: {n_sample} / {len(sub)}")

    spot_df = pd.concat(spot_samples, ignore_index=True)
    print(f"\nTotal spot-check samples: {len(spot_df)}")

    # Load source data for the spot-check sheet
    vuln_dataset_path = os.path.join(
        PROJECT_ROOT, "vuln_database", "VulTrial_486_samples_balanced.jsonl"
    )
    vuln_ds = {}
    with open(vuln_dataset_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            vuln_ds[int(rec["idx"])] = rec

    think_jsonl, inst_jsonl = find_source_files(model_key)
    think_data = load_jsonl(think_jsonl)
    inst_data = load_jsonl(inst_jsonl)

    # Build spot-check sheet
    spot_rows = []
    for _, row in spot_df.iterrows():
        eid = int(row["entry_id"])
        rid = row["response_id"]
        data_dict = think_data if rid == "think" else inst_data
        rec = data_dict.get(eid, {})
        vul_rec = vuln_ds.get(eid, {})

        response_text = rec.get("reasoning", "")
        rater_text = prepare_rater_response_text(response_text, rid)

        spot_row = {
            "entry_id": eid,
            "response_id": rid,
            "ground_truth_label": row["ground_truth_label"],
            "stratum": row["stratum"],
            "source_code": vul_rec.get("func", ""),
            "cwe": str(vul_rec.get("cwe", "")),
            "cve_desc": str(vul_rec.get("cve_desc", "")),
            "response_text": rater_text,
        }
        # LLM scores
        for dim in DIMENSIONS:
            spot_row[f"llm_{dim}_score"] = row[f"{dim}_score"]
        # Human verification columns
        for dim in DIMENSIONS:
            spot_row[f"human_{dim}_score"] = ""
        spot_row["human_notes"] = ""
        spot_rows.append(spot_row)

    spot_path = os.path.join(OUTPUT_DIR, f"{model_key}_zero_spot_check_sheet.csv")
    pd.DataFrame(spot_rows).to_csv(spot_path, index=False)
    print(f"\nSpot-check sheet: {spot_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="LLM-as-Judge pipeline for RQ3 explanation quality evaluation"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["calibrate", "validate", "evaluate", "spot-check"],
        help="Pipeline mode",
    )
    parser.add_argument(
        "--model",
        choices=["super49b", "qwen30b"],
        default="super49b",
        help="Target model (for evaluate and spot-check modes)",
    )
    parser.add_argument(
        "--iteration",
        type=int,
        default=1,
        help="Calibration iteration number (default: 1)",
    )
    args = parser.parse_args()

    if args.mode == "calibrate":
        mode_calibrate(iteration=args.iteration)
    elif args.mode == "validate":
        mode_validate(iteration=args.iteration)
    elif args.mode == "evaluate":
        mode_evaluate(model_key=args.model, iteration=args.iteration)
    elif args.mode == "spot-check":
        mode_spot_check(model_key=args.model)


if __name__ == "__main__":
    main()
