import json
import os
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from evaluate import load

os.environ["HF_ALLOW_CODE_EVAL"] = "1"


def extract_code_from_prediction(prediction):
    """Extract actual Python code from prediction"""
    import re
    
    if not prediction:
        return ""
    
    prediction = str(prediction).strip()
    
    # Remove <think> blocks entirely
    prediction = re.sub(r'<think>.*?</think>', '', prediction, flags=re.DOTALL)
    
    # Remove <ANS> tags but keep content
    prediction = prediction.replace("<ANS>", "").replace("</ANS>", "")
    
    # PRIORITY 1: Look for explicit code markers
    if "=== CODE START ===" in prediction and "=== CODE END ===" in prediction:
        start_idx = prediction.find("=== CODE START ===") + len("=== CODE START ===")
        end_idx = prediction.find("=== CODE END ===")
        code = prediction[start_idx:end_idx].strip()
        return code
    
    # PRIORITY 2: Extract from markdown code blocks (get LAST one for multi-turn)
    python_blocks = re.findall(r'```python\s*\n(.*?)\n```', prediction, re.DOTALL)
    if python_blocks:
        return python_blocks[-1].strip()  # Return LAST code block
    
    # Try generic code blocks
    generic_blocks = re.findall(r'```\s*\n(.*?)\n```', prediction, re.DOTALL)
    if generic_blocks:
        # Filter for blocks that contain 'def ' (actual code, not JSON)
        code_blocks = [block for block in generic_blocks if 'def ' in block]
        if code_blocks:
            return code_blocks[-1].strip()  # Return LAST code block
    
    # PRIORITY 3: Look for function definitions
    func_match = re.search(r'((?:from|import).*?\n)?def\s+\w+.*', prediction, re.DOTALL)
    if func_match:
        code = func_match.group(0).strip()
        # Remove trailing explanation text and stop markers
        for marker in ['\n\n#', '\nNote:', '\nExplanation:', '\n###', '\nThis ', 
                       '\nChallenge', '\nAPPROVED', '\nISSUES', '\n=== CODE END']:
            if marker in code:
                code = code[:code.index(marker)]
        return code.strip()
    
    # PRIORITY 4: If no function found, try to clean up and return
    lines = prediction.strip().split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip explanation lines
        if stripped.startswith(('To solve', 'The ', 'This ', '### ', '**', 'Here', 
                               'Challenge', 'APPROVED', 'ISSUES', '===')):
            if not in_code:
                continue
            else:
                break  # Stop at explanation after code
        
        # Start collecting at function/import
        if 'def ' in line or 'import ' in line or 'from ' in line:
            in_code = True
        
        if in_code:
            code_lines.append(line)
    
    return '\n'.join(code_lines).strip() if code_lines else prediction.strip()


def evaluate_code_generation(results_file, k=[1]):
    """Evaluate code generation results"""
    # Load the evaluation function
    code_eval = load("code_eval")
    
    # Read results file
    data = []
    with open(results_file, 'r') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    
    df = pd.DataFrame(data)
    
    # Handle different field names
    if 'test_cases' in df.columns:
        test_cases = df['test_cases'].tolist()
    elif 'test' in df.columns:
        test_cases = df['test'].tolist()
    else:
        raise ValueError(f"No test cases field found. Available: {df.columns.tolist()}")
    
    if 'prediction' in df.columns:
        prediction_field = 'prediction'
    elif 'generated_solution' in df.columns:
        prediction_field = 'generated_solution'
    else:
        raise ValueError(f"No prediction field found. Available: {df.columns.tolist()}")
    
    # Prepare candidates
    candidates = []
    df['cleaned_prediction'] = ""
    
    for index in range(len(df)):
        prediction = df[prediction_field].iloc[index]
        
        # Extract actual code
        cleaned_prediction = extract_code_from_prediction(prediction)
        
        # Store cleaned prediction
        df.loc[index, "cleaned_prediction"] = cleaned_prediction
        candidates.append([cleaned_prediction])
    
    # Compute pass@k
    print(f"Evaluating pass@{k}...")
    pass_at_k, results = code_eval.compute(references=test_cases, predictions=candidates, k=k)
    
    return pass_at_k, results, df

def copy_test_results_to_df(df, results):
    """Add test oracle results to dataframe"""
    df['test_oracle'] = ""
    
    for index in range(len(df)):
        result = results[index][0][1]['result']
        df.loc[index, "test_oracle"] = result
    
    return df

def save_evaluation_results(results_file, pass_at_k, df, model_name):
    """Save evaluation results as both JSON and TXT files"""
    results_dir = Path(results_file).parent
    
    total_samples = len(df)
    passed_samples = df['test_oracle'].apply(lambda x: x == 'passed').sum()
    failed_samples = total_samples - passed_samples
    pass_rate = (passed_samples / total_samples * 100) if total_samples > 0 else 0
    
    eval_data = {
        'model': model_name,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'results_file': str(results_file),
        'metrics': {
            'pass@1': float(pass_at_k.get('pass@1', 0)),
            'total_samples': int(total_samples),
            'passed_samples': int(passed_samples),
            'failed_samples': int(failed_samples),
            'pass_rate_percentage': float(pass_rate)
        },
        'per_sample_results': []
    }
    
    # Add per-sample results
    task_id_field = 'task_id' if 'task_id' in df.columns else 'idx'
    for index in range(len(df)):
        sample_data = {
            'task_id': df[task_id_field].iloc[index],
            'test_result': df['test_oracle'].iloc[index],
            'passed': df['test_oracle'].iloc[index] == 'passed'
        }
        eval_data['per_sample_results'].append(sample_data)
    
    # Save as JSON
    json_file = results_dir / f"{model_name}_evaluation.json"
    with open(json_file, 'w') as f:
        json.dump(eval_data, f, indent=2)
    print(f"JSON evaluation saved to: {json_file}")
    
    # Save as TXT
    txt_file = results_dir / f"{model_name}_evaluation.txt"
    with open(txt_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"CODE GENERATION EVALUATION RESULTS\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Model: {model_name}\n")
        f.write(f"Timestamp: {eval_data['timestamp']}\n")
        f.write(f"Results File: {results_file}\n\n")
        
        f.write("-"*80 + "\n")
        f.write("SUMMARY METRICS\n")
        f.write("-"*80 + "\n")
        f.write(f"Pass@1 Score: {eval_data['metrics']['pass@1']:.4f}\n")
        f.write(f"Total Samples: {eval_data['metrics']['total_samples']}\n")
        f.write(f"Passed Samples: {eval_data['metrics']['passed_samples']}\n")
        f.write(f"Failed Samples: {eval_data['metrics']['failed_samples']}\n")
        f.write(f"Pass Rate: {eval_data['metrics']['pass_rate_percentage']:.2f}%\n\n")
        
        f.write("-"*80 + "\n")
        f.write("PER-SAMPLE RESULTS\n")
        f.write("-"*80 + "\n\n")
        
        for sample in eval_data['per_sample_results']:
            status_symbol = "✓" if sample['passed'] else "✗"
            f.write(f"{status_symbol} {sample['task_id']}: {sample['test_result']}\n")
    
    print(f"TXT evaluation saved to: {txt_file}")
    
    return json_file, txt_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python evaluate_code_generation.py <results_file.jsonl>")
        sys.exit(1)
    
    results_file = sys.argv[1]
    
    if not os.path.exists(results_file):
        print(f"Error: Results file not found: {results_file}")
        sys.exit(1)
    
    # Extract model name from results file
    model_name = Path(results_file).stem
    
    k_values = [1]
    
    # Run evaluation
    print(f"Evaluating {results_file}...")
    pass_at_k, results, df = evaluate_code_generation(results_file, k=k_values)
    
    # Print results
    print(f"\nResults for {model_name}:")
    print(f"Pass@1: {pass_at_k['pass@1']:.4f}")
    
    # Add test oracle to dataframe
    df = copy_test_results_to_df(df, results)
    
    # Save evaluation results
    json_file, txt_file = save_evaluation_results(results_file, pass_at_k, df, model_name)
    
    # Also save detailed CSV with extracted code
    results_dir = Path(results_file).parent
    csv_file = results_dir / f"{model_name}_evaluated.csv"
    df.to_csv(csv_file, index=False)
    print(f"Detailed CSV saved to: {csv_file}")
    
    print("\n" + "="*80)
    print("EVALUATION COMPLETE")
    print("="*80)
