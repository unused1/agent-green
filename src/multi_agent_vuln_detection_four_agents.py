import os
import json
import argparse

# Dynamic config selection based on MODEL_FAMILY environment variable
# Usage: MODEL_FAMILY=nemotron python src/multi_agent_vuln_detection_four_agents.py --prompt_type few_shot
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
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
from vuln_evaluation import evaluate_and_save_vulnerability, normalize_vulnerability_basic
from agent_utils_vuln import create_agent
from resume_utils import ExperimentResume
from autogen.agentchat.conversable_agent import ConversableAgent
from pathlib import Path

# ---------------------------
# Parse Command Line Args
# ---------------------------
def parse_arguments():
    parser = argparse.ArgumentParser(description="Multi-Agent Vulnerability Detection (4 Agents)")
    parser.add_argument(
        "--prompt_type",
        type=str,
        choices=["zero_shot", "few_shot"],
        default="zero_shot",
        help="Prompt type: zero_shot, few_shot (default: zero_shot)"
    )
    return parser.parse_args()

args = parse_arguments()

# ---------------------------
# Configuration
# ---------------------------
llm_config = config.LLM_CONFIG
DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

# Design configuration
DESIGN = f"MA-vuln-four-{args.prompt_type}"
model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

print(f"Experiment: {exp_name}")
print(f"Dataset: {DATASET_FILE}")
print(f"Prompt Type: {args.prompt_type}")
print(f"Results will be saved to: {RESULT_DIR}")

# ---------------------------
# System Prompts Selection
# ---------------------------
if args.prompt_type == "zero_shot":
    researcher_prompt = config.SYS_MSG_SECURITY_RESEARCHER_ZERO_SHOT
    author_prompt = config.SYS_MSG_CODE_AUTHOR_ZERO_SHOT
    moderator_prompt = config.SYS_MSG_MODERATOR_ZERO_SHOT
    review_board_prompt = config.SYS_MSG_REVIEW_BOARD_ZERO_SHOT
else:  # few_shot
    researcher_prompt = config.SYS_MSG_SECURITY_RESEARCHER_FEW_SHOT
    author_prompt = config.SYS_MSG_CODE_AUTHOR_FEW_SHOT
    moderator_prompt = config.SYS_MSG_MODERATOR_FEW_SHOT
    review_board_prompt = config.SYS_MSG_REVIEW_BOARD_FEW_SHOT

# --- Agent Creation ---
def create_vulnerability_agents(llm_config, prompts):
    """Create the four vulnerability detection agents"""
    researcher_prompt, author_prompt, moderator_prompt, review_board_prompt = prompts

    user_proxy = create_agent(
        "conversable",
        "user_proxy_agent",
        llm_config,
        sys_prompt="A human admin coordinating the vulnerability assessment.",
        description="A proxy for human input coordinating the multi-agent vulnerability assessment."
    )

    security_researcher = create_agent(
        "assistant",
        "security_researcher_agent",
        llm_config,
        sys_prompt=researcher_prompt,
        description="Identify potential security vulnerabilities in code."
    )

    code_author = create_agent(
        "assistant",
        "code_author_agent",
        llm_config,
        sys_prompt=author_prompt,
        description="Defend code against vulnerability claims or propose mitigations."
    )

    moderator = create_agent(
        "assistant",
        "moderator_agent",
        llm_config,
        sys_prompt=moderator_prompt,
        description="Provide neutral summaries of the vulnerability discussion."
    )

    review_board = create_agent(
        "assistant",
        "review_board_agent",
        llm_config,
        sys_prompt=review_board_prompt,
        description="Make final decisions on vulnerability validity and severity."
    )

    return user_proxy, security_researcher, code_author, moderator, review_board


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
# NOTE: Resume functionality now handled by ExperimentResume class from resume_utils


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
            escape(result['cve_desc'])
        ]
        f.write(','.join(row) + '\n')


def extract_vulnerability_decision(review_board_response):
    """Parse review board response into (decision, reasoning)"""
    try:
        verdicts = json.loads(review_board_response.strip())
        has_vulnerability = any(v.get('decision') in ['valid', 'partially valid'] for v in verdicts)
        reasoning = "; ".join(
            f"{v.get('vulnerability','Unknown')}: {v.get('decision','Unknown')} ({v.get('reason','No reason')})"
            for v in verdicts
        )
        return (1 if has_vulnerability else 0), reasoning
    except Exception:
        text = review_board_response.lower()
        if any(k in text for k in ['valid', 'vulnerability', 'security risk']):
            return 1, review_board_response
        return 0, review_board_response


# --- Inference with Emissions ---
def run_inference_with_emissions(samples, llm_config, exp_name, result_dir, design, model, prompts):
    # Initialize resume helper
    resume = ExperimentResume(result_dir, design, model, exp_name)
    exp_name, detailed_file, energy_file, skip_next_sample = resume.initialize()

    # Setup CSV file (vuln-specific)
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")
    if not os.path.exists(csv_file):
        with open(csv_file, 'w') as f:
            f.write("idx,project,commit_id,project_url,commit_url,commit_message,"
                    "ground_truth,vuln,reasoning,cwe,cve,cve_desc\n")

    # Load existing results and energy data
    existing_results = resume.load_results(detailed_file)
    energy_data = resume.load_energy(energy_file)

    # Filter remaining samples
    remaining_samples = resume.filter_remaining_samples(samples, existing_results, id_field='idx')

    # Handle skip next sample option
    if skip_next_sample and remaining_samples:
        skip_sample = remaining_samples[0]
        failed_result = resume.create_skip_result(skip_sample, id_field='idx')
        failed_result.update({
            'ground_truth': skip_sample['target'],  # Map target → ground_truth for CSV
            'vuln': -1,
            'reasoning': 'SKIPPED - Sample marked as problematic by user',
            'cwe': skip_sample.get('cwe', []),
            'cve': skip_sample.get('cve', ''),
            'cve_desc': skip_sample.get('cve_desc', '')
        })
        append_result(failed_result, detailed_file, csv_file)
        existing_results.append(failed_result)
        remaining_samples = remaining_samples[1:]

    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        save_to_file=True,
        country_iso_code="CAN"
    )
    tracker.start()

    user_proxy, security_researcher, code_author, moderator, review_board = create_vulnerability_agents(llm_config, prompts)
    results = existing_results.copy()

    try:
        for i, sample in enumerate(remaining_samples):
            sample_info = f"Sample {i+1}/{len(remaining_samples)}, idx: {sample['idx']}"
            print(f"\n--- Processing {sample_info} ---")

            # Step 1: Security Researcher
            print(f"\n[{sample_info}] Phase 1/4: Security Researcher analyzing...")
            researcher = user_proxy.initiate_chat(
                recipient=security_researcher,
                message=config.MULTI_AGENT_TASK_SECURITY_RESEARCHER.format(code=sample['func']),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Step 2: Code Author
            print(f"\n[{sample_info}] Phase 2/4: Code Author responding...")
            author = user_proxy.initiate_chat(
                recipient=code_author,
                message=config.MULTI_AGENT_TASK_CODE_AUTHOR.format(
                    researcher_findings=researcher,
                    code=sample['func']
                ),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Step 3: Moderator
            print(f"\n[{sample_info}] Phase 3/4: Moderator summarizing...")
            moderator_resp = user_proxy.initiate_chat(
                recipient=moderator,
                message=config.MULTI_AGENT_TASK_MODERATOR.format(
                    researcher_findings=researcher,
                    author_response=author
                ),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Step 4: Review Board
            print(f"\n[{sample_info}] Phase 4/4: Review Board deciding...")
            board = user_proxy.initiate_chat(
                recipient=review_board,
                message=config.MULTI_AGENT_TASK_REVIEW_BOARD.format(
                    moderator_summary=moderator_resp,
                    code=sample['func'],
                    researcher_findings=researcher,
                    author_response=author
                ),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Decision
            vuln_decision, reasoning = extract_vulnerability_decision(board)

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
                'full_discussion': {
                    'security_researcher': researcher,
                    'code_author': author,
                    'moderator': moderator_resp,
                    'review_board': board
                },
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

        # Update energy tracking
        resume.save_energy(energy_data, energy_file, emissions, len(remaining_samples))

        print(f"Total emissions (all sessions): {energy_data['total_emissions']:.6f} kg CO2")

    return results, exp_name


# --- Main Execution ---
def main():
    print("\n" + "="*60)
    print(f"MULTI-AGENT VULNERABILITY DETECTION (4 AGENTS) - {args.prompt_type.upper()}")
    print("="*60)

    print("\nLoading dataset...")
    samples = load_vulnerability_dataset(DATASET_FILE)
    print(f"Loaded {len(samples)} samples")

    # Package prompts for passing to inference function
    prompts = (researcher_prompt, author_prompt, moderator_prompt, review_board_prompt)

    print(f"\nRunning {DESIGN} vulnerability detection...")
    results, final_exp_name = run_inference_with_emissions(
        samples,
        llm_config,
        exp_name,
        RESULT_DIR,
        DESIGN,
        model,
        prompts
    )

    predictions = [r.get('vuln', -1) for r in results]
    ground_truth = [r.get('ground_truth', r.get('target', 0)) for r in results]

    try:
        eval_results = evaluate_and_save_vulnerability(
            normalize_vulnerability_basic,
            predictions,
            DATASET_FILE,
            final_exp_name
        )
        print("Evaluation Results:", eval_results)
    except Exception as e:
        print("Evaluation failed:", e)

    print("\n=== FINAL SUMMARY ===")
    print(f"Samples processed: {len(results)}")
    print(f"Experiment name: {final_exp_name}")
    print("Multi-agent vulnerability detection completed!")


if __name__ == "__main__":
    main()
