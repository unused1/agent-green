# ================================================================
# Dual-Agent Vulnerability Detection
# ================================================================

import os
import json
import argparse
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
from sklearn.metrics import classification_report, confusion_matrix
import time
from ollama_utils import start_ollama_server,stop_ollama_server
import config
from vuln_evaluation import evaluate_and_save_vulnerability, normalize_vulnerability_basic
from agent_utils_vuln import create_agent


# ================================================================
# CONFIGURATION
# ================================================================
llm_config = config.LLM_CONFIG
DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)


# ================================================================
# Helper functions
# ================================================================
def find_most_recent_results(result_dir, design, model):
    """Find the most recent result files for this design/model combination"""
    import glob
    pattern = f"{design}_{model}_*_detailed_results.jsonl"
    matching_files = glob.glob(os.path.join(result_dir, pattern))

    if matching_files:
        most_recent = max(matching_files, key=os.path.getmtime)
        base_name = os.path.basename(most_recent).replace('_detailed_results.jsonl', '')
        print(f"[RESUME] Found existing results: {most_recent}")
        return base_name
    return None


def initialize_results_files(exp_name, result_dir, header_fields, design=None, model=None):
    """Initialize result files for incremental saving, or resume existing"""
    skip_next_sample = False

    # Check if we should resume from an existing run
    if design and model:
        existing_base = find_most_recent_results(result_dir, design, model)
        if existing_base:
            print(f"\n[FOUND] Existing experiment: {existing_base}")
            print("Options:")
            print("  1. Resume from last completed sample (continue normally)")
            print("  2. Skip the next sample and mark as failed (if it's problematic)")
            print("  3. Start a fresh new experiment")

            response = input("\nEnter choice (1/2/3): ").strip()

            if response == '1':
                exp_name = existing_base
                print(f"[RESUME] Continuing with experiment: {exp_name}")
            elif response == '2':
                exp_name = existing_base
                skip_next_sample = True
                print(f"[RESUME] Will skip the next problematic sample and mark as FAILED")
            else:
                print(f"[NEW] Starting fresh experiment: {exp_name}")

    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")
    energy_file = os.path.join(result_dir, f"{exp_name}_energy_tracking.json")

    # Only write CSV header if starting fresh
    if not os.path.exists(csv_file):
        with open(csv_file, "w") as f:
            f.write(",".join(header_fields) + "\n")

    return detailed_file, csv_file, energy_file, skip_next_sample, exp_name


def load_existing_results(detailed_file):
    """Load existing results if the script was interrupted"""
    results = []
    if os.path.exists(detailed_file):
        print(f"Found existing results file: {detailed_file}")
        with open(detailed_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        results.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        print(f"Loaded {len(results)} existing results")
    return results


def load_existing_energy(energy_file):
    """Load existing energy consumption data"""
    if os.path.exists(energy_file):
        with open(energy_file, 'r') as f:
            energy_data = json.load(f)
        print(f"Loaded existing energy data: {energy_data['total_emissions']:.6f} kg CO2 from {energy_data['sessions']} sessions")
        return energy_data
    else:
        return {
            "total_emissions": 0.0,
            "sessions": 0,
            "session_history": []
        }


def save_energy_data(energy_data, energy_file):
    """Save updated energy consumption data"""
    with open(energy_file, 'w') as f:
        json.dump(energy_data, f, indent=2)


def append_result(result, detailed_file, csv_file, header_fields):
    with open(detailed_file, "a") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    def esc(x):
        if x is None:
            return ""
        s = str(x)
        if "," in s or '"' in s or "\n" in s:
            return '"' + s.replace('"', '""') + '"'
        return s

    with open(csv_file, "a") as f:
        row = [esc(result.get(h, "")) for h in header_fields]
        f.write(",".join(row) + "\n")


# ================================================================
# DECISION PARSER
# ================================================================
def extract_vulnerability_decision(response):
    """Extract (1=vulnerable, 0=safe) and reasoning text."""
    try:
        text = response.strip()
        if text.startswith("{") or text.startswith("["):
            data = json.loads(text)
            if isinstance(data, dict):
                decision = data.get("vulnerability_detected", False)
                reasoning = data.get("analysis", data.get("reasoning", text))
            elif isinstance(data, list):
                decision = any(d.get("vulnerability_detected", False) for d in data)
                reasoning = "; ".join(d.get("analysis", d.get("reasoning", "")) for d in data)
            else:
                decision, reasoning = False, text
        else:
            lowered = text.lower()
            decision = any(k in lowered for k in ["vulnerable", "unsafe", "security issue"])
            reasoning = text
            
        return (1 if decision else 0), reasoning
    except Exception as e:
        return 0, f"Error parsing: {e}"


# ================================================================
# VulTrial metrics calculation
# ================================================================
def calculate_pair_wise_metrics(predictions, ground_truth):
    """
    Calculate pair-wise metrics (P-C, P-V, P-B, P-R) for VulTrial compatibility.
    """
    total_samples = len(predictions)
    
    # P-C: Percentage of samples correctly classified (both vulnerable and benign)
    p_c = sum(p == g for p, g in zip(predictions, ground_truth)) / total_samples
    
    # P-V: Percentage of vulnerable samples correctly classified
    vulnerable_samples = [i for i, g in enumerate(ground_truth) if g == 1]
    p_v = sum(predictions[i] == 1 for i in vulnerable_samples) / len(vulnerable_samples) if vulnerable_samples else 0
    
    # P-B: Percentage of benign samples correctly classified
    benign_samples = [i for i, g in enumerate(ground_truth) if g == 0]
    p_b = sum(predictions[i] == 0 for i in benign_samples) / len(benign_samples) if benign_samples else 0
    
    # P-R: Percentage of samples with reversed classification
    p_r = sum(p != g for p, g in zip(predictions, ground_truth)) / total_samples
    
    # FPR: False Positive Rate
    fpr = sum(predictions[i] == 1 and ground_truth[i] == 0 for i in range(total_samples)) / len(benign_samples) if benign_samples else 0
    
    return {
        "P-C": p_c * 100,
        "P-V": p_v * 100,
        "P-B": p_b * 100,
        "P-R": p_r * 100,
        "FPR": fpr * 100
    }


# ================================================================
# Metrics CSV output
# ================================================================
def save_metrics_csv(preds, gts, exp_name, result_dir):
    """Save metrics in simple CSV format."""
    # Calculate confusion matrix elements
    TP = sum(1 for p, g in zip(preds, gts) if p == 1 and g == 1)
    FP = sum(1 for p, g in zip(preds, gts) if p == 1 and g == 0)
    TN = sum(1 for p, g in zip(preds, gts) if p == 0 and g == 0)
    FN = sum(1 for p, g in zip(preds, gts) if p == 0 and g == 1)
    
    accuracy = (TP + TN) / len(preds) if preds else 0
    
    # Save metrics CSV
    metrics_file = os.path.join(result_dir, f"{exp_name}_metrics.csv")
    with open(metrics_file, "w") as f:
        f.write("Accuracy,TP,FP,TN,FN\n")
        f.write(f"{accuracy:.4f},{TP},{FP},{TN},{FN}\n")
    
    print(f"Metrics saved to {metrics_file}")
    
    return {
        "TP": TP,
        "FP": FP,
        "TN": TN,
        "FN": FN,
        "accuracy": accuracy
    }


# ================================================================
# Agent creation
# ================================================================
def create_dual_agents(llm_config, prompt_type="zero_shot"):
    """Create Code Author + Security Analyst agents (few/zero shot)."""
    if prompt_type == "few_shot":
        code_author_prompt = config.SYS_MSG_CODE_AUTHOR_DUAL_FEW_SHOT
        analyst_prompt = config.SYS_MSG_SECURITY_ANALYST_FEW_SHOT
        print("Using FEW-SHOT prompts for both agents.")
    else:
        code_author_prompt = config.SYS_MSG_CODE_AUTHOR_DUAL_ZERO_SHOT
        analyst_prompt = config.SYS_MSG_SECURITY_ANALYST_ZERO_SHOT
        print("Using ZERO-SHOT prompts for both agents.")

    code_author = create_agent(
        "assistant", "code_author_agent", llm_config,
        sys_prompt=code_author_prompt,
        description="Explains or defends the code snippet."
    )

    security_analyst = create_agent(
        "assistant", "security_analyst_agent", llm_config,
        sys_prompt=analyst_prompt,
        description="Analyzes the code and produces final vulnerability decision."
    )

    return code_author, security_analyst


# ================================================================
# Inference with emissions tracking
# ================================================================
def run_inference_with_emissions(samples, llm_config, exp_name, result_dir, prompt_type, design=None, model=None):
    dataset_keys = list(samples[0].keys()) if samples else []
    header_fields = dataset_keys + ["vuln", "reasoning", "timestamp"]

    # Initialize result files (will resume from existing if found)
    detailed_file, csv_file, energy_file, skip_next_sample, exp_name = initialize_results_files(
        exp_name, result_dir, header_fields, design, model
    )

    # Load existing results and energy data
    existing_results = load_existing_results(detailed_file)
    energy_data = load_existing_energy(energy_file)
    processed_indices = {r.get('idx', r.get('id', -1)) for r in existing_results}

    # Filter out already processed samples
    remaining_samples = [s for s in samples if s.get('idx', s.get('id', -1)) not in processed_indices]

    # Handle skip next sample option
    if skip_next_sample and remaining_samples:
        skip_sample = remaining_samples[0]
        print(f"[SKIP] Marking sample {skip_sample.get('idx', 'unknown')} as FAILED and skipping")

        failed_result = dict(skip_sample)
        failed_result.update({
            "vuln": -1,
            "reasoning": "SKIPPED - Sample marked as problematic by user",
            "timestamp": datetime.now().isoformat(),
            "error": "USER_SKIP"
        })
        append_result(failed_result, detailed_file, csv_file, header_fields)
        existing_results.append(failed_result)
        remaining_samples = remaining_samples[1:]

    print(f"\nProcessing {len(remaining_samples)} remaining samples (out of {len(samples)} total)")
    print(f"Already completed: {len(processed_indices)} samples\n")

    tracker = OfflineEmissionsTracker(
        project_name=exp_name, output_dir=result_dir, save_to_file=True, country_iso_code="CAN"
    )
    tracker.start()

    code_author, security_analyst = create_dual_agents(llm_config, prompt_type)
    results, errors = existing_results.copy(), 0

    try:
        for i, s in enumerate(remaining_samples):
            print(f"\n--- Processing sample {i+1}/{len(remaining_samples)} ---")

            try:
                #Code Author Stage
                author_task = config.DUAL_AGENT_TASK_CODE_SUBMISSION.format(code=s["func"])
                author_submission = code_author.generate_reply(messages=[{
                    "role": "user", 
                    "content": author_task
                }])
                if isinstance(author_submission, dict):
                    author_submission = author_submission.get("content", "")
                author_submission = str(author_submission).strip()
                print(f"  ✓ Author submission: {len(author_submission)} chars")

                #Security Analyst Stage
                analyst_task = config.DUAL_AGENT_TASK_FINAL_DECISION.format(
                    code=s["func"], author_response=author_submission
                )
                # Add an emphasis note to increase vulnerability detection
                analyst_task = f"""You are the Security Analyst reviewing the Code Author's explanation.
When in doubt, err on the side of caution and consider code vulnerable.
Security vulnerabilities can be subtle, so even minor issues should be flagged.
The absence of security measures is often itself a vulnerability.

{analyst_task}"""
                
                analyst_feedback = security_analyst.generate_reply(messages=[{
                    "role": "user",
                    "content": analyst_task
                }])
                if isinstance(analyst_feedback, dict):
                    analyst_feedback = analyst_feedback.get("content", "")
                analyst_feedback = str(analyst_feedback).strip()
                print(f"  ✓ Analyst feedback: {len(analyst_feedback)} chars")

                # Extract decision
                vuln, reasoning = extract_vulnerability_decision(analyst_feedback)
                
                result = dict(s)
                result.update({
                    "vuln": vuln,
                    "reasoning": reasoning,
                    "discussion": {
                        "author_submission": author_submission,
                        "analyst_feedback": analyst_feedback
                    },
                    "timestamp": datetime.now().isoformat(),
                })

                append_result(result, detailed_file, csv_file, header_fields)
                results.append(result)
                print(f"Completed: vuln={vuln}, gt={s.get('target')}")

            except Exception as e:
                errors += 1
                print(f"Error: {e}")
                result = dict(s)
                result.update({
                    "vuln": 0,
                    "reasoning": f"ERROR: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "skipped": True,
                })
                append_result(result, detailed_file, csv_file, header_fields)
                results.append(result)

    finally:
        emissions = tracker.stop()
        print(f"\nEmissions this run: {emissions:.6f} kg CO₂")

        # Update energy tracking
        energy_data['total_emissions'] += emissions
        energy_data['sessions'] += 1
        energy_data['session_history'].append({
            'timestamp': datetime.now().isoformat(),
            'emissions_kg_co2': emissions,
            'samples_processed': len(remaining_samples)
        })
        save_energy_data(energy_data, energy_file)

        print(f"Total emissions (all sessions): {energy_data['total_emissions']:.6f} kg CO₂")
        print(f"Errors encountered: {errors}")

    return results


# ================================================================
# Main entry point
# ================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt_type", choices=["zero_shot", "few_shot"], default="zero_shot")
    args = parser.parse_args()

    prompt_type = args.prompt_type
    DESIGN = f"DA-vuln-two-{prompt_type}"

    model = llm_config["config_list"][0]["model"].replace(":", "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_name = f"{DESIGN}_{model}_vuln_{timestamp}"

    print("Starting Ollama server ....")
    proc = start_ollama_server()
    time.sleep(5)
    try:
        print("Loading dataset...")
        samples = []
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if "func" in data and "target" in data:
                        samples.append(data)
                except json.JSONDecodeError:
                    continue

        print(f"Loaded {len(samples)} samples.")
        if not samples:
            print("No valid samples found. Exiting.")
            return

        print(f"Running {DESIGN} (1 round per agent, {prompt_type.upper()} mode)...")
        results = run_inference_with_emissions(samples, llm_config, exp_name, RESULT_DIR, prompt_type, DESIGN, model)

    except Exception as e:
        print(f"Error during inference: {e}")
    
    finally:
        print("Stopping Ollama server ....")
        stop_ollama_server(proc)
    # ==================== Inline Evaluation ====================
    preds = [r.get("vuln", 0) for r in results]
    gts = [r.get("target", 0) for r in results]
    
    # Calculate metrics
    acc = sum(p == g for p, g in zip(preds, gts)) / len(results) if results else 0
    cm = confusion_matrix(gts, preds)
    report = classification_report(gts, preds, target_names=["Not Vulnerable", "Vulnerable"])

    print("\n=== EVALUATION SUMMARY ===")
    print(f"Samples evaluated: {len(results)}")
    print(f"Accuracy: {acc:.4f}")
    print("\nConfusion Matrix:\n", cm)
    print("\nClassification Report:\n", report)

    # Calculate VulTrial metrics
    pair_wise_metrics = calculate_pair_wise_metrics(preds, gts)
    print("\nPair-wise Metrics (VulTrial):")
    for metric, value in pair_wise_metrics.items():
        print(f"{metric}: {value:.2f}%")
    
    # Save simple metrics CSV
    metrics_details = save_metrics_csv(preds, gts, exp_name, RESULT_DIR)
    
    # Save distribution information
    vulnerable_count = sum(preds)
    vuln_ratio = vulnerable_count / len(preds) if preds else 0
    print(f"\nVulnerability detection ratio: {vuln_ratio:.4f} ({vulnerable_count}/{len(preds)})")

    # Append summary to same file
    detailed_file = os.path.join(RESULT_DIR, f"{exp_name}_detailed_results.jsonl")
    eval_summary = {
        "evaluation_summary": {
            "accuracy": round(acc, 4),
            "confusion_matrix": cm.tolist(),
            "classification_report": report,
            "pair_wise_metrics": {k: round(v, 2) for k, v in pair_wise_metrics.items()},
            "confusion_elements": {
                "TP": metrics_details['TP'],
                "FP": metrics_details['FP'],
                "TN": metrics_details['TN'],
                "FN": metrics_details['FN']
            }
        }
    }
    with open(detailed_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(eval_summary, ensure_ascii=False) + "\n")

    print(f"Evaluation results appended to {detailed_file}")

    try:
        evaluate_and_save_vulnerability(normalize_vulnerability_basic, preds, DATASET_FILE, exp_name)
    except Exception as e:
        print(f"Evaluation skipped due to: {e}")

    print("\n=== FINAL SUMMARY ===")
    print(f"Samples processed: {len(results)}")
    print("Dual-agent vulnerability detection completed successfully.")


if __name__ == "__main__":
    main()
    
