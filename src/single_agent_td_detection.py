#!/usr/bin/env python3
"""
Run TD detection experiment using a single agent.

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


def run_inference_with_emissions_td_detection_agent(code_snippets, llm_config, sys_prompt, task_prompt, exp_name, result_dir):
    td_results = []
    tracker = OfflineEmissionsTracker(project_name=exp_name, output_dir=result_dir, country_iso_code="CAN", save_to_file=True)
    tracker.start()
    try:
        td_detector_gen = create_agent(
            agent_type="assistant",
            name="td_detection_generator_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt,
            description="Analyze the code snippet in order to determine whether it contains a code smell.",
        )
        for i, code_snippet in enumerate(code_snippets):
            content = task_prompt + code_snippet
            #print(f"Processing code_snippet {i+1}/{len(code_snippets)}")
            res = td_detector_gen.generate_reply(messages=[{"content": content, "role": "user"}])
            if res is not None and "content" in res:
                td_results.append(res["content"].strip())
                #print(f"[Info] Processed code_snippet {i+1}: {res['content'].strip()}")
            else:
                td_results.append("NONE")
                print(f"[Warning] Skipped code_snippet {i} — no response or invalid format.")
    finally:
        emissions = tracker.stop()
    print(f"Emissions: {emissions} kg CO2")
    return td_results


def main():
    parser = argparse.ArgumentParser(description="Run single-agent TD detection experiment")
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
    if args.design and args.design.upper().startswith("SA-"):
        DESIGN = args.design.capitalize()
    else:
        DESIGN = f"SA-{shot}"

    project_name = f"{TASK}_{DESIGN}"
    model_name = llm_config["config_list"][0]["model"]
    model = llm_config["config_list"][0]["model"].replace(":", "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_name = f"{project_name}_{model}_{timestamp}"

    input_file_path = os.path.join(DATA_DIR, args.input)
    ground_truth_file_path = os.path.join(DATA_DIR, args.gt)

    task_prompt = config.TASK_PROMPT_TD_DETECTION
    if shot == "zero":
        sys_prompt_generator = config.SYS_MSG_TD_DETECTION_GENERATOR_ZERO_SHOT
    else:
        sys_prompt_generator = config.SYS_MSG_TD_DETECTION_GENERATOR_FEW_SHOT

    code_snippets = get_code_snippets(input_file_path)

    proc = start_ollama_server()
    time.sleep(5)
    try:
        td_results = run_inference_with_emissions_td_detection_agent(code_snippets, llm_config, sys_prompt_generator, task_prompt, exp_name, RESULT_DIR)
        save_td_labels(td_results, llm_config, DESIGN, RESULT_DIR)
    finally:
        stop_ollama_server(proc)

    # Load ground truth and evaluate
    gt = get_td_ground_truth(ground_truth_file_path)
    results = evaluate_and_save_td(normalize_td_label, gt, td_results, exp_name)
    #print("Evaluation results:", results)


if __name__ == "__main__":
    main()
