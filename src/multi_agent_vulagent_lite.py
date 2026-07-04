"""VulAgent-lite — role-sensitivity variant for Item 9 (RA7).

A materially different multi-agent role/coordination scheme from our VulTrial-style
MA (adversarial role debate). Anchored on VulAgent (arXiv 2509.11523):
perspective-specialist detection -> aggregation -> validation, implemented with LLM
calls only (no Joern static analysis).

Pipeline per function (6 LLM calls):
  4 perspective specialists (memory / input-injection / resource-logic / auth-crypto)
  -> Aggregator (merge + de-duplicate candidates)
  -> Validator (retain/discard; final VERDICT line -> label)

Context-safe by design (unlike the accumulating VulTrial-MA group chat): each stage
is a DISCRETE call, and <think> traces are STRIPPED between stages, so no call
carries the whole pipeline history. Full trajectory stored for re-aggregation.

Usage:
  MODEL_FAMILY=nemotron ENABLE_REASONING=false \\
    EXP_NAME=VulAgentLite_super49b_instruct \\
    python src/multi_agent_vulagent_lite.py
"""

import os
import sys
import re
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
from vuln_parser import strip_think_block, parse_na_sa  # noqa: E402

llm_config = copy.deepcopy(config.LLM_CONFIG)
DATASET_FILE = config.VULN_DATASET
RESULT_DIR = config.RESULT_DIR
model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
exp_name = os.getenv("EXP_NAME") or f"VulAgentLite_{model}_{datetime.now():%Y%m%d-%H%M%S}"

# --- Role definitions ---
SPECIALISTS = {
    "memory": "memory-safety (buffer overflow, out-of-bounds read/write, use-after-free, "
              "null-pointer dereference, uninitialised memory)",
    "input_injection": "input-validation and injection (command/SQL injection, format-string, "
                       "integer overflow/underflow causing unsafe sizes, unchecked untrusted input)",
    "resource_logic": "resource and error-handling (memory/resource leaks, double-free, missing "
                      "error checks, race conditions, improper cleanup)",
    "auth_crypto": "authentication, authorization, and cryptography (broken access control, "
                   "privilege errors, unsafe file permissions, weak or misused cryptography)",
}

SPECIALIST_SYS = (
    "You are a security specialist focused on {desc} vulnerabilities in C/C++ code. "
    "Analyse the provided function ONLY from this perspective and CONSERVATIVELY MAXIMISE "
    "RECALL: flag ANY potential or suspected issue of this class, including low-confidence "
    "ones — a later validation stage will filter false positives, so prefer over-reporting to "
    "missing a real issue. In particular, flag risks that depend on the caller or external "
    "state (e.g. a pointer that may already be freed, a size that may be attacker-controlled). "
    "Report each potential issue as a numbered finding with (a) the specific concern, (b) the "
    "code location, and (c) the condition under which it could be exploited. Respond with "
    "exactly 'NO FINDINGS' ONLY if you are confident there is genuinely nothing of this class. "
    "Do not comment on vulnerability classes outside your specialty."
)
AGGREGATOR_SYS = (
    "You are a triage lead. You will receive vulnerability findings from several specialist "
    "analysts for the same C/C++ function. Merge and de-duplicate them into a single consolidated "
    "list of distinct candidate vulnerabilities; for each give the issue, its location, and the "
    "strongest supporting evidence. Preserve every distinct candidate; drop only exact duplicates. "
    "If there are no findings, respond with exactly 'NO CANDIDATES'."
)
VALIDATOR_SYS = (
    "You are a senior security reviewer making the final call, and you are deliberately STRICT: on "
    "real code most flagged candidates are false alarms, and your job is to filter them out. Mark a "
    "candidate VALID only if you can point to CONCRETE evidence IN THIS FUNCTION that (a) the "
    "vulnerable operation is genuinely reachable with attacker-influenced input, and (b) there is NO "
    "check, bound, guard, length/null test, or early return in the code that prevents it. Mark it "
    "INVALID if it relies on unstated assumptions about callers or external state that the function "
    "itself does not establish, if a plausible guard is present, or if the evidence is speculative. "
    "When genuinely in doubt, mark INVALID. For each candidate, state VALID or INVALID with a one-line "
    "justification that cites the specific code. Then output a final line exactly as "
    "'VERDICT: VULNERABLE' if at least one candidate is VALID, otherwise 'VERDICT: NOT VULNERABLE'."
)


def make_sys(text):
    if _model_family == "nemotron" and hasattr(config, "prepend_thinking_toggle"):
        return config.prepend_thinking_toggle(text)
    return text


def make_agent(name, sys_text):
    return AssistantAgent(name=name, system_message=make_sys(sys_text),
                          llm_config=llm_config, human_input_mode="NEVER")


def reply(agent, user_msg):
    r = agent.generate_reply(messages=[{"content": user_msg, "role": "user"}])
    text = (r.get("content") if isinstance(r, dict) else r) or ""
    return strip_think_block(text.strip())  # never pass reasoning traces downstream


def parse_verdict(text):
    m = re.search(r"verdict\s*[:\-]?\s*\**\s*(not\s+vulnerable|vulnerable)", text, re.I)
    if m:
        return 0 if "not" in m.group(1).lower() else 1
    v, _ = parse_na_sa(text)  # fallback to canonical text parser
    return v


def run_pipeline(specialists, aggregator, validator, code):
    findings = {}
    for name, ag in specialists.items():
        findings[name] = reply(ag, f"Analyse this C/C++ function for {SPECIALISTS[name]} "
                                   f"vulnerabilities:\n\n{code}")
    findings_text = "\n\n".join(f"[{n} specialist]\n{f}" for n, f in findings.items())
    candidates = reply(aggregator, f"Function:\n{code}\n\nSpecialist findings:\n{findings_text}")
    validation = reply(validator, f"Function:\n{code}\n\nCandidate vulnerabilities:\n{candidates}")
    vuln = parse_verdict(validation)
    n_calls = len(specialists) + 2
    traj = {"findings": findings, "candidates": candidates, "validation": validation}
    return vuln, validation, traj, n_calls


def load_dataset(path):
    out = []
    with open(path) as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                if "func" in d and "target" in d:
                    out.append(d)
    return out


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)
    samples = load_dataset(DATASET_FILE)
    print(f"[vulagent-lite] exp={exp_name}  loaded {len(samples)} samples")

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
        specialists = {name: make_agent(f"{name}_specialist", SPECIALIST_SYS.format(desc=SPECIALISTS[name]))
                       for name in SPECIALISTS}
        aggregator = make_agent("aggregator", AGGREGATOR_SYS)
        validator = make_agent("validator", VALIDATOR_SYS)

        for i, s in enumerate(remaining):
            try:
                vuln, validation, traj, n_calls = run_pipeline(specialists, aggregator, validator, s["func"])
            except Exception as e:  # noqa: BLE001 — skip-and-continue on per-sample failure
                print(f"[skip] idx {s.get('idx')}: {e}")
                vuln, validation, traj, n_calls = -1, f"SKIPPED: {e}", {}, 0
            rec = {
                "idx": s.get("idx"), "project": s.get("project"),
                "commit_id": s.get("commit_id"), "project_url": s.get("project_url"),
                "commit_url": s.get("commit_url"), "commit_message": s.get("commit_message"),
                "ground_truth": s["target"], "vuln": vuln, "reasoning": validation,
                "cwe": s.get("cwe"), "cve": s.get("cve"), "cve_desc": s.get("cve_desc"),
                "design_variant": "vulagent_lite", "n_calls": n_calls,
                "skipped": vuln == -1, "full_discussion": traj,
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
