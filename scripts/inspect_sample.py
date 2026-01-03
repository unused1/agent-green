#!/usr/bin/env python3
"""
Inspect a sample from experiment results by ID.

Usage:
    python scripts/inspect_sample.py <sample_id> <experiment>

Examples:
    python scripts/inspect_sample.py 343298 "MA zero Nemotron 8B vuln"
    python scripts/inspect_sample.py 195023 "MA few thinking 8B"
    python scripts/inspect_sample.py 360829 "DA zero Qwen 30B"

Experiment keywords (case-insensitive, partial match):
    - Design: SA, DA, MA
    - Task: vuln, code
    - Model: Qwen, Nemotron, 4B, 8B, 30B, 49B
    - Mode: instruct, thinking
    - Prompting: zero, few
"""

import json
import sys
from pathlib import Path
import textwrap

# Base results directory
RESULTS_DIR = Path(__file__).parent.parent / "results"

# Canonical files to load experiments from
CANONICAL_FILES = [
    "canonical_sa_vuln.json",
    "canonical_da_vuln.json",
    "canonical_ma_vuln.json",
]


def load_canonical_experiments() -> list[dict]:
    """Load all experiments from canonical files."""
    experiments = []

    for filename in CANONICAL_FILES:
        filepath = RESULTS_DIR / filename
        if filepath.exists():
            with open(filepath) as f:
                data = json.load(f)
                for exp in data.get("canonical", []):
                    exp["canonical_source"] = filename
                    experiments.append(exp)

    return experiments


def match_experiment(exp: dict, query: str) -> bool:
    """Check if experiment matches query keywords."""
    query_lower = query.lower()
    words = query_lower.split()

    # Check design
    design = exp.get("design", "").lower()
    if "sa" in words and design != "sa":
        return False
    if "da" in words and design != "da":
        return False
    if "ma" in words and design != "ma":
        return False

    # Check task
    task = exp.get("task", "")
    if "vuln" in query_lower and "vuln" not in task.lower():
        return False
    if "code" in query_lower and "code" not in task.lower():
        return False

    # Check model family
    model_family = exp.get("model_family", "").lower()
    if "qwen" in query_lower and model_family != "qwen":
        return False
    if "nemotron" in query_lower and model_family != "nemotron":
        return False

    # Check model size
    params = exp.get("parameters_b", 0)
    if "4b" in query_lower and params != 4:
        return False
    if "8b" in query_lower and params != 8:
        return False
    if "30b" in query_lower and params != 30:
        return False
    if "49b" in query_lower and params != 49:
        return False

    # Check mode
    mode = exp.get("mode", "").lower()
    if "thinking" in query_lower and mode != "thinking":
        return False
    if "instruct" in query_lower and mode != "instruct":
        return False

    # Check prompting
    prompting = exp.get("prompting", "").lower()
    if "zero" in query_lower and "zero" not in prompting:
        return False
    if "few" in query_lower and "few" not in prompting:
        return False

    return True


def find_matching_experiments(experiments: list[dict], query: str) -> list[dict]:
    """Find experiments matching the query."""
    return [exp for exp in experiments if match_experiment(exp, query)]


def find_sample(file_path: Path, sample_id: int) -> dict | None:
    """Find a sample by ID in a JSONL file."""
    with open(file_path, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                sid = data.get('idx') or data.get('sample_id') or data.get('task_id')
                if sid == sample_id:
                    return data
            except json.JSONDecodeError:
                continue
    return None


def format_experiment_id(exp: dict) -> str:
    """Create a readable experiment ID."""
    parts = []
    if exp.get("model_family"):
        parts.append(exp["model_family"])
    if exp.get("parameters_b"):
        parts.append(f"{exp['parameters_b']}B")
    if exp.get("design"):
        parts.append(exp["design"])
    if exp.get("prompting"):
        parts.append(exp["prompting"].replace("-shot", ""))
    if exp.get("mode"):
        parts.append(exp["mode"][:5])  # instr or think
    return "-".join(parts) if parts else "unknown"


def format_sample(data: dict, file_path: Path, exp: dict = None) -> str:
    """Format a sample for readable display."""
    output = []

    output.append("=" * 80)
    output.append(f"SAMPLE: {data.get('idx') or data.get('sample_id')}")
    if exp:
        output.append(f"EXPERIMENT: {format_experiment_id(exp)}")
    output.append(f"FILE: {file_path.name}")
    output.append(f"PATH: {file_path.parent.name}")
    output.append("=" * 80)

    # Basic info
    output.append("\n### BASIC INFO ###")
    for key in ['project', 'commit_id', 'cwe', 'cve']:
        if key in data and data[key]:
            output.append(f"  {key}: {data[key]}")

    # Ground truth and prediction
    output.append("\n### PREDICTION ###")
    gt = data.get('ground_truth', data.get('target', 'N/A'))
    pred = data.get('vuln', data.get('predicted', data.get('prediction', 'N/A')))
    output.append(f"  Ground Truth: {gt} ({'VULNERABLE' if gt == 1 else 'SAFE' if gt == 0 else 'N/A'})")
    output.append(f"  Prediction:   {pred} ({'VULNERABLE' if pred == 1 else 'SAFE' if pred == 0 else 'FAILED/N/A'})")

    correct = "✓ CORRECT" if gt == pred else "✗ INCORRECT"
    if pred is None or pred == -1:
        correct = "⚠ FAILED EXTRACTION"
    output.append(f"  Result:       {correct}")

    # Error/skip status
    if data.get('skipped'):
        output.append(f"  Skipped:      True")
    if data.get('error'):
        output.append(f"  Error:        {data.get('error')}")

    # Commit message
    if data.get('commit_message'):
        output.append("\n### COMMIT MESSAGE ###")
        msg = data['commit_message'][:500]
        output.append(textwrap.indent(msg, "  "))
        if len(data['commit_message']) > 500:
            output.append("  ...")

    # Reasoning/Analysis
    if data.get('reasoning'):
        output.append("\n### REASONING ###")
        reasoning = data['reasoning']
        # Truncate if too long
        if len(reasoning) > 2000:
            reasoning = reasoning[:2000] + "\n... [truncated, full length: {}]".format(len(data['reasoning']))
        output.append(textwrap.indent(reasoning, "  "))

    # Full discussion (for MA experiments)
    if data.get('full_discussion'):
        fd = data['full_discussion']
        output.append("\n### FULL DISCUSSION ###")

        for role in ['security_researcher', 'code_author', 'moderator', 'review_board']:
            if role in fd and fd[role]:
                output.append(f"\n  [{role.upper().replace('_', ' ')}]")
                content = str(fd[role])
                if len(content) > 1000:
                    content = content[:1000] + "... [truncated]"
                output.append(textwrap.indent(content, "    "))

    # Session info
    if data.get('session') or data.get('timestamp'):
        output.append("\n### METADATA ###")
        if data.get('session'):
            output.append(f"  Session: {data['session']}")
        if data.get('timestamp'):
            output.append(f"  Timestamp: {data['timestamp']}")

    output.append("\n" + "=" * 80)

    return "\n".join(output)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    try:
        sample_id = int(sys.argv[1])
    except ValueError:
        print(f"Error: Sample ID must be an integer, got '{sys.argv[1]}'")
        sys.exit(1)

    experiment_query = " ".join(sys.argv[2:])

    print(f"Searching for sample {sample_id} in experiments matching: '{experiment_query}'")
    print()

    # Load canonical experiments
    experiments = load_canonical_experiments()
    if not experiments:
        print("Error: No canonical experiment files found in results/")
        print("Run: python scripts/find_canonical_results.py --task vuln --design <SA|DA|MA> --output results/canonical_<design>_vuln.json")
        sys.exit(1)

    # Find matching experiments
    matches = find_matching_experiments(experiments, experiment_query)

    if not matches:
        print(f"No experiments found matching: '{experiment_query}'")
        print("\nAvailable experiments:")
        for exp in sorted(experiments, key=lambda x: format_experiment_id(x)):
            print(f"  - {format_experiment_id(exp)}")
        sys.exit(1)

    if len(matches) > 1:
        print(f"Found {len(matches)} matching experiments:")
        for i, exp in enumerate(matches, 1):
            print(f"  {i}. {format_experiment_id(exp)}: {exp['file_name']}")
        print()

    # Search in each match
    found = False
    for exp in matches:
        file_path = RESULTS_DIR.parent / exp["file_path"]
        if not file_path.exists():
            print(f"Warning: File not found: {file_path}")
            continue

        sample = find_sample(file_path, sample_id)
        if sample:
            print(format_sample(sample, file_path, exp))
            found = True
            break

    if not found:
        print(f"Sample {sample_id} not found in any matching experiment.")
        print(f"Searched {len(matches)} experiment(s).")


if __name__ == "__main__":
    main()
