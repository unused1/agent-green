import os
import time
import config
from datetime import datetime
import ollama
from codecarbon import EmissionsTracker
from log_utils import save_templates
from ollama_utils import start_ollama_server, stop_ollama_server
from vuln_evaluation import evaluate_and_save_vulnerability, normalize_vulnerability_basic, normalize_vulnerability_conservative, normalize_vulnerability_strict
import json

# --- Configuration ---
llm_config = config.LLM_CONFIG
task = config.VULNERABILITY_TASK_PROMPT
sys_prompt_few_shot_vuln_detector = config.SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT
sys_prompt_zero_shot_vuln_detector = config.SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT

LOG_DIR = config.LOG_DIR
RESULT_DIR = config.RESULT_DIR
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

# Use vulnerability dataset from config
DATASET_FILE = config.VULN_DATASET

DESIGN = "NA-zero-vuln"  # Change to "NA-few-vuln" for few-shot
model_name = llm_config["config_list"][0]["model"]
model = llm_config["config_list"][0]["model"].replace(":", "-")
temperature = llm_config["temperature"]
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
project_name = DESIGN.capitalize()
exp_name = f"{project_name}_{model}_{timestamp}"

# --- Ollama Query Function ---
def ask_ollama(model, prompt):
    """Query Ollama model with a prompt"""
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

# --- Read Vulnerability Data ---
def read_vulnerability_data(vuln_dataset_path):
    """Read vulnerability data from JSONL file"""
    vulnerabilities = []
    with open(vuln_dataset_path, 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            vulnerabilities.append(data)
    return vulnerabilities

# Read vulnerability dataset
print(f"Reading vulnerability dataset from: {DATASET_FILE}")
vuln_data = read_vulnerability_data(DATASET_FILE)
print(f"Loaded {len(vuln_data)} vulnerability samples")

# Extract ground truth from the vulnerability data
ground_truth = [item['target'] for item in vuln_data]
print(f"Extracted {len(ground_truth)} ground truth labels")

# --- With CodeCarbon ---
def run_vulnerability_detection_with_emissions(vuln_data, model_name, prompt_prefix, task, exp_name, result_dir):
    """
    Run vulnerability detection inference with emissions tracking
    """
    vulnerability_detections = []
    
    # Create JSON results file
    json_results_file = os.path.join(result_dir, f"{exp_name}_results.json")
    
    tracker = EmissionsTracker(project_name=exp_name, output_dir=result_dir, save_to_file=True)
    tracker.start()
    
    try:
        for i, vuln_item in enumerate(vuln_data):
            print(f"Processing vulnerability detection for item {i+1}/{len(vuln_data)}")
            
            # Format the task prompt with the function code
            formatted_task = task.format(func=vuln_item['func'])
            prompt = prompt_prefix + formatted_task
            response = ask_ollama(model_name, prompt)
            
            if response is not None:
                vulnerability_detections.append(response)
                prediction = response
            else:
                print(f"[Warning] Skipped vulnerability item {i} — no response or invalid format.")
                vulnerability_detections.append("")
                prediction = ""
            
            # Create record in the same format as your vulnerability dataset
            record = {
                'idx': vuln_item.get('idx', i),
                'project': vuln_item.get('project', ''),
                'commit_id': vuln_item.get('commit_id', ''),
                'project_url': vuln_item.get('project_url', ''),
                'commit_url': vuln_item.get('commit_url', ''),
                'commit_message': vuln_item.get('commit_message', ''),
                'ground_truth': vuln_item.get('ground_truth', vuln_item.get('target')),
                'cwe': vuln_item.get('cwe', []),
                'cve': vuln_item.get('cve', ''),
                'cve_desc': vuln_item.get('cve_desc', ''),
                'vuln': vuln_item.get('vuln', vuln_item.get('target')),
                'func': vuln_item['func'],
                'target': vuln_item['target'],
                'prediction': prediction,
                'reasoning': prediction
            }
            
            # Save each record as a separate JSONL line (append mode)
            with open(json_results_file, 'a') as f:
                json.dump(record, f)
                f.write('\n')
            
            print(f"Saved result for item {i+1} to {json_results_file}")
                
    finally:
        emissions = tracker.stop()
        print(f"Vulnerability Detection Emissions: {emissions} kg CO2")
        
    return vulnerability_detections

# --- Main Execution ---
print(f"\nStarting {DESIGN} vulnerability detection...")
print(f"Model: {model_name}")
print(f"Temperature: {temperature}")
print(f"Experiment name: {exp_name}")

# Start Ollama server
print("\nStarting Ollama server...")
proc = start_ollama_server()
time.sleep(5)  # Give it some time to initialize

try:
    # Run vulnerability detection with emissions tracking
    # Change to sys_prompt_few_shot_vuln_detector for few-shot learning
    vulnerability_detections = run_vulnerability_detection_with_emissions(
        vuln_data, 
        model_name, 
        sys_prompt_zero_shot_vuln_detector,  # or sys_prompt_few_shot_vuln_detector
        task, 
        exp_name, 
        RESULT_DIR
    )

    print(f"\nAll detailed results saved incrementally to: {os.path.join(RESULT_DIR, f'{exp_name}_results.json')} in JSONL format")

    # Save vulnerability detection results (original format)
    print("\nSaving templates...")
    save_templates(vulnerability_detections, llm_config, DESIGN, RESULT_DIR)
    print(f"Templates saved for experiment: {exp_name}")

finally:
    # Stop Ollama server
    print("\nStopping Ollama server...")
    stop_ollama_server(proc)

# --- Evaluation ---
print("\n" + "="*60)
print("STARTING EVALUATIONS")
print("="*60)

# Extract predictions and ground truth
predictions = vulnerability_detections  # These are the raw string responses
ground_truth_labels = ground_truth  # These are the binary labels (0 or 1)

# Using basic normalization (searches for YES/NO)
print("\n[1/3] Evaluating with basic normalization...")
try:
    results = evaluate_and_save_vulnerability(
        normalize_vulnerability_basic, 
        predictions, 
        DATASET_FILE,  # Pass the dataset file path
        exp_name
    )
    print("✓ Basic normalization completed")
    print(f"   Accuracy: {results.get('accuracy', 0):.4f}")
except Exception as e:
    print(f"✗ Error in basic evaluation: {e}")
    import traceback
    traceback.print_exc()

# Using conservative normalization
print("\n[2/3] Evaluating with conservative normalization...")
try:
    results_v1 = evaluate_and_save_vulnerability(
        normalize_vulnerability_conservative, 
        predictions, 
        DATASET_FILE,
        f"{exp_name}_conservative"
    )
    print("✓ Conservative normalization completed")
    print(f"   Accuracy: {results_v1.get('accuracy', 0):.4f}")
except Exception as e:
    print(f"✗ Error in conservative evaluation: {e}")
    import traceback
    traceback.print_exc()

# Using strict normalization
print("\n[3/3] Evaluating with strict normalization...")
try:
    results_v2 = evaluate_and_save_vulnerability(
        normalize_vulnerability_strict, 
        predictions, 
        DATASET_FILE,
        f"{exp_name}_strict"
    )
    print("✓ Strict normalization completed")
    print(f"   Accuracy: {results_v2.get('accuracy', 0):.4f}")
except Exception as e:
    print(f"✗ Error in strict evaluation: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("ALL EVALUATIONS COMPLETED")
print("="*60)
print(f"Experiment name: {exp_name}")
print(f"Results saved in: {RESULT_DIR}")
print("\nFiles generated:")
print(f"  - {exp_name}_results.json (detailed JSONL results)")
print(f"  - {DESIGN}_{model}_{timestamp}_raw.txt (raw templates)")
print(f"  - {DESIGN}_{model}_{timestamp}_normalized.txt (normalized templates)")
print(f"  - emissions.csv (carbon emissions)")
print(f"  - {exp_name}_eval_*.json (evaluation results)")