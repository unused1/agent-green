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

DESIGN = "MA-code-gen"
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"

print(f"Experiment: {exp_name}")
print(f"Dataset: {DATASET_FILE}")
print(f"Results will be saved to: {RESULT_DIR}")


# --- Agent Creation ---
def create_requirements_analyst(llm_config, sys_prompt):
    return AssistantAgent(
        name="requirements_analyst",
        system_message=sys_prompt,
        description="Analyze requirements and identify challenges.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

def create_programmer_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="programmer",
        system_message=sys_prompt,
        description="Implement code solutions.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

def create_moderator_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="moderator",
        system_message=sys_prompt,
        description="Provide neutral summaries.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

def create_review_board_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="review_board",
        system_message=sys_prompt,
        description="Make final assessments.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )


# --- Data Reading ---
def read_code_generation_data(dataset_path):
    """Read code generation data from JSONL file"""
    code_problems = []
    print(f"\nReading dataset from: {dataset_path}")
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                code_problems.append(data)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipped malformed line: {e}")
                continue
    
    print(f"Loaded {len(code_problems)} code samples")
    return code_problems


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
def run_inference_with_emissions(code_samples, llm_config, exp_name, result_dir):
    """Run multi-agent code generation with proper skip optimization"""
    
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
        'skipped_review': 0,
        'full_pipeline': 0
    }
    
    try:
        analyst = create_requirements_analyst(llm_config, config.SYS_MSG_REQUIREMENTS_ANALYST)
        programmer = create_programmer_agent(llm_config, config.SYS_MSG_PROGRAMMER_MA)
        moderator = create_moderator_agent(llm_config, config.SYS_MSG_MODERATOR_CODE)
        review_board = create_review_board_agent(llm_config, config.SYS_MSG_REVIEW_BOARD_CODE)
        
        for i, sample in enumerate(code_samples):
            task_id = sample.get('task_id', f'sample_{i}')
            print(f"\n{'='*60}")
            print(f"Processing {i+1}/{len(code_samples)}: {task_id}")
            print(f"{'='*60}")
            
            problem_prompt = sample.get('prompt', '')
            
            # === TURN 1: Requirements Analyst ===
            print("Turn 1: Requirements Analyst analyzing...")
            analyst_task = config.MULTI_AGENT_TASK_REQUIREMENTS_ANALYST.format(prompt=problem_prompt)
            res1 = analyst.generate_reply(messages=[{"content": analyst_task, "role": "user"}])
            analyst_findings = res1.get("content", "") if res1 else ""
            print(f"  Analyst findings: {len(analyst_findings)} chars")
            
            # === TURN 2: Programmer Implementation ===
            print("Turn 2: Programmer implementing...")
            programmer_task = config.MULTI_AGENT_TASK_PROGRAMMER.format(
                analyst_findings=analyst_findings,
                prompt=problem_prompt
            )
            res2 = programmer.generate_reply(messages=[{"content": programmer_task, "role": "user"}])
            programmer_response = res2.get("content", "") if res2 else ""
            initial_code = extract_code_from_response(programmer_response)
            print(f"  Programmer response: {len(programmer_response)} chars")
            
            # === TURN 3: Moderator Review ===
            print("Turn 3: Moderator reviewing...")
            moderator_task = config.MULTI_AGENT_TASK_MODERATOR_CODE.format(
                analyst_findings=analyst_findings,
                programmer_response=programmer_response,
                prompt=problem_prompt
            )
            res3 = moderator.generate_reply(messages=[{"content": moderator_task, "role": "user"}])
            moderator_summary = res3.get("content", "") if res3 else ""
            print(f"  Moderator summary: {len(moderator_summary)} chars")
            
            # === SKIP LOGIC: Check if revision is needed ===
            moderator_upper = moderator_summary.upper()
            code_approved = ("CODE LOOKS CORRECT" in moderator_upper or 
                           "CORRECT" in moderator_upper or
                           len(moderator_summary.strip()) < 20)
            
            if code_approved:
                # Skip Turn 4 - use initial code
                print("  ✓ Code approved by moderator - skipping Turn 4")
                final_code = initial_code
                review_assessment = "APPROVED - Skipped review"
                stats['skipped_review'] += 1
            else:
                # === TURN 4: Review Board Revision ===
                print("Turn 4: Review Board revising...")
                review_task = config.MULTI_AGENT_TASK_REVIEW_BOARD_CODE.format(
                    moderator_summary=moderator_summary,
                    prompt=problem_prompt,
                    analyst_findings=analyst_findings,
                    programmer_response=programmer_response
                )
                res4 = review_board.generate_reply(messages=[{"content": review_task, "role": "user"}])
                review_assessment = res4.get("content", "") if res4 else ""
                final_code = extract_code_from_response(review_assessment)
                stats['full_pipeline'] += 1
                print(f"  Review assessment: {len(review_assessment)} chars")
            
            # === Validate Final Code ===
            if final_code and 'def' in final_code:
                stats['successful_extractions'] += 1
                print(f"  ✓ Code extracted: {len(final_code)} chars")
            else:
                stats['failed_extractions'] += 1
                print(f"  ✗ WARNING: No valid function definition found!")
            
            # === Save Result ===
            result = {
                'task_id': task_id,
                'prompt': problem_prompt,
                'entry_point': sample.get('entry_point', ''),
                'canonical_solution': sample.get('canonical_solution', ''),
                'test': sample.get('test', ''),
                'generated_solution': final_code,
                'conversation': {
                    'analyst_findings': analyst_findings,
                    'programmer_response': programmer_response,
                    'moderator_summary': moderator_summary,
                    'review_assessment': review_assessment
                },
                'metadata': {
                    'review_skipped': code_approved,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            with open(detailed_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result) + '\n')
            
            if (i + 1) % 10 == 0:
                print(f"\n✓ Progress: {i + 1}/{len(code_samples)} | Success: {stats['successful_extractions']}/{i+1} ({stats['successful_extractions']/(i+1)*100:.1f}%)")
                print(f"  Skipped: {stats['skipped_review']} | Full pipeline: {stats['full_pipeline']}")
    
    finally:
        emissions = tracker.stop()
        stats['emissions_kg_co2'] = emissions
        
        print(f"\n{'='*60}")
        print("MULTI-AGENT GENERATION COMPLETED")
        print(f"{'='*60}")
        print(f"Total: {stats['total_samples']}")
        print(f"Success: {stats['successful_extractions']} ({stats['successful_extractions']/stats['total_samples']*100:.1f}%)")
        print(f"Skipped Turn 4: {stats['skipped_review']}")
        print(f"Full pipeline: {stats['full_pipeline']}")
        print(f"Emissions: {emissions:.6f} kg CO2")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
    
    return detailed_file

# --- Main Execution ---
def main():
    print("\n" + "="*60)
    print("MULTI-AGENT CODE GENERATION (OPTIMIZED)")
    print("="*60)
    
    code_samples = read_code_generation_data(DATASET_FILE)
    
    print(f"\nRunning {DESIGN} multi-agent code generation...")
    detailed_file = run_inference_with_emissions(
        code_samples,
        llm_config,
        exp_name,
        RESULT_DIR
    )
    
    print(f"\nResults saved to: {detailed_file}")
    
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
        
        if eval_result.returncode != 0:
            print("Evaluation encountered an error:")
            print(eval_result.stderr)
        else:
            print("\n" + "="*60)
            print("EVALUATION COMPLETED SUCCESSFULLY")
            print("="*60)
    
    except subprocess.TimeoutExpired:
        print("Evaluation timed out after 10 minutes")
    except Exception as e:
        print(f"Failed to run evaluation: {e}")
        print(f"You can manually evaluate by running:")
        print(f"python evaluate_code_generation.py {detailed_file}")


if __name__ == "__main__":
    main()
