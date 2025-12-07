import os
import json
import time
import re
import argparse

# Dynamic config selection based on MODEL_FAMILY environment variable
# Usage: MODEL_FAMILY=nemotron python src/dual_agent_code_generation.py --prompt_type few_shot
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
from autogen import AssistantAgent
from codecarbon import OfflineEmissionsTracker
from ollama_utils import start_ollama_server,stop_ollama_server
import subprocess
from resume_utils import ExperimentResume

# ---------------------------
# Parse Command Line Args
# ---------------------------
def parse_arguments():
    parser = argparse.ArgumentParser(description="Dual-Agent Code Generation")
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
DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

# Design configuration
DESIGN = f"DA-code-{args.prompt_type}"
model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

print(f"Experiment: {exp_name}")
print(f"Dataset: {DATASET_FILE}")
print(f"Prompt Type: {args.prompt_type}")
print(f"Results will be saved to: {RESULT_DIR}")

# ---------------------------
# System Prompts
# ---------------------------
if args.prompt_type == "zero_shot":
    programmer_sys_prompt = config.SYS_MSG_PROGRAMMER_ZERO_SHOT
    reviewer_sys_prompt = config.SYS_MSG_CODE_REVIEWER_ZERO_SHOT
else:
    programmer_sys_prompt = config.SYS_MSG_PROGRAMMER_FEW_SHOT
    reviewer_sys_prompt = config.SYS_MSG_CODE_REVIEWER_FEW_SHOT

# ---------------------------
# Agent Creation
# ---------------------------
def create_programmer_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="programmer",
        system_message=sys_prompt,
        description="Implements code solutions.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

def create_refiner_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="refiner",
        system_message=sys_prompt,
        description="Reviews code and provides refined version.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

# ---------------------------
# Helper: Extract code block
# ---------------------------
def extract_code_from_response(response_text):
    """Extract Python code from model response"""
    if not response_text:
        return ""
    
    # Remove <think> blocks if present
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
    response_text = response_text.strip()
    
    # Method 1: ```python blocks
    if "```python" in response_text:
        parts = response_text.split("```python")
        if len(parts) > 1:
            code = parts[1].split("```")[0]
            return code.strip()
    
    # Method 2: ``` blocks
    if "```" in response_text:
        parts = response_text.split("```")
        if len(parts) >= 3:
            code = parts[1]
            lines = code.split('\n')
            if lines[0].strip() in ['python', 'py', 'json']:
                code = '\n'.join(lines[1:])
            return code.strip()
    
    # Method 3: Extract from 'def' or 'from' or 'import' to end
    lines = response_text.split('\n')
    code_lines = []
    found_start = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip explanatory text
        if not found_start and stripped.startswith(('To solve', 'The ', 'This ', 'Here', 'Note:', '**', '[', 'I ', 'First', 'Challenge', 'Wait,', 'Let', 'So ', 'Yes,', 'Okay')):
            continue
        
        # Start collecting from imports or code
        if stripped.startswith(('def ', 'from ', 'import ', 'class ')):
            found_start = True
        
        if found_start:
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return response_text.strip()

# ---------------------------
# Data Loading
# ---------------------------
def read_dataset(path):
    """Read code generation data from JSONL file"""
    data = []
    print(f"\nReading dataset from: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError as e:
                print(f"Warning: Skipped malformed line: {e}")
                continue
    
    print(f"Loaded {len(data)} code samples")
    return data

# ---------------------------
# Inference Loop
# ---------------------------
def run_dual_agent_inference(samples, llm_config, exp_name, result_dir, prompt_type, design=None, model=None):
    # Initialize resume helper
    resume = ExperimentResume(result_dir, design, model, exp_name)
    exp_name, detailed_file, energy_file, skip_next_sample = resume.initialize()

    summary_file = os.path.join(result_dir, f"{exp_name}_summary.json")

    # Load existing results and energy
    existing_results = resume.load_results(detailed_file)
    energy_data = resume.load_energy(energy_file)

    # Filter remaining samples
    remaining_samples = resume.filter_remaining_samples(samples, existing_results, id_field='task_id')

    # Handle skip next
    if skip_next_sample and remaining_samples:
        skip_sample = remaining_samples[0]
        failed_result = resume.create_skip_result(skip_sample, id_field='task_id')
        with open(detailed_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(failed_result) + '\n')
        existing_results.append(failed_result)
        remaining_samples = remaining_samples[1:]

    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        country_iso_code="CAN",
        save_to_file=True,
    )
    tracker.start()

    stats = {
        'total_samples': len(samples),
        'successful_extractions': len([r for r in existing_results if r.get('generated_solution', '') and 'def' in r.get('generated_solution', '')]),
        'failed_extractions': len([r for r in existing_results if not r.get('generated_solution', '') or 'def' not in r.get('generated_solution', '')]),
        'prompt_type': prompt_type
    }

    try:
        # Create the agents
        programmer = create_programmer_agent(llm_config, programmer_sys_prompt)
        refiner = create_refiner_agent(llm_config, reviewer_sys_prompt)

        for i, sample in enumerate(remaining_samples):
            task_id = sample.get('task_id', f'sample_{i}')
            print(f"\n{'='*60}")
            print(f"Processing {i+1}/{len(samples)}: {task_id}")
            print(f"{'='*60}")
            
            prompt = sample.get('prompt', sample.get('description', ''))
            
            # === TURN 1: Programmer ===
            print("Turn 1: Programmer implementing solution...")

            # Select appropriate task prompt
            if args.prompt_type == 'zero_shot':
                programmer_task = config.DUAL_AGENT_TASK_CODE_GENERATION.format(prompt=prompt)
            else:  # few_shot
                programmer_task = config.DUAL_AGENT_TASK_CODE_GENERATION.format(prompt=prompt)

            res1 = programmer.generate_reply(messages=[{"content": programmer_task, "role": "user"}])
            programmer_response = res1.get("content", "") if res1 else ""
            code_output = extract_code_from_response(programmer_response)
            print(f"  Programmer code: {len(code_output)} chars")
            
            # === TURN 2: Refiner ===
            print("Turn 2: Refiner refining solution...")

            reviewer_task = config.DUAL_AGENT_TASK_CODE_REVIEW.format(
                prompt=prompt,
                generated_code=code_output
            )

            res2 = refiner.generate_reply(messages=[{"content": reviewer_task, "role": "user"}])
            reviewer_response = res2.get("content", "") if res2 else ""
            reviewer_code = extract_code_from_response(reviewer_response)
            print(f"  Refiner code: {len(reviewer_code)} chars")
            
            # Use reviewer's code as final output
            final_code = reviewer_code if reviewer_code and 'def' in reviewer_code else code_output
            
            # Check extraction quality
            if final_code and 'def' in final_code:
                stats['successful_extractions'] += 1
            else:
                stats['failed_extractions'] += 1
                print("  ✗ WARNING: No valid function definition found!")
            
            # Save result
            result = {
                'task_id': task_id,
                'prompt': prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', ''),
                'initial_code': code_output,         # generated by the programmer
                'generated_solution': final_code,    # final output for evaluation
                'review': reviewer_response,         # text feedback from reviewer
                'conversation': {
                    'programmer_code': code_output,
                    'refiner_code': reviewer_code,
                },
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'prompt_type': prompt_type
                }
            }

            with open(detailed_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result) + '\n')
            
            # Progress checkpoint
            if (i + 1) % 10 == 0:
                print(f"\n✓ Progress checkpoint: {i + 1}/{len(remaining_samples)} samples completed")
                print(f"  Success rate: {stats['successful_extractions']}/{i+1} ({stats['successful_extractions']/(i+1)*100:.1f}%)")

    finally:
        emissions = tracker.stop()
        print(f"\nEmissions this run: {emissions:.6f} kg CO2")

        # Update energy tracking
        resume.save_energy(energy_data, energy_file, emissions, len(remaining_samples))

        stats['emissions_kg_co2'] = emissions
        stats['total_emissions'] = energy_data['total_emissions']

        print(f"\n{'='*60}")
        print("DUAL-AGENT CODE GENERATION COMPLETED")
        print(f"{'='*60}")
        print(f"Total samples: {stats['total_samples']}")
        print(f"Successful extractions: {stats['successful_extractions']} ({stats['successful_extractions']/stats['total_samples']*100:.1f}%)")
        print(f"Failed extractions: {stats['failed_extractions']}")
        print(f"Prompt type: {stats['prompt_type']}")
        print(f"Emissions this session: {emissions:.6f} kg CO2")
        print(f"Total emissions (all sessions): {energy_data['total_emissions']:.6f} kg CO2")

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

    return detailed_file, exp_name

# ---------------------------
# Main
# ---------------------------
def main():
    print("\n" + "="*60)
    print(f"DUAL-AGENT CODE GENERATION - {args.prompt_type.upper()}")
    print("="*60)

    # Start Ollama server and wait a few seconds
    proc = start_ollama_server()
    time.sleep(5)

    results_file = None  # Initialize to None in case of early error
    try:
        # --- Run code generation ---
        samples = read_dataset(DATASET_FILE)
        print(f"\nRunning {DESIGN} dual-agent code generation...")
        results_file, final_exp_name = run_dual_agent_inference(
            samples,
            llm_config,
            exp_name,
            RESULT_DIR,
            args.prompt_type,
            DESIGN,
            model
        )

        print(f"\nResults saved to: {results_file}")
        print(f"Experiment name: {final_exp_name}")

    except Exception as e:
        print(f"Error during code generation: {e}")

    finally:
        stop_ollama_server(proc)

    # --- Run evaluation ---
    if results_file is None:
        print("\n⚠️ Skipping evaluation: No results file generated due to error")
        return

    print("\n" + "="*80)
    print("STARTING EVALUATION")
    print("="*80)
    try:
        eval_result = subprocess.run(
            ["python", "src/evaluate_code_generation.py", results_file],
            capture_output=True,
            text=True,
            timeout=600
        )

        print(eval_result.stdout)
        if eval_result.returncode != 0:
            print("Evaluation encountered an error:")
            print(eval_result.stderr)
        else:
            print("\n" + "="*80)
            print("EVALUATION COMPLETED SUCCESSFULLY")
            print("="*80)

    except subprocess.TimeoutExpired:
        print("Evaluation timed out after 10 minutes.")
    except Exception as e:
        print(f"Failed to run evaluation: {e}")
        
if __name__ == "__main__":
    main()
