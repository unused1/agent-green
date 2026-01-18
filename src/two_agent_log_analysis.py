#!/usr/bin/env python3
"""
Run two-agent log analysis experiment:
 - creates a parser agent and an anomaly detector agent
 - parser preprocesses sessions of log messages, anamaly detector analyzes them
 - collects anomaly detector outputs, tracks emissions, saves results and evaluates
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
from agent_utils import create_agent
from ollama_utils import start_ollama_server, stop_ollama_server, start_ollama_server_log
from evaluation import evaluate_and_save_log_analysis
from resume_utils import ExperimentResume


def run_two_agent_inference_with_emissions_log_analysis(log_sessions, llm_config, sys_prompt_parser, sys_prompt_anomaly_detector, task_prompt, exp_name, result_dir):
    parser_results = []
    anomaly_detector_results = []
    tracker = OfflineEmissionsTracker(project_name=exp_name, output_dir=result_dir, country_iso_code="CAN", save_to_file=True)
    tracker.start()
    try:
        log_parser = create_agent(
            agent_type="assistant",
            name="log_parser_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_parser,
            #description=task_prompt,
        )
        anomaly_detector = create_agent(
            agent_type="assistant",
            name="log_anomaly_detector_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_anomaly_detector,
        )

        for i, session in enumerate(log_sessions):
            blk_id = session.get("block_id")
            log_content = session.get("content")
            print(f"\n--- Processing {blk_id} ({i+1}/{len(log_sessions)}) ---")
            content = "Extract only the message bodies by removing automatically generated headers (timestamp, log level, class, etc.) from the following log messages:" + log_content
            res_parser = log_parser.generate_reply(messages=[{"content": content, "role": "user"}])
            if res_parser is not None and "content" in res_parser:
                raw_output_parser = res_parser["content"].strip()
            else:
                raw_output_parser = "NONE"
                print(f"[Warning] Skipped parsing for log session {i+1} — no response or invalid format.")

            parser_results.append({
                "block_id": blk_id,
                "raw_output": raw_output_parser,
            })

            content_anomaly_detector = task_prompt + raw_output_parser
            res_anomaly_detector = anomaly_detector.generate_reply(messages=[{"content": content_anomaly_detector, "role": "user"}])
            if res_anomaly_detector is not None and "content" in res_anomaly_detector:
                raw_output_anomaly = res_anomaly_detector["content"].strip()
            else:
                raw_output_anomaly = "NONE"
                print(f"[Warning] Skipped anomaly detection for log session {i+1} — no response or invalid format.")
            
            anomaly_detector_results.append({
                "block_id": blk_id,
                "raw_output": raw_output_anomaly,
            })
    finally:
        emissions = tracker.stop()
    print(f"Emissions: {emissions} kg CO2")
    return anomaly_detector_results

def parse_args():
    p = argparse.ArgumentParser(description="Dual-agent log analysis runner")
    p.add_argument("--input", default="HDFS_385_sampled_sessions", help="Input sessions directory name (in config.DATA_DIR)")
    p.add_argument("--gt", default="HDFS_anomaly_label_385_session_sampled.csv", help="Ground-truth file name (in config.DATA_DIR)")
    p.add_argument("--result-dir", default=config.RESULT_DIR, help="Directory to store results")
    p.add_argument("--design", default=None, help="Experiment design name (prefixes allowed: NA-, SA-, DA-, MA-). If omitted, DA-{shot} will be used.")
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
        sys_prompt_parser = config.SYS_MSG_LOG_PREPROCESSOR_ZERO_SHOT
        sys_prompt_anomaly_detector = config.SYS_MSG_LOG_ANOMALY_DETECTOR_ZERO_SHOT
    else:
        sys_prompt_parser = config.SYS_MSG_LOG_PREPROCESSOR_FEW_SHOT
        sys_prompt_anomaly_detector = config.SYS_MSG_LOG_ANOMALY_DETECTOR_FEW_SHOT

    llm_config = config.LLM_CONFIG
    DATA_DIR = config.DATA_DIR
    RESULT_DIR = args.result_dir
    os.makedirs(RESULT_DIR, exist_ok=True)

    # Determine DESIGN with DA- prefix by default for dual-agent runs unless explicitly provided
    design = args.design
    if design is None:
        DESIGN = f"DA-{shot}"
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
        log_parser = create_agent(
            agent_type="assistant",
            name="log_parser_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_parser,
        )
        anomaly_detector = create_agent(
            agent_type="assistant",
            name="log_anomaly_detector_agent",
            llm_config=llm_config,
            sys_prompt=sys_prompt_anomaly_detector,
        )

        for i, session in enumerate(remaining_sessions):
            blk_id = session.get("block_id")
            log_content = session.get("content")
            print(f"\n--- Processing {blk_id} ({i+1}/{len(remaining_sessions)}) ---")

            try:
                # Parser agent
                content = "Extract only the message bodies by removing automatically generated headers (timestamp, log level, class, etc.) from the following log messages:" + log_content
                res_parser = log_parser.generate_reply(messages=[{"content": content, "role": "user"}])
                if res_parser is not None and "content" in res_parser:
                    raw_output_parser = res_parser["content"].strip()
                else:
                    raw_output_parser = "NONE"
                    print(f"[Warning] Skipped parsing for log session {i+1} — no response or invalid format.")

                # Anomaly detector agent
                content_anomaly_detector = config.TASK_PROMPT_LOG_ANALYSIS + raw_output_parser
                res_anomaly_detector = anomaly_detector.generate_reply(messages=[{"content": content_anomaly_detector, "role": "user"}])
                if res_anomaly_detector is not None and "content" in res_anomaly_detector:
                    raw_output_anomaly = res_anomaly_detector["content"].strip()
                else:
                    raw_output_anomaly = "NONE"
                    print(f"[Warning] Skipped anomaly detection for log session {i+1} — no response or invalid format.")
            except Exception as e:
                print(f"[Error] Failed to process {blk_id}: {e}")
                raw_output_anomaly = f"ERROR: {str(e)}"

            # Normalize and save result immediately
            normalized = normalize_log_analysis_result(raw_output_anomaly)
            result = {
                "block_id": blk_id,
                "raw_output": raw_output_anomaly,
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
