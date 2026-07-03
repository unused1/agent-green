"""Budget-matched single-agent vulnerability-detection baselines (Item 5 / RA1).

Tests whether DA/MA gains are attributable to collaboration or merely to a larger
inference budget, by spending DA/MA's *call budget* on a SINGLE agent — no role
differentiation:

  MODE=self_revision  N_CALLS=2   -> initial answer + 1 self-revision  (matches DA)
  MODE=self_revision  N_CALLS=4   -> initial answer + 3 self-revisions (matches MA)
  MODE=best_of_n      N_CALLS=4   -> 4 independent samples + majority vote (matches MA)

Mirrors src/single_agent_vuln_detection.py (config selection, vLLM/autogen client,
CodeCarbon, resume, output format). The final `vuln` label is parsed with the
canonical parser. Each record stores the full trajectory (per-round/per-sample
verdict + response) so token budgets can be computed post-hoc and any aggregation
re-run without re-inference.

Usage:
  MODEL_FAMILY=nemotron MODE=self_revision N_CALLS=4 ENABLE_REASONING=false \\
    EXP_NAME=SA-selfrev4_super49b_instruct \\
    python src/single_agent_budget_vuln.py SA-zero
"""

import os
import sys
import json
import copy
from datetime import datetime

_model_family = os.getenv("MODEL_FAMILY", "").lower()
if _model_family == "deepseek":
    import config_deepseek as config
elif _model_family == "nemotron":
    import config_nemotron as config
else:
    import config
from autogen import AssistantAgent  # noqa: E402
from codecarbon import OfflineEmissionsTracker  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vuln_parser import parse_na_sa  # noqa: E402

# --- Budget config ---
MODE = os.getenv("MODE", "self_revision").lower()          # self_revision | best_of_n
N_CALLS = int(os.getenv("N_CALLS", "2"))                    # LLM calls per sample
BON_TEMPERATURE = float(os.getenv("BEST_OF_N_TEMPERATURE", "0.7"))
assert MODE in ("self_revision", "best_of_n"), f"bad MODE={MODE}"

REVISE_PROMPT = (
    "Review your vulnerability analysis above. Check for any errors, overlooked edge "
    "cases, or incorrect assumptions. If your assessment holds, restate it; otherwise "
    "revise it. Give your final determination in the same format (a clear YES/NO on "
    "whether the code is vulnerable, with reasoning)."
)

# --- Base config (mirrors single_agent_vuln_detection.py) ---
llm_config = copy.deepcopy(config.LLM_CONFIG)
if MODE == "best_of_n":
    # Independent samples need diversity; the primary runs use temperature 0.
    llm_config["temperature"] = BON_TEMPERATURE
    for c in llm_config.get("config_list", []):
        c["temperature"] = BON_TEMPERATURE

task = config.VULNERABILITY_TASK_PROMPT
sys_prompt = config.SYS_MSG_VULNERABILITY_DETECTOR_ZERO_SHOT
if _model_family == "nemotron" and hasattr(config, "prepend_thinking_toggle"):
    sys_prompt = config.prepend_thinking_toggle(sys_prompt)
    print(f"[Nemotron] thinking toggle ENABLE_REASONING={config.ENABLE_REASONING}")

DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR

DESIGN = sys.argv[1] if len(sys.argv) > 1 else "SA-zero"
model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
exp_name = os.getenv("EXP_NAME") or f"SA-budget-{MODE}{N_CALLS}_{model}_{datetime.now():%Y%m%d-%H%M%S}"
print(f"[budget] MODE={MODE} N_CALLS={N_CALLS} exp={exp_name}")


def load_dataset(path):
    out = []
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            if "func" in d and "target" in d:
                out.append(d)
    return out


def reply_text(agent, messages):
    r = agent.generate_reply(messages=messages)
    if isinstance(r, dict):
        return (r.get("content") or "").strip()
    return (r or "").strip() if isinstance(r, str) else ""


def run_self_revision(agent, func):
    """Initial answer + (N_CALLS-1) self-revision rounds; final round is the label."""
    msgs = [{"content": task.format(code=func), "role": "user"}]
    rounds = []
    for k in range(N_CALLS):
        if k > 0:
            msgs.append({"content": REVISE_PROMPT, "role": "user"})
        text = reply_text(agent, msgs)
        msgs.append({"content": text, "role": "assistant"})
        v, _ = parse_na_sa(text)
        rounds.append({"round": k + 1, "vuln": v, "response": text})
    final = rounds[-1]
    return final["vuln"], final["response"], rounds


def run_best_of_n(agent, func):
    """N_CALLS independent samples; majority vote (ties -> vulnerable)."""
    samples = []
    for k in range(N_CALLS):
        text = reply_text(agent, [{"content": task.format(code=func), "role": "user"}])
        v, _ = parse_na_sa(text)
        samples.append({"sample": k + 1, "vuln": v, "response": text})
    n1 = sum(1 for s in samples if s["vuln"] == 1)
    final_v = 1 if n1 >= (len(samples) - n1) else 0
    # representative reasoning: first sample matching the majority verdict
    rep = next((s["response"] for s in samples if s["vuln"] == final_v), samples[0]["response"])
    return final_v, rep, samples


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)
    samples = load_dataset(DATASET_FILE)
    print(f"Loaded {len(samples)} samples from {DATASET_FILE}")

    detailed_file = os.path.join(RESULT_DIR, f"{exp_name}_detailed_results.jsonl")
    energy_file = os.path.join(RESULT_DIR, f"{exp_name}_energy_tracking.json")

    done = set()
    if os.path.exists(detailed_file):
        for line in open(detailed_file):
            if line.strip():
                done.add(json.loads(line)["idx"])
    remaining = [s for s in samples if s.get("idx") not in done]
    print(f"Resuming: {len(done)} done, {len(remaining)} remaining")

    energy = {"total_emissions": 0.0, "sessions": 0}
    if os.path.exists(energy_file):
        energy = json.load(open(energy_file))

    tracker = OfflineEmissionsTracker(
        project_name=f"{exp_name}_session_{energy['sessions'] + 1}",
        output_dir=RESULT_DIR, country_iso_code="CAN", save_to_file=True)
    tracker.start()
    try:
        agent = AssistantAgent(name="budget_detector", system_message=sys_prompt,
                               llm_config=llm_config, human_input_mode="NEVER")
        for i, s in enumerate(remaining):
            if MODE == "self_revision":
                vuln, reasoning, traj = run_self_revision(agent, s["func"])
            else:
                vuln, reasoning, traj = run_best_of_n(agent, s["func"])
            rec = {
                "idx": s.get("idx"), "project": s.get("project"),
                "commit_id": s.get("commit_id"), "project_url": s.get("project_url"),
                "commit_url": s.get("commit_url"), "commit_message": s.get("commit_message"),
                "ground_truth": s["target"], "vuln": vuln, "reasoning": reasoning,
                "cwe": s.get("cwe"), "cve": s.get("cve"), "cve_desc": s.get("cve_desc"),
                "budget_mode": MODE, "n_calls": N_CALLS, "trajectory": traj,
            }
            with open(detailed_file, "a") as f:
                f.write(json.dumps(rec) + "\n")
            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{len(remaining)} (idx {s.get('idx')} -> vuln={vuln})")
    finally:
        em = tracker.stop()
        energy["total_emissions"] += em
        energy["sessions"] += 1
        json.dump(energy, open(energy_file, "w"), indent=2)
        print(f"Session emissions: {em:.6f} kg CO2; total {energy['total_emissions']:.6f}")
    print(f"Done -> {detailed_file}")


if __name__ == "__main__":
    main()
