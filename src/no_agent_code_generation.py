#!/usr/bin/env python3
"""
No-Agent Code Generation (Zero-Shot Version)
Compatible with reasoning model: qwen3:4b-thinking
"""

import os
import json
import time
import config
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
import requests
import subprocess
from config import CODE_GENERATION_TASK_PROMPT 

# ==============================================================================
# Configuration
# ==============================================================================
llm_config = config.LLM_CONFIG
DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

DESIGN = "no-agent-code-gen"
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
project_name = DESIGN.capitalize()
exp_name = f"{project_name}_{model}_{timestamp}"

# ==============================================================================
# Data Reading
# ==============================================================================
def read_code_generation_data(dataset_path):
    """Read code generation data from JSONL file."""
    code_problems = []
    with open(dataset_path, 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            code_problems.append(data)
    return code_problems


print(f"Reading dataset from: {DATASET_FILE}")
code_samples = read_code_generation_data(DATASET_FILE)
print(f"Loaded {len(code_samples)} code samples")

# ==============================================================================
# Helper Functions
# ==============================================================================
def generate_code_with_ollama(prompt, model_name, api_base, retries=2, timeout=300):
    """Robust Ollama API call for Qwen/Llama reasoning models."""
    import requests, time

    url = f"{api_base}/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    for attempt in range(retries + 1):
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                # ✅ Qwen-style response
                text = data.get("response", "").strip()
                if text:
                    return text
            print(f"[Attempt {attempt+1}] Empty response. Retrying...")
        except Exception as e:
            print(f"[Attempt {attempt+1}] Error: {e}")
        time.sleep(2)
    print("[Error] All attempts failed or returned empty text.")
    return ""

def enforce_ans_tags(text: str) -> str:
    """Ensure every code snippet has <ANS> ... </ANS> tags."""
    text = text.strip()
    if not text:
        return ""
    if not text.startswith("<ANS>"):
        text = "<ANS>\n" + text
    if not text.endswith("</ANS>"):
        text = text.rstrip() + "\n</ANS>"
    return text




def extract_code_from_response(response_text):
    """Extract code from <ANS></ANS> tags."""
    import re
    if not response_text:
        return ""

    # Remove reasoning/thinking blocks
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
    response_text = response_text.strip()

    # Extract content between <ANS> tags
    ans_pattern = r'<ANS>(.*?)</ANS>'
    matches = re.findall(ans_pattern, response_text, re.DOTALL | re.IGNORECASE)
    if matches:
        code = matches[0].strip()
    else:
        # Fallback: find def ... pattern if tags missing
        match = re.search(r"(def\s+\w+\(.*?\):[\s\S]+)", response_text)
        code = match.group(1).strip() if match else ""

    # Cleanup markdown or language prefixes
    code = code.strip('`').strip()
    if code.lower().startswith("python\n"):
        code = code[7:].strip()

    if len(code) < 10 or "def " not in code:
        print("[Warning] Malformed or empty code block detected.")
        return ""

    return code


# ==============================================================================
# Core Inference Loop (with emissions tracking)
# ==============================================================================
def run_inference_with_emissions(code_samples, llm_config, exp_name, result_dir):
    """Run code generation with emissions tracking and incremental saving."""
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")

    model_name = llm_config["config_list"][0]["model"]
    api_base = llm_config["config_list"][0]["api_base"]

    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        country_iso_code="CAN",
        save_to_file=True
    )
    tracker.start()

    try:
        for i, sample in enumerate(code_samples):
            print(f"\nProcessing sample {i+1}/{len(code_samples)} "
                  f"(task_id: {sample.get('task_id', i)})")

            # --- Build prompt using zero-shot template ---
            problem_prompt = sample.get('prompt', sample.get('description', ''))
            full_prompt = CODE_GENERATION_TASK_PROMPT.format(prompt=problem_prompt)

            if i == 0:
                print("\nDEBUG: First prompt preview:\n", full_prompt[:400], "\n")

            # --- Call model ---
            response_text = generate_code_with_ollama(full_prompt, model_name, api_base)

            # --- Store result ---
            result = {
                'task_id': sample.get('task_id', ''),
                'prompt': problem_prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', '')
            }

            if response_text:
                generated_code = extract_code_from_response(response_text)

                generated_code = enforce_ans_tags(generated_code)

                result['generated_solution'] = generated_code
            else:
                result['generated_solution'] = ""
                print(f"[Warning] Skipped sample {i} — no response.")



            # --- Save incrementally ---
            with open(detailed_file, 'a') as f:
                f.write(json.dumps(result) + '\n')

            if (i + 1) % 10 == 0:
                print(f"Progress saved: {i + 1}/{len(code_samples)} samples done.")

    finally:
        emissions = tracker.stop()
        print(f"\nEmissions logged: {emissions} kg CO₂\n")

    return detailed_file


# ==============================================================================
# Main Execution
# ==============================================================================
time.sleep(1)
print(f"Running {DESIGN} code generation (no agent framework)...")

detailed_file = run_inference_with_emissions(
    code_samples,
    llm_config,
    exp_name,
    RESULT_DIR
)

print(f"\nCode generation completed for experiment: {exp_name}")
print(f"Total samples processed: {len(code_samples)}")
print(f"Results saved to: {detailed_file}")

# ==============================================================================
# Evaluation
# ==============================================================================
print("\n" + "=" * 80)
print("STARTING EVALUATION")
print("=" * 80)

try:
    eval_result = subprocess.run(
        ["python", "src/evaluate_code_generation.py", detailed_file],
        capture_output=True,
        text=True
    )
    print(eval_result.stdout)

    if eval_result.returncode != 0:
        print("Evaluation encountered an error:")
        print(eval_result.stderr)
    else:
        print("\n" + "=" * 80)
        print("EVALUATION COMPLETED SUCCESSFULLY")
        print("=" * 80)

except Exception as e:
    print(f"Failed to run evaluation: {e}")
    print("You can manually evaluate by running:")
    print(f"python src/evaluate_code_generation.py {detailed_file}")
