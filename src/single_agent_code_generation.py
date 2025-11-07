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
task = config.CODE_GENERATION_TASK_PROMPT
sys_prompt_few_shot = config.SYS_MSG_CODE_GENERATOR_FEW_SHOT
sys_prompt_zero_shot = config.SYS_MSG_CODE_GENERATOR_ZERO_SHOT

DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

# Parse command line arguments
if len(sys.argv) > 1:
    DESIGN = sys.argv[1]
    if DESIGN not in ["SA-zero", "SA-few"]:
        print(f"Error: Invalid design '{DESIGN}'. Must be 'SA-zero' or 'SA-few'")
        sys.exit(1)
else:
    print("Usage: python single_agent_code_generation.py <design>")
    print("design: SA-zero or SA-few")
    sys.exit(1)

model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
project_name = DESIGN.capitalize()

# Search for existing results file for this design+model combination (resume capability)
import glob
existing_files = glob.glob(os.path.join(RESULT_DIR, f"{project_name}_{model}_*_detailed_results.jsonl"))

if existing_files:
    # Resume from existing file (use the most recent one if multiple exist)
    existing_files.sort(reverse=True)  # Most recent first
    existing_file = existing_files[0]
    # Extract the timestamp from the existing filename
    exp_name = os.path.basename(existing_file).replace("_detailed_results.jsonl", "")
    print(f"Found existing experiment file: {existing_file}")
    print(f"Resuming experiment: {exp_name}")
else:
    # Create new experiment with current timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_name = f"{project_name}_{model}_{timestamp}"
    print(f"Starting new experiment: {exp_name}")

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

# --- With CodeCarbon Emissions Tracking ---
def run_inference_with_emissions(code_samples, llm_config, sys_prompt, task, exp_name, result_dir):
    """Run code generation with emissions tracking and incremental saving"""

    # Create the output file path
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")

    # Load already completed task_ids (for resume capability)
    completed_task_ids = set()
    if os.path.exists(detailed_file):
        print(f"Found existing results file, loading completed tasks...")
        with open(detailed_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        result = json.loads(line)
                        task_id = result.get('task_id', '')
                        # Only add non-empty task_ids to avoid treating all empty task_ids as the same
                        if task_id:
                            completed_task_ids.add(task_id)
                    except json.JSONDecodeError:
                        pass
        print(f"Found {len(completed_task_ids)} already completed tasks. Resuming from where we left off...")

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

        for i, sample in enumerate(code_samples):
            task_id = sample.get('task_id', '')

            # Skip if already completed
            if task_id in completed_task_ids:
                print(f"Skipping sample {i+1}/{len(code_samples)} (task_id: {task_id}) - already completed")
                continue
            print(f"Processing sample {i+1}/{len(code_samples)} (task_id: {sample.get('task_id', i)})")
            
            # Format task with prompt
            problem_prompt = sample.get('prompt', sample.get('description', ''))
            content = task.format(prompt=problem_prompt)
            
            # Store result with full sample information
            result = {
                'task_id': sample.get('task_id', ''),
                'prompt': problem_prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', '')
            }

            try:
                res = code_generator.generate_reply(messages=[{"content": content, "role": "user"}])

                if res is not None and "content" in res:
                    response_text = res["content"].strip()
                    generated_code = extract_code_from_response(response_text)
                    result['generated_solution'] = generated_code
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
                print(f"Progress saved: {i + 1}/{len(code_samples)} samples completed")
                
    finally:
        emissions = tracker.stop()
        print(f"Emissions: {emissions} kg CO2")
    
    return detailed_file

# --- Main Execution ---
time.sleep(1)  # Brief initialization pause

# Select system prompt based on design
if DESIGN == "SA-few":
    sys_prompt = sys_prompt_few_shot
    print("Using few-shot system prompt")
else:
    sys_prompt = sys_prompt_zero_shot
    print("Using zero-shot system prompt")

print(f"Running {DESIGN} code generation...")
detailed_file = run_inference_with_emissions(
    code_samples, 
    llm_config, 
    sys_prompt, 
    task, 
    exp_name, 
    RESULT_DIR
)

print(f"\nCode generation completed for experiment: {exp_name}")
print(f"Total samples processed: {len(code_samples)}")
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
