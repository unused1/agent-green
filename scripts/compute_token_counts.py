#!/usr/bin/env python3
"""Compute accurate BPE token counts for all VulTrial-870 configs.

Uses model-specific tokenizers:
- Qwen3: Qwen/Qwen3-4B tokenizer (shared across 4B and 30B)
- Nemotron: nvidia/Llama-3.1-Nemotron-Nano-8B-v1 tokenizer (Llama-based, shared across 8B and 49B)

Computes both input tokens (system prompt + task prompt + source code) and
output tokens (all agent response fields).
"""

import json
import glob
import sys
import os
import csv

csv.field_size_limit(sys.maxsize)

import pandas as pd
from transformers import AutoTokenizer

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(PROJECT_ROOT, "results")

# Rate for cost calculation
RUNPOD_H100_RATE = 2.69  # USD/GPU-hr

print("Loading tokenizers...")
QWEN_TOK = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B", trust_remote_code=True)
NEM_TOK = AutoTokenizer.from_pretrained("nvidia/Llama-3.1-Nemotron-Nano-8B-v1", trust_remote_code=True)
print(f"  Qwen3 vocab: {QWEN_TOK.vocab_size}")
print(f"  Nemotron vocab: {NEM_TOK.vocab_size}")


def get_tokenizer(model_name):
    if "Nemotron" in model_name:
        return NEM_TOK
    return QWEN_TOK


def count_output_tokens(rec, tokenizer):
    """Count BPE tokens across all output fields (excluding metadata)."""
    skip_keys = {"idx", "project", "commit_id", "project_url", "commit_url",
                 "commit_message", "ground_truth", "target", "cwe", "cve",
                 "cve_desc", "vuln", "func", "file_hash", "file_name",
                 "nvd_url", "timestamp", "session"}
    total = 0
    for k, v in rec.items():
        if k in skip_keys:
            continue
        if isinstance(v, str) and v.strip():
            total += len(tokenizer.encode(v))
        elif isinstance(v, dict):
            for v2 in v.values():
                if isinstance(v2, str) and v2.strip():
                    total += len(tokenizer.encode(v2))
    return total


def _load_config_prompts():
    """Load actual prompt templates from config.py."""
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
    import config as qwen_config
    return {
        # NA/SA system messages
        "sys_zero": qwen_config.SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT,
        "sys_few": qwen_config.SYS_MSG_VULNERABILITY_DETECTOR_FEW_SHOT,
        "task": qwen_config.VULNERABILITY_TASK_PROMPT,
        # DA system messages + task templates
        "da_author_sys_zero": qwen_config.SYS_MSG_CODE_AUTHOR_DUAL_ZERO_SHOT,
        "da_author_sys_few": qwen_config.SYS_MSG_CODE_AUTHOR_DUAL_FEW_SHOT,
        "da_analyst_sys_zero": qwen_config.SYS_MSG_SECURITY_ANALYST_ZERO_SHOT,
        "da_analyst_sys_few": qwen_config.SYS_MSG_SECURITY_ANALYST_FEW_SHOT,
        "da_task_submission": qwen_config.DUAL_AGENT_TASK_CODE_SUBMISSION,
        "da_task_final": qwen_config.DUAL_AGENT_TASK_FINAL_DECISION,
        "da_emphasis": qwen_config.DUAL_AGENT_ANALYST_EMPHASIS_WRAPPER,
        # MA system messages + task templates
        "ma_researcher_sys_zero": qwen_config.SYS_MSG_SECURITY_RESEARCHER_ZERO_SHOT,
        "ma_researcher_sys_few": qwen_config.SYS_MSG_SECURITY_RESEARCHER_FEW_SHOT,
        "ma_author_sys_zero": qwen_config.SYS_MSG_CODE_AUTHOR_ZERO_SHOT,
        "ma_author_sys_few": qwen_config.SYS_MSG_CODE_AUTHOR_FEW_SHOT,
        "ma_moderator_sys_zero": qwen_config.SYS_MSG_MODERATOR_ZERO_SHOT,
        "ma_moderator_sys_few": qwen_config.SYS_MSG_MODERATOR_FEW_SHOT,
        "ma_board_sys_zero": qwen_config.SYS_MSG_REVIEW_BOARD_ZERO_SHOT,
        "ma_board_sys_few": qwen_config.SYS_MSG_REVIEW_BOARD_FEW_SHOT,
        "ma_task_researcher": qwen_config.MULTI_AGENT_TASK_SECURITY_RESEARCHER,
        "ma_task_author": qwen_config.MULTI_AGENT_TASK_CODE_AUTHOR,
        "ma_task_moderator": qwen_config.MULTI_AGENT_TASK_MODERATOR,
        "ma_task_review": qwen_config.MULTI_AGENT_TASK_REVIEW_BOARD,
    }


PROMPTS = None


def count_input_tokens(rec, design, mode, prompting, tokenizer):
    """Count exact input tokens by reconstructing the full prompt per design.

    For multi-turn designs (DA/MA), sums input tokens across all turns,
    where each turn's input includes the prior turn's output.
    """
    global PROMPTS
    if PROMPTS is None:
        PROMPTS = _load_config_prompts()

    code = rec.get("func", "")
    shot = "few" if prompting == "few-shot" else "zero"

    # Nemotron thinking prefix
    think_prefix = ""
    if "Nemotron" in str(rec.get("model", "")) or mode == "thinking":
        # Only add for Nemotron models — Qwen uses API param
        pass  # We don't know model at this point, handled below

    def tok_len(text):
        return len(tokenizer.encode(text)) if text else 0

    if design in ("NoAgent", "SA"):
        # Single turn: system_msg + task_prompt(code)
        sys_msg = PROMPTS[f"sys_{shot}"]
        task = PROMPTS["task"].format(code=code)
        return tok_len(sys_msg) + tok_len(task)

    elif design == "DA":
        # Turn 1: Code Author — sys_msg + code_submission(code)
        author_sys = PROMPTS[f"da_author_sys_{shot}"]
        author_task = PROMPTS["da_task_submission"].format(code=code)

        # Turn 2: Security Analyst — sys_msg + emphasis_wrapper(final_decision(code, author_response))
        analyst_sys = PROMPTS[f"da_analyst_sys_{shot}"]
        # Author response from JSONL
        author_resp = ""
        disc = rec.get("discussion", {})
        if isinstance(disc, dict):
            author_resp = disc.get("author_submission", "")
        base_task = PROMPTS["da_task_final"].format(code=code, author_response=author_resp)
        analyst_task = PROMPTS["da_emphasis"].format(analyst_task=base_task)

        turn1_input = tok_len(author_sys) + tok_len(author_task)
        turn2_input = tok_len(analyst_sys) + tok_len(analyst_task)
        return turn1_input + turn2_input

    elif design == "MA":
        # Turn 1: Security Researcher — sys_msg + task(code)
        researcher_sys = PROMPTS[f"ma_researcher_sys_{shot}"]
        researcher_task = PROMPTS["ma_task_researcher"].format(code=code)

        # Get agent outputs from JSONL
        fd = rec.get("full_discussion", {})
        if isinstance(fd, dict):
            researcher_resp = fd.get("security_researcher", "")
            author_resp = fd.get("code_author", "")
            moderator_resp = fd.get("moderator", "")
        else:
            researcher_resp = author_resp = moderator_resp = ""

        # Turn 2: Code Author — sys_msg + task(researcher_findings, code)
        author_sys = PROMPTS[f"ma_author_sys_{shot}"]
        author_task = PROMPTS["ma_task_author"].format(
            researcher_findings=researcher_resp, code=code)

        # Turn 3: Moderator — sys_msg + task(researcher_findings, author_response)
        mod_sys = PROMPTS[f"ma_moderator_sys_{shot}"]
        mod_task = PROMPTS["ma_task_moderator"].format(
            researcher_findings=researcher_resp, author_response=author_resp)

        # Turn 4: Review Board — sys_msg + task(moderator_summary, code, researcher, author)
        board_sys = PROMPTS[f"ma_board_sys_{shot}"]
        board_task = PROMPTS["ma_task_review"].format(
            moderator_summary=moderator_resp, code=code,
            researcher_findings=researcher_resp, author_response=author_resp)

        turn1 = tok_len(researcher_sys) + tok_len(researcher_task)
        turn2 = tok_len(author_sys) + tok_len(author_task)
        turn3 = tok_len(mod_sys) + tok_len(mod_task)
        turn4 = tok_len(board_sys) + tok_len(board_task)
        return turn1 + turn2 + turn3 + turn4

    return 0


def find_jsonl_files(design, model_name, mode, prompting):
    """Find matching JSONL files across 486 and 384-incr."""
    model_patterns = {
        "Nemotron-Nano-8B": "Nemotron-Nano-8B",
        "Nemotron-Super-49B": "Nemotron-Super-49B",
        "Qwen3-4B-Instruct": "Qwen3-4B-Instruct",
        "Qwen3-4B-Thinking": "Qwen3-4B-Thinking",
        "Qwen3-30B-A3B-Instruct": "Qwen3-30B-A3B-Instruct",
        "Qwen3-30B-A3B-Thinking": "Qwen3-30B-A3B-Thinking",
    }
    mp = model_patterns.get(model_name, model_name)

    design_prefixes = {
        "NoAgent": ["NA-vuln"],
        "SA": ["Sa-zero", "Sa-few"],
        "DA": ["DA-vuln-two"],
        "MA": ["MA-vuln-four"],
    }
    prefixes = design_prefixes.get(design, [design])
    shot = "zero_shot" if prompting == "zero-shot" else "few_shot"

    files = []
    for d in ["runpod_vuln_486", "runpod_vuln_384_incremental"]:
        dir_path = os.path.join(BASE, d)
        if not os.path.exists(dir_path):
            continue
        for f in sorted(glob.glob(os.path.join(dir_path, "*_detailed_results.jsonl"))):
            fname = os.path.basename(f)
            if "_conservative_" in fname or "_strict_" in fname:
                continue
            if not any(fname.startswith(p) for p in prefixes):
                continue
            if design == "SA":
                if prompting == "zero-shot" and not fname.startswith("Sa-zero"):
                    continue
                if prompting == "few-shot" and not fname.startswith("Sa-few"):
                    continue
            else:
                if shot not in fname:
                    continue
            if mp not in fname:
                continue
            if "Nemotron" in model_name:
                is_think = "_thinking_" in fname
                if mode == "thinking" and not is_think:
                    continue
                if mode == "instruct" and is_think:
                    continue
            files.append(f)
    return files


def main():
    em = pd.read_csv(os.path.join(PROJECT_ROOT, "results", "consolidated_emissions.csv"))
    v870 = em[em["dataset"] == "VulTrial-870"].copy()
    print(f"\nConfigs: {len(v870)}")

    rows = []
    for _, r in v870.iterrows():
        design = r["design"]
        model = r["model"]
        mode = r["mode"]
        prompting = r["prompting"]
        tokenizer = get_tokenizer(model)

        files = find_jsonl_files(design, model, mode, prompting)
        if not files:
            print(f"  WARNING: No files for {design} {model} {mode} {prompting}")
            continue

        # Load records (dedup by idx)
        seen = set()
        total_input = 0
        total_output = 0
        count = 0

        for f in files:
            with open(f) as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    idx = rec.get("idx")
                    if idx is None or int(idx) in seen:
                        continue
                    seen.add(int(idx))

                    total_input += count_input_tokens(rec, design, mode, prompting, tokenizer)
                    total_output += count_output_tokens(rec, tokenizer)
                    count += 1

        avg_input = round(total_input / count) if count else 0
        avg_output = round(total_output / count) if count else 0

        # Cost
        gpu_count = int(r.get("gpu_count", 1)) if pd.notna(r.get("gpu_count")) else 1
        cost = r["duration_hours"] * gpu_count * RUNPOD_H100_RATE

        rows.append({
            "design": design, "model": model, "mode": mode, "prompting": prompting,
            "duration_hours": round(r["duration_hours"], 1),
            "energy_kwh": round(r["total_energy_kwh"], 2),
            "avg_input_tokens": avg_input,
            "avg_output_tokens": avg_output,
            "avg_total_tokens": avg_input + avg_output,
            "cost_usd": round(cost, 1),
            "samples": count,
        })
        print(f"  {design:8s} {model:30s} {mode:10s} {prompting:10s} "
              f"in={avg_input} out={avg_output} total={avg_input+avg_output} ${cost:.1f}")

    df = pd.DataFrame(rows).sort_values(["design", "model", "mode", "prompting"])

    # Summary by design x mode
    print(f"\n{'='*80}")
    print("SUMMARY (mean across 8 configs per cell)")
    print(f"{'='*80}")
    for design in ["NoAgent", "SA", "DA", "MA"]:
        for mode in ["instruct", "thinking"]:
            sub = df[(df["design"] == design) & (df["mode"] == mode)]
            print(f"  {design:8s} {mode:10s}: "
                  f"in={sub['avg_input_tokens'].mean():.0f} "
                  f"out={sub['avg_output_tokens'].mean():.0f} "
                  f"total={sub['avg_total_tokens'].mean():.0f} "
                  f"dur={sub['duration_hours'].mean():.1f}h "
                  f"${sub['cost_usd'].mean():.1f}")

    out_path = os.path.join(PROJECT_ROOT, "results", "rq3_baseline", "cost_analysis_870_bpe.csv")
    df.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
