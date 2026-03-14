#!/usr/bin/env python3
"""
Re-run skipped samples from MA Vuln experiments with extended context.

This script re-runs samples that were skipped due to context overflow
to test if increased context length (e.g., 128K) allows them to complete.

Usage:
    python scripts/rerun_skipped_samples.py <experiment> [--dry-run]

Arguments:
    experiment: One of: few-instruct, few-think, zero-instruct, zero-think

Examples:
    # Dry run to see which samples would be re-run
    python scripts/rerun_skipped_samples.py few-instruct --dry-run

    # Actually re-run the skipped samples
    python scripts/rerun_skipped_samples.py few-instruct

Prerequisites:
    1. Start vLLM with extended context:
       MAX_MODEL_LEN=131072 ./scripts/deploy_nemotron_vllm.sh 8b

    2. Set environment variables:
       export MODEL_FAMILY=nemotron
       export ENABLE_REASONING=false  # or true for thinking mode
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Experiment configurations
EXPERIMENTS = {
    "few-instruct": {
        "prompting": "few_shot",
        "thinking": False,
        "result_dir": "results/rq2_cross_architecture/nemotron_8b_vuln_MA-few_instruct",
    },
    "few-think": {
        "prompting": "few_shot",
        "thinking": True,
        "result_dir": "results/rq2_cross_architecture/nemotron_8b_vuln_MA-few_think",
    },
    "zero-instruct": {
        "prompting": "zero_shot",
        "thinking": False,
        "result_dir": "results/rq2_cross_architecture/nemotron_8b_vuln_MA-zero_instruct",
    },
    "zero-think": {
        "prompting": "zero_shot",
        "thinking": True,
        "result_dir": "results/rq2_cross_architecture/nemotron_8b_vuln_MA-zero_think",
    },
}


def find_skipped_samples(result_dir: Path) -> list[dict]:
    """Find all skipped samples from the original experiment results."""
    # Find the detailed results file (not corrected)
    jsonl_files = list(result_dir.glob("*detailed_results.jsonl"))
    jsonl_files = [f for f in jsonl_files if "corrected" not in f.name]

    if not jsonl_files:
        raise FileNotFoundError(f"No detailed_results.jsonl found in {result_dir}")

    results_file = jsonl_files[0]
    print(f"Loading results from: {results_file.name}")

    skipped = []
    with open(results_file) as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                if record.get("skipped") == True:
                    skipped.append(record)

    return skipped


def load_dataset_samples(dataset_file: str, sample_ids: set) -> list[dict]:
    """Load only specified samples from the vulnerability dataset."""
    samples = []

    with open(dataset_file) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                idx = data.get("idx")
                if idx in sample_ids:
                    samples.append({
                        "idx": idx,
                        "project": data.get("project"),
                        "project_url": data.get("project_url"),
                        "commit_id": data.get("commit_id"),
                        "commit_url": data.get("commit_url"),
                        "commit_message": data.get("commit_message"),
                        "target": data.get("target"),
                        "func": data.get("func"),
                        "cwe": data.get("cwe"),
                        "cve": data.get("cve"),
                        "cve_desc": data.get("cve_desc"),
                    })
            except json.JSONDecodeError:
                continue

    return samples


def run_sample(sample: dict, agents: tuple, config) -> dict:
    """Run a single sample through the MA 4-agent pipeline."""
    user_proxy, security_researcher, code_author, moderator, review_board = agents

    # Phase 1: Security Researcher
    print(f"    Phase 1/4: Security Researcher...")
    researcher_result = user_proxy.initiate_chat(
        recipient=security_researcher,
        message=config.MULTI_AGENT_TASK_SECURITY_RESEARCHER.format(code=sample["func"]),
        max_turns=1,
        summary_method="last_msg"
    )
    researcher_response = researcher_result.summary.strip()

    # Phase 2: Code Author
    print(f"    Phase 2/4: Code Author...")
    author_result = user_proxy.initiate_chat(
        recipient=code_author,
        message=config.MULTI_AGENT_TASK_CODE_AUTHOR.format(
            researcher_findings=researcher_response,
            code=sample["func"]
        ),
        max_turns=1,
        summary_method="last_msg"
    )
    author_response = author_result.summary.strip()

    # Phase 3: Moderator
    print(f"    Phase 3/4: Moderator...")
    moderator_result = user_proxy.initiate_chat(
        recipient=moderator,
        message=config.MULTI_AGENT_TASK_MODERATOR.format(
            researcher_findings=researcher_response,
            author_response=author_response
        ),
        max_turns=1,
        summary_method="last_msg"
    )
    moderator_response = moderator_result.summary.strip()

    # Phase 4: Review Board
    print(f"    Phase 4/4: Review Board...")
    board_result = user_proxy.initiate_chat(
        recipient=review_board,
        message=config.MULTI_AGENT_TASK_REVIEW_BOARD.format(
            moderator_summary=moderator_response,
            code=sample["func"],
            researcher_findings=researcher_response,
            author_response=author_response
        ),
        max_turns=1,
        summary_method="last_msg"
    )
    board_response = board_result.summary.strip()

    return {
        "security_researcher": researcher_response,
        "code_author": author_response,
        "moderator": moderator_response,
        "review_board": board_response,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Re-run skipped samples from MA Vuln experiments"
    )
    parser.add_argument(
        "experiment",
        choices=list(EXPERIMENTS.keys()),
        help="Experiment to re-run: few-instruct, few-think, zero-instruct, zero-think"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without executing"
    )
    parser.add_argument(
        "--output-dir",
        default="results/context_overflow_test",
        help="Output directory for rerun results"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of samples to re-run (for testing)"
    )

    args = parser.parse_args()

    exp_config = EXPERIMENTS[args.experiment]
    result_dir = PROJECT_ROOT / exp_config["result_dir"]

    print("=" * 60)
    print("CONTEXT OVERFLOW RERUN TEST")
    print("=" * 60)
    print(f"Experiment: {args.experiment}")
    print(f"Prompting: {exp_config['prompting']}")
    print(f"Thinking mode: {exp_config['thinking']}")
    print(f"Result dir: {result_dir}")
    print()

    # Find skipped samples
    skipped = find_skipped_samples(result_dir)
    print(f"Found {len(skipped)} skipped samples")

    if args.limit:
        skipped = skipped[:args.limit]
        print(f"Limited to {len(skipped)} samples")

    skipped_ids = {s["idx"] for s in skipped}
    print(f"Sample IDs: {list(skipped_ids)[:10]}{'...' if len(skipped_ids) > 10 else ''}")
    print()

    if args.dry_run:
        print("=" * 60)
        print("DRY RUN - No samples will be processed")
        print("=" * 60)
        print(f"Would re-run {len(skipped)} samples")
        print()
        print("Sample details:")
        for s in skipped[:5]:
            func_len = len(s.get("func", "")) if "func" in s else "N/A"
            print(f"  - idx={s['idx']}, project={s.get('project', 'N/A')}, func_len={func_len}")
        if len(skipped) > 5:
            print(f"  ... and {len(skipped) - 5} more")
        return

    # Set environment variables BEFORE importing config
    os.environ["MODEL_FAMILY"] = "nemotron"
    os.environ["ENABLE_REASONING"] = "true" if exp_config["thinking"] else "false"

    print("Environment:")
    print(f"  MODEL_FAMILY={os.environ['MODEL_FAMILY']}")
    print(f"  ENABLE_REASONING={os.environ['ENABLE_REASONING']}")
    print()

    # Clear sys.argv before importing config (it uses argparse)
    original_argv = sys.argv.copy()
    sys.argv = [sys.argv[0]]  # Keep only script name

    # Import after setting environment
    import config_nemotron as config
    from codecarbon import OfflineEmissionsTracker
    from agent_utils_vuln import create_agent
    from multi_agent_vuln_detection_four_agents import extract_vulnerability_decision

    # Restore sys.argv
    sys.argv = original_argv

    # Load samples from dataset
    print("Loading samples from dataset...")
    samples = load_dataset_samples(config.VULN_DATASET, skipped_ids)
    print(f"Loaded {len(samples)} samples")

    if len(samples) != len(skipped_ids):
        missing = skipped_ids - {s["idx"] for s in samples}
        print(f"Warning: {len(missing)} samples not found in dataset")
    print()

    # Create output directory
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_suffix = args.experiment.replace("-", "_")
    output_file = output_dir / f"rerun_{exp_suffix}_{timestamp}.jsonl"

    print(f"Output file: {output_file}")
    print()

    # Get prompts based on experiment config
    if exp_config["prompting"] == "zero_shot":
        prompts = (
            config.SYS_MSG_SECURITY_RESEARCHER_ZERO_SHOT,
            config.SYS_MSG_CODE_AUTHOR_ZERO_SHOT,
            config.SYS_MSG_MODERATOR_ZERO_SHOT,
            config.SYS_MSG_REVIEW_BOARD_ZERO_SHOT,
        )
    else:
        prompts = (
            config.SYS_MSG_SECURITY_RESEARCHER_FEW_SHOT,
            config.SYS_MSG_CODE_AUTHOR_FEW_SHOT,
            config.SYS_MSG_MODERATOR_FEW_SHOT,
            config.SYS_MSG_REVIEW_BOARD_FEW_SHOT,
        )

    # Apply thinking toggle if needed
    if hasattr(config, "prepend_thinking_toggle"):
        prompts = tuple(config.prepend_thinking_toggle(p) for p in prompts)
        print(f"Applied thinking toggle: ENABLE_REASONING={config.ENABLE_REASONING}")

    # Create agents
    researcher_prompt, author_prompt, moderator_prompt, review_board_prompt = prompts

    user_proxy = create_agent(
        "conversable",
        "user_proxy_agent",
        config.LLM_CONFIG,
        sys_prompt="A human admin coordinating the vulnerability assessment.",
        description="A proxy for human input."
    )

    security_researcher = create_agent(
        "assistant",
        "security_researcher_agent",
        config.LLM_CONFIG,
        sys_prompt=researcher_prompt,
        description="A security researcher who identifies vulnerabilities."
    )

    code_author = create_agent(
        "assistant",
        "code_author_agent",
        config.LLM_CONFIG,
        sys_prompt=author_prompt,
        description="The original author responding to security findings."
    )

    moderator_agent = create_agent(
        "assistant",
        "moderator_agent",
        config.LLM_CONFIG,
        sys_prompt=moderator_prompt,
        description="A moderator summarizing the discussion."
    )

    review_board = create_agent(
        "assistant",
        "review_board_agent",
        config.LLM_CONFIG,
        sys_prompt=review_board_prompt,
        description="Review board making final vulnerability decisions."
    )

    agents = (user_proxy, security_researcher, code_author, moderator_agent, review_board)

    # Start emissions tracking
    tracker = OfflineEmissionsTracker(
        project_name=f"rerun_{exp_suffix}",
        output_dir=str(output_dir),
        country_iso_code="CAN",
        log_level="error",
    )
    tracker.start()

    print("=" * 60)
    print("STARTING RERUN")
    print("=" * 60)

    results = []
    successful = 0
    failed = 0

    for i, sample in enumerate(samples, 1):
        print(f"\n[{i}/{len(samples)}] Sample {sample['idx']} ({sample['project']})...")
        func_len = len(sample.get("func", ""))
        print(f"    Function length: {func_len} chars")

        try:
            discussion = run_sample(sample, agents, config)

            # Extract decision
            vuln_decision, reasoning = extract_vulnerability_decision(discussion["review_board"])

            result = {
                "idx": sample["idx"],
                "project": sample["project"],
                "commit_id": sample["commit_id"],
                "ground_truth": sample["target"],
                "vuln": vuln_decision,
                "reasoning": reasoning,
                "full_discussion": discussion,
                "cwe": sample.get("cwe"),
                "cve": sample.get("cve"),
                "func_length": func_len,
                "rerun_context_test": True,
                "timestamp": datetime.now().isoformat(),
            }

            results.append(result)

            # Write immediately
            with open(output_file, "a") as f:
                f.write(json.dumps(result) + "\n")

            status = "VULN" if vuln_decision == 1 else "SAFE" if vuln_decision == 0 else "FAILED"
            gt = "VULN" if sample["target"] == 1 else "SAFE"

            if vuln_decision in [0, 1]:
                successful += 1
                print(f"    ✓ SUCCESS: {status} (GT: {gt})")
            else:
                failed += 1
                print(f"    ✗ FAILED: Could not extract decision")

        except Exception as e:
            failed += 1
            print(f"    ✗ ERROR: {e}")

            error_result = {
                "idx": sample["idx"],
                "project": sample["project"],
                "ground_truth": sample["target"],
                "vuln": -1,
                "error": str(e),
                "func_length": func_len,
                "rerun_context_test": True,
                "timestamp": datetime.now().isoformat(),
            }
            results.append(error_result)

            with open(output_file, "a") as f:
                f.write(json.dumps(error_result) + "\n")

    emissions = tracker.stop()

    print()
    print("=" * 60)
    print("RERUN COMPLETE")
    print("=" * 60)
    print(f"Total samples: {len(samples)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(samples)*100:.1f}%")
    print(f"Emissions: {emissions:.6f} kg CO2")
    print(f"Results saved to: {output_file}")

    # Save summary
    summary_file = output_dir / f"rerun_{exp_suffix}_{timestamp}_summary.json"
    summary = {
        "experiment": args.experiment,
        "prompting": exp_config["prompting"],
        "thinking": exp_config["thinking"],
        "total_samples": len(samples),
        "successful": successful,
        "failed": failed,
        "success_rate": successful / len(samples) if samples else 0,
        "emissions_kg_co2": emissions,
        "output_file": str(output_file),
        "timestamp": datetime.now().isoformat(),
    }

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to: {summary_file}")

    # Show failed sample IDs if any
    if failed > 0:
        failed_ids = [r["idx"] for r in results if r.get("vuln") not in [0, 1]]
        print(f"\nStill failed IDs: {failed_ids}")


if __name__ == "__main__":
    main()
