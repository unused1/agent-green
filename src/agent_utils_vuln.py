import os
import json
import time
import config
from datetime import datetime
from autogen import AssistantAgent, ConversableAgent
from codecarbon import OfflineEmissionsTracker
from vuln_evaluation import evaluate_and_save_vulnerability, normalize_vulnerability_basic

# --- Configuration ---
llm_config = config.LLM_CONFIG
task = config.VULNERABILITY_TASK_PROMPT
sys_prompt_few = config.SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT
sys_prompt_zero = config.SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT

DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
os.makedirs(RESULT_DIR, exist_ok=True)

DESIGN = "SA-zero"   # or "SA-few"
model = llm_config["config_list"][0]["model"].replace(":", "-")
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exp_name = f"{DESIGN}_{model}_{timestamp}"


# --- Agent Creation ---
def create_vulnerability_agent(llm_config, sys_prompt):
    return AssistantAgent(
        name="vulnerability_detector",
        system_message=sys_prompt,
        description="Analyze code functions to detect vulnerabilities.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )


# --- Dataset Loading ---
def load_dataset(file_path):
    samples = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if "func" in data and "target" in data:
                    samples.append(data)
            except json.JSONDecodeError:
                continue
    return samples


# --- Inference with Emissions ---
def run_inference_with_emissions(samples, llm_config, sys_prompt, task, exp_name, result_dir):
    results = []
    tracker = OfflineEmissionsTracker(
        project_name=exp_name,
        output_dir=result_dir,
        country_iso_code="CAN",   # reproducibility
        save_to_file=True
    )
    tracker.start()

    try:
        agent = create_vulnerability_agent(llm_config, sys_prompt)
        for i, sample in enumerate(samples):
            print(f"Processing sample {i+1}/{len(samples)} (idx: {sample.get('idx')})")

            content = task.format(func=sample["func"])
            res = agent.generate_reply(messages=[{"content": content, "role": "user"}])

            result = {
                "idx": sample.get("idx"),
                "project": sample.get("project"),
                "commit_id": sample.get("commit_id"),
                "project_url": sample.get("project_url"),
                "commit_url": sample.get("commit_url"),
                "commit_message": sample.get("commit_message"),
                "ground_truth": sample.get("target"),
                "cwe": sample.get("cwe"),
                "cve": sample.get("cve"),
                "cve_desc": sample.get("cve_desc"),
            }

            if res is not None and "content" in res:
                response_text = res["content"].strip().lower()
                if any(k in response_text for k in ["yes", "vulnerable", "security risk", "exploit"]):
                    result["vuln"] = 1
                else:
                    result["vuln"] = 0
                result["reasoning"] = res["content"].strip()
            else:
                result["vuln"] = 0
                result["reasoning"] = "No response"

            results.append(result)
    finally:
        emissions = tracker.stop()
        print(f"Emissions this run: {emissions:.6f} kg CO2")

    # Save results once
    results_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
    with open(results_file, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    print(f"Results saved to: {results_file}")
    return results

# --- Generic Agent Creation ---
def create_agent(agent_type, name, llm_config=None, sys_prompt=None, description=None):
    if agent_type == "assistant":
        return AssistantAgent(
            name=name,
            system_message=sys_prompt,
            description=description,
            llm_config=llm_config,
            human_input_mode="NEVER",
        )
    elif agent_type == "conversable":
        return ConversableAgent(
            name=name,
            system_message=sys_prompt,
            description=description,
            llm_config=llm_config,
            human_input_mode="TERMINATE",
        )
    elif agent_type == "code_executor":
        try:
            executor = LocalCommandLineCodeExecutor(
                timeout=10,
                work_dir=Path(config.WORK_DIR)
            )
            return ConversableAgent(
                name=name,
                description=description,
                code_execution_config={"executor": executor},
                human_input_mode="NEVER",
                llm_config=False,
            )
        except Exception as e:
            print(f"Warning: Could not create code executor agent: {e}")
            # Return a basic conversable agent as fallback
            return ConversableAgent(
                name=name,
                description=description,
                human_input_mode="NEVER",
                llm_config=False,
            )
    else:
        raise ValueError("Unknown agent type.")

# --- Main Execution ---
def main():
    print("Loading dataset...")
    samples = load_dataset(DATASET_FILE)
    print(f"Loaded {len(samples)} samples")

    sys_prompt = sys_prompt_few if DESIGN == "SA-few" else sys_prompt_zero
    results = run_inference_with_emissions(samples, llm_config, sys_prompt, task, exp_name, RESULT_DIR)

    predictions = [r["vuln"] for r in results]
    ground_truth = [r["ground_truth"] for r in results]

    try:
        eval_results = evaluate_and_save_vulnerability(
            normalize_vulnerability_basic, predictions, DATASET_FILE, exp_name
        )
        print("Evaluation Results:", eval_results)
    except Exception as e:
        print("Evaluation failed:", e)
        from collections import Counter
        acc = sum(1 for p, g in zip(predictions, ground_truth) if p == g) / len(predictions)
        print(f"Fallback Accuracy: {acc:.4f}")
        print("Prediction dist:", Counter(predictions))
        print("Ground truth dist:", Counter(ground_truth))


if __name__ == "__main__":
    main()
