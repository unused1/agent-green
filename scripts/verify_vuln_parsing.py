#!/usr/bin/env python3
"""
LLM-as-a-judge verification script for vulnerability parsing.

This script feeds the final conclusion text (with <think> tags stripped) of a vulnerability 
detection model to a Judge LLM and asks it to determine if the model concluded the code is 
vulnerable or not. It then compares the Judge LLM's understanding with the keyword parser's 
outcome (`vuln` field) to find potential parsing errors.

Usage:
    # Run on specific files or directories with OpenRouter
    python scripts/verify_vuln_parsing.py --dirs results/run1 results/run2
    
    # Run using local Ollama instance
    python scripts/verify_vuln_parsing.py --local --dirs results/SA_runs --model qwen2.5-coder:7b-instruct
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

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
    
    # Add explicitly specified files
    if files_arg:
        for f in files_arg:
            if os.path.exists(f) and f.endswith(".jsonl"):
                jsonl_files.append(f)
                
    # Search specified directories
    if dirs_arg:
        for d in dirs_arg:
            d_path = Path(d)
            if not d_path.exists() or not d_path.is_dir():
                print(f"Warning: Directory {d} not found or is not a directory.")
                continue
            for jsonl_path in d_path.rglob("*_detailed_results.jsonl"):
                jsonl_files.append(str(jsonl_path))
                
    # Deduplicate
    return list(set(jsonl_files))


def call_llm_judge(client, model, system_prompt, user_prompt, max_retries=3):
    """Call the LLM judge via the OpenAI compatible client."""
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
                response_format={"type": "json_object"} if "openrouter" not in str(client.base_url).lower() else None
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
        # Check if the string starts properly with {
        start = response_text.find("{")
        end = response_text.rfind("}")
        if start != -1 and end != -1:
            json_str = response_text[start:end+1]
        else:
            return None

    try:
        data = json.loads(json_str)
        # Handle variations of key names the LLM might use
        conclusion = data.get("vulnerable_conclusion")
        if conclusion is None:
            conclusion = data.get("vulnerabile_conclusion")
            
        if conclusion not in [0, 1]:
            # Convert string booleans if necessary
            if str(conclusion).lower() in ["true", "1", "yes"]:
                conclusion = 1
            elif str(conclusion).lower() in ["false", "0", "no"]:
                conclusion = 0
            else:
                return None
                
        return {
            "vulnerable_conclusion": int(conclusion),
            "confidence": data.get("confidence", "N/A"),
            "explanation": data.get("explanation", "")
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
    parser = argparse.ArgumentParser(description="LLM-as-a-judge to verify vulnerability parsing")
    parser.add_argument("--files", nargs="+", help="Specific JSONL files to process")
    parser.add_argument("--dirs", nargs="+", help="Directories to scan for *_detailed_results.jsonl")
    parser.add_argument("--sample-size", type=int, default=0, help="Max entries to evaluate across all files")
    
    # LLM Settings
    parser.add_argument("--local", action="store_true", help="Use local Ollama instance (http://localhost:11434/v1)")
    parser.add_argument("--base-url", type=str, default="", help="Custom OpenAI-compatible base URL")
    parser.add_argument("--model", type=str, default="meta-llama/llama-3.3-70b-instruct", help="Judge model name")
    
    args = parser.parse_args()

    if not args.files and not args.dirs:
        print("Please provide at least one --files or --dirs to process.")
        sys.exit(1)

    jsonl_files = find_jsonl_files(args.files, args.dirs)
    if not jsonl_files:
        print("No JSONL files found in the specified locations.")
        sys.exit(0)

    print(f"Found {len(jsonl_files)} files to check.")

    # Setup LLM Client
    if args.local:
        api_base = args.base_url or "http://localhost:11434/v1"
        api_key = "ollama"
        model = args.model if args.model != "meta-llama/llama-3.3-70b-instruct" else "qwen2.5-coder:7b-instruct"
        print(f"Using local inference: {api_base} with model {model}")
    else:
        api_base = args.base_url or os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        model = args.model
        if not api_key:
            print("ERROR: OPENROUTER_API_KEY not set for remote inference. Use --local for Ollama.")
            sys.exit(1)
        print(f"Using OpenRouter: {model}")

    client = openai.OpenAI(api_key=api_key, base_url=api_base)
    system_prompt = build_system_prompt()
    
    all_discrepancies = []
    processed_count = 0
    match_count = 0

    for fpath in jsonl_files:
        if args.sample_size > 0 and processed_count >= args.sample_size:
            break
            
        print(f"\nProcessing {os.path.basename(fpath)}...")
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if args.sample_size > 0 and processed_count >= args.sample_size:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if "vuln" not in entry or "reasoning" not in entry:
                    # Looking specifically for parsed entries
                    continue
                
                keyword_vuln = entry["vuln"]
                raw_reasoning = entry["reasoning"]
                
                # IMPORTANT: Strip think block so LLM only judges final conclusion
                conclusion_text = strip_think_block(raw_reasoning).strip()
                if not conclusion_text:
                    continue

                user_prompt = f"AI Final Conclusion Text:\n\"\"\"\n{conclusion_text}\n\"\"\""
                
                response = call_llm_judge(client, model, system_prompt, user_prompt)
                parsed = parse_judge_response(response)
                
                if parsed:
                    judge_vuln = parsed["vulnerable_conclusion"]
                    
                    if judge_vuln == keyword_vuln:
                        match_count += 1
                        print(f"  [OK] idx={entry.get('idx', '?')} - Both parsed ({keyword_vuln})")
                    else:
                        print(f"  [DISCREPANCY] idx={entry.get('idx', '?')} | Keyword: {keyword_vuln} vs Judge: {judge_vuln}")
                        print(f"      Explanation: {parsed['explanation']}")
                        
                        discrepancy = {
                            "file": os.path.basename(fpath),
                            "idx": entry.get("idx", "?"),
                            "keyword_vuln": keyword_vuln,
                            "judge_vuln": judge_vuln,
                            "ground_truth": entry.get("ground_truth", "?"),
                            "judge_confidence": parsed["confidence"],
                            "judge_explanation": parsed["explanation"],
                            "conclusion_text": conclusion_text
                        }
                        all_discrepancies.append(discrepancy)
                else:
                    print(f"  [ERR] Failed to parse judge output for idx={entry.get('idx', '?')}")
                    
                processed_count += 1
                time.sleep(0.1) # Small delay to avoid aggressive rate limiting locally

    print("\n" + "="*50)
    print("VERIFICATION COMPLETE")
    print("="*50)
    print(f"Total processed: {processed_count}")
    print(f"Matches: {match_count}")
    print(f"Discrepancies found: {len(all_discrepancies)}")
    
    if all_discrepancies:
        report_path = "parsing_discrepancies.csv"
        with open(report_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "file", "idx", "keyword_vuln", "judge_vuln", "ground_truth",
                "judge_confidence", "judge_explanation", "conclusion_text"
            ])
            writer.writeheader()
            writer.writerows(all_discrepancies)
        print(f"Report saved to: {report_path}")

if __name__ == "__main__":
    main()
