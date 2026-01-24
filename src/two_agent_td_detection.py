#!/usr/bin/env python3
"""
Run two-agent TD detection experiment:
 - creates a generator agent and a critic agent
 - generator proposes labels, critic reviews/corrects them
 - collects critic outputs, tracks emissions, saves labels and evaluates
"""
import os
import time
import argparse
from datetime import datetime

import config
from codecarbon import OfflineEmissionsTracker
from debt_utils import get_code_snippets, get_td_ground_truth, save_td_labels, normalize_td_label
from agent_utils import create_agent
from ollama_utils import start_ollama_server, stop_ollama_server
from evaluation import evaluate_and_save_td


def run_two_agent_inference_with_emissions_td_detection(code_snippets, llm_config, sys_prompt_detector, sys_prompt_critic, task_prompt, exp_name, result_dir):
    gen_td_results = []
    critic_td_results = []
    tracker = OfflineEmissionsTracker(project_name=exp_name, output_dir=result_dir, country_iso_code="CAN", save_to_file=True)
    tracker.start()
    try:
        td_detector_gen = create_agent(
            agent_type="assistant",
            name="td_detection_generator_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_detector,
            description="Analyze the code snippet in order to determine whether it contains a code smell.",
        )
        critic = create_agent(
            agent_type="assistant",
            name="td_detection_critic_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_critic,
        )

        for i, code_snippet in enumerate(code_snippets):
            content_detection = task_prompt + code_snippet
            res_gen = td_detector_gen.generate_reply(messages=[{"content": content_detection, "role": "user"}])
            if res_gen is not None and "content" in res_gen:
                gen_td_result = normalize_td_label(res_gen["content"].strip())
                gen_td_results.append(gen_td_result)
            else:
                gen_td_results.append("NONE")
                print(f"[Warning] Skipped code_snippet {i+1} — no response or invalid format.")

            content_critic = f"""
                Verify or correct the code smell label assigned to a Java code snippet by the td_detection_generator_agent.

                Code Snippet:
                {code_snippet}

                The proposed label produced by the td_detection_generator_agent was: {gen_td_result}
            """
            res_critic = critic.generate_reply(messages=[{"content": content_critic, "role": "user"}])
            if res_critic is not None and "content" in res_critic:
                critic_td_result = normalize_td_label(res_critic["content"].strip())
                critic_td_results.append(critic_td_result)
            else:
                critic_td_results.append("NONE")
                print(f"[Warning] Critic skipped code_snippet {i+1} — no response or invalid format.")
    finally:
        emissions = tracker.stop()
    print(f"Emissions: {emissions} kg CO2")
    return critic_td_results


def main():
    parser = argparse.ArgumentParser(description="Run two-agent TD detection experiment")
    parser.add_argument("--input", default=config.IN_FILE, help="Input file name in data dir")
    parser.add_argument("--gt", default=config.GT_FILE, help="Ground truth file name in data dir")
    parser.add_argument("--result-dir", default=config.RESULT_DIR, help="Directory to save results")
    parser.add_argument("--design", default=config.DESIGN, help="Design label (overrides config.DESIGN)")
    parser.add_argument("--shot", choices=["zero","few"], default="few", help="Use zero-shot or few-shot system prompt")
    args = parser.parse_args()

    llm_config = config.LLM_CONFIG
    DATA_DIR = config.DATA_DIR
    RESULT_DIR = args.result_dir
    os.makedirs(RESULT_DIR, exist_ok=True)

    TASK = "td-detection"
    shot = args.shot
    if args.design and args.design.upper().startswith("DA-"):
        DESIGN = args.design.capitalize()
    else:
        DESIGN = f"DA-{shot}"

    project_name = f"{TASK}_{DESIGN}"
    model_name = llm_config["config_list"][0]["model"]
    model = llm_config["config_list"][0]["model"].replace(":", "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_name = f"{project_name}_{model}_{timestamp}"

    input_file_path = os.path.join(DATA_DIR, args.input)
    ground_truth_file_path = os.path.join(DATA_DIR, args.gt)

    # Choose system prompts based on shot
    if shot == "zero":
        sys_prompt_generator = config.SYS_MSG_TD_DETECTION_GENERATOR_ZERO_SHOT
        sys_prompt_critic = config.SYS_MSG_TD_DETECTION_CRITIC_ZERO_SHOT
    else:
        sys_prompt_generator = config.SYS_MSG_TD_DETECTION_GENERATOR_FEW_SHOT
        sys_prompt_critic = config.SYS_MSG_TD_DETECTION_CRITIC_FEW_SHOT

    task_prompt = config.TASK_PROMPT_TD_DETECTION

    code_snippets = get_code_snippets(input_file_path)

    proc = start_ollama_server()
    time.sleep(5)
    try:
        td_results = run_two_agent_inference_with_emissions_td_detection(code_snippets, llm_config, sys_prompt_generator, sys_prompt_critic, task_prompt, exp_name, RESULT_DIR)
        save_td_labels(td_results, llm_config, DESIGN, RESULT_DIR)
    finally:
        stop_ollama_server(proc)

    # Load ground truth and evaluate
    gt = get_td_ground_truth(ground_truth_file_path)
    results = evaluate_and_save_td(normalize_td_label, gt, td_results, exp_name)
    #print("Evaluation results:", results)

if __name__ == "__main__":
    main()
