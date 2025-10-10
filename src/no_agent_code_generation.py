import os
import json
import time
import config
from datetime import datetime
from codecarbon import OfflineEmissionsTracker
import requests
import subprocess

# --- Configuration ---
llm_config = config.LLM_CONFIG
DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

DESIGN = "no-agent"
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
project_name = DESIGN.capitalize()
exp_name = f"{project_name}_{model}_{timestamp}"

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

# --- Helper Functions ---
def generate_code_with_ollama(prompt, model_name, api_base):
    """Call Ollama API directly without agents"""
    url = f"{api_base}/v1/chat/completions"
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are an expert Python programmer."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling Ollama API: {e}")
        return ""

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
def run_inference_with_emissions(code_samples, llm_config, exp_name, result_dir):
    """Run code generation with emissions tracking and incremental saving"""
    
    # Create the output file path
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    
    model_name = llm_config["config_list"][0]["model"]
    api_base = llm_config["config_list"][0]["api_base"]
    
    tracker = OfflineEmissionsTracker(
        project_name=exp_name, 
        output_dir=result_dir, 
        country_iso_code="CAN",
        save_to_file=True
    )
    tracker.start()
    
    try:
        for i, sample in enumerate(code_samples):
            print(f"Processing sample {i+1}/{len(code_samples)} (task_id: {sample.get('task_id', i)})")
            
            # Get problem prompt (minimal, no extra instructions)
            problem_prompt = sample.get('prompt', sample.get('description', ''))
            
            # Direct API call without agent framework
            response_text = generate_code_with_ollama(problem_prompt, model_name, api_base)
            
            # Store result with full sample information
            result = {
                'task_id': sample.get('task_id', ''),
                'prompt': problem_prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', '')
            }
            
            if response_text:
                generated_code = extract_code_from_response(response_text)
                result['generated_solution'] = generated_code
            else:
                result['generated_solution'] = ""
                print(f"[Warning] Skipped sample {i} — no response.")
            
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
time.sleep(1)

print(f"Running {DESIGN} code generation (no agent framework)...")
detailed_file = run_inference_with_emissions(
    code_samples, 
    llm_config, 
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
