import os
import json
import time
import config
from datetime import datetime
from autogen import AssistantAgent
from codecarbon import OfflineEmissionsTracker
import sys
import subprocess


# --- Configuration ---
llm_config = config.LLM_CONFIG
DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

# Design configuration
DESIGN = "DA-code"
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

print(f"Experiment: {exp_name}")
print(f"Dataset: {DATASET_FILE}")
print(f"Results will be saved to: {RESULT_DIR}")


# --- Agent Creation ---
def create_programmer_agent(llm_config, sys_prompt):
    """Create programmer agent"""
    return AssistantAgent(
        name="programmer",
        system_message=sys_prompt,
        description="Generate and revise Python code based on requirements and feedback.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )


def create_critic_agent(llm_config, sys_prompt):
    """Create critic/reviewer agent"""
    return AssistantAgent(
        name="critic",
        system_message=sys_prompt,
        description="Review code quality, correctness, and provide constructive feedback.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )


# --- Data Reading ---
def read_code_generation_data(dataset_path):
    """Read code generation dataset from JSONL file"""
    code_problems = []
    print(f"\nReading dataset from: {dataset_path}")
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                code_problems.append(data)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipped malformed line: {e}")
                continue
    
    print(f"Loaded {len(code_problems)} code samples")
    return code_problems


# --- Code Extraction ---
def extract_code_from_response(response_text):
    """Extract Python code from model response"""
    if not response_text:
        return ""

    response_text = response_text.strip()

    # Method 1: Look for ```python code blocks
    if "```python" in response_text:
        parts = response_text.split("```python")
        if len(parts) > 1:
            code_part = parts[1].split("```")[0]
            return code_part.strip()

    # Method 2: Look for ``` code blocks
    elif "```" in response_text:
        parts = response_text.split("```")
        if len(parts) >= 3:
            code_part = parts[1]
            # Remove language identifier if present
            lines = code_part.split('\n')
            if lines[0].strip() in ['python', 'py']:
                code_part = '\n'.join(lines[1:])
            return code_part.strip()

    # Method 3: Extract from first 'def' to end
    lines = response_text.split('\n')
    code_lines = []
    found_def = False

    for line in lines:
        stripped = line.strip()

        # Skip explanatory text before function definition
        if not found_def and stripped.startswith(('To solve', 'The ', 'This ', 'Here', 'Note:', '**', 'Let', 'I ', 'First')):
            continue

        # Start collecting from function definition
        if stripped.startswith(('def ', 'from ', 'import ', 'class ')):
            found_def = True

        if found_def:
            code_lines.append(line)

    if code_lines:
        return '\n'.join(code_lines).strip()

    # If all else fails, return the whole response
    return response_text.strip()


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

    # Initialize detailed results JSONL file
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")

    # Initialize summary file
    summary_file = os.path.join(result_dir, f"{exp_name}_summary.json")

    # Initialize energy tracking file
    energy_file = os.path.join(result_dir, f"{exp_name}_energy_tracking.json")

    return detailed_file, summary_file, energy_file, skip_next_sample, exp_name


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


# --- Dual-Agent Inference with Emissions Tracking ---
# def run_inference_with_emissions(code_samples, llm_config, sys_prompt_programmer, sys_prompt_critic, exp_name, result_dir):
#     """
#     Run dual-agent code generation with emissions tracking.
    
#     Workflow (Option A):
#     1. Programmer generates initial code
#     2. Critic reviews and provides feedback
#     3. Programmer revises based on feedback
#     4. Critic does final assessment
#     """
    
#     detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
#     summary_file = os.path.join(result_dir, f"{exp_name}_summary.json")
    
#     # Clear previous results
#     if os.path.exists(detailed_file):
#         os.remove(detailed_file)
    
#     # Initialize emissions tracker
#     tracker = OfflineEmissionsTracker(
#         project_name=exp_name,
#         output_dir=result_dir,
#         country_iso_code="CAN",
#         save_to_file=True
#     )
#     tracker.start()
    
#     # Create agents
#     programmer = create_programmer_agent(llm_config, sys_prompt_programmer)
#     critic = create_critic_agent(llm_config, sys_prompt_critic)
    
#     results = []
#     stats = {
#         'total_samples': len(code_samples),
#         'successful_extractions': 0,
#         'failed_extractions': 0,
#         'used_initial_code': 0,
#         'used_revised_code': 0
#     }
    
#     try:
#         for i, sample in enumerate(code_samples):
#             task_id = sample.get('task_id', f'sample_{i}')
#             print(f"\n{'='*60}")
#             print(f"Processing {i+1}/{len(code_samples)}: {task_id}")
#             print(f"{'='*60}")
            
#             problem_prompt = sample.get('prompt', '')
            
#             # === TURN 1: Programmer generates initial code ===
#             print("Turn 1: Programmer generating initial code...")
#             initial_task = config.DUAL_AGENT_TASK_CODE_GENERATION.format(prompt=problem_prompt)
            
#             res1 = programmer.generate_reply(messages=[{"content": initial_task, "role": "user"}])
#             initial_response = res1.get("content", "") if res1 else ""
#             initial_code = extract_code_from_response(initial_response)
            
#             print(f"  Initial code extracted: {len(initial_code)} chars, has 'def': {'def' in initial_code}")
            
#             # === TURN 2: Critic reviews ===
#             print("Turn 2: Critic reviewing initial code...")
#             review_task = config.DUAL_AGENT_TASK_CODE_REVIEW.format(
#                 prompt=problem_prompt,
#                 generated_code=initial_code
#             )
            
#             res2 = critic.generate_reply(messages=[{"content": review_task, "role": "user"}])
#             feedback = res2.get("content", "") if res2 else ""
            
#             print(f"  Feedback received: {len(feedback)} chars")
            
#             # === TURN 3: Programmer revises based on feedback ===
#             print("Turn 3: Programmer revising code...")
#             revision_task = config.DUAL_AGENT_TASK_CODE_REVISION.format(
#                 original_prompt=problem_prompt,
#                 initial_code=initial_code,
#                 feedback=feedback
#             )
            
#             res3 = programmer.generate_reply(messages=[{"content": revision_task, "role": "user"}])
#             revised_response = res3.get("content", "") if res3 else ""
#             revised_code = extract_code_from_response(revised_response)
            
#             print(f"  Revised code extracted: {len(revised_code)} chars, has 'def': {'def' in revised_code}")
            
#             # === TURN 4: Critic final assessment ===
#             print("Turn 4: Critic final assessment...")
#             final_task = config.DUAL_AGENT_TASK_FINAL_ASSESSMENT.format(
#                 original_prompt=problem_prompt,
#                 revised_code=revised_code,
#                 previous_feedback=feedback
#             )
            
#             res4 = critic.generate_reply(messages=[{"content": final_task, "role": "user"}])
#             final_assessment = res4.get("content", "") if res4 else ""
            
#             # === Determine which code to use ===
#             final_code = revised_code if (revised_code and 'def' in revised_code) else initial_code
            
#             if final_code == revised_code:
#                 stats['used_revised_code'] += 1
#                 print("  ✓ Using revised code")
#             else:
#                 stats['used_initial_code'] += 1
#                 print("  ⚠ Using initial code (revision failed)")
            
#             if final_code and 'def' in final_code:
#                 stats['successful_extractions'] += 1
#             else:
#                 stats['failed_extractions'] += 1
#                 print("  ✗ WARNING: No valid function definition found!")
            
#             # === Save result ===
#             result = {
#                 'task_id': task_id,
#                 'prompt': problem_prompt,
#                 'entry_point': sample.get('entry_point', ''),
#                 'canonical_solution': sample.get('canonical_solution', ''),
#                 'test': sample.get('test', ''),
#                 'generated_solution': final_code,
#                 'conversation': {
#                     'initial_code': initial_code,
#                     'critic_feedback': feedback,
#                     'revised_code': revised_code,
#                     'final_assessment': final_assessment
#                 },
#                 'metadata': {
#                     'used_code_version': 'revised' if final_code == revised_code else 'initial',
#                     'timestamp': datetime.now().isoformat()
#                 }
#             }
            
#             with open(detailed_file, 'a', encoding='utf-8') as f:
#                 f.write(json.dumps(result) + '\n')
            
#             results.append(result)
            
#             # Progress checkpoint
#             if (i + 1) % 10 == 0:
#                 print(f"\n✓ Progress checkpoint: {i + 1}/{len(code_samples)} samples completed")
#                 print(f"  Success rate: {stats['successful_extractions']}/{i+1} ({stats['successful_extractions']/(i+1)*100:.1f}%)")
    
#     finally:
#         emissions = tracker.stop()
#         stats['emissions_kg_co2'] = emissions
        
#         print(f"\n{'='*60}")
#         print("DUAL-AGENT GENERATION COMPLETED")
#         print(f"{'='*60}")
#         print(f"Total samples: {stats['total_samples']}")
#         print(f"Successful extractions: {stats['successful_extractions']}")
#         print(f"Failed extractions: {stats['failed_extractions']}")
#         print(f"Used revised code: {stats['used_revised_code']}")
#         print(f"Used initial code: {stats['used_initial_code']}")
#         print(f"Emissions: {emissions:.6f} kg CO2")
#         print(f"{'='*60}")
        
#         # Save summary
#         with open(summary_file, 'w', encoding='utf-8') as f:
#             json.dump(stats, f, indent=2)
    
#     return detailed_file

def run_inference_with_emissions(code_samples, llm_config, sys_prompt_programmer, sys_prompt_critic, exp_name, result_dir, design, model):
    """
    Run dual-agent code generation with emissions tracking.

    Workflow (Optimized):
    1. Programmer generates initial code
    2. Critic reviews - if CORRECT, skip to save
    3. (Optional) Programmer revises only if bugs found
    4. (Optional) Critic final assessment only if revised
    """

    # Initialize result files (will resume from existing if found)
    detailed_file, summary_file, energy_file, skip_next_sample, exp_name = initialize_results_files(exp_name, result_dir, design, model)

    # Load existing results and energy data if any (for resuming interrupted runs)
    existing_results = load_existing_results(detailed_file)
    energy_data = load_existing_energy(energy_file)
    processed_task_ids = {r['task_id'] for r in existing_results}

    # Filter out already processed samples
    remaining_samples = [s for s in code_samples if s.get('task_id', '') not in processed_task_ids]

    # If user chose to skip the next sample, mark it as failed and remove from queue
    if skip_next_sample and remaining_samples:
        skip_sample = remaining_samples[0]
        task_id = skip_sample.get('task_id', 'unknown')
        print(f"[SKIP] Marking sample {task_id} as FAILED and skipping")

        # Create failed result
        failed_result = {
            'task_id': task_id,
            'prompt': skip_sample.get('prompt', ''),
            'entry_point': skip_sample.get('entry_point', ''),
            'canonical_solution': skip_sample.get('canonical_solution', ''),
            'test': skip_sample.get('test', ''),
            'generated_solution': '',
            'conversation': {
                'initial_code': '',
                'critic_feedback': '',
                'revised_code': None,
                'final_assessment': 'Skipped'
            },
            'metadata': {
                'used_code_version': 'skipped',
                'revision_skipped': True,
                'timestamp': datetime.now().isoformat(),
                'error': 'USER_SKIP'
            }
        }

        # Save the failed result
        with open(detailed_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(failed_result) + '\n')
        existing_results.append(failed_result)

        # Remove from remaining samples
        remaining_samples = remaining_samples[1:]

    print(f"\n{'='*80}")
    print(f"Processing {len(remaining_samples)} remaining samples (out of {len(code_samples)} total)")
    print(f"Already completed: {len(processed_task_ids)} samples")
    print(f"{'='*80}\n")

    # Start CodeCarbon tracker
    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        country_iso_code="CAN",
        save_to_file=True
    )
    tracker.start()

    programmer = create_programmer_agent(llm_config, sys_prompt_programmer)
    critic = create_critic_agent(llm_config, sys_prompt_critic)

    results = existing_results.copy()  # Start with existing results
    stats = {
        'total_samples': len(code_samples),
        'successful_extractions': len([r for r in existing_results if r.get('generated_solution', '') and 'def' in r.get('generated_solution', '')]),
        'failed_extractions': len([r for r in existing_results if not r.get('generated_solution', '') or 'def' not in r.get('generated_solution', '')]),
        'used_initial_code': len([r for r in existing_results if r.get('metadata', {}).get('used_code_version') == 'initial']),
        'used_revised_code': len([r for r in existing_results if r.get('metadata', {}).get('used_code_version') == 'revised']),
        'skipped_revision': len([r for r in existing_results if r.get('metadata', {}).get('revision_skipped', False)])
    }
    
    try:
        for i, sample in enumerate(remaining_samples):
            task_id = sample.get('task_id', f'sample_{i}')
            print(f"\n{'='*60}")
            print(f"Processing {i+1}/{len(remaining_samples)}: {task_id}")
            print(f"{'='*60}")

            try:
                problem_prompt = sample.get('prompt', '')

                # === TURN 1: Programmer generates initial code ===
                print("Turn 1: Programmer generating initial code...")
                initial_task = config.DUAL_AGENT_TASK_CODE_GENERATION.format(prompt=problem_prompt)

                res1 = programmer.generate_reply(messages=[{"content": initial_task, "role": "user"}])
                initial_response = res1.get("content", "") if res1 else ""
                initial_code = extract_code_from_response(initial_response)

                print(f"  Initial code extracted: {len(initial_code)} chars, has 'def': {'def' in initial_code}")

                # === TURN 2: Critic reviews ===
                print("Turn 2: Critic reviewing initial code...")
                review_task = config.DUAL_AGENT_TASK_CODE_REVIEW.format(
                    prompt=problem_prompt,
                    generated_code=initial_code
                )

                res2 = critic.generate_reply(messages=[{"content": review_task, "role": "user"}])
                feedback = res2.get("content", "") if res2 else ""

                print(f"  Feedback received: {len(feedback)} chars")

                # === CRITICAL: Check if revision is needed ===
                feedback_upper = feedback.upper()
                needs_revision = not ("CORRECT" in feedback_upper or
                                     "NO BUG" in feedback_upper or
                                     "LOOKS GOOD" in feedback_upper or
                                     len(feedback.strip()) < 15)

                if needs_revision:
                    # === TURN 3: Programmer revises based on feedback ===
                    print("Turn 3: Programmer revising code...")
                    revision_task = config.DUAL_AGENT_TASK_CODE_REVISION.format(
                        original_prompt=problem_prompt,
                        initial_code=initial_code,
                        feedback=feedback
                    )

                    res3 = programmer.generate_reply(messages=[{"content": revision_task, "role": "user"}])
                    revised_response = res3.get("content", "") if res3 else ""
                    revised_code = extract_code_from_response(revised_response)

                    print(f"  Revised code extracted: {len(revised_code)} chars, has 'def': {'def' in revised_code}")

                    # === TURN 4: Critic final assessment ===
                    print("Turn 4: Critic final assessment...")
                    final_task = config.DUAL_AGENT_TASK_FINAL_ASSESSMENT.format(
                        original_prompt=problem_prompt,
                        revised_code=revised_code,
                        previous_feedback=feedback
                    )

                    res4 = critic.generate_reply(messages=[{"content": final_task, "role": "user"}])
                    final_assessment = res4.get("content", "") if res4 else ""

                    # Use revised code
                    final_code = revised_code if (revised_code and 'def' in revised_code) else initial_code

                    if final_code == revised_code:
                        stats['used_revised_code'] += 1
                        print("  ✓ Using revised code")
                    else:
                        stats['used_initial_code'] += 1
                        print("  ⚠ Using initial code (revision failed)")

                else:
                    # Skip revision - code is correct
                    print("  ✓ Code approved - skipping revision (Turns 3-4)")
                    revised_code = initial_code
                    final_assessment = "APPROVED - No revision needed"
                    final_code = initial_code
                    stats['used_initial_code'] += 1
                    stats['skipped_revision'] += 1

                # === Check extraction quality ===
                if final_code and 'def' in final_code:
                    stats['successful_extractions'] += 1
                else:
                    stats['failed_extractions'] += 1
                    print("  ✗ WARNING: No valid function definition found!")

                # === Save result ===
                result = {
                    'task_id': task_id,
                    'prompt': problem_prompt,
                    'entry_point': sample.get('entry_point', ''),
                    'canonical_solution': sample.get('canonical_solution', ''),
                    'test': sample.get('test', ''),
                    'generated_solution': final_code,
                    'conversation': {
                        'initial_code': initial_code,
                        'critic_feedback': feedback,
                        'revised_code': revised_code if needs_revision else None,
                        'final_assessment': final_assessment if needs_revision else "Skipped"
                    },
                    'metadata': {
                        'used_code_version': 'revised' if (needs_revision and final_code == revised_code) else 'initial',
                        'revision_skipped': not needs_revision,
                        'timestamp': datetime.now().isoformat(),
                        'error': ''
                    }
                }

                with open(detailed_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(result) + '\n')

                results.append(result)

                if (i + 1) % 10 == 0:
                    print(f"\n✓ Progress checkpoint: {i + 1}/{len(remaining_samples)} samples completed")
                    print(f"  Success rate: {stats['successful_extractions']}/{i+1} ({stats['successful_extractions']/(i+1)*100:.1f}%)")
                    print(f"  Revisions skipped: {stats['skipped_revision']}")

            except Exception as e:
                print(f"ERROR processing sample {task_id}: {e}")
                # Save failed result
                failed_result = {
                    'task_id': task_id,
                    'prompt': sample.get('prompt', ''),
                    'entry_point': sample.get('entry_point', ''),
                    'canonical_solution': sample.get('canonical_solution', ''),
                    'test': sample.get('test', ''),
                    'generated_solution': '',
                    'conversation': {
                        'initial_code': '',
                        'critic_feedback': '',
                        'revised_code': None,
                        'final_assessment': ''
                    },
                    'metadata': {
                        'used_code_version': 'error',
                        'revision_skipped': False,
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e)
                    }
                }
                with open(detailed_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(failed_result) + '\n')
                results.append(failed_result)
                stats['failed_extractions'] += 1
                continue
    
    finally:
        emissions = tracker.stop()
        print(f"\nEmissions this run: {emissions:.6f} kg CO2")

        # Update energy tracking
        energy_data['total_emissions'] += emissions
        energy_data['sessions'] += 1
        energy_data['session_history'].append({
            'timestamp': datetime.now().isoformat(),
            'emissions_kg_co2': emissions,
            'samples_processed': len(remaining_samples)
        })
        save_energy_data(energy_data, energy_file)

        stats['emissions_kg_co2'] = emissions
        stats['total_emissions'] = energy_data['total_emissions']

        print(f"\n{'='*60}")
        print("DUAL-AGENT GENERATION COMPLETED")
        print(f"{'='*60}")
        print(f"Total samples: {stats['total_samples']}")
        print(f"Successful extractions: {stats['successful_extractions']}")
        print(f"Failed extractions: {stats['failed_extractions']}")
        print(f"Used revised code: {stats['used_revised_code']}")
        print(f"Used initial code: {stats['used_initial_code']}")
        print(f"Revisions skipped: {stats['skipped_revision']}")
        print(f"Emissions this session: {emissions:.6f} kg CO2")
        print(f"Total emissions (all sessions): {energy_data['total_emissions']:.6f} kg CO2")
        print(f"{'='*60}")

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

    return detailed_file, exp_name






# --- Main Execution ---
def main():
    print("\n" + "="*60)
    print("DUAL-AGENT CODE GENERATION")
    print("="*60)

    # Load dataset
    code_samples = read_code_generation_data(DATASET_FILE)

    # Run dual-agent generation
    print(f"\nRunning {DESIGN} dual-agent code generation...")
    detailed_file, final_exp_name = run_inference_with_emissions(
        code_samples,
        llm_config,
        config.SYS_MSG_PROGRAMMER,      # ✅ Correct from config
        config.SYS_MSG_CODE_REVIEWER,   # ✅ Correct from config
        exp_name,
        RESULT_DIR,
        DESIGN,  # Pass design parameter
        model    # Pass model parameter
    )

    print(f"\nResults saved to: {detailed_file}")
    print(f"Experiment name: {final_exp_name}")

    # Run evaluation
    print("\n" + "="*60)
    print("STARTING EVALUATION")
    print("="*60)

    try:
        eval_result = subprocess.run(
            ["python", "src/evaluate_code_generation.py", detailed_file],
            capture_output=True,
            text=True,
            timeout=600
        )

        print(eval_result.stdout)

        if eval_result.returncode != 0:
            print("Evaluation encountered an error:")
            print(eval_result.stderr)
        else:
            print("\n" + "="*60)
            print("EVALUATION COMPLETED SUCCESSFULLY")
            print("="*60)

    except subprocess.TimeoutExpired:
        print("Evaluation timed out after 10 minutes")
    except Exception as e:
        print(f"Failed to run evaluation: {e}")
        print(f"You can manually evaluate by running:")
        print(f"python src/evaluate_code_generation.py {detailed_file}")


if __name__ == "__main__":
    main()
