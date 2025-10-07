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
DATASET_FILE = config.HUMANEVAL_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

DESIGN = "DA-code-gen"
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

print(f"Experiment: {exp_name}")
print(f"Dataset: {DATASET_FILE}")

# --- Agent Creation ---
def create_programmer_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="programmer",
        system_message=sys_prompt,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

def create_critic_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="critic",
        system_message=sys_prompt,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

# --- Data Reading ---
def read_code_generation_data(dataset_path):
    code_problems = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            code_problems.append(json.loads(line.strip()))
    return code_problems

# --- Code Extraction ---
def extract_code_from_response(response_text):
    """Extract code from <ANS></ANS> tags"""
    import re
    
    if not response_text:
        return ""
    
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
    response_text = response_text.strip()
    
    ans_pattern = r'<ANS>(.*?)</ANS>'
    matches = re.findall(ans_pattern, response_text, re.DOTALL | re.IGNORECASE)
    
    if matches:
        code = matches[0].strip().strip('`').strip()
        if code.startswith('python\n'):
            code = code[7:]
        elif code.startswith('python '):
            code = code[7:]
        return code
    
    ans_start = re.search(r'<ANS>', response_text, re.IGNORECASE)
    if ans_start:
        code = response_text[ans_start.end():]
        ans_end = re.search(r'</ANS>', code, re.IGNORECASE)
        if ans_end:
            code = code[:ans_end.start()]
        code = code.strip().strip('`').strip()
        if code.startswith('python\n'):
            code = code[7:]
        elif code.startswith('python '):
            code = code[7:]
        return code
    
    return ""

# --- Dual-Agent Inference ---
def run_inference_with_emissions(code_samples, llm_config, sys_msg_programmer, sys_msg_reviewer, exp_name, result_dir):
    detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    summary_file = os.path.join(result_dir, f"{exp_name}_summary.json")
    
    if os.path.exists(detailed_file):
        os.remove(detailed_file)
    
    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        country_iso_code="CAN",
        save_to_file=True
    )
    tracker.start()
    
    stats = {
        'total_samples': len(code_samples),
        'successful_extractions': 0,
        'failed_extractions': 0,
        'skipped_revision': 0,
        'full_pipeline': 0
    }
    
    try:
        programmer = create_programmer_agent(llm_config, sys_msg_programmer)
        reviewer = create_critic_agent(llm_config, sys_msg_reviewer)
        
        for i, sample in enumerate(code_samples):
            task_id = sample.get('task_id', f'sample_{i}')
            print(f"\n{'='*60}")
            print(f"Processing {i+1}/{len(code_samples)}: {task_id}")
            print(f"{'='*60}")
            
            problem_prompt = sample.get('prompt', '')
            
            # === TURN 1: Programmer generates initial code ===
            print("Turn 1: Programmer generating code...")
            gen_task = config.DUAL_AGENT_TASK_CODE_GENERATION.format(prompt=problem_prompt)
            res1 = programmer.generate_reply(messages=[{"content": gen_task, "role": "user"}])
            programmer_response = res1.get("content", "") if res1 else ""
            initial_code = extract_code_from_response(programmer_response)
            print(f"  Generated: {len(initial_code)} chars")
            
            # === TURN 2: Reviewer checks code ===
            print("Turn 2: Reviewer checking...")
            review_task = config.DUAL_AGENT_TASK_CODE_REVIEW.format(generated_code=initial_code)
            res2 = reviewer.generate_reply(messages=[{"content": review_task, "role": "user"}])
            review_feedback = res2.get("content", "") if res2 else ""
            print(f"  Feedback: {review_feedback[:100]}")
            
            # === SKIP LOGIC ===
            review_upper = review_feedback.upper()
            code_approved = ("CORRECT" in review_upper or len(review_feedback.strip()) < 20)
            
            if code_approved:
                print("  ✓ Code approved - skipping Turn 3")
                final_code = initial_code
                revision_response = "APPROVED - Skipped revision"
                stats['skipped_revision'] += 1
            else:
                # === TURN 3: Programmer revises ===
                print("Turn 3: Programmer revising...")
                revision_task = config.DUAL_AGENT_TASK_CODE_REVISION.format(
                    initial_code=initial_code,
                    feedback=review_feedback,
                    prompt=problem_prompt
                )
                res3 = programmer.generate_reply(messages=[{"content": revision_task, "role": "user"}])
                revision_response = res3.get("content", "") if res3 else ""
                final_code = extract_code_from_response(revision_response)
                stats['full_pipeline'] += 1
                print(f"  Revised: {len(final_code)} chars")
            
            # === Validate ===
            if final_code and 'def' in final_code:
                stats['successful_extractions'] += 1
                print(f"  ✓ Valid code extracted")
            else:
                stats['failed_extractions'] += 1
                print(f"  ✗ No valid function definition")
            
            # === Save ===
            result = {
                'task_id': task_id,
                'prompt': problem_prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', ''),
                'generated_solution': final_code,
                'conversation': {
                    'programmer_response': programmer_response,
                    'review_feedback': review_feedback,
                    'revision_response': revision_response
                },
                'metadata': {
                    'revision_skipped': code_approved,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            with open(detailed_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result) + '\n')
            
            if (i + 1) % 10 == 0:
                print(f"\n✓ Progress: {i + 1}/{len(code_samples)} | Success: {stats['successful_extractions']}")
    
    finally:
        emissions = tracker.stop()
        stats['emissions_kg_co2'] = emissions
        
        print(f"\n{'='*60}")
        print("DUAL-AGENT GENERATION COMPLETED")
        print(f"{'='*60}")
        print(f"Total: {stats['total_samples']}")
        print(f"Success: {stats['successful_extractions']} ({stats['successful_extractions']/stats['total_samples']*100:.1f}%)")
        print(f"Skipped Turn 3: {stats['skipped_revision']}")
        print(f"Emissions: {emissions:.6f} kg CO2")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
    
    return detailed_file

# --- Main ---
def main():
    print("\n" + "="*60)
    print("DUAL-AGENT CODE GENERATION")
    print("="*60)
    
    code_samples = read_code_generation_data(DATASET_FILE)
    
    detailed_file = run_inference_with_emissions(
        code_samples,
        llm_config,
        config.SYS_MSG_PROGRAMMER,
        config.SYS_MSG_CODE_REVIEWER,
        exp_name,
        RESULT_DIR
    )
    
    print(f"\nResults saved to: {detailed_file}")
    
    # Evaluate
    print("\n" + "="*60)
    print("STARTING EVALUATION")
    print("="*60)
    
    try:
        eval_result = subprocess.run(
            ["python", "src/evaluate_code_generation.py", detailed_file],
            capture_output=True,
            text=True,
            timeout=600
        )
        print(eval_result.stdout)
    except Exception as e:
        print(f"Evaluation failed: {e}")

if __name__ == "__main__":
    main()
