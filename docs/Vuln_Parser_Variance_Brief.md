# Brief: Vulnerability Detection Parser Variance Across Agent Designs

**Date:** 2026-03-01
**Status:** For discussion with research team
**Impact:** Vulnerability detection metrics in `consolidated_performance.csv` (48 experiments)

---

## 1. Summary

The vulnerability detection evaluation pipeline uses **three distinct parsers** to convert raw model output into binary predictions (0 = safe, 1 = vulnerable), one per agent design (SA, DA, MA). These parsers differ in matching strategy, keyword sets, and default behaviour. An empirical analysis shows that a substantial proportion of predictions — particularly in DA instruct mode — rely on keyword fallback paths where the parser differences have the greatest impact.

This variance is a potential threat to the reliability of cross-design comparisons (e.g., SA vs DA vs MA performance) reported in the paper.

---

## 2. Parser Specifications

### 2.1 SA (Single-Agent) — Keyword Pattern Matching

**File:** `src/single_agent_vuln_openrouter.py` lines 130-182
**Origin:** Adapted from upstream (merveast/agent-green `single_agent_vuln_detection.py`), with two local fixes applied.

| Step | Logic | Result |
|------|-------|--------|
| 1. Think-tag strip | Split on `</think>`, parse only text after | — |
| 2. NO patterns (checked first) | 7 substring patterns: `'final answer: no'`, `'(2) no'`, `'no vulnerability'`, etc. | 0 |
| 3. YES patterns | 7 substring patterns: `'final answer: yes'`, `'(1) yes'`, `'vulnerability detected'`, etc. | 1 |
| 4. Fallback (strong positives) | 4 narrow keywords: `'is vulnerable'`, `'contains a vulnerability'`, `'security vulnerability exists'`, `'can be exploited'` | 1 |
| 5. Default | No match | 0 |

**Local fixes applied:**
- 2026-02-09: Think-tag stripping (upstream searched entire output including `<think>` block)
- 2026-02-22: NO checked before YES (upstream checked YES first, causing "no vulnerability detected" to match "vulnerability detected" substring); broad fallback keywords removed

### 2.2 DA (Dual-Agent) — JSON Parse + Keyword Fallback

**File:** `src/dual_agent_vuln.py` lines 63-85
**Origin:** Virtually unchanged from upstream (merveast/agent-green), except for think-tag stripping added locally.

| Step | Logic | Result |
|------|-------|--------|
| 1. Think-tag strip | Split on `</think>` | — |
| 2. JSON parse (primary) | If text starts with `{` or `[`: parse `vulnerability_detected` boolean field | 0 or 1 |
| 3. Keyword fallback | 3 broad substrings: `'vulnerable'`, `'unsafe'`, `'security issue'` | 1 if any match, else 0 |
| 4. Exception default | JSON parse error | 0 |

### 2.3 MA (Multi-Agent) — Signal-Counting Consensus

**File:** `src/multi_agent_vuln_detection_four_agents.py` lines 194-296
**Origin:** Substantially rewritten from upstream's simpler majority vote (`valid > invalid + partial`).

| Step | Logic | Result |
|------|-------|--------|
| 1. Think-tag strip | Split on `</think>` | — |
| 2. JSON array extraction | Regex for `[...]`, parse as list of verdict objects | — |
| 3. Per-verdict signal counting | Safe keywords (+2): `'reject'`, `'invalid'`, `'safe'`, `'mitigated'`, etc. Vuln keywords (+2): `'confirmed'`, `'valid'`, `'accept'`, `'critical'`, etc. Severity tiebreaker (+1) | Weighted |
| 4. Decision | `vuln_signals >= safe_signals AND vuln_signals > 0` (tie goes to vulnerable) | 0 or 1 |
| 5. Fallback on parse error | Keyword matching: `'confirmed vulnerability'`, `'exploitable'` vs `'no vulnerability'`, `'safe'` | 0 or 1 |
| 6. Default | No fallback match | 0 |

---

## 3. Divergence Points

### 3.1 Keyword fallback bias

DA's fallback keywords (`'vulnerable'`, `'unsafe'`, `'security issue'`) are broad substring matches that trigger on almost any security discussion text. SA's fallback requires more specific phrases (`'is vulnerable'`, `'contains a vulnerability'`). MA's fallback requires strong phrases (`'confirmed vulnerability'`, `'exploitable'`).

**Impact:** DA fallback is biased toward predicting vulnerable (1); MA fallback is biased toward predicting safe (0).

### 3.2 Substring matching limitations (all designs)

All parsers use Python's `in` operator (substring matching), not exact or regex matching. This creates edge cases where negated sentences are misclassified:

| Example output | SA result | Reason |
|---|---|---|
| "nothing here is vulnerable" | **1 (wrong)** | NO patterns don't match; fallback `'is vulnerable'` matches |
| "the code is not vulnerable" | **1 (wrong)** | `'is vulnerable'` is a substring of "is not vulnerable" |
| "no vulnerability detected" | **0 (correct)** | `'no vulnerability'` matches first (NO-before-YES fix) |

### 3.3 Format-dependent primary path

The DA and MA parsers expect structured JSON output. When models produce free-form text instead, the prediction falls through to keyword heuristics with different rules than SA. This is not an edge case — it affects a majority of DA instruct-mode predictions.

---

## 4. Empirical Fallback Rates

Analysis of all DA and MA vulnerability detection JSONL files:

| Design | Mode | Total Samples | Keyword Fallback | Fallback Rate |
|--------|------|--------------|-----------------|---------------|
| DA | Instruct | 3,096 | 1,684 | **54.4%** |
| DA | Thinking | 3,096 | 155 | 5.0% |
| MA | Instruct | 3,082 | 477 | 15.5% |
| MA | Thinking | 3,076 | 438 | 14.2% |

DA instruct mode is critically affected: over half of all predictions rely on the broad keyword heuristic rather than structured JSON parsing.

---

## 5. Options for Resolution

### Option A: Acknowledge as limitation
Note in the paper that cross-design vulnerability detection comparisons are confounded by parser variance, particularly for DA instruct mode. Within-design comparisons (e.g., thinking vs instruct within SA) are unaffected.

### Option B: Unified re-parsing
Apply a single standardized parser to all raw model outputs across all designs. Recompute metrics. Report both original and standardized results. The SA parser (with NO-before-YES fix) is the most well-tested candidate.

### Option C: Unified re-parsing + semantic robustness
As Option B, plus add negative-context guards (e.g., check for "not vulnerable", "is not vulnerable", "no evidence of") to address substring matching limitations. This would require re-validation of all 48 experiments.

---

## 6. Recommendation

For the conference submission, **Option B is recommended** as the minimum viable approach. It directly addresses the cross-design reliability concern without requiring a new parser design. Option C could be pursued as a follow-up if the team determines the substring matching edge cases are frequent enough in the actual data to affect reported metrics.

**Immediate next step:** Quantify how many predictions would actually change under unified re-parsing, to assess whether the current metrics are materially affected.

---

## 7. Provenance Note

The SA and DA parsers originate from the upstream repository (merveast/agent-green). The upstream SA parser contained two bugs (think-tag inclusion, YES-before-NO ordering) that were fixed locally. The upstream DA parser was adopted with minimal changes (think-tag stripping only). The MA parser was substantially rewritten from upstream's simpler majority-vote logic.

The DA parser's keyword fallback (`'vulnerable'`, `'unsafe'`, `'security issue'`) is the original upstream (merveast) implementation, which was not revised when the SA parser was tightened.
