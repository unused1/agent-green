#!/usr/bin/env python3
"""Non-agentic Log Analysis runner

This script runs session-based log analysis (anomaly detection) by
calling the configured LLM via `ask_ollama`. It supports `--shot` to
select zero/few-shot system prompts. TASK is hard-coded to "log-analysis"
and DESIGN defaults to `NA-{shot}` unless an explicit prefixed design is given.
"""
import os
import time
import json
import argparse
from datetime import datetime
import config
from codecarbon import OfflineEmissionsTracker
from log_utils import (
    read_log_sessions,
    save_log_analysis_results,
    normalize_log_analysis_result,
    get_log_analysis_gt,
)
from ollama_utils import ask_ollama, start_ollama_server, stop_ollama_server, start_ollama_server_log
from evaluation import evaluate_and_save_log_analysis
from resume_utils import ExperimentResume


def run_inference_with_emissions_log_analysis(log_sessions, model_name, sys_prompt, task_prompt, exp_name, result_dir):
    """Run non-agentic inference over sessions while recording emissions.

    Returns a list of dicts with keys: block_id, raw_output
    """
    log_anomaly_results = []
    tracker = OfflineEmissionsTracker(project_name=exp_name, output_dir=result_dir, country_iso_code="CAN", save_to_file=True)
    tracker.start()
    try:
        for i, session in enumerate(log_sessions):
            blk_id = session.get("block_id")
            content = session.get("content")
            print(f"Processing {blk_id} ({i+1}/{len(log_sessions)})")
            prompt = sys_prompt + content
            response = ask_ollama(model_name, prompt)
            #print(f"Response: {response}")
            if response:
                log_anomaly_results.append({
                    "block_id": blk_id,
                    "raw_output": response,
                })
            else:
                print(f"[Warning] Skipped log session {i+1} — no response or invalid format.")
    finally:
        emissions = tracker.stop()
    print(f"Emissions: {emissions} kg CO2")
    return log_anomaly_results


def parse_args():
    p = argparse.ArgumentParser(description="Non-agentic log analysis runner")
    p.add_argument("--input", default="HDFS_385_sampled_sessions", help="Input sessions directory name (in config.DATA_DIR)")
    p.add_argument("--gt", default="HDFS_anomaly_label_385_session_sampled.csv", help="Ground-truth file name (in config.DATA_DIR)")
    p.add_argument("--result-dir", default=config.RESULT_DIR, help="Directory to store results")
    p.add_argument("--design", default=None, help="Experiment design name (prefixes allowed: NA-, SA-, DA-, MA-). If omitted, NA-{shot} will be used.")
    p.add_argument("--shot", default="few", choices=["zero", "few"], help="zero or few shot prompt selection")
    return p.parse_args()


def main():
    args = parse_args()
    TASK = "log-analysis"

    shot = args.shot.lower()
    if shot not in ("zero", "few"):
        raise SystemExit("--shot must be 'zero' or 'few'")

    # Select prompts based on shot
    if shot == "zero":
        sys_prompt = config.SYS_MSG_SINGLE_LOG_ANALYSIS_ZERO_SHOT
    else:
        sys_prompt = config.SYS_MSG_SINGLE_LOG_ANALYSIS_FEW_SHOT

    llm_config = config.LLM_CONFIG
    DATA_DIR = config.DATA_DIR
    RESULT_DIR = args.result_dir
    os.makedirs(RESULT_DIR, exist_ok=True)

    # Determine DESIGN with NA- prefix by default for non-agentic runs unless explicitly provided
    design = args.design
    if design is None:
        DESIGN = f"NA-{shot}"
    else:
        if any(design.startswith(p) for p in ("NA-", "SA-", "DA-", "MA-")):
            DESIGN = design
        else:
            DESIGN = design

    project_name = f"{TASK}_{DESIGN}"
    model_name = llm_config["config_list"][0]["model"]
    model = model_name.replace(":", "-").replace("/", "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_name = f"{project_name}_{model}_{timestamp}"

    input_dir_path = os.path.join(DATA_DIR, args.input)
    ground_truth_file_path = os.path.join(DATA_DIR, args.gt)

    # Read inputs
    log_sessions = read_log_sessions(input_dir_path)

    # Initialize resume helper (use project_name which includes TASK prefix for correct file pattern matching)
    resume = ExperimentResume(RESULT_DIR, project_name, model, exp_name)
    exp_name, detailed_file, energy_file, skip_next_sample = resume.initialize()

    # Load existing results
    existing_results = resume.load_results(detailed_file)
    energy_data = resume.load_energy(energy_file)

    # Filter remaining sessions
    remaining_sessions = resume.filter_remaining_samples(log_sessions, existing_results, id_field='block_id')

    if not remaining_sessions:
        print("[INFO] All sessions already processed. Loading results for evaluation.")
        all_results = []
        with open(detailed_file, 'r') as f:
            for line in f:
                if line.strip():
                    all_results.append(json.loads(line.strip()))
        normalized_results = [{"block_id": r["block_id"], "normalized": r.get("normalized", "0")} for r in all_results]
        gt = get_log_analysis_gt(ground_truth_file_path)
        evaluate_and_save_log_analysis(gt, normalized_results, exp_name, RESULT_DIR)
        return

    # Handle skip if requested
    if skip_next_sample and remaining_sessions:
        skip_session = remaining_sessions[0]
        print(f"[SKIP] Skipping session {skip_session['block_id']} and marking as FAILED")
        failed_result = {
            "block_id": skip_session["block_id"],
            "raw_output": "SKIPPED",
            "normalized": "0",
            "error": "USER_SKIP",
            "timestamp": datetime.now().isoformat()
        }
        with open(detailed_file, 'a') as f:
            f.write(json.dumps(failed_result) + '\n')
        remaining_sessions = remaining_sessions[1:]

    # Start Ollama server, run inference, stop server
    proc = start_ollama_server()
    time.sleep(5)

    tracker = OfflineEmissionsTracker(project_name=exp_name, output_dir=RESULT_DIR, country_iso_code="CAN", save_to_file=True)
    tracker.start()

    try:
        for i, session in enumerate(remaining_sessions):
            blk_id = session.get("block_id")
            log_content = session.get("content")
            print(f"Processing {blk_id} ({i+1}/{len(remaining_sessions)})")
            prompt = sys_prompt + log_content

            try:
                response = ask_ollama(model_name, prompt)
                if response:
                    raw_output = response
                else:
                    raw_output = "NONE"
                    print(f"[Warning] Skipped log session {i+1} — no response or invalid format.")
            except Exception as e:
                print(f"[Error] Failed to process {blk_id}: {e}")
                raw_output = f"ERROR: {str(e)}"

            # Normalize and save result immediately
            normalized = normalize_log_analysis_result(raw_output)
            result = {
                "block_id": blk_id,
                "raw_output": raw_output,
                "normalized": normalized,
                "timestamp": datetime.now().isoformat()
            }

            # Append to detailed file
            with open(detailed_file, 'a') as f:
                f.write(json.dumps(result) + '\n')

    except Exception as e:
        print(f"[Error] Inference failed: {e}")
        raise
    finally:
        emissions = tracker.stop()
        print(f"Emissions: {emissions} kg CO2")
        resume.save_energy(energy_data, energy_file, emissions, len(remaining_sessions))
        stop_ollama_server(proc)

    # Load all results for evaluation
    all_results = []
    with open(detailed_file, 'r') as f:
        for line in f:
            if line.strip():
                all_results.append(json.loads(line.strip()))

    normalized_results = [{"block_id": r["block_id"], "normalized": r.get("normalized", "0")} for r in all_results]

    # Load ground truth and evaluate
    gt = get_log_analysis_gt(ground_truth_file_path)
    evaluate_and_save_log_analysis(gt, normalized_results, exp_name, RESULT_DIR)


if __name__ == "__main__":
    main()
