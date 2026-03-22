#!/usr/bin/env python3
"""
LLM-as-a-judge verification script for vulnerability parsing.

This script feeds the final conclusion text (with <think> tags stripped) of a vulnerability
detection model to a Judge LLM and asks it to determine if the model concluded the code is
vulnerable or not. It then compares the Judge LLM's understanding with the keyword parser's
outcome (`vuln` field) to find potential parsing errors.

Usage:
    # Google AI Studio (Gemini Flash) — recommended for speed/cost
    python scripts/verify_vuln_parsing.py --google --dirs results/runpod_vuln_384_incremental --sample-size 100

    # OpenRouter
    python scripts/verify_vuln_parsing.py --dirs results/run1 --model meta-llama/llama-3.3-70b-instruct

    # Local Ollama
    python scripts/verify_vuln_parsing.py --local --dirs results/SA_runs --model qwen2.5-coder:7b-instruct

    # Specific files with custom output
    python scripts/verify_vuln_parsing.py --google --files results/file1.jsonl --output results/parsing_check.csv
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

csv.field_size_limit(sys.maxsize)

# Try to import openai for API calls
try:
    import openai
except ImportError:
    print("ERROR: openai package required. Install with: pip install openai")
    sys.exit(1)


def strip_think_block(text):
    """Return only the response portion after </think>, or full text if no tag."""
    if "</think>" in text:
        return text.split("</think>", 1)[1].strip()
    return text


def find_jsonl_files(files_arg, dirs_arg):
    """Find all relevant JSONL files from provided files and directories."""
    jsonl_files = []

    if files_arg:
        for f in files_arg:
            if os.path.exists(f) and f.endswith(".jsonl"):
                jsonl_files.append(f)

    if dirs_arg:
        for d in dirs_arg:
            d_path = Path(d)
            if not d_path.exists() or not d_path.is_dir():
                print(f"Warning: Directory {d} not found or is not a directory.")
                continue
            for jsonl_path in d_path.rglob("*_detailed_results.jsonl"):
                # Skip stray/orphan folders
                if "_stray" in str(jsonl_path):
                    continue
                jsonl_files.append(str(jsonl_path))

    return sorted(set(jsonl_files))


def call_llm_judge(client, model, system_prompt, user_prompt, max_retries=3):
    """Call the LLM judge via the OpenAI-compatible client."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  API error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
    return None


def parse_judge_response(response_text):
    """Parse LLM judge response to extract the conclusion."""
    if not response_text:
        return None

    # Clean the response string from markdown formatting
    if "```json" in response_text:
        json_str = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        json_str = response_text.split("```")[1].split("```")[0].strip()
    else:
        start = response_text.find("{")
        end = response_text.rfind("}")
        if start != -1 and end != -1:
            json_str = response_text[start:end + 1]
        else:
            return None

    try:
        data = json.loads(json_str)
        conclusion = data.get("vulnerable_conclusion")
        if conclusion is None:
            conclusion = data.get("vulnerabile_conclusion")

        if conclusion not in [0, 1]:
            if str(conclusion).lower() in ["true", "1", "yes"]:
                conclusion = 1
            elif str(conclusion).lower() in ["false", "0", "no"]:
                conclusion = 0
            else:
                return None

        return {
            "vulnerable_conclusion": int(conclusion),
            "confidence": data.get("confidence", "N/A"),
            "explanation": data.get("explanation", ""),
        }
    except json.JSONDecodeError:
        return None


def build_system_prompt():
    return """You are an expert evaluator verifying the output of an AI vulnerability detection model.
The text provided to you is the FINAL TEXT CONCLUSION produced by the AI after its reasoning phase.

Your task is to determine: Did the AI conclude that the provided code IS VULNERABLE or NOT VULNERABLE?
DO NOT evaluate the vulnerability yourself. ONLY evaluate what the AI concluded in the text.

If the AI concluded the code is vulnerable (or highlighted clear security flaws as an exploit), output 1.
If the AI concluded the code is safe / no vulnerability detected, output 0.

Respond strictly with a JSON object in the following format:
{
    "vulnerable_conclusion": 1 or 0,
    "confidence": <integer from 1 to 10>,
    "explanation": "<brief 1 sentence reason explaining how you understood the AI's conclusion>"
}"""


def main():
    parser = argparse.ArgumentParser(
        description="LLM-as-a-judge to verify vulnerability parsing"
    )
    parser.add_argument("--files", nargs="+", help="Specific JSONL files to process")
    parser.add_argument(
        "--dirs",
        nargs="+",
        help="Directories to scan for *_detailed_results.jsonl",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=0,
        help="Max entries to evaluate in total (0=all)",
    )
    parser.add_argument(
        "--per-file-limit",
        type=int,
        default=0,
        help="Max entries per file (0=all). Useful for spot-checking many files.",
    )

    # Provider selection
    provider_group = parser.add_mutually_exclusive_group()
    provider_group.add_argument(
        "--google",
        action="store_true",
        help="Use Google AI Studio (Gemini). Requires GOOGLE_API_KEY env var.",
    )
    provider_group.add_argument(
        "--local",
        action="store_true",
        help="Use local Ollama instance (http://localhost:11434/v1)",
    )
    provider_group.add_argument(
        "--openai",
        action="store_true",
        help="Use OpenAI API. Requires OPENAI_API_KEY env var.",
    )

    # LLM Settings
    parser.add_argument(
        "--base-url", type=str, default="", help="Custom OpenAI-compatible base URL"
    )
    parser.add_argument(
        "--model", type=str, default="", help="Judge model name (auto-selected if omitted)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/parsing_discrepancies.csv",
        help="Output CSV path for discrepancy report",
    )

    args = parser.parse_args()

    if not args.files and not args.dirs:
        print("Please provide at least one --files or --dirs to process.")
        sys.exit(1)

    jsonl_files = find_jsonl_files(args.files, args.dirs)
    if not jsonl_files:
        print("No JSONL files found in the specified locations.")
        sys.exit(0)

    print(f"Found {len(jsonl_files)} files to check.")

    # Setup LLM Client based on provider
    if args.google:
        api_base = args.base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        api_key = os.getenv("GOOGLE_API_KEY", "")
        model = args.model or "gemini-2.5-flash"
        if not api_key:
            print("ERROR: GOOGLE_API_KEY not set. Get one from https://aistudio.google.com/apikey")
            sys.exit(1)
        print(f"Using Google AI Studio: {model}")
    elif args.local:
        api_base = args.base_url or "http://localhost:11434/v1"
        api_key = "ollama"
        model = args.model or "qwen2.5-coder:7b-instruct"
        print(f"Using local Ollama: {model}")
    elif args.openai:
        api_base = args.base_url or "https://api.openai.com/v1"
        api_key = os.getenv("OPENAI_API_KEY", "")
        model = args.model or "gpt-4.1-mini"
        if not api_key:
            print("ERROR: OPENAI_API_KEY not set.")
            sys.exit(1)
        print(f"Using OpenAI: {model}")
    else:
        # Default: OpenRouter
        api_base = args.base_url or os.getenv(
            "OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"
        )
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        model = args.model or "meta-llama/llama-3.3-70b-instruct"
        if not api_key:
            print(
                "ERROR: OPENROUTER_API_KEY not set. Use --google, --local, or --openai instead."
            )
            sys.exit(1)
        print(f"Using OpenRouter: {model}")

    client = openai.OpenAI(api_key=api_key, base_url=api_base)
    system_prompt = build_system_prompt()

    all_discrepancies = []
    processed_count = 0
    match_count = 0
    error_count = 0

    for fpath in jsonl_files:
        if args.sample_size > 0 and processed_count >= args.sample_size:
            break

        fname = os.path.basename(fpath)
        print(f"\nProcessing {fname}...")

        file_count = 0
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if args.sample_size > 0 and processed_count >= args.sample_size:
                    break
                if args.per_file_limit > 0 and file_count >= args.per_file_limit:
                    break

                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if "vuln" not in entry or "reasoning" not in entry:
                    continue

                keyword_vuln = int(entry["vuln"])
                raw_reasoning = entry["reasoning"]

                # Strip think block so LLM only judges final conclusion
                conclusion_text = strip_think_block(raw_reasoning).strip()
                if not conclusion_text:
                    continue

                # Truncate very long conclusions to save tokens
                if len(conclusion_text) > 3000:
                    conclusion_text = conclusion_text[:1500] + "\n...[truncated]...\n" + conclusion_text[-1500:]

                user_prompt = f'AI Final Conclusion Text:\n"""\n{conclusion_text}\n"""'

                response = call_llm_judge(client, model, system_prompt, user_prompt)
                parsed = parse_judge_response(response)

                if parsed:
                    judge_vuln = parsed["vulnerable_conclusion"]

                    if judge_vuln == keyword_vuln:
                        match_count += 1
                    else:
                        print(
                            f"  [MISMATCH] idx={entry.get('idx', '?')} | Parser: {keyword_vuln} vs Judge: {judge_vuln} "
                            f"(conf={parsed['confidence']})"
                        )
                        print(f"      {parsed['explanation'][:100]}")

                        discrepancy = {
                            "file": fname,
                            "idx": entry.get("idx", "?"),
                            "keyword_vuln": keyword_vuln,
                            "judge_vuln": judge_vuln,
                            "ground_truth": entry.get("ground_truth", "?"),
                            "judge_confidence": parsed["confidence"],
                            "judge_explanation": parsed["explanation"],
                        }
                        all_discrepancies.append(discrepancy)
                else:
                    error_count += 1
                    if error_count <= 5:
                        print(
                            f"  [ERR] Failed to parse judge output for idx={entry.get('idx', '?')}"
                        )

                processed_count += 1
                file_count += 1

                # Progress
                if processed_count % 50 == 0:
                    disc_rate = len(all_discrepancies) / processed_count * 100
                    print(
                        f"  ... {processed_count} processed, {len(all_discrepancies)} discrepancies ({disc_rate:.1f}%)"
                    )

                time.sleep(0.05)  # Small delay to avoid rate limiting

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    print(f"Total processed:    {processed_count}")
    print(f"Matches:            {match_count}")
    print(f"Discrepancies:      {len(all_discrepancies)}")
    print(f"Parse errors:       {error_count}")
    if processed_count > 0:
        print(f"Discrepancy rate:   {len(all_discrepancies)/processed_count*100:.1f}%")

    if all_discrepancies:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "file",
                    "idx",
                    "keyword_vuln",
                    "judge_vuln",
                    "ground_truth",
                    "judge_confidence",
                    "judge_explanation",
                ],
            )
            writer.writeheader()
            writer.writerows(all_discrepancies)
        print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()
