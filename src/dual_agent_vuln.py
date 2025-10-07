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
def initialize_results_files(exp_name, result_dir):
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")
    energy_file = os.path.join(result_dir, f"{exp_name}_energy_tracking.json")

    with open(csv_file, 'w') as f:
        f.write("idx,project,commit_id,project_url,commit_url,commit_message,"
                "ground_truth,vuln,reasoning,cwe,cve,cve_desc,iteration_1_feedback,"
                "iteration_2_decision\n")

    return detailed_file, csv_file, energy_file


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
            escape(result.get('iteration_2_decision', ''))
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
def run_dual_agent_inference_with_emissions(samples, llm_config, exp_name, result_dir):
    detailed_file, csv_file, energy_file = initialize_results_files(exp_name, result_dir)
    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        save_to_file=True,
        country_iso_code="CAN"
    )

    tracker.start()

    user_proxy, code_author, security_analyst = create_vulnerability_agents(llm_config)
    results = []

    try:
        for i, sample in enumerate(samples):
            print(f"\n--- Processing sample {i+1}/{len(samples)} (idx: {sample['idx']}) ---")

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
                'timestamp': datetime.now().isoformat()
            }

            append_result(result, detailed_file, csv_file)
            results.append(result)

            if (i + 1) % 5 == 0:
                print(f"Progress saved: {i+1} samples")

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
    results = run_dual_agent_inference_with_emissions(samples, llm_config, exp_name, RESULT_DIR)

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