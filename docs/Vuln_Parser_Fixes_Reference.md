# Vulnerability Detection Parser Fixes — Reference

This document summarises four rounds of parser fixes applied to the agent-green vulnerability detection pipeline between February and March 2026. The fixes corrected systematic biases in how SA, DA, and MA parsers extracted binary predictions (0 = safe, 1 = vulnerable) from LLM output. In the VulTrial-486 dataset alone, over 4,800 predictions changed — the vast majority from 1 to 0, eliminating false positives caused by overly aggressive keyword matching.

---

## Fix 1 — Think-Tag Stripping (2026-02-09)

**Problem.** All three parsers (SA, DA, MA) searched the *entire* model output for keywords, including the `<think>...</think>` reasoning block. Reasoning text routinely contains phrases like "this could be a vulnerability" or "buffer overflow is possible" as the model deliberates, triggering false-positive matches even when the final answer was "no vulnerability."

**Fix.** Before any keyword matching, we strip the think block:

```python
parse_text = response.split("</think>", 1)[1].strip() \
    if "</think>" in response else response
```

Only content *after* the closing `</think>` tag is parsed. This was applied to all five source scripts (`single_agent_vuln_openrouter.py`, `single_agent_vuln.py`, `dual_agent_vuln.py`, `multi_agent_vuln_detection_three_agents.py`, `multi_agent_vuln_detection_four_agents.py`) and retroactively corrected 25 JSONL result files via `scripts/fix_vuln_think_tag_parsing.py`.

**Affected designs.** SA, DA, MA (all designs).

---

## Fix 2 — SA Keyword Ordering (2026-02-22)

**Problem.** The SA parser checked YES patterns before NO patterns. This meant a response like *"no vulnerability detected"* matched the YES substring `"vulnerability detected"` and returned 1 (vulnerable). Additionally, broad fallback keywords such as `"buffer overflow"` and `"memory leak"` produced false positives when they appeared in negative contexts (e.g., "no buffer overflow was detected").

**Fix.** Two changes were applied:

1. **NO-before-YES ordering** — NO patterns are now checked first, so `"no vulnerability detected"` matches the NO pattern `"no vulnerability"` and correctly returns 0.
2. **Narrowed fallback keywords** — Broad terms were replaced with specific positive indicators (`"is vulnerable"`, `"contains a vulnerability"`, `"security vulnerability exists"`, `"can be exploited"`).

**Impact.** 1,021 predictions changed (all from 1 to 0) across 37 SA vuln JSONL files, corrected via `scripts/fix_vuln_keyword_parsing.py`.

---

## Fix 3 — DA Keyword Fallback (2026-03-01)

**Problem.** The DA parser's text fallback (used when JSON parsing fails) used broad substrings — `"vulnerable"`, `"unsafe"`, `"security issue"` — with no NO-before-YES structure. Approximately 54.4% of DA instruct-mode predictions hit this fallback path, so the impact was substantial.

**Fix.** The DA text fallback was restructured to mirror the SA parser:

```python
# NO-before-YES ordering
if any(p in lowered for p in [
    "final answer: no", "no vulnerability", ...
]):
    decision = False
elif any(p in lowered for p in [
    "final answer: yes", "vulnerability detected", ...
]):
    decision = True
elif any(k in lowered for k in [
    "is vulnerable", "contains a vulnerability",
    "security vulnerability exists", "can be exploited",
]):
    decision = True
else:
    decision = False
```

The JSON-first path (`vulnerability_detected` field) was unchanged.

**Impact.** 2,597 predictions changed (2,556 from 1 to 0; 41 from 0 to 1) across 16 DA vuln JSONL files, corrected via `scripts/fix_da_keyword_fallback.py`.

---

## Fix 4 — MA "Mitigated/Fixed/Resolved" Semantics (2026-03-14)

**Problem.** The MA parser (Review Board verdicts) treated `"decision": "Mitigated"`, `"Fixed"`, and `"Resolved"` as vulnerable signals because these strings were listed in `valid_keywords` alongside `"Confirmed"` and `"Vulnerable"`. Semantically, when the Review Board says a vulnerability was *mitigated* or *fixed*, it means the code is safe — these should be safe signals.

Additionally, Nemotron models often wrapped their JSON output in markdown code blocks (`` ```json ... ``` ``), which caused the JSON parser to fail and fall through to the keyword fallback.

**Fix.** Two changes were applied:

1. **Reclassified safe signals** — `"mitigated"`, `"resolved"`, `"fixed"`, and `"patched"` now contribute +2 to `safe_signals` instead of `vuln_signals`.
2. **Markdown stripping** — Code blocks are stripped before JSON extraction:

```python
text = re.sub(r'```(?:json)?\s*', '', clean_response)
text = re.sub(r'```\s*', '', text)
```

**Impact.** 2,928 predictions changed (2,870 from 1 to 0; 58 from 0 to 1) across MA vuln JSONL files in `results/runpod_vuln_486/`.

---

## Current Parser Logic (Post-Fix)

### SA Parser (`single_agent_vuln_openrouter.py`)

1. Strip `<think>...</think>` block.
2. Lowercase the remaining text.
3. Check **NO patterns** first: `"final answer: no"`, `"no vulnerability"`, `"no security vulnerability"`, etc. If matched, return 0.
4. Check **YES patterns**: `"final answer: yes"`, `"vulnerability detected"`, `"yes: vulnerability"`, etc. If matched, return 1.
5. **Narrow fallback**: `"is vulnerable"`, `"contains a vulnerability"`, `"security vulnerability exists"`, `"can be exploited"`. If matched, return 1.
6. **Default**: return 0.

### DA Parser (`dual_agent_vuln.py`)

1. Strip `<think>...</think>` block.
2. **Try JSON parse** — if the response starts with `{` or `[`, extract `vulnerability_detected` (bool). If found, return that value directly.
3. **Text fallback** — same NO-before-YES keyword approach as SA (step 3-6 above), with the same narrow fallback terms.
4. **Default**: return 0.

### MA Parser (`multi_agent_vuln_detection_four_agents.py`)

1. Strip `<think>...</think>` block.
2. Strip markdown code blocks (`` ```json ``` ``).
3. Extract JSON array from response (regex: `\[[\s\S]*\]`).
4. Iterate over verdict objects; for each, read `decision` and `severity` fields.
5. **Weighted signal system**:
   - **Safe signals (+2 each)**: `"no vulnerability"`, `"reject"`, `"invalid"`, `"safe"`, `"not exploitable"`, `"mitigated"`, `"resolved"`, `"fixed"`, `"patched"`
   - **Strong vuln signals (+2 each)**: `"confirmed"`, `"vulnerable"`, `"exploitable"`, `"valid"`, `"partially valid"`, `"accept"`, `"critical"`, `"high"`
   - **Weak vuln signals (+1)**: `"fix required"`, `"action required"`, `"medium"`, `"low"`, `"moderate"`
   - **Severity tiebreaker (+1)**: critical/high to vuln; low/medium/moderate to safe
6. **Decision**: vulnerable if `vuln_signals >= safe_signals` AND `vuln_signals > 0`.
7. **Fallback** (on JSON parse failure): narrow keywords — `"confirmed vulnerability"`, `"critical vulnerability"`, `"exploitable"` for 1; `"no vulnerability"`, `"not vulnerable"`, `"safe"`, `"mitigated"`, `"resolved"` for 0.
8. **Default**: return 0.

---

## Remaining Limitation

All keyword parsers short-circuit on the **first match**, not the last or final conclusion. A response that says *"no vulnerability was found in the first function"* before concluding *"YES: Vulnerability detected in the main handler"* will match the NO pattern and incorrectly return 0.

Five such entries were identified in the Super-49B SA zero-shot RQ3 intersection pool, where the response text's final conclusion contradicted the parser's output. These were excluded from the pool via the `EXCLUDE_PARSER_MISMATCH` set in `scripts/rq3_generate_human_rating_set.py`:

- IDs **197518, 204017, 206676** — ground truth = 1, response text concludes NO
- IDs **270922, 387593** — ground truth = 0, response text concludes YES

The pool was reduced from 140 to 135 entries (77 TP + 58 TN) after exclusion.

A more robust approach would parse only the final paragraph or explicit answer line, but this has not yet been implemented.
