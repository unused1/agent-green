#!/usr/bin/env python3
"""
No-Agent Vulnerability Detection (Zero-Shot and Few-Shot)

Direct LLM inference without AutoGen agent framework.
Uses OpenAI-compatible API (vLLM) with the same parser as SA experiments.

Usage:
    python src/no_agent_vuln_detection.py --prompt_type zero_shot
    python src/no_agent_vuln_detection.py --prompt_type few_shot
    python src/no_agent_vuln_detection.py --prompt_type few_shot --resume <exp_name>

Environment variables:
    MODEL_FAMILY: nemotron | deepseek | (default: qwen3)
    ENABLE_REASONING: true | false
    VULN_DATASET: path to dataset JSONL
    RESULTS_DIR: output directory
"""

import os
import json
import argparse
from datetime import datetime
from openai import OpenAI

# Dynamic config selection based on MODEL_FAMILY environment variable
_model_family = os.getenv('MODEL_FAMILY', '').lower()
if _model_family == 'deepseek':
    import config_deepseek as config
    print("[Config] Using DeepSeek configuration")
elif _model_family == 'nemotron':
    import config_nemotron as config
    print("[Config] Using Nemotron configuration")
else:
    import config
    print("[Config] Using Qwen3 configuration")

from codecarbon import OfflineEmissionsTracker
from vuln_evaluation import (
    evaluate_and_save_vulnerability,
    normalize_vulnerability_basic,
    normalize_vulnerability_conservative,
    normalize_vulnerability_strict,
)

# ================================================================
# CLI ARGUMENT PARSING
# ================================================================
def parse_arguments():
    parser = argparse.ArgumentParser(description="No-Agent Vulnerability Detection")
    parser.add_argument(
        "--prompt_type", choices=["zero_shot", "few_shot"], default="zero_shot",
        help="Prompt type: zero_shot or few_shot"
    )
    parser.add_argument(
        "--resume", type=str, default=None,
        help="Resume from existing experiment name"
    )
    return parser.parse_args()

args = parse_arguments()
prompt_type = args.prompt_type

# ================================================================
# CONFIGURATION
# ================================================================
llm_config = config.LLM_CONFIG
task = config.VULNERABILITY_TASK_PROMPT

# Select system prompt based on prompt type
if prompt_type == "few_shot":
    sys_prompt = config.SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT
    print("Using FEW-SHOT prompt for vulnerability detection.")
else:
    sys_prompt = config.SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT
    print("Using ZERO-SHOT prompt for vulnerability detection.")

# Apply Nemotron thinking toggle if using Nemotron config
if _model_family == 'nemotron' and hasattr(config, 'prepend_thinking_toggle'):
    sys_prompt = config.prepend_thinking_toggle(sys_prompt)
    print(f"[Nemotron] Applied thinking toggle: ENABLE_REASONING={config.ENABLE_REASONING}")

DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

DESIGN = f"NA-vuln-{prompt_type}"
model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

if args.resume:
    exp_name = args.resume
    print(f"Resuming experiment: {exp_name}")
elif os.getenv("EXP_NAME"):
    exp_name = os.getenv("EXP_NAME")
    print(f"Using EXP_NAME env override: {exp_name}")
else:
    exp_name = f"{DESIGN}_{model}_{timestamp}"

print(f"Experiment: {exp_name}")
print(f"Dataset: {DATASET_FILE}")
print(f"Design: {DESIGN}")
print(f"Results: {RESULT_DIR}")

# ================================================================
# OpenAI-Compatible Client (for vLLM)
# ================================================================
client = OpenAI(
    base_url=llm_config["config_list"][0]["base_url"],
    api_key=llm_config["config_list"][0].get("api_key", "dummy-key"),
)
model_name = llm_config["config_list"][0]["model"]
temperature = llm_config["temperature"]


def query_model(sys_prompt, user_prompt):
    """Query the model via OpenAI-compatible API (vLLM)."""
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [Error] API call failed: {e}")
        return None


# ================================================================
# VULNERABILITY RESPONSE PARSER
# (Same as single_agent_vuln_detection.py — fixed 2026-02-22)
# ================================================================
def parse_vulnerability_response(response_text):
    """
    Parse the LLM response to extract vulnerability decision.

    Returns:
        tuple: (decision, reasoning)
            decision: 1 (vulnerable) or 0 (not vulnerable)
            reasoning: str containing the full response

    Delegates to the canonical parser in src/vuln_parser.py (single source of
    truth shared across NA/SA/DA/MA and the offline reparser), so live inference
    and re-parsing stay identical. Uses last-decisive-marker-wins on the
    post-</think> output.
    """
    from vuln_parser import parse_na_sa
    return parse_na_sa(response_text)


# ================================================================
# DATA LOADING
# ================================================================
def load_dataset(dataset_path):
    """Load vulnerability dataset from JSONL file."""
    samples = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if 'func' in data and 'target' in data:
                    samples.append(data)
            except json.JSONDecodeError:
                continue
    return samples


# ================================================================
# RESULTS FILE INITIALIZATION
# ================================================================
def initialize_results_files(exp_name, result_dir):
    """Initialize result files for incremental saving."""
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")
    if not os.path.exists(csv_file):
        with open(csv_file, 'w') as f:
            f.write("idx,project,commit_id,project_url,commit_url,commit_message,"
                    "ground_truth,vuln,reasoning,cwe,cve,cve_desc\n")
    energy_file = os.path.join(result_dir, f"{exp_name}_energy_tracking.json")
    return detailed_file, csv_file, energy_file


def append_result(result, detailed_file, csv_file):
    """Append a single result to JSONL and CSV files."""
    with open(detailed_file, 'a') as f:
        f.write(json.dumps(result) + '\n')

    def esc(x):
        if x is None:
            return ""
        s = str(x)
        if ',' in s or '"' in s or '\n' in s:
            return '"' + s.replace('"', '""') + '"'
        return s

    with open(csv_file, 'a') as f:
        row = [esc(result.get(k, '')) for k in [
            'idx', 'project', 'commit_id', 'project_url', 'commit_url',
            'commit_message', 'ground_truth', 'vuln', 'reasoning',
            'cwe', 'cve', 'cve_desc'
        ]]
        f.write(','.join(row) + '\n')


def load_existing_results(detailed_file):
    """Load existing results for resume support."""
    results = []
    if os.path.exists(detailed_file):
        with open(detailed_file, 'r') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line.strip()))
        print(f"Loaded {len(results)} existing results for resume")
    return results


def load_existing_energy(energy_file):
    """Load existing energy tracking data."""
    if os.path.exists(energy_file):
        with open(energy_file, 'r') as f:
            return json.load(f)
    return {"total_emissions": 0.0, "sessions": 0, "session_history": []}


def save_energy_data(energy_data, energy_file):
    """Save energy tracking data."""
    with open(energy_file, 'w') as f:
        json.dump(energy_data, f, indent=2)


# ================================================================
# CORE INFERENCE
# ================================================================
def run_inference_with_emissions(samples, sys_prompt, task_prompt, exp_name, result_dir):
    """Run no-agent vulnerability detection with emissions tracking."""

    detailed_file, csv_file, energy_file = initialize_results_files(exp_name, result_dir)

    # Resume support
    existing_results = load_existing_results(detailed_file)
    energy_data = load_existing_energy(energy_file)
    processed_indices = {r['idx'] for r in existing_results}
    remaining_samples = [s for s in samples if s.get('idx') not in processed_indices]

    if len(remaining_samples) < len(samples):
        print(f"Resuming: {len(existing_results)} done, {len(remaining_samples)} remaining")

    session_start = datetime.now().isoformat()
    tracker = OfflineEmissionsTracker(
        project_name=f"{exp_name}_session_{energy_data['sessions'] + 1}",
        output_dir=result_dir, country_iso_code="CAN", save_to_file=True,
    )
    tracker.start()

    results = list(existing_results)

    try:
        for i, sample in enumerate(remaining_samples):
            overall_idx = len(existing_results) + i + 1
            print(f"Processing sample {overall_idx}/{len(samples)} (idx: {sample.get('idx')})")

            # Format user prompt
            user_prompt = task_prompt.format(code=sample['func'])

            # Direct LLM call — no agent framework
            response_text = query_model(sys_prompt, user_prompt)

            result = {
                'idx': sample.get('idx'),
                'project': sample.get('project', ''),
                'commit_id': sample.get('commit_id', ''),
                'project_url': sample.get('project_url', ''),
                'commit_url': sample.get('commit_url', ''),
                'commit_message': sample.get('commit_message', ''),
                'ground_truth': sample.get('target'),
                'cwe': sample.get('cwe', ''),
                'cve': sample.get('cve', ''),
                'cve_desc': sample.get('cve_desc', ''),
            }

            if response_text is not None:
                prediction, reasoning = parse_vulnerability_response(response_text)
                result['vuln'] = prediction
                result['reasoning'] = reasoning
            else:
                result['vuln'] = 0
                result['reasoning'] = "No response from model"
                print(f"  [Warning] No response for sample {overall_idx}")

            append_result(result, detailed_file, csv_file)
            results.append(result)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {overall_idx}/{len(samples)}")

    finally:
        session_emissions = tracker.stop()
        energy_data['total_emissions'] += session_emissions
        energy_data['sessions'] += 1
        energy_data['session_history'].append({
            'session': energy_data['sessions'],
            'start_time': session_start,
            'end_time': datetime.now().isoformat(),
            'samples_processed': len(remaining_samples),
            'session_emissions': session_emissions,
        })
        save_energy_data(energy_data, energy_file)
        print(f"Session emissions: {session_emissions:.6f} kg CO2")
        print(f"Total emissions: {energy_data['total_emissions']:.6f} kg CO2")

    return results


# ================================================================
# MAIN
# ================================================================
def main():
    print(f"\nRunning {DESIGN} (direct model inference, no agent framework)...")
    print(f"Model: {model_name}")
    print(f"Temperature: {temperature}")

    samples = load_dataset(DATASET_FILE)
    print(f"Loaded {len(samples)} samples")

    if not samples:
        print("No samples found. Exiting.")
        return

    results = run_inference_with_emissions(
        samples, sys_prompt, task, exp_name, RESULT_DIR
    )

    # Evaluation
    predictions = [r['vuln'] for r in results]

    print("\n" + "=" * 60)
    print("RUNNING EVALUATIONS")
    print("=" * 60)

    for i, (fn, name) in enumerate([
        (normalize_vulnerability_basic, "basic"),
        (normalize_vulnerability_conservative, "conservative"),
        (normalize_vulnerability_strict, "strict"),
    ], 1):
        suffix = exp_name if name == "basic" else f"{exp_name}_{name}"
        print(f"\n[{i}/3] {name} normalization...")
        try:
            eval_result = evaluate_and_save_vulnerability(fn, predictions, DATASET_FILE, suffix)
            print(f"  Accuracy: {eval_result.get('accuracy', 0):.4f}")
        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("COMPLETED")
    print("=" * 60)
    print(f"Results: {RESULT_DIR}")
    print(f"Experiment: {exp_name}")


if __name__ == "__main__":
    main()
