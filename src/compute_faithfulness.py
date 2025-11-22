#!/usr/bin/env python3
"""
Compute Faithfulness Metrics for RQ3 Experiments

This script processes RQ3 experiment results and computes faithfulness metrics
for explanations generated in explain-before mode.

Usage:
    python compute_faithfulness.py <results_file> <task_type>

    results_file: Path to JSONL results file
    task_type: Either 'vuln' or 'codegen'

Example:
    python compute_faithfulness.py results/vuln_SA-zero-explain_results.jsonl vuln
"""

import sys
import json
import os
from faithfulness_metrics import (
    compute_faithfulness_for_experiment,
    compute_faithfulness_metrics_vuln,
    compute_faithfulness_metrics_codegen
)


def save_metrics_to_file(metrics: dict, output_file: str):
    """Save metrics to JSON file"""
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to: {output_file}")


def print_aggregate_summary(aggregate: dict):
    """Print aggregate metrics summary"""
    print("\n" + "=" * 60)
    print("AGGREGATE FAITHFULNESS METRICS")
    print("=" * 60)

    print(f"\nMean Explanation Length: {aggregate.get('mean_explanation_length', 0):.1f} characters")
    print(f"Mean Word Count: {aggregate.get('mean_word_count', 0):.1f} words")
    print(f"Mean Citation Density: {aggregate.get('mean_citation_density', 0):.2f} refs/100 words")
    print(f"Structure Compliance Rate: {aggregate.get('structure_compliance_rate', 0):.1%}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python compute_faithfulness.py <results_file> <task_type>")
        print("\nArguments:")
        print("  results_file : Path to JSONL results file")
        print("  task_type    : Either 'vuln' or 'codegen'")
        print("\nExample:")
        print("  python compute_faithfulness.py results/vuln_SA-zero-explain_results.jsonl vuln")
        sys.exit(1)

    results_file = sys.argv[1]
    task_type = sys.argv[2]

    # Validate task type
    if task_type not in ['vuln', 'codegen']:
        print(f"Error: task_type must be 'vuln' or 'codegen', got '{task_type}'")
        sys.exit(1)

    # Check if file exists
    if not os.path.exists(results_file):
        print(f"Error: Results file not found: {results_file}")
        sys.exit(1)

    print(f"Computing faithfulness metrics for: {results_file}")
    print(f"Task type: {task_type}")
    print()

    # Compute metrics
    try:
        metrics = compute_faithfulness_for_experiment(results_file, task_type)

        # Print summary
        print(f"Total samples processed: {metrics['total_samples']}")

        # Print aggregate metrics
        print_aggregate_summary(metrics['aggregate_metrics'])

        # Generate output filename
        base_name = os.path.basename(results_file)
        output_file = results_file.replace('.jsonl', '_faithfulness_metrics.json')

        # Save detailed metrics
        save_metrics_to_file(metrics, output_file)

        print("\n" + "=" * 60)
        print("Faithfulness metrics computation completed successfully")
        print("=" * 60)

    except Exception as e:
        print(f"Error computing metrics: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
