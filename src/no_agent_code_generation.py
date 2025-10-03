import os
import time
import config
from datetime import datetime
import ollama
from codecarbon import EmissionsTracker
from log_utils import save_code_generation_results
from ollama_utils import start_ollama_server, stop_ollama_server
from code_gen_evaluation import evaluate_and_save_code_generation
import json

llm_config = config.LLM_CONFIG
task = config.CODE_GENERATION_TASK_PROMPT
sys_prompt_few_shot_code_gen = config.SYS_MSG_CODE_GENERATOR_FEW_SHOT
sys_prompt_zero_shot_code_gen = config.SYS_MSG_CODE_GENERATOR_ZERO_SHOT

LOG_DIR = config.LOG_DIR
RESULT_DIR = config.RESULT_DIR
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

# Use code generation dataset from config
code_gen_dataset = config.CODE_GEN_DATASET

DESIGN = "NA-zero-codegen"
model_name = llm_config["config_list"][0]["model"]
model = llm_config["config_list"][0]["model"].replace(":", "-")
temperature = llm_config["temperature"]
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
project_name = DESIGN.capitalize()
exp_name = f"{project_name}_{model}_{timestamp}"

# --- Ollama Query Function ---
def ask_ollama(model, prompt):
    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            options={'temperature': temperature}
        )
    except ollama.ResponseError as e:
        print('Error:', e.error)
        return None
    return response.get('response', None)

# --- Read Code Generation Data ---
def read_code_generation_data(dataset_path):
    """Read code generation data from JSONL file"""
    code_problems = []
    with open(dataset_path, 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            code_problems.append(data)
    return code_problems

# Read code generation dataset
print(f"Reading code generation dataset from: {code_gen_dataset}")
code_gen_data = read_code_generation_data(code_gen_dataset)
print(f"Loaded {len(code_gen_data)} code generation samples")

# Extract ground truth from the code generation data
# Assuming the dataset has a 'reference_solution' or 'canonical_solution' field
ground_truth = [item.get('canonical_solution', item.get('reference_solution', '')) for item in code_gen_data]
print(f"Extracted {len(ground_truth)} ground truth solutions")

# --- With CodeCarbon ---
def run_code_generation_with_emissions(code_gen_data, model_name, prompt_prefix, task, exp_name, result_dir):
    """
    Run code generation inference with emissions tracking
    """
    generated_codes = []
    
    # Create JSON results file
    json_results_file = os.path.join(result_dir, f"{exp_name}_results.json")
    
    tracker = EmissionsTracker(project_name=exp_name, output_dir=result_dir, save_to_file=True)
    tracker.start()
    
    try:
        for i, code_item in enumerate(code_gen_data):
            print(f"Processing code generation for item {i+1}/{len(code_gen_data)}")
            
            # Format the task prompt with the problem description
            # Adjust field names based on your dataset structure (e.g., 'prompt', 'description', 'instruction')
            problem_description = code_item.get('prompt', code_item.get('description', code_item.get('instruction', '')))
            formatted_task = task.format(problem=problem_description)
            prompt = prompt_prefix + formatted_task
            
            response = ask_ollama(model_name, prompt)
            
            if response is not None:
                generated_codes.append(response)
                prediction = response
            else:
                print(f"[Warning] Skipped code generation item {i} — no response or invalid format.")
                generated_codes.append("")
                prediction = ""
            
            # Create record in the same format as your code generation dataset
            record = {
                'idx': code_item.get('idx', code_item.get('task_id', i)),  # Use original idx/task_id if available
                'task_id': code_item.get('task_id', ''),
                'problem_description': problem_description,
                'entry_point': code_item.get('entry_point', ''),
                'canonical_solution': code_item.get('canonical_solution', code_item.get('reference_solution', '')),
                'test_cases': code_item.get('test', code_item.get('test_cases', '')),
                'difficulty': code_item.get('difficulty', ''),
                'language': code_item.get('language', 'python'),
                'prediction': prediction,
                'generated_code': prediction  # Store the generated code
            }
            
            # Save each record as a separate JSONL line (append mode)
            with open(json_results_file, 'a') as f:
                json.dump(record, f)
                f.write('\n')
            
            print(f"Saved result for item {i+1} to {json_results_file}")
                
    finally:
        emissions = tracker.stop()
        print(f"Code Generation Emissions: {emissions} kg CO2")
        
    return generated_codes

# Start Ollama server
proc = start_ollama_server()
time.sleep(5)  # Give it some time to initialize

# Run code generation with emissions tracking
# Change to sys_prompt_few_shot_code_gen for few-shot learning
generated_codes = run_code_generation_with_emissions(
    code_gen_data, 
    model_name, 
    sys_prompt_zero_shot_code_gen,  # or sys_prompt_few_shot_code_gen
    task, 
    exp_name, 
    RESULT_DIR
)

print(f"All detailed results saved incrementally to: {os.path.join(RESULT_DIR, f'{exp_name}_results.json')} in JSONL format")

# Save code generation results (if you have a save_code_generation_results function)
# print("Saving generated codes...")
# save_code_generation_results(generated_codes, llm_config, DESIGN, RESULT_DIR)
# print(f"Generated codes saved for experiment: {exp_name}")

# Stop Ollama server
stop_ollama_server(proc)

# Evaluate code generation results
# You'll need to implement evaluate_and_save_code_generation based on your evaluation metrics
# (e.g., pass@k, BLEU score, execution success rate, etc.)
print("Starting evaluations...")
print("Evaluating generated code...")
results = evaluate_and_save_code_generation(generated_codes, ground_truth, exp_name, RESULT_DIR)

print("All evaluations completed!")
print(f"Experiment name: {exp_name}")
print(f"Results should be in: {RESULT_DIR}")