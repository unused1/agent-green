#!/usr/bin/env python3
"""
RQ3 Explain-Before Mode Sample Test

This script tests the RQ3 explain-before implementation on a small sample
to verify that prompts, extraction logic, and faithfulness metrics work correctly.

Usage:
    python3 scripts/test_rq3_sample.py <task_type> <num_samples>

    task_type: 'vuln' or 'codegen'
    num_samples: Number of samples to test (default: 2)

Example:
    python3 scripts/test_rq3_sample.py vuln 2
    python3 scripts/test_rq3_sample.py codegen 2
"""

import sys
import os
import json
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import config
from autogen import AssistantAgent


def test_vulnerability_detection(num_samples=2):
    """Test vulnerability detection in explain-before mode"""
    print("\n" + "=" * 70)
    print("TESTING VULNERABILITY DETECTION (SA-zero-explain)")
    print("=" * 70)

    # Load dataset
    dataset_file = config.VULNERABILITY_DATASET
    print(f"\nLoading dataset: {dataset_file}")

    samples = []
    with open(dataset_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= num_samples:
                break
            samples.append(json.loads(line.strip()))

    print(f"Loaded {len(samples)} test samples")

    # Create agent with explain-before prompt
    print("\nCreating agent with explain-before system prompt...")
    agent = AssistantAgent(
        name="test_vuln_agent",
        system_message=config.SYS_MSG_VULNERABILITY_DETECTOR_EXPLAIN_BEFORE_ZERO_SHOT,
        llm_config=config.LLM_CONFIG,
        human_input_mode="NEVER"
    )

    # Test each sample
    results = []
    for i, sample in enumerate(samples):
        sample_id = sample.get('sample_id', f'sample_{i}')
        print(f"\n--- Testing Sample {i+1}/{len(samples)}: {sample_id} ---")

        # Format task prompt
        code = sample.get('func', '')
        content = config.VULNERABILITY_TASK_PROMPT_EXPLAIN_BEFORE.format(code=code)

        print(f"Code length: {len(code)} characters")
        print("Sending request to LLM...")

        try:
            # Get response
            start_time = time.time()
            res = agent.generate_reply(messages=[{"content": content, "role": "user"}])
            elapsed_time = time.time() - start_time

            if res and "content" in res:
                response_text = res["content"].strip()

                print(f"\nResponse received (in {elapsed_time:.1f}s)")
                print(f"Response length: {len(response_text)} characters")

                # Check for expected format
                has_reasoning = "reasoning:" in response_text.lower()
                has_decision = "decision:" in response_text.lower()

                print(f"\nFormat Check:")
                print(f"  ✓ Has REASONING section: {has_reasoning}")
                print(f"  ✓ Has DECISION section: {has_decision}")

                if has_reasoning and has_decision:
                    print("  ✓ Format is CORRECT")
                else:
                    print("  ✗ Format is INCORRECT - missing required sections!")

                # Show excerpt
                print(f"\nResponse excerpt (first 500 chars):")
                print("-" * 70)
                print(response_text[:500])
                if len(response_text) > 500:
                    print("... [truncated]")
                print("-" * 70)

                results.append({
                    "sample_id": sample_id,
                    "success": True,
                    "has_reasoning": has_reasoning,
                    "has_decision": has_decision,
                    "response_length": len(response_text),
                    "elapsed_time": elapsed_time
                })
            else:
                print("\n✗ ERROR: No response from LLM")
                results.append({
                    "sample_id": sample_id,
                    "success": False,
                    "error": "no_response"
                })

        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            results.append({
                "sample_id": sample_id,
                "success": False,
                "error": str(e)
            })

    # Summary
    print("\n" + "=" * 70)
    print("VULNERABILITY DETECTION TEST SUMMARY")
    print("=" * 70)

    success_count = sum(1 for r in results if r.get("success"))
    format_correct_count = sum(1 for r in results if r.get("has_reasoning") and r.get("has_decision"))

    print(f"\nTotal samples tested: {len(results)}")
    print(f"Successful responses: {success_count}/{len(results)}")
    print(f"Correct format: {format_correct_count}/{len(results)}")

    if format_correct_count == len(results):
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ {len(results) - format_correct_count} tests failed format check")

    return results


def test_code_generation(num_samples=2):
    """Test code generation in explain-before mode"""
    print("\n" + "=" * 70)
    print("TESTING CODE GENERATION (SA-zero-explain)")
    print("=" * 70)

    # Load dataset
    dataset_file = config.HUMANEVAL_DATASET
    print(f"\nLoading dataset: {dataset_file}")

    samples = []
    with open(dataset_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= num_samples:
                break
            samples.append(json.loads(line.strip()))

    print(f"Loaded {len(samples)} test samples")

    # Create agent with explain-before prompt
    print("\nCreating agent with explain-before system prompt...")
    agent = AssistantAgent(
        name="test_codegen_agent",
        system_message=config.SYS_MSG_CODE_GENERATOR_EXPLAIN_BEFORE_ZERO_SHOT,
        llm_config=config.LLM_CONFIG,
        human_input_mode="NEVER"
    )

    # Test each sample
    results = []
    for i, sample in enumerate(samples):
        task_id = sample.get('task_id', f'sample_{i}')
        print(f"\n--- Testing Sample {i+1}/{len(samples)}: {task_id} ---")

        # Format task prompt
        problem_prompt = sample.get('prompt', '')
        content = config.CODE_GENERATION_TASK_PROMPT_EXPLAIN_BEFORE.format(prompt=problem_prompt)

        print(f"Problem prompt length: {len(problem_prompt)} characters")
        print("Sending request to LLM...")

        try:
            # Get response
            start_time = time.time()
            res = agent.generate_reply(messages=[{"content": content, "role": "user"}])
            elapsed_time = time.time() - start_time

            if res and "content" in res:
                response_text = res["content"].strip()

                print(f"\nResponse received (in {elapsed_time:.1f}s)")
                print(f"Response length: {len(response_text)} characters")

                # Check for expected format
                has_reasoning = "reasoning:" in response_text.lower()
                has_code = "code:" in response_text.lower()

                print(f"\nFormat Check:")
                print(f"  ✓ Has REASONING section: {has_reasoning}")
                print(f"  ✓ Has CODE section: {has_code}")

                if has_reasoning and has_code:
                    print("  ✓ Format is CORRECT")
                else:
                    print("  ✗ Format is INCORRECT - missing required sections!")

                # Show excerpt
                print(f"\nResponse excerpt (first 500 chars):")
                print("-" * 70)
                print(response_text[:500])
                if len(response_text) > 500:
                    print("... [truncated]")
                print("-" * 70)

                results.append({
                    "task_id": task_id,
                    "success": True,
                    "has_reasoning": has_reasoning,
                    "has_code": has_code,
                    "response_length": len(response_text),
                    "elapsed_time": elapsed_time
                })
            else:
                print("\n✗ ERROR: No response from LLM")
                results.append({
                    "task_id": task_id,
                    "success": False,
                    "error": "no_response"
                })

        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            results.append({
                "task_id": task_id,
                "success": False,
                "error": str(e)
            })

    # Summary
    print("\n" + "=" * 70)
    print("CODE GENERATION TEST SUMMARY")
    print("=" * 70)

    success_count = sum(1 for r in results if r.get("success"))
    format_correct_count = sum(1 for r in results if r.get("has_reasoning") and r.get("has_code"))

    print(f"\nTotal samples tested: {len(results)}")
    print(f"Successful responses: {success_count}/{len(results)}")
    print(f"Correct format: {format_correct_count}/{len(results)}")

    if format_correct_count == len(results):
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ {len(results) - format_correct_count} tests failed format check")

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/test_rq3_sample.py <task_type> [num_samples]")
        print("\nArguments:")
        print("  task_type   : 'vuln' or 'codegen'")
        print("  num_samples : Number of samples to test (default: 2)")
        print("\nExample:")
        print("  python3 scripts/test_rq3_sample.py vuln 2")
        print("  python3 scripts/test_rq3_sample.py codegen 2")
        sys.exit(1)

    task_type = sys.argv[1]
    num_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    # Validate task type
    if task_type not in ['vuln', 'codegen']:
        print(f"Error: task_type must be 'vuln' or 'codegen', got '{task_type}'")
        sys.exit(1)

    print("=" * 70)
    print("RQ3 EXPLAIN-BEFORE MODE SAMPLE TEST")
    print("=" * 70)
    print(f"\nTask: {task_type}")
    print(f"Samples: {num_samples}")
    print(f"Model: {config.LLM_CONFIG['config_list'][0]['model']}")
    print(f"Reasoning: {'ENABLED' if config.ENABLE_REASONING else 'DISABLED'}")

    # Run test
    if task_type == 'vuln':
        results = test_vulnerability_detection(num_samples)
    else:
        results = test_code_generation(num_samples)

    # Final summary
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the output above to verify format compliance")
    print("2. If tests pass, proceed with full experiment execution")
    print("3. After experiments complete, run faithfulness metrics:")
    print(f"   python3 src/compute_faithfulness.py <results_file> {task_type}")


if __name__ == "__main__":
    main()
