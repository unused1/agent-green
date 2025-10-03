import os
import json
import time
import config
from datetime import datetime
from autogen import AssistantAgent
from codecarbon import OfflineEmissionsTracker
from code_evaluation import evaluate_and_save_code_generation
import sys

# Configuration
llm_config = config.LLM_CONFIG
task = config.CODE_GENERATION_TASK_PROMPT
sys_prompt_few_shot_code_generator = config.SYS_MSG_CODE_GENERATOR_FEW_SHOT
sys_prompt_zero_shot_code_generator = config.SYS_MSG_CODE_GENERATOR_ZERO_SHOT

# Directories
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
    print("Usage: python script.py <design>")
    print("design: SA-zero or SA-few")
    sys.exit(1)

print(f"Running with design: {DESIGN}")

# Set up experiment naming
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
project_name = DESIGN.capitalize()
exp_name = f"{project_name}_{model}_{timestamp}"

def create_code_generator_agent(llm_config, sys_prompt):
    """Create the code generation agent"""
    return AssistantAgent(
        name="code_generator_agent",
        system_message=sys_prompt,
        description="Generate Python code solutions for programming problems.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

def load_humaneval_dataset(file_path):
    """Load the HumanEval dataset from JSONL file"""
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
                        'test': data.get('test', '')
                    }
                    samples.append(sample)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON line: {e}")
                continue
    
    return samples

def initialize_result_files(exp_name, result_dir):
    """Initialize result files for incremental saving"""
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")
    with open(csv_file, 'w') as f:
        f.write("task_id,prompt,generated_solution,canonical_solution,entry_point,test\n")
    
    energy_file = os.path.join(result_dir, f"{exp_name}_energy_tracking.json")
    
    return detailed_file, csv_file, energy_file

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
    with open(detailed_file, 'a') as f:
        f.write(json.dumps(result) + '\n')
    
    with open(csv_file, 'a') as f:
        def escape_csv_field(field):
            if field is None:
                return ""
            field_str = str(field)
            if ',' in field_str or '"' in field_str or '\n' in field_str:
                return '"' + field_str.replace('"', '""') + '"'
            return field_str
        
        row = [
            escape_csv_field(result['task_id']),
            escape_csv_field(result['prompt']),
            escape_csv_field(result['generated_solution']),
            escape_csv_field(result['canonical_solution']),
            escape_csv_field(result['entry_point']),
            escape_csv_field(result['test'])
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

def extract_code_from_response(response_text):
    """Extract Python code from model response"""
    if not response_text:
        return ""
    
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

def save_predictions(code_predictions, llm_config, design, result_dir):
    """Save code generation predictions"""
    predictions = [r['generated_solution'] for r in code_predictions]
    
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

def run_inference_with_emissions(code_samples, llm_config, sys_prompt, task, exp_name, result_dir):
    """Run code generation with emissions tracking and incremental saving"""
    
    # Initialize result files
    detailed_file, csv_file, energy_file = initialize_result_files(exp_name, result_dir)
    
    # Load existing results and energy data if any
    existing_results = load_existing_results(detailed_file)
    energy_data = load_existing_energy(energy_file)
    processed_task_ids = {r['task_id'] for r in existing_results}
    
    # Filter out already processed samples
    remaining_samples = [s for s in code_samples if s['task_id'] not in processed_task_ids]
    
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
        code_generator = create_code_generator_agent(llm_config, sys_prompt)
        
        for i, sample in enumerate(remaining_samples):
            print(f"Processing sample {i+1}/{len(remaining_samples)} (task_id: {sample['task_id']})")
            
            # Format the task prompt
            content = task.format(prompt=sample['prompt'])
            response = code_generator.generate_reply(messages=[{"content": content, "role": "user"}])
            
            # Store result
            result = {
                'task_id': sample['task_id'],
                'prompt': sample['prompt'],
                'entry_point': sample['entry_point'],
                'canonical_solution': sample['canonical_solution'],
                'test': sample['test']
            }
            
            # Extract generated code
            if response is not None and "content" in response:
                response_text = response["content"].strip()
                generated_code = extract_code_from_response(response_text)
                result['generated_solution'] = generated_code
            else:
                result['generated_solution'] = ""
                print(f"Warning: No response for task {sample['task_id']}")
            
            # Save result immediately
            append_result(result, detailed_file, csv_file)
            existing_results.append(result)
            
            # Save progress every 10 samples
            if (i + 1) % 10 == 0:
                print(f"Progress saved: {i + 1} samples processed")
                
    finally:
        # Stop current tracking session
        session_emissions = tracker.stop()
        session_end_time = datetime.now().isoformat()
        
        # Update energy data
        energy_data['total_emissions'] += session_emissions
        energy_data['sessions'] += 1
        energy_data['session_history'].append({
            'session': energy_data['sessions'],
            'start_time': session_start_time,
            'end_time': session_end_time,
            'samples_processed': len(remaining_samples),
            'session_emissions': session_emissions
        })
        
        save_energy_data(energy_data, energy_file)
        
        print(f"Current session emissions: {session_emissions:.6f} kg CO2")
        print(f"Total cumulative emissions: {energy_data['total_emissions']:.6f} kg CO2")
    
    print(f"Detailed results saved incrementally to: {detailed_file}")
    print(f"CSV results saved incrementally to: {csv_file}")
    print(f"Energy tracking saved to: {energy_file}")
    
    return existing_results, energy_data

# Load dataset
print("Loading HumanEval dataset...")
code_samples = load_humaneval_dataset(DATASET_FILE)
print(f"Loaded {len(code_samples)} code samples")

print(f"Dataset file: {DATASET_FILE}")
print(f"Total samples: {len(code_samples)}")
if code_samples:
    print(f"First task: {code_samples[0]['task_id']}")
    print(f"Last task: {code_samples[-1]['task_id']}")

def main():
    """Main execution function"""
    try:
        # Select system prompt based on design
        if DESIGN == "SA-few":
            sys_prompt = sys_prompt_few_shot_code_generator
        else:
            sys_prompt = sys_prompt_zero_shot_code_generator
            
        print(f"Running {DESIGN} code generation experiment...")
        
        # Run the experiment
        code_predictions, energy_data = run_inference_with_emissions(
            code_samples, 
            llm_config, 
            sys_prompt, 
            task, 
            exp_name, 
            RESULT_DIR
        )
        
        # Save predictions
        save_predictions(code_predictions, llm_config, DESIGN, RESULT_DIR)
        
        # Extract predictions for evaluation
        predictions = [r['generated_solution'] for r in code_predictions]
        
        print(f"Sample predictions: {[p[:40]+'...' if len(p) > 40 else p for p in predictions[:2]]}")
        
        # Run evaluation with different normalization methods
        try:
            from code_evaluation import normalize_code_basic, normalize_code_conservative, normalize_code_strict
            
            results = evaluate_and_save_code_generation(normalize_code_basic, predictions, DATASET_FILE, exp_name)
            results_v1 = evaluate_and_save_code_generation(normalize_code_conservative, predictions, DATASET_FILE, f"{exp_name}_conservative")
            results_v2 = evaluate_and_save_code_generation(normalize_code_strict, predictions, DATASET_FILE, f"{exp_name}_strict")
            
            print("Results:", results)
        except Exception as e:
            print(f"Evaluation failed: {e}")
            from collections import Counter
            non_empty_count = sum(1 for p in predictions if p.strip())
            print(f"Fallback success rate: {non_empty_count}/{len(predictions)} ({non_empty_count/len(predictions):.3f})")
        
        # Print final energy summary
        print(f"\n=== FINAL ENERGY CONSUMPTION SUMMARY ===")
        print(f"Total emissions across all sessions: {energy_data['total_emissions']:.6f} kg CO2")
        print(f"Number of sessions: {energy_data['sessions']}")
        print(f"Total samples processed: {len(code_predictions)}")
        print(f"Average emissions per sample: {energy_data['total_emissions']/len(code_predictions):.8f} kg CO2")
        
        print("Code generation experiment completed successfully!")
        
    except Exception as e:
        print(f"Experiment failed: {e}")
        raise

if __name__ == "__main__":
    main()