#!/usr/bin/env python3
"""
Single-Agent Vulnerability Detection using OpenRouter API

SOTA comparison experiment for vulnerability detection task.
Supports Claude Sonnet 4.5 and Claude Opus 4.5 via OpenRouter.

Usage:
    # Set up environment
    export OPENROUTER_API_KEY=<your-key>

    # Run with Sonnet 4.5
    set -a && source .env.openrouter-sonnet && set +a
    python src/single_agent_vuln_openrouter.py --shot zero

    # Run with Opus 4.5
    set -a && source .env.openrouter-opus && set +a
    python src/single_agent_vuln_openrouter.py --shot few

    # Resume interrupted experiment
    python src/single_agent_vuln_openrouter.py --shot zero --resume results/sota_comparison/SA-zero_Claude-Sonnet-4.5/vuln_SA-zero_Claude-Sonnet-4.5_20260124-123456_detailed_results.jsonl
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from openai import OpenAI

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config_openrouter as config

# ========================================================================================
# CONFIGURATION
# ========================================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='SOTA Vulnerability Detection via OpenRouter')
    parser.add_argument('--shot', type=str, choices=['zero', 'few'], required=True,
                        help='Prompting strategy: zero-shot or few-shot')
    parser.add_argument('--resume', type=str, default=None,
                        help='Path to detailed_results.jsonl file to resume from')
    return parser.parse_args()


def load_processed_indices(resume_file):
    """Load already-processed sample indices from a results file."""
    processed = set()
    if resume_file and os.path.exists(resume_file):
        with open(resume_file, 'r') as f:
            for line in f:
                try:
                    result = json.loads(line.strip())
                    if result.get('idx') is not None:
                        processed.add(result['idx'])
                except json.JSONDecodeError:
                    continue
        print(f"Loaded {len(processed)} already-processed samples from {resume_file}")
    return processed


# Rate limiting configuration
MAX_RETRIES = 5
BASE_DELAY = 2  # seconds
REQUEST_DELAY = 0.5  # delay between successful requests


def call_api_with_retry(client, model, messages, temperature, max_tokens):
    """Call API with exponential backoff retry for rate limits."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            # Small delay between requests to avoid hitting rate limits
            time.sleep(REQUEST_DELAY)
            return response
        except Exception as e:
            error_str = str(e).lower()
            # Check for rate limit errors (429) or server overload (503)
            if '429' in str(e) or 'rate' in error_str or '503' in str(e) or 'overload' in error_str:
                delay = BASE_DELAY * (2 ** attempt)  # Exponential backoff
                print(f"\n  [Rate limited, waiting {delay}s before retry {attempt+1}/{MAX_RETRIES}]", end="")
                time.sleep(delay)
            else:
                # Non-rate-limit error, don't retry
                raise e
    # All retries exhausted
    raise Exception(f"Max retries ({MAX_RETRIES}) exceeded due to rate limiting")

# ========================================================================================
# DATA LOADING
# ========================================================================================

def load_vulnerability_dataset(file_path):
    """Load the vulnerability dataset from JSONL file."""
    samples = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if 'func' in data and 'target' in data:
                    sample = {
                        'idx': data.get('idx'),
                        'project': data.get('project'),
                        'func': data['func'],
                        'target': data['target'],  # Ground truth: 1 = vulnerable, 0 = not
                        'cwe': data.get('cwe'),
                        'cve': data.get('cve'),
                    }
                    samples.append(sample)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON line: {e}")
                continue

    return samples

# ========================================================================================
# RESPONSE PARSING
# ========================================================================================

def parse_vulnerability_response(response_text):
    """
    Parse the LLM response to extract vulnerability decision.

    Returns:
        tuple: (decision, reasoning)
            decision: 1 (vulnerable) or 0 (not vulnerable)
            reasoning: str containing the full response
    """
    # Strip think block — parse only the response after </think>
    parse_text = response_text.split("</think>", 1)[1].strip() if "</think>" in response_text else response_text
    response_lower = parse_text.lower()

    # Check for explicit YES answers
    if any(pattern in response_lower for pattern in [
        'final answer: yes',
        'final answer: (1) yes',
        '(1) yes',
        'answer: yes',
        'vulnerability detected',
        'yes, the code',
        'yes: vulnerability'
    ]):
        return 1, response_text

    # Check for explicit NO answers
    if any(pattern in response_lower for pattern in [
        'final answer: no',
        'final answer: (2) no',
        '(2) no',
        'answer: no',
        'no vulnerability',
        'no security vulnerability',
        'no, the code'
    ]):
        return 0, response_text

    # Fallback: look for vulnerability keywords
    if any(keyword in response_lower for keyword in [
        'is vulnerable',
        'contains a vulnerability',
        'security vulnerability exists',
        'security risk',
        'can be exploited',
        'buffer overflow',
        'memory leak',
        'sql injection',
        'xss',
        'race condition'
    ]):
        return 1, response_text

    # Default to not vulnerable
    return 0, response_text

# ========================================================================================
# INFERENCE
# ========================================================================================

def run_vulnerability_detection(samples, client, model, sys_prompt, task_template, result_dir, exp_name, resume_file=None):
    """Run vulnerability detection on all samples."""

    # Setup result files
    if resume_file:
        detailed_file = resume_file
        # Extract exp_name from resume file for summary
        summary_file = resume_file.replace('_detailed_results.jsonl', '_summary_metrics.csv')
    else:
        detailed_file = os.path.join(result_dir, f"{exp_name}_detailed_results.jsonl")
        summary_file = os.path.join(result_dir, f"{exp_name}_summary_metrics.csv")

    # Load already-processed samples if resuming
    processed_indices = load_processed_indices(resume_file)

    results = []

    # Metrics
    tp, tn, fp, fn = 0, 0, 0, 0

    # Count metrics from already-processed samples
    if resume_file and os.path.exists(resume_file):
        with open(resume_file, 'r') as f:
            for line in f:
                try:
                    result = json.loads(line.strip())
                    gt = result.get('ground_truth')
                    pred = result.get('prediction')
                    if gt is not None and pred is not None:
                        if pred == 1 and gt == 1:
                            tp += 1
                        elif pred == 0 and gt == 0:
                            tn += 1
                        elif pred == 1 and gt == 0:
                            fp += 1
                        else:
                            fn += 1
                except json.JSONDecodeError:
                    continue

    remaining = [s for s in samples if s['idx'] not in processed_indices]
    print(f"\nProcessing {len(remaining)} samples ({len(processed_indices)} already done)...")
    print(f"Model: {model}")
    print(f"Results: {detailed_file}\n")

    for i, sample in enumerate(remaining):
        print(f"Processing {sample['idx']} ({len(processed_indices) + i + 1}/{len(samples)})", end=" ")

        # Prepare prompt
        task_content = task_template.format(code=sample['func'])

        try:
            # Call OpenRouter API with retry logic
            response = call_api_with_retry(
                client=client,
                model=model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": task_content}
                ],
                temperature=config.TEMPERATURE,
                max_tokens=2048
            )

            response_text = response.choices[0].message.content.strip()
            prediction, reasoning = parse_vulnerability_response(response_text)
            error = None

        except Exception as e:
            print(f"[ERROR: {str(e)[:50]}]", end=" ")
            prediction = 0
            reasoning = f"ERROR: {str(e)}"
            error = str(e)

        # Record result
        result = {
            'idx': sample['idx'],
            'project': sample['project'],
            'ground_truth': sample['target'],
            'prediction': prediction,
            'reasoning': reasoning,
            'cwe': sample['cwe'],
            'cve': sample['cve'],
            'error': error
        }
        results.append(result)

        # Update metrics
        gt = sample['target']
        if prediction == 1 and gt == 1:
            tp += 1
            print("[TP]")
        elif prediction == 0 and gt == 0:
            tn += 1
            print("[TN]")
        elif prediction == 1 and gt == 0:
            fp += 1
            print("[FP]")
        else:  # prediction == 0 and gt == 1
            fn += 1
            print("[FN]")

        # Save incrementally
        with open(detailed_file, 'a') as f:
            f.write(json.dumps(result) + '\n')

    # Calculate final metrics
    total = len(samples)
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # Save summary metrics
    with open(summary_file, 'w') as f:
        f.write("Total,TP,TN,FP,FN,Accuracy,Precision,Recall,F1\n")
        f.write(f"{total},{tp},{tn},{fp},{fn},{accuracy},{precision},{recall},{f1}\n")

    print(f"\n{'='*60}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Total samples: {total}")
    print(f"TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")
    print(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"{'='*60}")
    print(f"Results saved to: {detailed_file}")
    print(f"Summary saved to: {summary_file}")

    return results, {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

# ========================================================================================
# MAIN
# ========================================================================================

def main():
    args = parse_args()

    # Validate API key
    if not config.OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set")
        print("Please set: export OPENROUTER_API_KEY=<your-key>")
        sys.exit(1)

    # Select prompts based on shot type
    if args.shot == 'zero':
        sys_prompt = config.SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT
        design = "SA-zero"
    else:
        sys_prompt = config.SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT
        design = "SA-few"

    task_template = config.VULNERABILITY_TASK_PROMPT

    # Get model info
    model = config.OPENROUTER_MODEL
    model_display = config.get_model_display_name()

    print(f"{'='*60}")
    print(f"SOTA VULNERABILITY DETECTION EXPERIMENT")
    print(f"{'='*60}")
    print(f"Model: {model_display} ({model})")
    print(f"Design: {design}")
    print(f"Extended Thinking: {config.ENABLE_EXTENDED_THINKING}")
    print(f"Temperature: {config.TEMPERATURE}")
    print(f"{'='*60}")

    # Setup result directory
    result_dir = os.path.join(config.RESULT_DIR, f"{design}_{model_display}")
    os.makedirs(result_dir, exist_ok=True)

    # Create experiment name
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    exp_name = f"vuln_{design}_{model_display}_{timestamp}"

    # Load dataset
    print(f"\nLoading dataset: {config.VULN_DATASET}")
    samples = load_vulnerability_dataset(config.VULN_DATASET)
    print(f"Loaded {len(samples)} samples")

    # Initialize OpenAI client for OpenRouter
    client = OpenAI(
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_API_BASE
    )

    # Run experiment
    results, metrics = run_vulnerability_detection(
        samples=samples,
        client=client,
        model=model,
        sys_prompt=sys_prompt,
        task_template=task_template,
        result_dir=result_dir,
        exp_name=exp_name,
        resume_file=args.resume
    )

    print(f"\nExperiment complete!")

if __name__ == "__main__":
    main()
