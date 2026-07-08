# Method designs — budget-matched single-agent baselines (Item 5) and VulAgent-lite (Item 9)

This note describes what each of the four new configurations actually does, so the
results can be interpreted. All are run on the pair-preserving VulTrial-386 set,
zero-shot, in both instruct and thinking modes, on Nemotron-Super-49B and
Qwen3-30B. Implementation: `src/single_agent_budget_vuln.py` (Item 5) and
`src/multi_agent_vulagent_lite.py` (Item 9).

## Why these configurations exist (the research questions)

- **Item 5 — budget-matched single-agent baselines.** The dual- and multi-agent
  designs (DA, MA) make more LLM calls per sample than a plain single agent (SA),
  so any accuracy difference could be a *compute* effect (more calls) rather than a
  *coordination* effect (agents working together). Item 5 gives **one** agent the
  **same call budget** as DA/MA, spent via two standard test-time-compute
  strategies — **sequential self-critique** (self-revision) and **parallel
  sampling + voting** (best-of-N). If a budget-matched single agent matches DA/MA,
  the multi-agent advantage is largely compute, not coordination.
- **Item 9 — VulAgent-lite (role sensitivity).** Our primary MA is an adversarial
  *role-debate* design. VulAgent-lite is a **different** multi-agent scheme —
  division of labour by vulnerability class, then aggregation and validation — to
  test whether MA behaviour is sensitive to the specific role/coordination design.

## Shared single-agent base (Item 5)

All three budget methods reuse the **same** model, system prompt, task prompt,
dataset, and output parser as the plain SA vulnerability detector. They differ
**only** in how the call budget is used. The final 0/1 label is parsed from the
model text with the canonical parser (`parse_na_sa`). Self-revision runs at
temperature 0 (deterministic); best-of-N uses temperature 0.7 (for sample
diversity).

### Rev2 / Rev4 — self-revision (sequential self-critique)

The agent produces an initial analysis, then performs **N − 1 revision rounds**.
Each round shows the model its own previous answer and asks it to *review the
analysis for errors, overlooked edge cases, or wrong assumptions; restate the
determination if it holds, otherwise revise it* — always returning a clear
YES/NO verdict.

- **Rev2** = 2 calls (initial + 1 revision) — matches the **DA** 2-call budget.
- **Rev4** = 4 calls (initial + 3 revisions) — matches the **MA** 4-call budget.
- The **final label is the last round's verdict.**
- Only the communicated answer is fed back between rounds (any `<think>` block is
  stripped), so the revision acts on the prior conclusion — and, in thinking mode,
  long reasoning traces do not accumulate and overflow the context.

*Idea being tested:* does letting a single agent iteratively critique and refine
its own answer improve it, at the same cost as DA/MA?

### Bon4 — best-of-4 (parallel self-consistency)

The agent answers the **same** prompt **4 independent times** (no conversation,
no revision) at temperature 0.7 for diversity. The **final label is the majority
vote** across the four samples (ties resolve to *vulnerable*). The stored reasoning
is the first sample that agrees with the majority.

- **Bon4** = 4 calls — matches the **MA** 4-call budget.

*Idea being tested:* does sampling several independent answers and voting
(self-consistency) improve a single agent, at the same cost as MA?

## VulAgent-lite (Item 9) — perspective specialists → aggregation → validation

A multi-agent pipeline with a **different role structure** from the VulTrial-style
adversarial debate, anchored on VulAgent (arXiv 2509.11523). It runs **6 sequential
LLM calls** per sample, each stage seeing the previous stage's output:

1. **Four perspective specialists** each scan the function through one security
   lens and report candidate issues:
   - **memory** safety,
   - **input-validation / injection** (command/SQL injection, format-string, …),
   - **resource & logic** (resource management, logic errors),
   - **auth & crypto**.
   Specialists are instructed to **over-report** (favour recall) because a later
   stage filters false positives.
2. **Aggregator** (a "triage lead") consolidates the four specialists' findings
   together with the code into a single, de-duplicated **candidate list**.
3. **Validator** reviews each candidate against the code and emits its decision on
   the **first line** — `VERDICT: VULNERABLE` if at least one candidate is judged
   valid, otherwise `VERDICT: NOT VULNERABLE` — followed by a justification. The
   final 0/1 label is read from that VERDICT line.

- **6 calls/sample** (4 specialists + aggregator + validator).
- This is a **division-of-labour** design (each agent owns a vulnerability class,
  then findings are merged and adjudicated), in contrast to the primary MA's
  **debate** design (agents argue toward a shared verdict). Item 9 asks whether
  this change in role scheme changes multi-agent behaviour.

## Cost and structure at a glance

| Config | Calls/sample | Structure | Final label from |
|--------|:---:|---|---|
| plain SA (reference) | 1 | single call | the one response |
| DA (reference) | 2 | two-agent | analyst/feedback |
| MA (reference) | 4 | four-agent adversarial debate | board vote |
| **Rev2** | 2 | sequential self-revision | last revision round |
| **Rev4** | 4 | sequential self-revision | last revision round |
| **Bon4** | 4 | 4 independent samples (T=0.7) | majority vote |
| **VulAgent-lite** | 6 | specialists → aggregator → validator | validator VERDICT line |

Notes: Rev2 mirrors the DA budget; Rev4 and Bon4 mirror the MA budget.
VulAgent-lite is not budget-matched — it is a role-scheme comparison, and its
6-call cost is reported as part of the efficiency picture.
