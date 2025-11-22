import os
import json
import time
import config
from datetime import datetime
from autogen import AssistantAgent
from codecarbon import OfflineEmissionsTracker
from resume_utils import ExperimentResume
import sys
import subprocess

# --- Configuration ---
llm_config = config.LLM_CONFIG

DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

# Parse command line arguments
if len(sys.argv) > 1:
    DESIGN = sys.argv[1]
    # Support both baseline and RQ3 explain-before modes
    valid_designs = ["SA-zero", "SA-few", "SA-zero-explain", "SA-few-explain"]
    if DESIGN not in valid_designs:
        print(f"Error: Invalid design '{DESIGN}'. Must be one of: {', '.join(valid_designs)}")
        sys.exit(1)
else:
    print("Usage: python single_agent_code_generation.py <design>")
    print("Designs:")
    print("  SA-zero          : Single-agent zero-shot (baseline)")
    print("  SA-few           : Single-agent few-shot (baseline)")
    print("  SA-zero-explain  : Single-agent zero-shot with explain-before (RQ3)")
    print("  SA-few-explain   : Single-agent few-shot with explain-before (RQ3)")
    sys.exit(1)

# Determine if this is an explanation mode run
EXPLANATION_MODE = DESIGN.endswith("-explain")
BASE_DESIGN = DESIGN.replace("-explain", "") if EXPLANATION_MODE else DESIGN

print(f"Running with design: {DESIGN}")
if EXPLANATION_MODE:
    print(f"[RQ3] Explanation mode enabled - using explain-before prompting")

# Select appropriate prompts based on mode
if EXPLANATION_MODE:
    # RQ3: Use explain-before prompts
    if BASE_DESIGN == "SA-zero":
        sys_prompt = config.SYS_MSG_CODE_GENERATOR_EXPLAIN_BEFORE_ZERO_SHOT
        task = config.CODE_GENERATION_TASK_PROMPT_EXPLAIN_BEFORE
    else:  # SA-few
        sys_prompt = config.SYS_MSG_CODE_GENERATOR_EXPLAIN_BEFORE_FEW_SHOT
        task = config.CODE_GENERATION_TASK_PROMPT_EXPLAIN_BEFORE
else:
    # Baseline: Use standard prompts
    if BASE_DESIGN == "SA-zero":
        sys_prompt = config.SYS_MSG_CODE_GENERATOR_ZERO_SHOT
        task = config.CODE_GENERATION_TASK_PROMPT
    else:  # SA-few
        sys_prompt = config.SYS_MSG_CODE_GENERATOR_FEW_SHOT
        task = config.CODE_GENERATION_TASK_PROMPT

model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

print(f"Experiment: {exp_name}")
print(f"Dataset: {DATASET_FILE}")
print(f"Results will be saved to: {RESULT_DIR}")

# --- Agent Creation ---
def create_code_generator_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="code_generator_agent",
        system_message=sys_prompt,
        description="Generate Python code solutions.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

# --- Data Reading ---
def read_code_generation_data(dataset_path):
    """Read code generation data from JSONL file"""
    code_problems = []
    with open(dataset_path, 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            code_problems.append(data)
    return code_problems

# Read dataset
print(f"Reading dataset from: {DATASET_FILE}")
code_samples = read_code_generation_data(DATASET_FILE)
print(f"Loaded {len(code_samples)} code samples")

# Validate dataset has valid task_ids
invalid_count = sum(1 for sample in code_samples if not sample.get('task_id', ''))
if invalid_count > 0:
    print(f"[WARNING] Found {invalid_count} samples without valid task_ids - these will be reprocessed on resume!")
    print(f"[WARNING] This could cause duplicate entries and inflated emissions measurements!")

# --- Helper Functions ---
def extract_code_from_response(response_text):
    """Extract Python code from model response"""
    if not response_text:
        return ""
    
    response_text = response_text.strip()
    
    # Check for code blocks
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
    
    # Find function definition
    lines = response_text.split('\n')
    code_lines = []
    found_def = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith(('To solve', 'The ', 'This ', 'Here', 'Note:', '**')):
            if not found_def:
                continue
            else:
                break
        
        if stripped.startswith(('def ', 'from ', 'import ')):
            found_def = True
        
        if found_def:
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return response_text.strip()

def extract_code_and_explanation(response_text, explanation_mode=False):
    """
    Extract explanation (REASONING) and code (CODE) from response.

    For RQ3 explain-before mode:
        Expected format: "REASONING: [plan] CODE: [implementation]"

    For baseline mode:
        Uses existing code extraction logic

    Returns:
        tuple: (code, reasoning, explanation_length)
    """
    if not response_text:
        return "", "", 0

    response_text = response_text.strip()
    response_lower = response_text.lower()

    if explanation_mode:
        # RQ3 mode: Extract structured REASONING and CODE
        reasoning = ""
        code_text = ""

        # Try to extract REASONING section
        if "reasoning:" in response_lower:
            reasoning_start = response_lower.find("reasoning:")
            reasoning_end = response_lower.find("code:", reasoning_start)

            if reasoning_end > reasoning_start:
                reasoning = response_text[reasoning_start + len("reasoning:"):reasoning_end].strip()
            else:
                # No CODE section found, treat rest as reasoning
                reasoning = response_text[reasoning_start + len("reasoning:"):].strip()

        # Try to extract CODE section
        if "code:" in response_lower:
            code_start = response_lower.find("code:")
            code_text = response_text[code_start + len("code:"):].strip()

        # Extract actual code from CODE section using existing logic
        if code_text:
            generated_code = extract_code_from_response(code_text)
        else:
            # Fallback: try to extract code from entire response
            generated_code = extract_code_from_response(response_text)

        # If no reasoning was extracted, use full response as reasoning
        if not reasoning:
            reasoning = response_text

        explanation_length = len(reasoning)

        return generated_code, reasoning, explanation_length
    else:
        # Baseline mode: existing code extraction logic
        generated_code = extract_code_from_response(response_text)
        reasoning = response_text
        explanation_length = 0

        return generated_code, reasoning, explanation_length

# --- With CodeCarbon Emissions Tracking ---
def run_inference_with_emissions(code_samples, llm_config, sys_prompt, task, exp_name, result_dir, design, model, explanation_mode=False):
    """Run code generation with emissions tracking and incremental saving"""

    # Initialize resume helper
    resume = ExperimentResume(result_dir, design, model, exp_name)
    exp_name, detailed_file, energy_file, skip_next_sample = resume.initialize()

    # Load existing results and energy data
    existing_results = resume.load_results(detailed_file)
    energy_data = resume.load_energy(energy_file)

    # Filter remaining samples
    remaining_samples = resume.filter_remaining_samples(code_samples, existing_results, id_field='task_id')

    # Handle skip next sample option
    if skip_next_sample and remaining_samples:
        skip_sample = remaining_samples[0]
        failed_result = resume.create_skip_result(skip_sample, id_field='task_id')
        with open(detailed_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(failed_result) + '\n')
        existing_results.append(failed_result)
        remaining_samples = remaining_samples[1:]

    # Create codecarbon subdirectory for this experiment (following vulnerability detection pattern)
    model_type = "thinking" if config.ENABLE_REASONING else "baseline"
    design_lower = DESIGN.lower()
    codecarbon_dir = os.path.join(result_dir, f"codecarbon_{model_type}_{design_lower}")
    os.makedirs(codecarbon_dir, exist_ok=True)

    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=codecarbon_dir,
        country_iso_code="CAN",
        save_to_file=True
    )
    tracker.start()

    try:
        code_generator = create_code_generator_agent(llm_config, sys_prompt)

        for i, sample in enumerate(remaining_samples):
            task_id = sample.get('task_id', f'sample_{i}')
            print(f"Processing sample {i+1}/{len(remaining_samples)} (task_id: {task_id})")
            
            # Format task with prompt
            problem_prompt = sample.get('prompt', sample.get('description', ''))
            content = task.format(prompt=problem_prompt)
            
            # Store result with full sample information
            result = {
                'task_id': sample.get('task_id', ''),
                'prompt': problem_prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', ''),
                'reasoning': '',
                'explanation_length': 0
            }

            try:
                res = code_generator.generate_reply(messages=[{"content": content, "role": "user"}])

                if res is not None and "content" in res:
                    response_text = res["content"].strip()

                    # Use explanation extraction function (handles both modes)
                    generated_code, reasoning, explanation_length = extract_code_and_explanation(
                        response_text,
                        explanation_mode=explanation_mode
                    )

                    result['generated_solution'] = generated_code
                    result['reasoning'] = reasoning
                    result['explanation_length'] = explanation_length
                else:
                    result['generated_solution'] = ""
                    result['error'] = "no_response"
                    print(f"[Warning] Skipped sample {i} — no response or invalid format.")

            except Exception as e:
                # Handle errors (timeout, API errors, etc.) - save error and continue
                error_msg = str(e)
                print(f"[ERROR] Sample {task_id} failed: {error_msg}")
                result['generated_solution'] = ""
                result['error'] = error_msg
            
            # Validate task_id before saving
            if not result.get('task_id', ''):
                print(f"[ERROR] Sample {i} missing task_id! This will cause issues on resume.")

            # Save immediately after each sample (append mode)
            with open(detailed_file, 'a') as f:
                f.write(json.dumps(result) + '\n')

            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"Progress saved: {i + 1}/{len(remaining_samples)} samples completed")

    finally:
        emissions = tracker.stop()
        print(f"\nEmissions this run: {emissions:.6f} kg CO2")

        # Update energy tracking
        resume.save_energy(energy_data, energy_file, emissions, len(remaining_samples))

        print(f"Total emissions (all sessions): {energy_data['total_emissions']:.6f} kg CO2")

    return detailed_file, exp_name

# --- Main Execution ---
time.sleep(1)  # Brief initialization pause

print(f"Running {DESIGN} code generation...")
detailed_file, final_exp_name = run_inference_with_emissions(
    code_samples,
    llm_config,
    sys_prompt,
    task,
    exp_name,
    RESULT_DIR,
    DESIGN,
    model,
    explanation_mode=EXPLANATION_MODE
)

print(f"\nCode generation completed for experiment: {final_exp_name}")
print(f"Total samples in dataset: {len(code_samples)}")
print(f"Results saved to: {detailed_file}")

# --- Call Evaluation Script ---
print("\n" + "="*80)
print("STARTING EVALUATION")
print("="*80)

try:
    # Call the evaluation script with the results file
    eval_result = subprocess.run(
        ["python3", "src/evaluate_code_generation.py", detailed_file],
        capture_output=True,
        text=True
    )
    
    print(eval_result.stdout)
    
    if eval_result.returncode != 0:
        print("Evaluation encountered an error:")
        print(eval_result.stderr)
    else:
        print("\n" + "="*80)
        print("EVALUATION COMPLETED SUCCESSFULLY")
        print("="*80)
        
except Exception as e:
    print(f"Failed to run evaluation: {e}")
    print("You can manually evaluate by running:")
    print(f"python evaluate_code_generation.py {detailed_file}")
