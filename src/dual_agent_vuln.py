import os
import json
import config
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
from vuln_evaluation import evaluate_and_save_vulnerability, normalize_vulnerability_basic
from agent_utils_vuln import create_agent
from autogen.agentchat.conversable_agent import ConversableAgent
from pathlib import Path

# --- Configuration ---
llm_config = config.LLM_CONFIG
DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

DESIGN = "DA-vuln-two"  # Dual Agent design
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"


# --- Agent Creation ---
def create_vulnerability_agents(llm_config):
    """Create the two vulnerability detection agents"""
    user_proxy = create_agent(
        "conversable",
        "user_proxy_agent",
        llm_config,
        sys_prompt="A human admin coordinating the vulnerability assessment.",
        description="A proxy for human input coordinating the dual-agent vulnerability assessment."
    )

    code_author = create_agent(
        "assistant",
        "code_author_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_CODE_AUTHOR,
        description="Generate and revise code based on security feedback."
    )

    security_analyst = create_agent(
        "assistant", 
        "security_analyst_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_SECURITY_ANALYST,
        description="Analyze code for vulnerabilities, provide feedback, and make final decisions."
    )

    return user_proxy, code_author, security_analyst


# --- Data Loading ---
def load_vulnerability_dataset(file_path):
    """Load vulnerability dataset from JSONL file"""
    samples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if 'func' in data and 'target' in data:
                    sample = {
                        'idx': data.get('idx'),
                        'project': data.get('project'),
                        'commit_id': data.get('commit_id'),
                        'project_url': data.get('project_url'),
                        'commit_url': data.get('commit_url'),
                        'commit_message': data.get('commit_message'),
                        'func': data['func'],
                        'target': data['target'],
                        'cwe': data.get('cwe'),
                        'cve': data.get('cve'),
                        'cve_desc': data.get('cve_desc')
                    }
                    samples.append(sample)
            except json.JSONDecodeError:
                continue
    return samples


# --- Result Helpers ---
def find_most_recent_results(result_dir, design, model):
    """Find the most recent result files for this design/model combination"""
    import glob
    pattern = f"{design}_{model}_*_detailed_results.jsonl"
    matching_files = glob.glob(os.path.join(result_dir, pattern))

    if matching_files:
        # Sort by modification time, get most recent
        most_recent = max(matching_files, key=os.path.getmtime)
        # Extract the base name (without _detailed_results.jsonl)
        base_name = os.path.basename(most_recent).replace('_detailed_results.jsonl', '')
        print(f"[RESUME] Found existing results: {most_recent}")
        print(f"[RESUME] Will continue from where it left off")
        return base_name
    return None


def initialize_results_files(exp_name, result_dir, design, model):
    """Initialize result files for incremental saving, or resume existing"""

    skip_next_sample = False

    # Check if we should resume from an existing run
    existing_base = find_most_recent_results(result_dir, design, model)
    if existing_base:
        # Prompt user to decide whether to resume
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

    # Initialize detailed results JSON file
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")

    # Initialize CSV file with headers (only if new file)
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")
    if not os.path.exists(csv_file):
        with open(csv_file, 'w') as f:
            f.write("idx,project,commit_id,project_url,commit_url,commit_message,"
                    "ground_truth,vuln,reasoning,cwe,cve,cve_desc,iteration_1_feedback,"
                    "iteration_2_decision,error\n")

    # Initialize energy tracking file
    energy_file = os.path.join(result_dir, f"{exp_name}_energy_tracking.json")

    return detailed_file, csv_file, energy_file, skip_next_sample


def load_existing_results(detailed_file):
    """Load existing results if the script was interrupted"""
    results = []
    if os.path.exists(detailed_file):
        print(f"Found existing results file: {detailed_file}")
        with open(detailed_file, 'r') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line.strip()))
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


def append_result(result, detailed_file, csv_file):
    """Append a result to both JSONL and CSV"""
    with open(detailed_file, 'a') as f:
        f.write(json.dumps(result) + '\n')

    with open(csv_file, 'a') as f:
        def escape(field):
            if field is None:
                return ""
            field_str = str(field)
            if ',' in field_str or '"' in field_str or '\n' in field_str:
                return '"' + field_str.replace('"', '""') + '"'
            return field_str

        row = [
            escape(result['idx']),
            escape(result['project']),
            escape(result['commit_id']),
            escape(result['project_url']),
            escape(result['commit_url']),
            escape(result['commit_message']),
            escape(result['ground_truth']),
            escape(result['vuln']),
            escape(result['reasoning']),
            escape(result['cwe']),
            escape(result['cve']),
            escape(result['cve_desc']),
            escape(result.get('iteration_1_feedback', '')),
            escape(result.get('iteration_2_decision', '')),
            escape(result.get('error', ''))
        ]
        f.write(','.join(row) + '\n')


def extract_vulnerability_decision(analyst_response):
    """Parse security analyst response into (decision, reasoning)"""
    try:
        # Try to parse as JSON first
        if analyst_response.strip().startswith('{') or analyst_response.strip().startswith('['):
            decision_data = json.loads(analyst_response.strip())
            if isinstance(decision_data, dict):
                decision = decision_data.get('vulnerability_detected', False)
                reasoning = decision_data.get('reasoning', analyst_response)
            elif isinstance(decision_data, list) and len(decision_data) > 0:
                decision = any(item.get('vulnerability_detected', False) for item in decision_data)
                reasoning = "; ".join(item.get('reasoning', '') for item in decision_data)
            else:
                decision = False
                reasoning = analyst_response
        else:
            # Parse text-based response
            text = analyst_response.lower()
            decision = any(keyword in text for keyword in [
                'vulnerability detected', 'vulnerable', 'security risk', 
                'exploit', 'attack vector', 'unsafe'
            ])
            reasoning = analyst_response
            
        return (1 if decision else 0), reasoning
    except Exception as e:
        print(f"Error parsing analyst response: {e}")
        # Fallback: keyword-based detection
        text = analyst_response.lower()
        decision = any(keyword in text for keyword in [
            'vulnerability', 'vulnerable', 'security risk', 'exploit'
        ])
        return (1 if decision else 0), analyst_response


# --- Dual Agent Inference ---
def run_dual_agent_inference_with_emissions(samples, llm_config, exp_name, result_dir, design, model):
    # Initialize result files (will resume from existing if found)
    detailed_file, csv_file, energy_file, skip_next_sample = initialize_results_files(exp_name, result_dir, design, model)

    # Load existing results and energy data if any (for resuming interrupted runs)
    existing_results = load_existing_results(detailed_file)
    energy_data = load_existing_energy(energy_file)
    processed_indices = {r['idx'] for r in existing_results}

    # Filter out already processed samples
    remaining_samples = [s for s in samples if s['idx'] not in processed_indices]

    # If user chose to skip the next sample, mark it as failed and remove from queue
    if skip_next_sample and remaining_samples:
        skip_sample = remaining_samples[0]
        print(f"[SKIP] Marking sample {skip_sample['idx']} as FAILED and skipping")

        # Create failed result
        failed_result = {
            'idx': skip_sample['idx'],
            'project': skip_sample['project'],
            'commit_id': skip_sample['commit_id'],
            'project_url': skip_sample['project_url'],
            'commit_url': skip_sample['commit_url'],
            'commit_message': skip_sample['commit_message'],
            'func': skip_sample['func'],
            'ground_truth': skip_sample['target'],
            'vuln': -1,  # Mark as skipped
            'reasoning': 'SKIPPED - Sample marked as problematic by user',
            'cwe': skip_sample.get('cwe'),
            'cve': skip_sample.get('cve'),
            'cve_desc': skip_sample.get('cve_desc'),
            'iteration_1_feedback': '',
            'iteration_2_decision': '',
            'error': 'USER_SKIP'
        }

        # Save the failed result
        append_result(failed_result, detailed_file, csv_file)
        existing_results.append(failed_result)

        # Remove from remaining samples
        remaining_samples = remaining_samples[1:]

    print(f"\n{'='*80}")
    print(f"Processing {len(remaining_samples)} remaining samples (out of {len(samples)} total)")
    print(f"Already completed: {len(processed_indices)} samples")
    print(f"{'='*80}\n")

    # Start CodeCarbon tracker
    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        save_to_file=True,
        country_iso_code="CAN"
    )

    tracker.start()

    user_proxy, code_author, security_analyst = create_vulnerability_agents(llm_config)
    results = existing_results.copy()  # Start with existing results

    try:
        for i, sample in enumerate(remaining_samples):
            print(f"\n--- Processing sample {i+1}/{len(remaining_samples)} (idx: {sample['idx']}) ---")

            try:
                # ITERATION 1: Initial submission and feedback
                print("Iteration 1: Code submission and initial analysis...")

                # Code author submits the code
                submission = user_proxy.initiate_chat(
                    recipient=code_author,
                    message=config.DUAL_AGENT_TASK_CODE_SUBMISSION.format(code=sample['func']),
                    max_turns=1,
                    summary_method="last_msg"
                ).summary.strip()

                # Security analyst provides feedback
                feedback = user_proxy.initiate_chat(
                    recipient=security_analyst,
                    message=config.DUAL_AGENT_TASK_SECURITY_FEEDBACK.format(
                        code=sample['func'],
                        submission=submission
                    ),
                    max_turns=1,
                    summary_method="last_msg"
                ).summary.strip()

                # ITERATION 2: Revision and final decision
                print("Iteration 2: Code revision and final assessment...")

                # Code author revises based on feedback
                revision = user_proxy.initiate_chat(
                    recipient=code_author,
                    message=config.DUAL_AGENT_TASK_CODE_REVISION.format(
                        original_code=sample['func'],
                        feedback=feedback
                    ),
                    max_turns=1,
                    summary_method="last_msg"
                ).summary.strip()

                # Security analyst makes final decision
                final_decision = user_proxy.initiate_chat(
                    recipient=security_analyst,
                    message=config.DUAL_AGENT_TASK_FINAL_DECISION.format(
                        original_code=sample['func'],
                        revised_analysis=revision,
                        previous_feedback=feedback
                    ),
                    max_turns=1,
                    summary_method="last_msg"
                ).summary.strip()

                # Extract final vulnerability decision
                vuln_decision, reasoning = extract_vulnerability_decision(final_decision)

                result = {
                    'idx': sample['idx'],
                    'project': sample['project'],
                    'commit_id': sample['commit_id'],
                    'project_url': sample['project_url'],
                    'commit_url': sample['commit_url'],
                    'commit_message': sample['commit_message'],
                    'ground_truth': sample['target'],
                    'vuln': vuln_decision,
                    'reasoning': reasoning,
                    'dual_agent_conversation': {
                        'iteration_1_submission': submission,
                        'iteration_1_feedback': feedback,
                        'iteration_2_revision': revision,
                        'iteration_2_final_decision': final_decision
                    },
                    'iteration_1_feedback': feedback,
                    'iteration_2_decision': final_decision,
                    'cwe': sample['cwe'],
                    'cve': sample['cve'],
                    'cve_desc': sample['cve_desc'],
                    'session': 1,
                    'timestamp': datetime.now().isoformat(),
                    'error': ''
                }

                append_result(result, detailed_file, csv_file)
                results.append(result)

                if (i + 1) % 5 == 0:
                    print(f"Progress saved: {i+1} samples")

            except Exception as e:
                print(f"ERROR processing sample {sample['idx']}: {e}")
                # Save failed result
                failed_result = {
                    'idx': sample['idx'],
                    'project': sample['project'],
                    'commit_id': sample['commit_id'],
                    'project_url': sample['project_url'],
                    'commit_url': sample['commit_url'],
                    'commit_message': sample['commit_message'],
                    'ground_truth': sample['target'],
                    'vuln': -1,
                    'reasoning': f'ERROR: {str(e)}',
                    'cwe': sample['cwe'],
                    'cve': sample['cve'],
                    'cve_desc': sample['cve_desc'],
                    'iteration_1_feedback': '',
                    'iteration_2_decision': '',
                    'error': str(e)
                }
                append_result(failed_result, detailed_file, csv_file)
                results.append(failed_result)
                continue

    finally:
        emissions = tracker.stop()
        print(f"\nEmissions this run: {emissions:.6f} kg CO2")

    return results


# --- Main Execution ---
def main():
    print("Loading dataset...")
    samples = load_vulnerability_dataset(DATASET_FILE)
    print(f"Loaded {len(samples)} samples")

    print(f"Running {DESIGN} dual-agent vulnerability detection...")
    results = run_dual_agent_inference_with_emissions(samples, llm_config, exp_name, RESULT_DIR, DESIGN, model)

    predictions = [r['vuln'] for r in results]
    ground_truth = [r['ground_truth'] for r in results]

    try:
        eval_results = evaluate_and_save_vulnerability(
            normalize_vulnerability_basic,
            predictions,
            DATASET_FILE,
            exp_name
        )
        print("Evaluation Results:", eval_results)
    except Exception as e:
        print("Evaluation failed:", e)

    print("\n=== FINAL SUMMARY ===")
    print(f"Samples processed: {len(results)}")
    print("Dual-agent vulnerability detection completed!")


if __name__ == "__main__":
    main()