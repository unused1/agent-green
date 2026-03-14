#!/usr/bin/env python3
"""
DeepSeek R1 Distill Thinking Mode Validation Script

This script validates that DeepSeek-R1-Distill-Llama models correctly:
1. Output <think>...</think> blocks when thinking=True (thinking mode)
2. Output direct responses when thinking=False (non-thinking mode)

IMPORTANT: vLLM must be started with these flags:
    --enable-reasoning --reasoning-parser deepseek_r1

NOTE: DeepSeek uses "thinking" parameter, not "enable_thinking" (Qwen3's param)

Usage:
    python scripts/validate_deepseek_modes.py --endpoint http://localhost:8000/v1

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
        "messages": [
            {"role": "user", "content": "What is 15 + 27?"}
        ],
        "expected_answer_contains": "42"
    },
    {
        "name": "code_analysis",
        "messages": [
            {"role": "user", "content": "Is this code vulnerable? `strcpy(buffer, user_input);`"}
        ],
        "expected_answer_contains": ["yes", "vulnerable", "buffer overflow"]
    },
    {
        "name": "reasoning_task",
        "messages": [
            {"role": "user", "content": "If all roses are flowers and all flowers need water, do roses need water?"}
        ],
        "expected_answer_contains": "yes"
    }
]


def call_deepseek_api(
    endpoint: str,
    model: str,
    messages: list,
    enable_thinking: bool,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    api_key: Optional[str] = None
) -> Tuple[str, bool, Optional[str]]:
    """
    Call DeepSeek API with thinking mode control.

    Args:
        endpoint: vLLM endpoint (e.g., http://localhost:8000/v1)
        model: Model name (e.g., deepseek-ai/DeepSeek-R1-Distill-Llama-8B)
        messages: Chat messages
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

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        # DeepSeek thinking mode control via chat_template_kwargs
        # NOTE: DeepSeek uses "thinking" parameter (not "enable_thinking" like Qwen3)
        # vLLM must be started with: --enable-reasoning --reasoning-parser deepseek_r1
        "extra_body": {
            "chat_template_kwargs": {
                "thinking": enable_thinking  # DeepSeek uses "thinking", not "enable_thinking"
            }
        }
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
        messages = test["messages"]

        print(f"\n{'='*60}")
        print(f"Test: {test_name}")
        print(f"{'='*60}")

        # Test with thinking ENABLED (default)
        print("\n[1] Testing with enable_thinking=True...")
        response_thinking, has_tags_thinking, error_thinking = call_deepseek_api(
            endpoint=endpoint,
            model=model,
            messages=messages,
            enable_thinking=True,
            api_key=api_key
        )

        if error_thinking:
            print(f"    ERROR: {error_thinking}")
            thinking_pass = False
        else:
            thinking_pass = has_tags_thinking
            print(f"    Has <think> tags: {has_tags_thinking}")
            print(f"    Response preview: {response_thinking[:200]}...")
            if thinking_pass:
                print("    ✅ PASS: Thinking mode produces <think> tags")
            else:
                print("    ❌ FAIL: Expected <think> tags but none found")

        results["summary"]["thinking_enabled_tests"] += 1
        if thinking_pass:
            results["summary"]["thinking_enabled_pass"] += 1

        # Test with thinking DISABLED
        print("\n[2] Testing with enable_thinking=False...")
        response_no_thinking, has_tags_no_thinking, error_no_thinking = call_deepseek_api(
            endpoint=endpoint,
            model=model,
            messages=messages,
            enable_thinking=False,
            api_key=api_key
        )

        if error_no_thinking:
            print(f"    ERROR: {error_no_thinking}")
            no_thinking_pass = False
        else:
            no_thinking_pass = not has_tags_no_thinking
            print(f"    Has <think> tags: {has_tags_no_thinking}")
            print(f"    Response preview: {response_no_thinking[:200]}...")
            if no_thinking_pass:
                print("    ✅ PASS: Non-thinking mode produces no <think> tags")
            else:
                print("    ❌ FAIL: Expected no <think> tags but found them")

        results["summary"]["thinking_disabled_tests"] += 1
        if no_thinking_pass:
            results["summary"]["thinking_disabled_pass"] += 1

        # Store test results
        results["tests"].append({
            "name": test_name,
            "thinking_enabled": {
                "response": response_thinking[:500] if response_thinking else None,
                "has_think_tags": has_tags_thinking,
                "error": error_thinking,
                "pass": thinking_pass
            },
            "thinking_disabled": {
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
    print()
    print("Thinking Enabled (thinking=True):")
    print(f"  Tests: {summary['thinking_enabled_tests']}")
    print(f"  Passed: {summary['thinking_enabled_pass']}")
    print(f"  Status: {'✅ ALL PASS' if summary['thinking_enabled_pass'] == summary['thinking_enabled_tests'] else '❌ SOME FAILED'}")
    print()
    print("Thinking Disabled (thinking=False):")
    print(f"  Tests: {summary['thinking_disabled_tests']}")
    print(f"  Passed: {summary['thinking_disabled_pass']}")
    print(f"  Status: {'✅ ALL PASS' if summary['thinking_disabled_pass'] == summary['thinking_disabled_tests'] else '❌ SOME FAILED'}")
    print()

    all_pass = (
        summary['thinking_enabled_pass'] == summary['thinking_enabled_tests'] and
        summary['thinking_disabled_pass'] == summary['thinking_disabled_tests']
    )

    if all_pass:
        print("🎉 OVERALL: ALL VALIDATIONS PASSED")
        print("   DeepSeek thinking mode is working correctly!")
    else:
        print("⚠️  OVERALL: SOME VALIDATIONS FAILED")
        print("   Please check the test results above.")

    print("="*60)

    return all_pass


def main():
    parser = argparse.ArgumentParser(
        description="Validate DeepSeek R1 Distill thinking mode control"
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
        default="deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
        help="Model name (default: deepseek-ai/DeepSeek-R1-Distill-Llama-8B)"
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

    print("DeepSeek R1 Distill Thinking Mode Validation")
    print("="*60)
    print(f"Endpoint: {args.endpoint}")
    print(f"Model: {args.model}")
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
