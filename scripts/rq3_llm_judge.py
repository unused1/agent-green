"""
LLM-as-Judge pipeline for RQ3 explanation quality evaluation.

Modes:
    --mode zero-shot-baseline  Score all 30 samples with rubric only (no examples),
                               compute agreement with human raters as "4th rater" baseline
    --mode calibrate  Select 8 calibration + 22 validation samples, build prompt
    --mode validate   Run judge on 22 held-out, check Spearman >= 0.7, MAE <= 1.0
    --mode evaluate   Run judge on full pool (~487 Super-49B or ~534 Qwen3-30B)
    --mode spot-check Generate 10% stratified sample for human verification

Backends:
    --claude   Use Anthropic API directly (requires ANTHROPIC_API_KEY)
    --google   Use Google AI Studio / Gemini (requires GOOGLE_API_KEY)
    (default)  Use OpenRouter (requires OPENROUTER_API_KEY)

Usage:
    # Claude (direct Anthropic API — recommended)
    export ANTHROPIC_API_KEY=<key>
    python scripts/rq3_llm_judge.py --claude --mode zero-shot-baseline
    python scripts/rq3_llm_judge.py --claude --judge-model claude-opus-4-20250514 --mode evaluate --model super49b

    # Google Gemini
    export GOOGLE_API_KEY=<key>
    python scripts/rq3_llm_judge.py --google --mode zero-shot-baseline

    # OpenRouter (legacy, routes to any model)
    export OPENROUTER_API_KEY=<key>
    python scripts/rq3_llm_judge.py --mode zero-shot-baseline
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
# Backend-specific defaults
JUDGE_MODELS = {
    "openrouter": "anthropic/claude-sonnet-4.6",
    "claude": "claude-sonnet-4-6",
    "google": "gemini-3-flash-preview",
}
JUDGE_BACKEND = "openrouter"  # default, overridden by --claude / --google flags
JUDGE_MODEL = os.getenv("RQ3_JUDGE_MODEL", "")  # env override for any backend

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

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
# LLM API backends
# ---------------------------------------------------------------------------
def _get_judge_model() -> str:
    """Return the effective judge model for the active backend."""
    if JUDGE_MODEL:
        return JUDGE_MODEL
    return JUDGE_MODELS.get(JUDGE_BACKEND, JUDGE_MODELS["openrouter"])


def _call_openrouter(
    system_prompt: str, user_prompt: str, temperature: float, max_retries: int,
) -> Optional[str]:
    """Call judge via OpenRouter (OpenAI-compatible API)."""
    try:
        import openai
    except ImportError:
        sys.exit("ERROR: openai package required. Install with: pip install openai")

    if not OPENROUTER_API_KEY:
        sys.exit("ERROR: OPENROUTER_API_KEY environment variable not set")

    model = _get_judge_model()
    client = openai.OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_API_BASE)

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


def _call_claude(
    system_prompt: str, user_prompt: str, temperature: float, max_retries: int,
) -> Optional[str]:
    """Call judge via Anthropic API directly."""
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("ERROR: anthropic package required. Install with: pip install anthropic")

    if not ANTHROPIC_API_KEY:
        sys.exit("ERROR: ANTHROPIC_API_KEY environment variable not set")

    model = _get_judge_model()
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return "".join(
                block.text for block in response.content if block.type == "text"
            )
        except Exception as e:
            print(f"  API error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
    return None


def _call_google(
    system_prompt: str, user_prompt: str, temperature: float, max_retries: int,
) -> Optional[str]:
    """Call judge via Google AI Studio (Gemini) API."""
    try:
        from google import genai
    except ImportError:
        sys.exit("ERROR: google-genai package required. Install with: pip install google-genai")

    if not GOOGLE_API_KEY:
        sys.exit("ERROR: GOOGLE_API_KEY environment variable not set")

    model = _get_judge_model()
    client = genai.Client(api_key=GOOGLE_API_KEY)

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=f"{system_prompt}\n\n{user_prompt}",
                config=genai.types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=2000,
                ),
            )
            return response.text
        except Exception as e:
            print(f"  API error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
    return None


def call_llm_judge(
    system_prompt: str,
    user_prompt: str,
    model: str = None,
    temperature: float = 0.0,
    max_retries: int = 3,
) -> Optional[str]:
    """Call the LLM judge via the configured backend.

    Backend is set by --claude, --google flags or defaults to OpenRouter.
    """
    dispatch = {
        "openrouter": _call_openrouter,
        "claude": _call_claude,
        "google": _call_google,
    }
    fn = dispatch.get(JUDGE_BACKEND, _call_openrouter)
    return fn(system_prompt, user_prompt, temperature, max_retries)


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
# Agreement metrics helper
# ---------------------------------------------------------------------------
def compute_agreement_metrics(
    results_df: pd.DataFrame,
    human_col_prefix: str = "human",
    llm_col_prefix: str = "llm",
    label: str = "",
) -> dict:
    """Compute Spearman, MAE, and bias between human and LLM scores.

    Args:
        results_df: DataFrame with {dim}_{human_col_prefix} and {dim}_{llm_col_prefix} columns
        human_col_prefix: prefix for human score columns (e.g., 'human' -> 'completeness_human')
        llm_col_prefix: prefix for LLM score columns
        label: label for print output

    Returns:
        dict of {dimension: {spearman_rho, spearman_p, mae, bias, pass}}
    """
    if label:
        print(f"\n{'=' * 60}")
        print(f"AGREEMENT METRICS — {label}")
        print(f"{'=' * 60}")

    metrics = {}
    all_pass = True
    for dim in DIMENSIONS:
        human = results_df[f"{dim}_{human_col_prefix}"].values
        llm = results_df[f"{dim}_{llm_col_prefix}"].values

        rho, rho_p = spearmanr(human, llm)
        mae = np.mean(np.abs(human - llm))
        bias = np.mean(llm - human)  # positive = LLM scores higher

        pass_rho = rho >= MIN_SPEARMAN
        pass_mae = mae <= MAX_MAE
        pass_bias = abs(bias) <= MAX_BIAS
        dim_pass = pass_rho and pass_mae and pass_bias

        if not dim_pass:
            all_pass = False

        if label:
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

    return metrics, all_pass


# ---------------------------------------------------------------------------
# Mode: zero-shot-baseline
# ---------------------------------------------------------------------------
def mode_zero_shot_baseline():
    """Score all 30 human-rated samples with rubric only (no few-shot examples).

    This establishes the LLM's natural alignment with human raters before any
    calibration, treating the LLM as a '4th rater'. The results quantify how
    much few-shot calibration improves agreement (compare with validate metrics).
    """
    print("=== ZERO-SHOT BASELINE (rubric only, no examples) ===\n")

    # Build zero-shot system prompt (rubric only)
    rubric_text = load_rubric_text()
    system_prompt = build_system_prompt(rubric_text)
    print(f"System prompt length: {len(system_prompt)} chars (rubric only)")
    print(f"Judge model: {JUDGE_MODEL}")

    # Save zero-shot prompt for reproducibility
    prompt_path = os.path.join(OUTPUT_DIR, "llm_judge_prompt_zero_shot_baseline.txt")
    with open(prompt_path, "w") as f:
        f.write(system_prompt)
    print(f"Prompt saved: {prompt_path}")

    # Load all 30 human-rated samples
    consensus_df = load_consensus_scores()
    rater_sheet = pd.read_csv(RATER_SHEET_CSV)
    # ground_truth_label already in consensus_df; only merge columns not already present
    consensus_df = consensus_df.merge(
        rater_sheet[["sample_id", "source_code", "response_text", "cwe", "cve_desc"]],
        on="sample_id",
        how="left",
    )
    print(f"\nSamples to evaluate: {len(consensus_df)}")

    # Check for existing partial results (crash recovery)
    output_path = os.path.join(OUTPUT_DIR, "llm_judge_zero_shot_baseline.csv")
    completed = {}
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        for _, row in existing_df.iterrows():
            completed[int(row["sample_id"])] = row.to_dict()
        print(f"Resuming: {len(completed)} already completed")

    # Run judge on each sample
    results = []
    for i, (_, row) in enumerate(consensus_df.iterrows(), 1):
        sid = int(row["sample_id"])

        # Use cached result if available
        if sid in completed:
            results.append(completed[sid])
            print(f"  [{i}/{len(consensus_df)}] sample_id={sid:2d} "
                  f"stratum={row['stratum']:10s} ... cached")
            continue

        print(f"  [{i}/{len(consensus_df)}] sample_id={sid:2d} "
              f"stratum={row['stratum']:10s} ... ", end="", flush=True)

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
            result = {
                "sample_id": sid,
                "stratum": row["stratum"],
                "entry_id": int(row["entry_id"]) if pd.notna(row["entry_id"]) else "",
                "response_id": row["response_id"],
            }
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
        sys.exit("ERROR: No valid results from zero-shot baseline run")

    results_df = pd.DataFrame(results)

    # Save detailed results
    results_df.to_csv(output_path, index=False)
    print(f"\nDetailed results: {output_path}")
    print(f"Scored: {len(results_df)} / {len(consensus_df)} samples")

    # Compute agreement metrics
    metrics, all_pass = compute_agreement_metrics(
        results_df, label="Zero-shot baseline (LLM as 4th rater)"
    )

    # Save metrics summary
    metrics_path = os.path.join(OUTPUT_DIR, "llm_judge_zero_shot_baseline_metrics.csv")
    metrics_rows = []
    for dim, m in metrics.items():
        metrics_rows.append({"dimension": dim, **m})
    pd.DataFrame(metrics_rows).to_csv(metrics_path, index=False)
    print(f"\nMetrics summary: {metrics_path}")

    # Per-rater comparison: compute LLM agreement with each individual rater
    rater_cols = [c for c in consensus_df.columns if c.startswith("completeness_")
                  and c != "completeness_consensus" and c != "completeness_diff"]
    rater_names = [c.replace("completeness_", "") for c in rater_cols]

    if rater_names:
        print(f"\n{'=' * 60}")
        print("PER-RATER AGREEMENT (LLM vs. each human rater)")
        print(f"{'=' * 60}")

        for rname in rater_names:
            print(f"\n  --- LLM vs. {rname} ---")
            # Build a temp df with rater scores as 'human' columns
            temp_df = results_df.copy()
            for dim in DIMENSIONS:
                rater_col = f"{dim}_{rname}"
                if rater_col in consensus_df.columns:
                    # Merge rater scores by sample_id
                    rater_scores = consensus_df[["sample_id", rater_col]].copy()
                    rater_scores = rater_scores.rename(columns={rater_col: f"{dim}_rater"})
                    temp_df = temp_df.merge(rater_scores, on="sample_id", how="left")
                else:
                    temp_df[f"{dim}_rater"] = np.nan

            has_data = not temp_df[[f"{d}_rater" for d in DIMENSIONS]].isna().any().any()
            if has_data:
                for dim in DIMENSIONS:
                    human_vals = temp_df[f"{dim}_rater"].values
                    llm_vals = temp_df[f"{dim}_llm"].values
                    rho, rho_p = spearmanr(human_vals, llm_vals)
                    mae = np.mean(np.abs(human_vals - llm_vals))
                    bias = np.mean(llm_vals - human_vals)
                    print(f"    {dim:18s}: ρ={rho:.3f} (p={rho_p:.3f}), "
                          f"MAE={mae:.2f}, bias={bias:+.2f}")

    # Summary
    print(f"\n{'=' * 60}")
    print("ZERO-SHOT BASELINE SUMMARY")
    print(f"{'=' * 60}")
    for dim, m in metrics.items():
        status = "PASS" if m["pass"] else "FAIL"
        print(f"  {dim:18s}: ρ={m['spearman_rho']:.3f}, "
              f"MAE={m['mae']:.2f}, bias={m['bias']:+.2f} [{status}]")

    if all_pass:
        print("\n  Zero-shot baseline passes all thresholds.")
        print("  Few-shot calibration may still improve alignment.")
    else:
        print("\n  Zero-shot baseline does not pass all thresholds.")
        print("  Few-shot calibration is needed — proceed to: --mode calibrate")

    return metrics


# ---------------------------------------------------------------------------
# Mode: calibrate
# ---------------------------------------------------------------------------
def mode_calibrate(iteration: int = 1, num_per_stratum: int = 2):
    """Select calibration/validation split and build prompt template.

    Args:
        iteration: Calibration iteration number.
        num_per_stratum: Number of calibration samples per stratum (default 2).
            Samples are selected to span the quality range: lowest, highest,
            and (if >2) evenly spaced between them.
    """
    print(f"=== CALIBRATION (iteration {iteration}, {num_per_stratum} per stratum) ===\n")

    consensus_df = load_consensus_scores()
    print(f"Loaded {len(consensus_df)} consensus scores")

    if "stratum" not in consensus_df.columns:
        sys.exit("ERROR: consensus scores missing 'stratum' column. Run IRR script first.")

    # Load response text from rater sheet for few-shot examples
    rater_sheet = pd.read_csv(RATER_SHEET_CSV)
    # ground_truth_label already in consensus_df; only merge columns not already present
    consensus_df = consensus_df.merge(
        rater_sheet[["sample_id", "source_code", "response_text"]],
        on="sample_id",
        how="left",
    )

    # Select calibration samples per stratum spanning the quality range
    consensus_df["mean_consensus"] = consensus_df[
        [f"{d}_consensus" for d in DIMENSIONS]
    ].mean(axis=1)

    calibration_ids = []
    for stratum in STRATA:
        sub = consensus_df[consensus_df["stratum"] == stratum].copy()
        if len(sub) <= num_per_stratum:
            print(f"  WARNING: stratum {stratum} has only {len(sub)} samples, using all")
            calibration_ids.extend(sub["sample_id"].tolist())
            continue
        # Sort by mean consensus and pick evenly spaced samples
        sorted_sub = sub.sort_values("mean_consensus")
        n = len(sorted_sub)
        if num_per_stratum == 1:
            indices = [n // 2]  # middle
        elif num_per_stratum == 2:
            indices = [0, n - 1]  # lowest + highest
        else:
            # Evenly spaced: always include lowest and highest
            indices = [int(round(i * (n - 1) / (num_per_stratum - 1)))
                       for i in range(num_per_stratum)]
            indices = sorted(set(indices))  # deduplicate if rounding collides
        for idx in indices:
            calibration_ids.append(sorted_sub.iloc[idx]["sample_id"])

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
    # ground_truth_label already in consensus_df; only merge columns not already present
    consensus_df = consensus_df.merge(
        rater_sheet[["sample_id", "source_code", "response_text", "cwe", "cve_desc"]],
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
    metrics, all_pass = compute_agreement_metrics(
        results_df, label=f"Few-shot validation (iteration {iteration})"
    )

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
    """Run judge on the intersection pool (both modes correct) for VulTrial-870.

    Evaluates only samples where BOTH thinking and instruct modes produced
    correct predictions on the same code snippet, enabling paired comparison.
    Loads from both VulTrial-486 and VulTrial-384-incr directories.

    For zero-shot judge (iteration=0), uses the rubric-only system prompt.
    For few-shot (iteration>=1), uses the calibrated prompt.
    """
    judge_label = "zero-shot" if iteration == 0 else f"prompt v{iteration}"
    print(f"=== FULL EVALUATION: {model_key} ({judge_label}) ===\n")

    # Load system prompt
    if iteration == 0:
        # Zero-shot: build rubric-only prompt
        rubric_text = load_rubric_text()
        system_prompt = build_system_prompt(rubric_text)
        print(f"Using zero-shot rubric-only prompt ({len(system_prompt)} chars)")
    else:
        prompt_path = os.path.join(OUTPUT_DIR, f"llm_judge_prompt_v{iteration}.txt")
        if not os.path.exists(prompt_path):
            sys.exit(f"ERROR: Prompt file not found: {prompt_path}")
        with open(prompt_path) as f:
            system_prompt = f.read()
        print(f"Using few-shot prompt v{iteration} ({len(system_prompt)} chars)")

    # Load source JSONL files from BOTH 486 and 384-incr (VulTrial-870)
    results_dir = os.path.join(PROJECT_ROOT, "results")
    vuln_dirs = [
        os.path.join(results_dir, "runpod_vuln_486"),
        os.path.join(results_dir, "runpod_vuln_384_incremental"),
    ]

    model_map = {
        "super49b": "Nemotron-Super-49B",
        "qwen30b": "Qwen3-30B-A3B",
    }
    model_name = model_map.get(model_key)
    if not model_name:
        sys.exit(f"ERROR: Unknown model key '{model_key}'")

    import glob as glob_mod

    think_data = {}
    inst_data = {}
    for vuln_dir in vuln_dirs:
        for jsonl_path in sorted(glob_mod.glob(os.path.join(vuln_dir, "Sa-zero_*_detailed_results.jsonl"))):
            fname = os.path.basename(jsonl_path)
            if model_name == "Nemotron-Super-49B" and "Super-49B" not in fname:
                continue
            if model_name == "Qwen3-30B-A3B" and "Qwen3-30B" not in fname:
                continue
            is_think = "_thinking_" in fname
            target = think_data if is_think else inst_data
            records = load_jsonl(jsonl_path)
            for idx, rec in records.items():
                if idx not in target:
                    target[idx] = rec
            print(f"  Loaded {len(records)} from {os.path.basename(jsonl_path)}")

    print(f"\nThinking records: {len(think_data)}")
    print(f"Instruct records: {len(inst_data)}")

    # Find intersection: both modes correct on same snippet
    common_idx = set(think_data.keys()) & set(inst_data.keys())
    intersection_ids = set()
    for idx in common_idx:
        t_rec = think_data[idx]
        i_rec = inst_data[idx]
        t_gt = int(t_rec.get("ground_truth", t_rec.get("target", -1)))
        t_pred = int(t_rec.get("vuln", -1))
        i_gt = int(i_rec.get("ground_truth", i_rec.get("target", -1)))
        i_pred = int(i_rec.get("vuln", -1))
        if t_pred == t_gt and i_pred == i_gt:
            intersection_ids.add(idx)

    # Count TP/TN in intersection
    tp_count = sum(1 for idx in intersection_ids
                   if int(think_data[idx].get("ground_truth",
                          think_data[idx].get("target", 0))) == 1)
    tn_count = len(intersection_ids) - tp_count
    print(f"Intersection (both correct): {len(intersection_ids)} snippets "
          f"({tp_count} TP, {tn_count} TN)")
    print(f"Total evaluations: {len(intersection_ids) * 2}")

    # Save intersection list for reference
    intersection_path = os.path.join(OUTPUT_DIR, f"{model_key}_870_intersection.csv")
    with open(intersection_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["entry_id", "ground_truth", "label"])
        writer.writeheader()
        for idx in sorted(intersection_ids):
            gt = int(think_data[idx].get("ground_truth",
                     think_data[idx].get("target", 0)))
            writer.writerow({"entry_id": idx, "ground_truth": gt,
                             "label": "TP" if gt == 1 else "TN"})
    print(f"Intersection list saved: {intersection_path}")

    # Include all intersection samples (including human-rated) for complete evaluation
    human_rated_ids = set()  # no exclusions — LLM judges all samples

    # Load VulTrial datasets for source code and metadata
    vuln_ds = {}
    for ds_path in [
        os.path.join(PROJECT_ROOT, "vuln_database", "VulTrial_486_samples_balanced.jsonl"),
        os.path.join(PROJECT_ROOT, "vuln_database", "VulTrial_384_incremental.jsonl"),
    ]:
        if os.path.exists(ds_path):
            with open(ds_path) as f:
                for line in f:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    idx = int(rec.get("idx", rec.get("id", -1)))
                    if idx not in vuln_ds:
                        vuln_ds[idx] = rec

    # Build evaluation queue (intersection only)
    eval_queue = []
    for mode_label, data_dict, resp_id in [
        ("thinking", think_data, "think"),
        ("instruct", inst_data, "inst"),
    ]:
        for eid in sorted(intersection_ids):
            if (eid, resp_id) in human_rated_ids:
                continue
            rec = data_dict[eid]
            gt = int(rec.get("ground_truth", rec.get("target", 0)))
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
    from collections import Counter
    strat_counts = Counter(e["stratum"] for e in eval_queue)
    for s in sorted(strat_counts):
        print(f"  {s}: {strat_counts[s]}")

    # Output file — include judge model short name for disambiguation
    judge_short = _get_judge_model().replace("claude-", "").replace("-20250514", "")
    iter_tag = "zeroshot" if iteration == 0 else f"v{iteration}"
    output_path = os.path.join(
        OUTPUT_DIR, f"{model_key}_870_llm_judged_{judge_short}_{iter_tag}.csv"
    )
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
# Mode: evaluate-incorrect (Reviewer B5 follow-up)
# ---------------------------------------------------------------------------
def mode_evaluate_incorrect():
    """Score the incorrect-intersection rating set produced by
    `scripts/rq3_generate_incorrect_rating_set.py`.

    Uses the same Opus 4.6 zero-shot rubric prompt selected as the final
    judge configuration (Section 11.5.3). Reads a pre-built CSV of 30
    eval-queue rows (15 snippets × {think, inst}) and emits scores in the
    same schema as `super49b_870_llm_judged_*_zeroshot.csv` so downstream
    comparison is direct.
    """
    print("=== EVALUATE-INCORRECT: Super-49B SA zero-shot incorrect-intersection ===\n")

    rating_set_path = os.path.join(OUTPUT_DIR, "super49b_zero_incorrect_rating_set.csv")
    if not os.path.exists(rating_set_path):
        sys.exit(f"ERROR: rating set not found: {rating_set_path}\n"
                 f"Run: python scripts/rq3_generate_incorrect_rating_set.py")

    rubric_text = load_rubric_text()
    system_prompt = build_system_prompt(rubric_text)
    print(f"Using zero-shot rubric-only prompt ({len(system_prompt)} chars)")

    eval_queue = []
    with open(rating_set_path, newline="") as f:
        for row in csv.DictReader(f):
            eval_queue.append({
                "entry_id": int(row["entry_id"]),
                "response_id": row["response_id"],
                "ground_truth": int(row["ground_truth"]),
                "ground_truth_label": row["ground_truth_label"],
                "stratum": row["stratum"],
                "source_code": row["source_code"],
                "response_text": prepare_rater_response_text(
                    row["response_text"], row["response_id"]),
                "cwe": row.get("cwe", ""),
                "cve_desc": row.get("cve_desc", ""),
            })

    print(f"Loaded {len(eval_queue)} evaluations from {os.path.basename(rating_set_path)}")
    from collections import Counter
    strat_counts = Counter(e["stratum"] for e in eval_queue)
    for s in sorted(strat_counts):
        print(f"  {s}: {strat_counts[s]}")

    judge_short = _get_judge_model().replace("claude-", "").replace("-20250514", "")
    output_path = os.path.join(
        OUTPUT_DIR, f"super49b_zero_incorrect_llm_judged_{judge_short}_zeroshot.csv"
    )
    fieldnames = [
        "entry_id", "response_id", "ground_truth", "ground_truth_label", "stratum",
    ] + [f"{d}_score" for d in DIMENSIONS] + [f"{d}_justification" for d in DIMENSIONS]

    # Crash-recovery: resume from any existing rows
    completed_keys = set()
    if os.path.exists(output_path):
        with open(output_path, newline="") as f:
            for row in csv.DictReader(f):
                completed_keys.add((int(row["entry_id"]), row["response_id"]))
        print(f"\nResuming: {len(completed_keys)} already completed")
    else:
        with open(output_path, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writeheader()

    remaining = [e for e in eval_queue
                 if (e["entry_id"], e["response_id"]) not in completed_keys]
    print(f"Remaining to evaluate: {len(remaining)}\n")

    if not remaining:
        print("All samples already evaluated.")
        print(f"Results: {output_path}")
        return

    success = failed = 0
    for i, sample in enumerate(remaining, 1):
        eid, rid = sample["entry_id"], sample["response_id"]
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
            with open(output_path, "a", newline="") as f:
                csv.DictWriter(f, fieldnames=fieldnames).writerow(row)
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
        choices=["zero-shot-baseline", "calibrate", "validate", "evaluate", "evaluate-incorrect", "spot-check"],
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

    # Backend selection (mutually exclusive)
    backend_group = parser.add_mutually_exclusive_group()
    backend_group.add_argument(
        "--claude",
        action="store_true",
        help="Use Anthropic API directly (requires ANTHROPIC_API_KEY)",
    )
    backend_group.add_argument(
        "--google",
        action="store_true",
        help="Use Google AI Studio / Gemini (requires GOOGLE_API_KEY)",
    )

    parser.add_argument(
        "--judge-model",
        default=None,
        help="Override judge model ID (e.g., claude-sonnet-4-20250514, gemini-2.5-flash)",
    )
    parser.add_argument(
        "--num-examples",
        type=int,
        default=2,
        help="Number of calibration examples per stratum (default: 2, i.e., 8 total)",
    )

    args = parser.parse_args()

    # Configure backend
    global JUDGE_BACKEND, JUDGE_MODEL
    if args.claude:
        JUDGE_BACKEND = "claude"
    elif args.google:
        JUDGE_BACKEND = "google"

    if args.judge_model:
        JUDGE_MODEL = args.judge_model

    effective_model = _get_judge_model()
    print(f"Judge backend: {JUDGE_BACKEND}")
    print(f"Judge model:   {effective_model}\n")

    if args.mode == "zero-shot-baseline":
        mode_zero_shot_baseline()
    elif args.mode == "calibrate":
        mode_calibrate(iteration=args.iteration, num_per_stratum=args.num_examples)
    elif args.mode == "validate":
        mode_validate(iteration=args.iteration)
    elif args.mode == "evaluate":
        mode_evaluate(model_key=args.model, iteration=args.iteration)
    elif args.mode == "evaluate-incorrect":
        mode_evaluate_incorrect()
    elif args.mode == "spot-check":
        mode_spot_check(model_key=args.model)


if __name__ == "__main__":
    main()
