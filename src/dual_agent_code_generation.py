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

DESIGN = "DA-code-two"  # Dual Agent design
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"


# --- Agent Creation ---
def create_code_generation_agents(llm_config):
    """Create the two code generation agents"""
    user_proxy = create_agent(
        "conversable",
        "user_proxy_agent",
        llm_config,
        sys_prompt="A human admin coordinating the code generation process.",
        description="A proxy for human input coordinating the dual-agent code generation."
    )

    programmer = create_agent(
        "assistant",
        "programmer_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_PROGRAMMER,
        description="Generate and revise code based on requirements and feedback."
    )

    code_reviewer = create_agent(
        "assistant", 
        "code_reviewer_agent",
        llm_config,
        sys_prompt=config.SYS_MSG_CODE_REVIEWER,
        description="Review code for correctness, provide feedback, and make final assessment."
    )

    return user_proxy, programmer, code_reviewer


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
                "generated_solution,final_code_quality,reasoning,"
                "iteration_1_feedback,iteration_2_decision\n")

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
            escape(result.get('final_code_quality', '')),
            escape(result['reasoning']),
            escape(result.get('iteration_1_feedback', '')),
            escape(result.get('iteration_2_decision', ''))
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


def extract_code_quality_assessment(reviewer_response):
    """Parse code reviewer response for final assessment"""
    try:
        # Try to parse as JSON first
        if reviewer_response.strip().startswith('{') or reviewer_response.strip().startswith('['):
            assessment_data = json.loads(reviewer_response.strip())
            if isinstance(assessment_data, dict):
                quality = assessment_data.get('code_quality', 'unknown')
                reasoning = assessment_data.get('reasoning', reviewer_response)
            else:
                quality = 'unknown'
                reasoning = reviewer_response
        else:
            # Parse text-based response
            text = reviewer_response.lower()
            if any(keyword in text for keyword in ['excellent', 'good', 'correct', 'passes']):
                quality = 'good'
            elif any(keyword in text for keyword in ['poor', 'incorrect', 'fails', 'error']):
                quality = 'poor'
            else:
                quality = 'acceptable'
            reasoning = reviewer_response
            
        return quality, reasoning
    except Exception as e:
        print(f"Error parsing reviewer response: {e}")
        return 'unknown', reviewer_response


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

    user_proxy, programmer, code_reviewer = create_code_generation_agents(llm_config)
    results = []

    try:
        for i, sample in enumerate(samples):
            print(f"\n--- Processing sample {i+1}/{len(samples)} (task_id: {sample['task_id']}) ---")

            # ITERATION 1: Initial code generation and review
            print("Iteration 1: Code generation and initial review...")
            
            # Programmer generates initial code
            initial_code = user_proxy.initiate_chat(
                recipient=programmer,
                message=config.DUAL_AGENT_TASK_CODE_GENERATION.format(prompt=sample['prompt']),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Code reviewer provides feedback
            feedback = user_proxy.initiate_chat(
                recipient=code_reviewer,
                message=config.DUAL_AGENT_TASK_CODE_REVIEW.format(
                    prompt=sample['prompt'],
                    generated_code=initial_code
                ),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # ITERATION 2: Code revision and final assessment
            print("Iteration 2: Code revision and final assessment...")
            
            # Programmer revises based on feedback
            revised_code = user_proxy.initiate_chat(
                recipient=programmer,
                message=config.DUAL_AGENT_TASK_CODE_REVISION.format(
                    original_prompt=sample['prompt'],
                    initial_code=initial_code,
                    feedback=feedback
                ),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Code reviewer makes final assessment
            final_assessment = user_proxy.initiate_chat(
                recipient=code_reviewer,
                message=config.DUAL_AGENT_TASK_FINAL_ASSESSMENT.format(
                    original_prompt=sample['prompt'],
                    revised_code=revised_code,
                    previous_feedback=feedback
                ),
                max_turns=1,
                summary_method="last_msg"
            ).summary.strip()

            # Extract final code and quality assessment
            final_code = extract_code_from_response(revised_code)
            code_quality, reasoning = extract_code_quality_assessment(final_assessment)

            result = {
                'task_id': sample['task_id'],
                'prompt': sample['prompt'],
                'entry_point': sample['entry_point'],
                'canonical_solution': sample['canonical_solution'],
                'test': sample['test'],
                'generated_solution': final_code,
                'final_code_quality': code_quality,
                'reasoning': reasoning,
                'dual_agent_conversation': {
                    'iteration_1_initial_code': initial_code,
                    'iteration_1_feedback': feedback,
                    'iteration_2_revised_code': revised_code,
                    'iteration_2_final_assessment': final_assessment
                },
                'iteration_1_feedback': feedback,
                'iteration_2_decision': final_assessment,
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

    print(f"Running {DESIGN} dual-agent code generation...")
    results = run_dual_agent_inference_with_emissions(samples, llm_config, exp_name, RESULT_DIR)

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
    print("Dual-agent code generation completed!")


if __name__ == "__main__":
    main()