import os
import json
import config
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
from code_evaluation import evaluate_and_save_code_generation, normalize_code_basic
from agent_utils_vuln import create_agent
from autogen.agentchat.conversable_agent import ConversableAgent
from pathlib import Path

# --- Configuration ---
llm_config = config.LLM_CONFIG
DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

DESIGN = "MA-code-four"
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"


# --- Agent Creation ---
def create_code_generation_agents(llm_config):
    """Create the four code generation agents"""
    user_proxy = create_agent(
        "conversable",
        "user_proxy_agent",
        llm_config,
        sys_prompt="A human admin coordinating the code generation process.",
        description="A proxy for human input coordinating the multi-agent code generation."
    )

    requirements_analyst = create_agent(
        "assistant",
        "requirements_analyst_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_REQUIREMENTS_ANALYST,
        description="Analyze requirements and identify potential implementation issues."
    )

    programmer = create_agent(
        "assistant",
        "programmer_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_PROGRAMMER_MA,
        description="Implement code based on requirements and address concerns."
    )

    moderator = create_agent(
        "assistant",
        "moderator_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_MODERATOR_CODE,
        description="Provide neutral summaries of the code generation discussion."
    )

    review_board = create_agent(
        "assistant",
        "review_board_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_REVIEW_BOARD_CODE,
        description="Make final decisions on code quality and correctness."
    )

    return user_proxy, requirements_analyst, programmer, moderator, review_board


# --- Data Loading ---
def load_code_generation_dataset(file_path):
    """Load code generation dataset from JSONL file"""
    samples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if 'prompt' in data and 'task_id' in data:
                    sample = {
                        'task_id': data['task_id'],
                        'prompt': data['prompt'],
                        'entry_point': data.get('entry_point', ''),
                        'canonical_solution': data.get('canonical_solution', ''),
                        'test': data.get('test', ''),
                        'docstring': data.get('docstring', '')
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
        f.write("task_id,prompt,entry_point,canonical_solution,test,"
                "generated_solution,code_quality,reasoning\n")

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
            escape(result['task_id']),
            escape(result['prompt']),
            escape(result['entry_point']),
            escape(result['canonical_solution']),
            escape(result['test']),
            escape(result['generated_solution']),
            escape(result.get('code_quality', '')),
            escape(result['reasoning'])
        ]
        f.write(','.join(row) + '\n')


def extract_code_from_response(response_text):
    """Extract Python code from response"""
    if not response_text:
        return ""
    
    # Look for code blocks
    if "```python" in response_text:
        parts = response_text.split("```python")
        if len(parts) > 1:
            code_part = parts[1].split("```")[0]
            return code_part.strip()
    elif "```" in response_text:
        parts = response_text.split("```")
        if len(parts) >= 3:
            code_part = parts[1]
            return code_part.strip()
    
    # Try to find function definition
    lines = response_text.split('\n')
    code_lines = []
    found_def = False
    
    for line in lines:
        if line.strip().startswith('def '):
            found_def = True
        
        if found_def:
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return response_text.strip()


def extract_code_quality_decision(review_board_response):
    """Parse review board response into (code_quality, reasoning)"""
    try:
        assessments = json.loads(review_board_response.strip())
        overall_quality = "good"
        all_reasons = []
        
        for assessment in assessments:
            decision = assessment.get('decision', 'acceptable')
            if decision in ['poor', 'needs_revision']:
                overall_quality = "poor"
            elif decision == 'acceptable' and overall_quality == 'good':
                overall_quality = "acceptable"
            
            all_reasons.append(f"{assessment.get('aspect','Unknown')}: {assessment.get('reason','No reason')}")
        
        reasoning = "; ".join(all_reasons)
        return overall_quality, reasoning
    except Exception:
        text = review_board_response.lower()
        if any(k in text for k in ['good', 'excellent', 'correct']):
            return "good", review_board_response
        elif any(k in text for k in ['poor', 'incorrect', 'fails']):
            return "poor", review_board_response
        return "acceptable", review_board_response


# --- Inference with Emissions ---
def run_inference_with_emissions(samples, llm_config, exp_name, result_dir):
    detailed_file, csv_file, energy_file = initialize_results_files(exp_name, result_dir)
    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        save_to_file=True,
        country_iso_code="CAN"
    )

    tracker.start()

    user_proxy, requirements_analyst, programmer, moderator, review_board = create_code_generation_agents(llm_config)
    results = []

    try:
        for i, sample in enumerate(samples):
            print(f"\n--- Processing sample {i+1}/{len(samples)} (task_id: {sample['task_id']}) ---")

            # Step 1: Requirements Analyst
            analyst_response = user_proxy.initiate_chat(
                recipient=requirements_analyst,
                message=config.MULTI_AGENT_TASK_REQUIREMENTS_ANALYST.format(prompt=sample['prompt']),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Step 2: Programmer
            programmer_response = user_proxy.initiate_chat(
                recipient=programmer,
                message=config.MULTI_AGENT_TASK_PROGRAMMER.format(
                    analyst_findings=analyst_response,
                    prompt=sample['prompt']
                ),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Step 3: Moderator
            moderator_response = user_proxy.initiate_chat(
                recipient=moderator,
                message=config.MULTI_AGENT_TASK_MODERATOR_CODE.format(
                    analyst_findings=analyst_response,
                    programmer_response=programmer_response
                ),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Step 4: Review Board
            board_response = user_proxy.initiate_chat(
                recipient=review_board,
                message=config.MULTI_AGENT_TASK_REVIEW_BOARD_CODE.format(
                    moderator_summary=moderator_response,
                    prompt=sample['prompt'],
                    analyst_findings=analyst_response,
                    programmer_response=programmer_response
                ),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Extract final code and decision
            final_code = extract_code_from_response(programmer_response)
            code_quality, reasoning = extract_code_quality_decision(board_response)

            result = {
                'task_id': sample['task_id'],
                'prompt': sample['prompt'],
                'entry_point': sample['entry_point'],
                'canonical_solution': sample['canonical_solution'],
                'test': sample['test'],
                'generated_solution': final_code,
                'code_quality': code_quality,
                'reasoning': reasoning,
                'full_discussion': {
                    'requirements_analyst': analyst_response,
                    'programmer': programmer_response,
                    'moderator': moderator_response,
                    'review_board': board_response
                },
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
    samples = load_code_generation_dataset(DATASET_FILE)
    print(f"Loaded {len(samples)} samples")

    print(f"Running {DESIGN} code generation...")
    results = run_inference_with_emissions(samples, llm_config, exp_name, RESULT_DIR)

    predictions = [r['generated_solution'] for r in results]

    try:
        eval_results = evaluate_and_save_code_generation(
            normalize_code_basic,
            predictions,
            DATASET_FILE,
            exp_name
        )
        print("Evaluation Results:", eval_results)
    except Exception as e:
        print("Evaluation failed:", e)

    print("\n=== FINAL SUMMARY ===")
    print(f"Samples processed: {len(results)}")
    print("Multi-agent code generation completed!")


if __name__ == "__main__":
    main()