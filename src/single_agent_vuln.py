import os
import json
import time
import config
from datetime import datetime
from autogen import AssistantAgent
from codecarbon import OfflineEmissionsTracker
#from codecarbon import EmissionsTracker
from vuln_evaluation import evaluate_and_save_vulnerability
import sys

# --- Configuration ---
llm_config = config.LLM_CONFIG

# Task prompt for vulnerability detection (using your simplified prompts)
task = config.VULNERABILITY_TASK_PROMPT

# System prompts for vulnerability detection (using your simplified prompts)
sys_prompt_few_shot_vulnerability_detector = config.SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT
sys_prompt_zero_shot_vulnerability_detector = config.SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT

# Directories (following original pattern)
DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

# change this for different designs: "SA-few" or "SA-zero"
#DESIGN = "SA-zero" #"SA-few"  # Change to "SA-zero" to test zero-shot approach

if len(sys.argv) > 1:
    DESIGN = sys.argv[1]
    if DESIGN not in ["SA-zero", "SA-few"]:
        print(f"Error: Invalid design '{DESIGN}'. Must be 'SA-zero' or 'SA-few'")
        sys.exit(1)
else:
    print("Usage: python script.py <design>")
    print("design: SA-zero or SA-few")
    sys.exit(1)

print(f"Running with design: {DESIGN}")


model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
project_name = DESIGN.capitalize()
exp_name = f"{project_name}_{model}_{timestamp}"
input_dataset_file = "VulTrial_386_samples_balanced.jsonl"  # Example dataset file name

# --- Agent Creation ---
def create_vulnerability_detector_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="vulnerability_detector_agent",
        system_message=sys_prompt,
        description="Analyze code functions to detect security vulnerabilities.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

# --- Data Loading ---
def detect_programming_language(code):
    """Simple heuristic to detect programming language from code syntax"""
    code_lower = code.lower()
    
    # C/C++ indicators
    if any(keyword in code for keyword in ['#include', 'printf', 'malloc', 'free', 'struct', 'typedef']):
        if any(keyword in code for keyword in ['std::', 'class', 'namespace', 'template', 'new ', 'delete']):
            return 'cpp'
        return 'c'
    
    # Java indicators
    elif any(keyword in code for keyword in ['public class', 'private ', 'protected ', 'import java', 'System.out']):
        return 'java'
    
    # C# indicators  
    elif any(keyword in code for keyword in ['using System', 'namespace ', 'public class', 'Console.Write']):
        return 'csharp'
    
    # JavaScript indicators
    elif any(keyword in code for keyword in ['function ', 'var ', 'let ', 'const ', 'document.', '$.', 'console.log']):
        return 'javascript'
    
    # Python indicators
    elif any(keyword in code for keyword in ['def ', 'import ', 'print(', 'if __name__', 'self.']):
        return 'python'
    
    # Default to unknown
    return 'unknown'

def analyze_dataset_languages(samples):
    """Analyze the programming languages in the dataset"""
    language_counts = {}
    
    for sample in samples:
        lang = detect_programming_language(sample['func'])
        language_counts[lang] = language_counts.get(lang, 0) + 1
    
    print("\n=== DATASET LANGUAGE ANALYSIS ===")
    total_samples = len(samples)
    for lang, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_samples) * 100
        print(f"{lang.upper()}: {count} samples ({percentage:.1f}%)")
    
    return language_counts

def load_vulnerability_dataset(file_path):
    """Load the vulnerability dataset from JSONL file (following original pattern)"""
    samples = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if 'func' in data and 'target' in data:
                    # Keep all original fields plus the function code
                    sample = {
                        'idx': data.get('idx'),
                        'project': data.get('project'),
                        'commit_id': data.get('commit_id'),
                        'project_url': data.get('project_url'),
                        'commit_url': data.get('commit_url'),
                        'commit_message': data.get('commit_message'),
                        'func': data['func'],
                        'target': data['target'],  # Ground truth: 1 = vulnerable, 0 = not vulnerable
                        'cwe': data.get('cwe'),
                        'cve': data.get('cve'),
                        'cve_desc': data.get('cve_desc')
                    }
                    samples.append(sample)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON line: {e}")
                continue
    
    return samples

# --- Initialize Results Files ---
def initialize_results_files(exp_name, result_dir):
    """Initialize result files for incremental saving"""
    
    # Initialize detailed results JSON file
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    
    # Initialize CSV file with headers
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")
    with open(csv_file, 'w') as f:
        f.write("idx,project,commit_id,project_url,commit_url,commit_message,ground_truth,vuln,reasoning,cwe,cve,cve_desc\n")
    
    # Initialize energy tracking file
    energy_file = os.path.join(result_dir, f"{exp_name}_energy_tracking.json")
    
    return detailed_file, csv_file, energy_file

# --- Save Templates (following original pattern) ---
def save_templates(vulnerability_predictions, llm_config, design, result_dir):
    """Save vulnerability predictions in format similar to original save_templates function"""
    
    # Extract just the predictions for the simple save (like original)
    predictions = [r['vuln'] for r in vulnerability_predictions]
    
    # Save predictions in simple format (similar to original save_templates)
    model = llm_config["config_list"][0]["model"].replace(":", "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    predictions_file = os.path.join(result_dir, f"{design}_{model}_{timestamp}_predictions.json")
    with open(predictions_file, 'w') as f:
        json.dump({
            "design": design,
            "model": model,
            "timestamp": timestamp,
            "predictions": predictions
        }, f, indent=2)
    
    print(f"Predictions saved to: {predictions_file}")
    return predictions

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

def append_result(result, detailed_file, csv_file):
    """Append a single result to both JSON and CSV files"""
    
    # Append to JSONL file (one JSON object per line)
    with open(detailed_file, 'a') as f:
        f.write(json.dumps(result) + '\n')
    
    # Append to CSV file
    with open(csv_file, 'a') as f:
        # Escape fields that might contain commas or quotes
        def escape_csv_field(field):
            if field is None:
                return ""
            field_str = str(field)
            if ',' in field_str or '"' in field_str or '\n' in field_str:
                return '"' + field_str.replace('"', '""') + '"'
            return field_str
        
        row = [
            escape_csv_field(result['idx']),
            escape_csv_field(result['project']),
            escape_csv_field(result['commit_id']),
            escape_csv_field(result['project_url']),
            escape_csv_field(result['commit_url']),
            escape_csv_field(result['commit_message']),
            escape_csv_field(result['ground_truth']),
            escape_csv_field(result['vuln']),
            escape_csv_field(result['reasoning']),
            escape_csv_field(result['cwe']),
            escape_csv_field(result['cve']),
            escape_csv_field(result['cve_desc'])
        ]
        f.write(','.join(row) + '\n')

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

# --- With CodeCarbon Emissions Tracking (following original pattern) ---
def run_inference_with_emissions(code_samples, llm_config, sys_prompt_vulnerability_detector, task, exp_name, result_dir):
    """Run vulnerability detection with emissions tracking and incremental saving"""
    
    # Initialize result files
    detailed_file, csv_file, energy_file = initialize_results_files(exp_name, result_dir)
    
    # Load existing results and energy data if any (for resuming interrupted runs)
    existing_results = load_existing_results(detailed_file)
    energy_data = load_existing_energy(energy_file)
    processed_indices = {r['idx'] for r in existing_results}
    
    # Filter out already processed samples
    remaining_samples = [s for s in code_samples if s['idx'] not in processed_indices]
    
    if len(remaining_samples) < len(code_samples):
        print(f"Resuming from {len(existing_results)} existing results")
        print(f"Processing remaining {len(remaining_samples)} samples")
        print(f"Previous energy consumption: {energy_data['total_emissions']:.6f} kg CO2")
    
    # Start new emissions tracking session
    session_start_time = datetime.now().isoformat()
    tracker = OfflineEmissionsTracker(
        project_name=f"{exp_name}_session_{energy_data['sessions'] + 1}", 
        output_dir=result_dir, 
        country_iso_code="CAN",
        save_to_file=True
    )
    tracker.start()
    
    try:
        vulnerability_detector = create_vulnerability_detector_agent(llm_config, sys_prompt_vulnerability_detector)
        
        for i, sample in enumerate(remaining_samples):
            print(f"Processing sample {i+1}/{len(remaining_samples)} (idx: {sample['idx']})")
            
            # Use format to insert function code into prompt template
            content = task.format(func=sample['func'])
            res = vulnerability_detector.generate_reply(messages=[{"content": content, "role": "user"}])
            
            # Initialize result with original metadata
            result = {
                'idx': sample['idx'],
                'project': sample['project'],
                'commit_id': sample['commit_id'],
                'project_url': sample['project_url'],
                'commit_url': sample['commit_url'],
                'commit_message': sample['commit_message'],
                'ground_truth': sample['target'],
                'cwe': sample['cwe'],
                'cve': sample['cve'],
                'cve_desc': sample['cve_desc']
            }
            
            # Updated response parsing for YES/NO format
            if res is not None and "content" in res:
                response_text = res["content"].strip()
                response_lower = response_text.lower()
                
                # Parse YES/NO responses (looking for your specific format)
                if "(1) yes" in response_lower or "yes:" in response_lower or "vulnerability detected" in response_lower:
                    result['vuln'] = 1
                    result['reasoning'] = response_text
                elif "(2) no" in response_lower or "no:" in response_lower or "no security vulnerability" in response_lower:
                    result['vuln'] = 0
                    result['reasoning'] = response_text
                else:
                    # Fallback: look for more general keywords
                    if any(keyword in response_lower for keyword in ['vulnerable', 'security risk', 'exploit', 'attack']):
                        result['vuln'] = 1
                    else:
                        result['vuln'] = 0  # Default to not vulnerable for unclear responses
                    result['reasoning'] = response_text
                    print(f"[Warning] Unclear response format for sample {i}: {response_text[:100]}...")
            else:
                result['vuln'] = 0  # Default to not vulnerable
                result['reasoning'] = "No response from agent"
                print(f"[Warning] Skipped sample {i} — no response or invalid format.")
            
            # Append result immediately to files
            append_result(result, detailed_file, csv_file)
            
            # Also add to existing results for final evaluation
            existing_results.append(result)
            
            # Optional: Save progress every 10 samples
            if (i + 1) % 10 == 0:
                print(f"Progress saved: {i + 1} samples processed")
                
    finally:
        # Stop current tracking session
        session_emissions = tracker.stop()
        session_end_time = datetime.now().isoformat()
        
        # Update energy data with this session
        energy_data['total_emissions'] += session_emissions
        energy_data['sessions'] += 1
        energy_data['session_history'].append({
            'session': energy_data['sessions'],
            'start_time': session_start_time,
            'end_time': session_end_time,
            'samples_processed': len(remaining_samples),
            'session_emissions': session_emissions
        })
        
        # Save updated energy data
        save_energy_data(energy_data, energy_file)
        
        print(f"Current session emissions: {session_emissions:.6f} kg CO2")
        print(f"Total cumulative emissions: {energy_data['total_emissions']:.6f} kg CO2")
    
    print(f"Detailed results saved incrementally to: {detailed_file}")
    print(f"CSV results saved incrementally to: {csv_file}")
    print(f"Energy tracking saved to: {energy_file}")
    
    return existing_results, energy_data

# --- Code Reading (following original pattern) ---
print("Loading vulnerability dataset...")
code_samples = load_vulnerability_dataset(DATASET_FILE)
print(f"Loaded {len(code_samples)} code samples")

# Debug information
print(f"DEBUG: DATASET_FILE path = {DATASET_FILE}")
print(f"DEBUG: Total samples loaded = {len(code_samples)}")
if code_samples:
    print(f"DEBUG: First sample idx = {code_samples[0]['idx']}")
    print(f"DEBUG: Last sample idx = {code_samples[-1]['idx']}")

# Analyze language distribution
language_distribution = analyze_dataset_languages(code_samples)

# --- Main Execution (following original pattern) ---
def main():
    # Start ollama server if needed (from original script)
    #try:
        #from ollama_utils import start_ollama_server, stop_ollama_server
        #proc = start_ollama_server()
        #time.sleep(5)  # Give it some time to initialize
        #ollama_started = True
    #except ImportError:
    #    print("Ollama utils not available, proceeding without local server management")
    #    proc = None
    #    ollama_started = False
    
    try:
        # Select system prompt based on design (following original pattern)
        if DESIGN == "SA-few":
            sys_prompt = sys_prompt_few_shot_vulnerability_detector
        else:  # SA-zero
            sys_prompt = sys_prompt_zero_shot_vulnerability_detector
            
        print(f"Running {DESIGN} vulnerability detection...")
        
        # Run vulnerability detection (following original pattern)
        vulnerability_predictions, energy_data = run_inference_with_emissions(
            code_samples, 
            llm_config, 
            sys_prompt, 
            task, 
            exp_name, 
            RESULT_DIR
        )
        
        # Save templates (following original pattern)
        save_templates(vulnerability_predictions, llm_config, DESIGN, RESULT_DIR)
        
        # Extract ground truth for evaluation (following original pattern)
        ground_truth = [r['ground_truth'] for r in vulnerability_predictions]
        predictions = [r['vuln'] for r in vulnerability_predictions]
        
        print("Vulnerability predictions:", predictions[:10], "..." if len(predictions) > 10 else "")
        
        # Evaluate with different normalization approaches (following original pattern)
        try:
            # Import normalization functions from vulnerability_evaluation module
            from vuln_evaluation import normalize_vulnerability_basic, normalize_vulnerability_conservative, normalize_vulnerability_strict
            
            # Use normalization functions with vulnerability-specific evaluation
            results = evaluate_and_save_vulnerability(normalize_vulnerability_basic, predictions, DATASET_FILE, exp_name)
            results_v1 = evaluate_and_save_vulnerability(normalize_vulnerability_conservative, predictions, DATASET_FILE, f"{exp_name}_conservative")
            results_v2 = evaluate_and_save_vulnerability(normalize_vulnerability_strict, predictions, DATASET_FILE, f"{exp_name}_strict")
            print("Results:", results)
        except Exception as e:
            print(f"evaluate_and_save_vulnerability function failed: {e}")
            # Fallback evaluation
            from collections import Counter
            accuracy = sum(1 for p, g in zip(predictions, ground_truth) if p == g) / len(predictions)
            print(f"Fallback Accuracy: {accuracy:.4f}")
            print(f"Prediction distribution: {Counter(predictions)}")
            print(f"Ground truth distribution: {Counter(ground_truth)}")
        
        # Print final energy consumption summary
        print(f"\n=== FINAL ENERGY CONSUMPTION SUMMARY ===")
        print(f"Total emissions across all sessions: {energy_data['total_emissions']:.6f} kg CO2")
        print(f"Number of sessions: {energy_data['sessions']}")
        print(f"Total samples processed: {len(vulnerability_predictions)}")
        print(f"Average emissions per sample: {energy_data['total_emissions']/len(vulnerability_predictions):.8f} kg CO2")
        
        print("Vulnerability detection completed successfully!")
        
    finally:
    #     # Stop ollama server if we started it (following original pattern)
    #     if ollama_started and proc:
    #         from ollama_utils import stop_ollama_server
    #         stop_ollama_server(proc)
            print("Ollama server doesn't need to stop as this is not started here.")

if __name__ == "__main__":
    main()