import os
import json
import time
import config
from datetime import datetime
from autogen import AssistantAgent
from codecarbon import OfflineEmissionsTracker
#from codecarbon import EmissionsTracker
from vuln_evaluation import evaluate_and_save_vulnerability
from resume_utils import ExperimentResume
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


model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
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
# NOTE: Resume functionality now handled by ExperimentResume class from resume_utils

# --- Save Templates (following original pattern) ---
def save_templates(vulnerability_predictions, llm_config, design, result_dir):
    """Save vulnerability predictions in format similar to original save_templates function"""
    
    # Extract just the predictions for the simple save (like original)
    predictions = [r['vuln'] for r in vulnerability_predictions]
    
    # Save predictions in simple format (similar to original save_templates)
    model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
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

# NOTE: Energy tracking now handled by ExperimentResume class from resume_utils

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
            escape_csv_field(result['cve_desc']),
            escape_csv_field(result.get('error', ''))  # Add error field (empty if no error)
        ]
        f.write(','.join(row) + '\n')

# NOTE: Loading results now handled by ExperimentResume class from resume_utils

# --- With CodeCarbon Emissions Tracking (following original pattern) ---
def run_inference_with_emissions(code_samples, llm_config, sys_prompt_vulnerability_detector, task, exp_name, result_dir, design, model):
    """Run vulnerability detection with emissions tracking and incremental saving"""

    # Initialize resume helper
    resume = ExperimentResume(result_dir, design, model, exp_name)
    exp_name, detailed_file, energy_file, skip_next_sample = resume.initialize()

    # Setup CSV file (single-agent specific)
    csv_file = os.path.join(result_dir, f"{exp_name}_detailed_results.csv")
    if not os.path.exists(csv_file):
        with open(csv_file, 'w') as f:
            f.write("idx,project,commit_id,project_url,commit_url,commit_message,ground_truth,vuln,reasoning,cwe,cve,cve_desc,error\n")

    # Load existing results and energy data if any (for resuming interrupted runs)
    existing_results = resume.load_results(detailed_file)
    energy_data = resume.load_energy(energy_file)

    # Filter out already processed samples
    remaining_samples = resume.filter_remaining_samples(code_samples, existing_results, id_field='idx')

    # If user chose to skip the next sample, mark it as failed and remove from queue
    if skip_next_sample and remaining_samples:
        skip_sample = remaining_samples[0]
        print(f"[SKIP] Marking sample {skip_sample['idx']} as FAILED and skipping")

        # Create failed result using resume utility
        failed_result = resume.create_skip_result(skip_sample, id_field='idx')

        # Add vulnerability-specific fields
        failed_result.update({
            'vuln': 0,
            'reasoning': 'SKIPPED: Sample manually skipped by user (likely problematic/stuck)',
            'error': 'skipped'
        })

        # Save the skipped sample
        append_result(failed_result, detailed_file, csv_file)
        existing_results.append(failed_result)

        # Remove from remaining samples
        remaining_samples = remaining_samples[1:]
        print(f"[SKIP] Continuing with {len(remaining_samples)} remaining samples")
    
    if len(remaining_samples) < len(code_samples):
        print(f"Resuming from {len(existing_results)} existing results")
        print(f"Processing remaining {len(remaining_samples)} samples")
        if config.ENABLE_CODECARBON:
            print(f"Previous energy consumption: {energy_data['total_emissions']:.6f} kg CO2")
    
    # Start new emissions tracking session
    session_start_time = datetime.now().isoformat()

    # CodeCarbon energy tracking based on ENABLE_CODECARBON flag
    if not config.ENABLE_CODECARBON:
        print("[INFO] CodeCarbon disabled (set ENABLE_CODECARBON=true in .env to enable)")
        tracker = None
    else:
        # Use separate output directories based on reasoning mode AND experiment design
        # to avoid conflicts when running multiple experiments in parallel
        reasoning_suffix = "thinking" if config.ENABLE_REASONING else "baseline"
        codecarbon_dir = os.path.join(result_dir, f"codecarbon_{reasoning_suffix}_{design.lower()}")
        os.makedirs(codecarbon_dir, exist_ok=True)

        tracker = OfflineEmissionsTracker(
            project_name=f"{exp_name}_session_{energy_data['sessions'] + 1}",
            output_dir=codecarbon_dir,
            country_iso_code="CAN",
            save_to_file=True
        )
        tracker.start()
        print(f"[INFO] CodeCarbon output directory: {codecarbon_dir}")
    
    try:
        vulnerability_detector = create_vulnerability_detector_agent(llm_config, sys_prompt_vulnerability_detector)

        for i, sample in enumerate(remaining_samples):
            print(f"Processing sample {i+1}/{len(remaining_samples)} (idx: {sample['idx']})")
            print(f"[TIP] Press Ctrl+C to stop. You can resume later and skip problematic samples.")

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

            # Try to process with timeout handling
            try:
                # Use format to insert function code into prompt template
                content = task.format(func=sample['func'])
                res = vulnerability_detector.generate_reply(messages=[{"content": content, "role": "user"}])
            except TimeoutError as e:
                print(f"[TIMEOUT] Sample {sample['idx']} timed out after 5 minutes - marking as failed and continuing")
                result['vuln'] = 0  # Default to not vulnerable
                result['reasoning'] = f"TIMEOUT: Request timed out after 5 minutes. {str(e)}"
                result['error'] = 'timeout'
                # Append result and continue to next sample
                append_result(result, detailed_file, csv_file)
                existing_results.append(result)
                continue
            except Exception as e:
                print(f"[ERROR] Sample {sample['idx']} failed with error: {str(e)}")
                result['vuln'] = 0  # Default to not vulnerable
                result['reasoning'] = f"ERROR: {str(e)}"
                result['error'] = 'exception'
                # Append result and continue to next sample
                append_result(result, detailed_file, csv_file)
                existing_results.append(result)
                continue
            
            # Updated response parsing for YES/NO format
            if res is not None and "content" in res:
                response_text = res["content"].strip()
                response_lower = response_text.lower()

                # Parse YES/NO responses - check multiple formats
                # Format 1: "Final Answer: YES/NO" (from zero-shot system prompt)
                # Format 2: "(1) YES" or "(2) NO" (from task prompt)
                # Format 3: Keywords like "vulnerability detected"

                is_vulnerable = None  # Track if we found a clear answer

                # Check for explicit YES answers
                if any(pattern in response_lower for pattern in [
                    'final answer: yes',
                    'final answer: (1) yes',
                    '(1) yes',
                    'answer: yes',
                    'vulnerability detected'
                ]):
                    is_vulnerable = True

                # Check for explicit NO answers
                elif any(pattern in response_lower for pattern in [
                    'final answer: no',
                    'final answer: (2) no',
                    '(2) no',
                    'answer: no',
                    'no security vulnerability'
                ]):
                    is_vulnerable = False

                # If we found a clear answer, use it
                if is_vulnerable is not None:
                    result['vuln'] = 1 if is_vulnerable else 0
                    result['reasoning'] = response_text
                else:
                    # Fallback: look for vulnerability keywords (less reliable)
                    if any(keyword in response_lower for keyword in [
                        'is vulnerable',
                        'contains a vulnerability',
                        'security vulnerability exists',
                        'security risk',
                        'can be exploited'
                    ]):
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

    except KeyboardInterrupt:
        print(f"\n\n[INTERRUPTED] Experiment stopped by user (Ctrl+C)")
        print(f"[SAVED] Progress has been saved. {len(existing_results)} samples completed.")
        print(f"[RESUME] Run the script again and choose option 1 to continue, or option 2 to skip the problematic sample.")
        # Re-raise to ensure proper cleanup
        raise

    finally:
        # Stop current tracking session (if enabled)
        session_end_time = datetime.now().isoformat()

        if tracker is not None:
            session_emissions = tracker.stop()

            # Update energy tracking using resume utility
            resume.save_energy(energy_data, energy_file, session_emissions, len(remaining_samples))

            print(f"Current session emissions: {session_emissions:.6f} kg CO2")
            print(f"Total cumulative emissions: {energy_data['total_emissions']:.6f} kg CO2")
        else:
            print("[INFO] Energy tracking skipped (API-based inference)")
    
    print(f"Detailed results saved incrementally to: {detailed_file}")
    print(f"CSV results saved incrementally to: {csv_file}")
    if config.ENABLE_CODECARBON:
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
            RESULT_DIR,
            DESIGN,
            model
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
        
        # Print final energy consumption summary (if tracking was enabled)
        if config.ENABLE_CODECARBON:
            print(f"\n=== FINAL ENERGY CONSUMPTION SUMMARY ===")
            print(f"Total emissions across all sessions: {energy_data['total_emissions']:.6f} kg CO2")
            print(f"Number of sessions: {energy_data['sessions']}")
            print(f"Total samples processed: {len(vulnerability_predictions)}")
            print(f"Average emissions per sample: {energy_data['total_emissions']/len(vulnerability_predictions):.8f} kg CO2")
        else:
            print(f"\n[INFO] Energy tracking was disabled")
        
        print("Vulnerability detection completed successfully!")

    except KeyboardInterrupt:
        print("\n[EXIT] Experiment interrupted. Progress saved.")
        sys.exit(0)

    finally:
    #     # Stop ollama server if we started it (following original pattern)
    #     if ollama_started and proc:
    #         from ollama_utils import stop_ollama_server
    #         stop_ollama_server(proc)
            print("Ollama server doesn't need to stop as this is not started here.")

if __name__ == "__main__":
    main()