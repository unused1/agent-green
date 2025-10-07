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
sys_prompt_zero_shot = config.CODE_GENERATION_TASK_PROMPT #config.SYS_MSG_CODE_GENERATOR_ZERO_SHOT

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

model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
project_name = DESIGN.capitalize()
exp_name = f"{project_name}_{model}_{timestamp}"

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

### code extraction ###
def extract_code_from_response(response_text):
    """Extract code from <ANS></ANS> tags"""
    import re
    
    if not response_text:
        return ""
    
    # Remove thinking blocks if present
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
    response_text = response_text.strip()
    
    # Extract content between <ANS> and </ANS>
    ans_pattern = r'<ANS>(.*?)</ANS>'
    matches = re.findall(ans_pattern, response_text, re.DOTALL | re.IGNORECASE)
    
    if matches:
        code = matches[0].strip()
        # Remove markdown backticks if present
        code = code.strip('`').strip()
        # If code starts with "python", remove it
        if code.startswith('python\n'):
            code = code[7:]
        elif code.startswith('python '):
            code = code[7:]
        return code
    
    # Handle malformed tags - content after <ANS> without closing tag
    ans_start = re.search(r'<ANS>', response_text, re.IGNORECASE)
    if ans_start:
        code = response_text[ans_start.end():]
        # Try to find closing tag
        ans_end = re.search(r'</ANS>', code, re.IGNORECASE)
        if ans_end:
            code = code[:ans_end.start()]
        code = code.strip().strip('`').strip()
        if code.startswith('python\n'):
            code = code[7:]
        elif code.startswith('python '):
            code = code[7:]
        return code
    
    # If no ANS tags found, return empty
    return ""


# --- With CodeCarbon Emissions Tracking ---
def run_inference_with_emissions(code_samples, llm_config, sys_prompt, task, exp_name, result_dir):
    """Run code generation with emissions tracking and incremental saving"""
    
    # Create the output file path
    detailed_file = os.path.join(result_dir, f"{exp_name}-code-gen_detailed_results.jsonl")
    
    tracker = OfflineEmissionsTracker(
        project_name=exp_name, 
        output_dir=result_dir, 
        country_iso_code="CAN",
        save_to_file=True
    )
    tracker.start()
    
    try:
        code_generator = create_code_generator_agent(llm_config, sys_prompt)
        
        for i, sample in enumerate(code_samples):
            print(f"Processing sample {i+1}/{len(code_samples)} (task_id: {sample.get('task_id', i)})")
            
            # Format task with prompt
            problem_prompt = sample.get('prompt', sample.get('description', ''))
            content = task.format(prompt=problem_prompt)
            
            res = code_generator.generate_reply(messages=[{"content": content, "role": "user"}])
            
            # Store result with full sample information
            result = {
                'task_id': sample.get('task_id', ''),
                'prompt': problem_prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', '')
            }
            
            if res is not None and "content" in res:
                response_text = res["content"].strip()
                generated_code = extract_code_from_response(response_text)
                result['generated_solution'] = generated_code
            else:
                result['generated_solution'] = ""
                print(f"[Warning] Skipped sample {i} — no response or invalid format.")
            
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
        ["python", "src/evaluate_code_generation.py", detailed_file],
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
