#!/usr/bin/env python3
"""
Llama-Nemotron Thinking Mode Validation Script

This script validates that Llama-Nemotron models correctly:
1. Output <think>...</think> blocks when thinking mode is enabled
2. Output direct responses when thinking mode is disabled

IMPORTANT: Nemotron uses SYSTEM PROMPT to toggle thinking mode, not API parameters!
- Nano-8B v1: "detailed thinking on" / "detailed thinking off"
- Super-49B v1.5: default=ON, "/no_think"=OFF

vLLM Deployment:
    python3 -m vllm.entrypoints.openai.api_server \
        --model "nvidia/Llama-3.1-Nemotron-Nano-8B-v1" \
        --trust-remote-code \
        --max-model-len=65536 \
        --gpu-memory-utilization 0.9

Usage:
    python scripts/validate_nemotron_modes.py --endpoint http://localhost:8000/v1

Reference: docs/Cross_Architecture_Validation_Plan.md
"""

import argparse
import json
import requests
from typing import Tuple, Optional

# Test prompts for validation
TEST_PROMPTS = [
    {
        "name": "simple_math",
        "prompt": "What is 15 + 27?",
        "expected_answer_contains": "42"
    },
    {
        "name": "code_analysis",
        "prompt": "Is this code vulnerable? `strcpy(buffer, user_input);`",
        "expected_answer_contains": ["yes", "vulnerable", "buffer overflow"]
    },
    {
        "name": "reasoning_task",
        "prompt": "If all roses are flowers and all flowers need water, do roses need water?",
        "expected_answer_contains": "yes"
    }
]


def get_thinking_system_prompt(model: str) -> str:
    """Get system prompt to ENABLE thinking mode."""
    if 'Super' in model or '49B' in model:
        # Super-49B v1.5: default (empty) enables thinking
        return ""
    else:
        # Nano-8B v1: explicit toggle
        return "detailed thinking on"


def get_non_thinking_system_prompt(model: str) -> str:
    """Get system prompt to DISABLE thinking mode."""
    if 'Super' in model or '49B' in model:
        # Super-49B v1.5: "/no_think" disables thinking
        return "/no_think"
    else:
        # Nano-8B v1: explicit toggle
        return "detailed thinking off"


def call_nemotron_api(
    endpoint: str,
    model: str,
    user_prompt: str,
    enable_thinking: bool,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    api_key: Optional[str] = None
) -> Tuple[str, bool, Optional[str]]:
    """
    Call Nemotron API with thinking mode control via system prompt.

    Args:
        endpoint: vLLM endpoint (e.g., http://localhost:8000/v1)
        model: Model name (e.g., nvidia/Llama-3.1-Nemotron-Nano-8B-v1)
        user_prompt: The user's question
        enable_thinking: Whether to enable thinking mode
        temperature: Generation temperature
        max_tokens: Maximum tokens to generate
        api_key: Optional API key

    Returns:
        Tuple of (response_text, has_think_tags, error_message)
    """
    url = f"{endpoint}/chat/completions"

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Build messages with appropriate system prompt for thinking mode
    if enable_thinking:
        system_prompt = get_thinking_system_prompt(model)
    else:
        system_prompt = get_non_thinking_system_prompt(model)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Check for thinking tags
        has_think_tags = "<think>" in content and "</think>" in content

        return content, has_think_tags, None

    except requests.exceptions.RequestException as e:
        return "", False, str(e)
    except (KeyError, IndexError) as e:
        return "", False, f"Unexpected response format: {e}"


def validate_thinking_mode(
    endpoint: str,
    model: str,
    api_key: Optional[str] = None
) -> dict:
    """
    Validate that thinking mode works correctly.

    Returns:
        Dictionary with validation results
    """
    results = {
        "model": model,
        "endpoint": endpoint,
        "toggle_mechanism": "system_prompt",
        "tests": [],
        "summary": {
            "thinking_enabled_tests": 0,
            "thinking_disabled_tests": 0,
            "thinking_enabled_pass": 0,
            "thinking_disabled_pass": 0
        }
    }

    for test in TEST_PROMPTS:
        test_name = test["name"]
        user_prompt = test["prompt"]

        print(f"\n{'='*60}")
        print(f"Test: {test_name}")
        print(f"{'='*60}")

        # Test with thinking ENABLED
        print("\n[1] Testing with thinking ENABLED...")
        thinking_prompt = get_thinking_system_prompt(model)
        print(f"    System prompt: '{thinking_prompt or '(empty - default ON)'}'")

        response_thinking, has_tags_thinking, error_thinking = call_nemotron_api(
            endpoint=endpoint,
            model=model,
            user_prompt=user_prompt,
            enable_thinking=True,
            api_key=api_key
        )

        if error_thinking:
            print(f"    ERROR: {error_thinking}")
            thinking_pass = False
        else:
            thinking_pass = has_tags_thinking
            print(f"    Has <think> tags: {has_tags_thinking}")
            print(f"    Response preview: {response_thinking[:300]}...")
            if thinking_pass:
                print("    PASS: Thinking mode produces <think> tags")
            else:
                print("    FAIL: Expected <think> tags but none found")

        results["summary"]["thinking_enabled_tests"] += 1
        if thinking_pass:
            results["summary"]["thinking_enabled_pass"] += 1

        # Test with thinking DISABLED
        print("\n[2] Testing with thinking DISABLED...")
        non_thinking_prompt = get_non_thinking_system_prompt(model)
        print(f"    System prompt: '{non_thinking_prompt}'")

        response_no_thinking, has_tags_no_thinking, error_no_thinking = call_nemotron_api(
            endpoint=endpoint,
            model=model,
            user_prompt=user_prompt,
            enable_thinking=False,
            api_key=api_key
        )

        if error_no_thinking:
            print(f"    ERROR: {error_no_thinking}")
            no_thinking_pass = False
        else:
            no_thinking_pass = not has_tags_no_thinking
            print(f"    Has <think> tags: {has_tags_no_thinking}")
            print(f"    Response preview: {response_no_thinking[:300]}...")
            if no_thinking_pass:
                print("    PASS: Non-thinking mode produces no <think> tags")
            else:
                print("    FAIL: Expected no <think> tags but found them")

        results["summary"]["thinking_disabled_tests"] += 1
        if no_thinking_pass:
            results["summary"]["thinking_disabled_pass"] += 1

        # Store test results
        results["tests"].append({
            "name": test_name,
            "thinking_enabled": {
                "system_prompt": thinking_prompt or "(empty)",
                "response": response_thinking[:500] if response_thinking else None,
                "has_think_tags": has_tags_thinking,
                "error": error_thinking,
                "pass": thinking_pass
            },
            "thinking_disabled": {
                "system_prompt": non_thinking_prompt,
                "response": response_no_thinking[:500] if response_no_thinking else None,
                "has_think_tags": has_tags_no_thinking,
                "error": error_no_thinking,
                "pass": no_thinking_pass
            }
        })

    return results


def print_summary(results: dict):
    """Print validation summary."""
    summary = results["summary"]

    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Model: {results['model']}")
    print(f"Endpoint: {results['endpoint']}")
    print(f"Toggle Mechanism: {results['toggle_mechanism']}")
    print()
    print("Thinking Enabled (system prompt toggle):")
    print(f"  Tests: {summary['thinking_enabled_tests']}")
    print(f"  Passed: {summary['thinking_enabled_pass']}")
    print(f"  Status: {'ALL PASS' if summary['thinking_enabled_pass'] == summary['thinking_enabled_tests'] else 'SOME FAILED'}")
    print()
    print("Thinking Disabled (system prompt toggle):")
    print(f"  Tests: {summary['thinking_disabled_tests']}")
    print(f"  Passed: {summary['thinking_disabled_pass']}")
    print(f"  Status: {'ALL PASS' if summary['thinking_disabled_pass'] == summary['thinking_disabled_tests'] else 'SOME FAILED'}")
    print()

    all_pass = (
        summary['thinking_enabled_pass'] == summary['thinking_enabled_tests'] and
        summary['thinking_disabled_pass'] == summary['thinking_disabled_tests']
    )

    if all_pass:
        print("OVERALL: ALL VALIDATIONS PASSED")
        print("   Nemotron thinking mode toggle is working correctly!")
        print("   You can proceed with cross-architecture experiments.")
    else:
        print("OVERALL: SOME VALIDATIONS FAILED")
        print("   Please check the test results above.")
        print("   The system prompt toggle may not be working as expected.")

    print("="*60)

    return all_pass


def main():
    parser = argparse.ArgumentParser(
        description="Validate Llama-Nemotron thinking mode control via system prompt"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="http://localhost:8000/v1",
        help="vLLM API endpoint (default: http://localhost:8000/v1)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="nvidia/Llama-3.1-Nemotron-Nano-8B-v1",
        help="Model name (default: nvidia/Llama-3.1-Nemotron-Nano-8B-v1)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key (optional)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file for results (optional)"
    )

    args = parser.parse_args()

    print("Llama-Nemotron Thinking Mode Validation")
    print("="*60)
    print(f"Endpoint: {args.endpoint}")
    print(f"Model: {args.model}")
    print()
    print("Toggle Mechanism: System Prompt")
    if 'Super' in args.model or '49B' in args.model:
        print("  - Thinking ON: (empty system prompt - default)")
        print("  - Thinking OFF: '/no_think' in system prompt")
    else:
        print("  - Thinking ON: 'detailed thinking on'")
        print("  - Thinking OFF: 'detailed thinking off'")
    print()

    # Run validation
    results = validate_thinking_mode(
        endpoint=args.endpoint,
        model=args.model,
        api_key=args.api_key
    )

    # Print summary
    all_pass = print_summary(results)

    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")

    # Exit with appropriate code
    exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
