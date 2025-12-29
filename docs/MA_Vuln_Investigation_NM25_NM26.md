# Investigation: MA Vuln 49B Experiments (NM-25, NM-26) Predicting All Samples as Vulnerable

**Date:** December 29, 2025
**Experiments Affected:** NM-25 (MA-few Instruct), NM-26 (MA-zero Instruct), and likely all MA Vuln experiments
**Status:** Root cause identified - Prompt/Extraction mismatch

---

## Summary

Both NM-25 and NM-26 show 50% accuracy with 100% recall - meaning they predict **all 386 samples as vulnerable**. Investigation revealed this is due to a combination of:

1. **JSON parsing failure** - Review Board responses wrapped in markdown code blocks
2. **Fallback keyword matching** - Always triggers on the word "vulnerability"
3. **Prompt-extraction mismatch** - Prompt doesn't specify decision values, extraction expects specific strings
4. **Fundamental design issue** - Review Board evaluates discussion quality, not vulnerability presence

---

## Evidence

### Prediction Distribution

| Experiment | Pred 0 (safe) | Pred 1 (vuln) | Accuracy |
|------------|---------------|---------------|----------|
| NM-25 (49B MA-few Instruct) | 0 | 386 | 50.0% |
| NM-26 (49B MA-zero Instruct) | 0 | 386 | 50.0% |
| NM-29 (8B MA-few Instruct) | 4 | 363 | ~50% |
| NM-30 (8B MA-zero Instruct) | 0 | 359 | ~50% |

Ground truth is balanced: 193 safe, 193 vulnerable.

---

## Root Cause Analysis

### Issue 1: JSON Parsing Failure

The Review Board returns responses wrapped in markdown code blocks:

```
'```json
[
  {
    "vulnerability": "Potential Information Leak",
    "decision": "Acknowledged - No Immediate Action",
    ...
  }
]
```'
```

The extraction code does:
```python
verdicts = json.loads(review_board_response.strip())  # FAILS due to ```json wrapper
```

### Issue 2: Fallback Keyword Matching

When JSON parsing fails, the code falls back to:
```python
except Exception:
    text = review_board_response.lower()
    if any(k in text for k in ['valid', 'vulnerability', 'security risk']):
        return 1, review_board_response  # Always returns VULNERABLE
```

Since every response discusses "vulnerability", this **always triggers**.

### Issue 3: Prompt-Extraction Mismatch

**Review Board Prompt:**
```
You are the Review Board. Based on the Moderator's summary, issue final verdicts
in JSON array with fields: vulnerability, decision, severity, recommended_action, reason.
```

**Extraction Code Expects:**
```python
has_vulnerability = any(v.get('decision') in ['valid', 'partially valid'] for v in verdicts)
```

**What the Model Actually Outputs:**
- "Accepted and Mitigated" (392 occurrences)
- "Accepted" (90)
- "Mitigated" (30)
- "Confirmed" (8)
- "Acknowledged with Monitoring" (5)

The prompt never specifies what `decision` values to use, so the model uses natural language.

### Issue 4: Decision Values Don't Correlate with Ground Truth

Even when properly parsed, the decision values show no correlation with actual vulnerabilities:

| Decision | GT=0 (safe) | GT=1 (vuln) | % Actually Vuln |
|----------|-------------|-------------|-----------------|
| Accepted | 155 | 164 | 51.4% (random!) |
| Mitigated | 20 | 13 | 39.4% |
| Confirmed | 4 | 6 | 60.0% |
| Acknowledged | 6 | 2 | 25.0% |

The Review Board's "Accepted" means "this discussion is reasonable" - NOT "there is a real vulnerability".

---

## Detailed Example

### Sample from NM-25 (idx: first sample)

**Ground Truth:** 0 (NOT vulnerable)
**Prediction:** 1 (vulnerable) - WRONG

**4-Agent Discussion Flow:**

1. **Security Researcher** identifies potential issues:
   - "Potential Information Leak / Data Exposure"
   - "Invalid Memory Access (Use-After-Free or Stale Pointer)"
   - "Integer Overflow / Wrap-around (Theoretical)"

2. **Code Author** responds with mitigations:
   - "acknowledgement-mitigation" for info leak
   - "mitigation" for memory access
   - "acknowledgement-monitoring" for integer overflow

3. **Moderator** summarizes both perspectives neutrally

4. **Review Board** issues verdicts:
```json
[
  {
    "vulnerability": "Potential Information Leak / Data Exposure",
    "decision": "Acknowledged - No Immediate Action",
    "severity": "Low",
    "recommended_action": "Explore hardware-level security features...",
    "reason": "While array_index_nospec mitigates timing attacks, theoretical risks..."
  },
  {
    "vulnerability": "Invalid Memory Access (Use-After-Free or Stale Pointer)",
    "decision": "Mitigation Required",
    "severity": "High",
    "recommended_action": "Add validation and lifetime checks...",
    "reason": "Accessing ctx->file_table and cd->ctx without validity checks..."
  },
  {
    "vulnerability": "Integer Overflow / Wrap-around (Theoretical)",
    "decision": "Monitoring Advised",
    "severity": "Low (Theoretical)",
    "recommended_action": "Implement runtime assertions...",
    "reason": "Although the likelihood is low..."
  }
]
```

**Why Extraction Failed:**

1. JSON wrapped in ` ```json ``` ` blocks → `json.loads()` fails
2. Fallback triggers: `"vulnerability" in text.lower()` → True
3. Returns `1` (vulnerable) regardless of actual decisions
4. Even if parsed correctly: no decision matches "valid" or "partially valid"
5. Correct extraction would return `0`, but this still doesn't reflect reality

**The Fundamental Problem:**

The Security Researcher's job is to find *potential* issues. The Code Author responds. The Review Board evaluates if the discussion was reasonable - NOT if there's an actual CVE-worthy vulnerability.

The decisions "Acknowledged", "Mitigation Required", "Monitoring Advised" mean:
- The discussion points are valid concerns worth addressing
- NOT that the code has a confirmed exploitable vulnerability

---

## Comparison: Single-Agent vs Multi-Agent

| Design | 8B | 49B | Pattern |
|--------|-----|-----|---------|
| SA zero-shot | 16% vuln | 48% vuln | Balanced/conservative |
| DA | 87-93% vuln | 30-69% vuln | Moderate bias |
| MA | 89-95% vuln | **100% vuln** | Extreme bias |

Single-agent (SA) shows more balanced predictions. Multi-agent (MA) amplifies vulnerability bias because:
- Security Researcher always finds "potential" issues
- Discussion inherently focuses on vulnerabilities
- Review Board confirms discussion is reasonable
- No agent explicitly checks: "Is this actually exploitable?"

---

## Recommendations

### Short-term Fixes

1. **Fix JSON extraction** - Strip markdown code blocks before parsing:
   ```python
   import re
   text = re.sub(r'```json\s*', '', response)
   text = re.sub(r'```\s*', '', text)
   verdicts = json.loads(text.strip())
   ```

2. **Fix fallback keywords** - Remove "vulnerability" from fallback (too broad)

3. **Update prompt** - Specify exact decision values:
   ```
   decision: must be exactly "valid", "partially valid", or "invalid"
   ```

### Long-term Fixes

4. **Add explicit vulnerability confirmation step** - Ask Review Board directly:
   ```
   Based on your analysis, does this code contain an actual exploitable
   security vulnerability (not just theoretical concerns)? Answer: YES or NO
   ```

5. **Re-evaluate MA design** - The current design evaluates discussion quality, not vulnerability presence

---

## Files Involved

- `src/multi_agent_vuln_detection_four_agents.py` - Lines 194-208 (extraction logic)
- `src/config.py` - Lines 1129-1132 (Review Board prompts)
- `results/rq2_cross_architecture/nemotron_49b_vuln_MA-few_instruct/` - NM-25 results
- `results/rq2_cross_architecture/nemotron_49b_vuln_MA-zero_instruct/` - NM-26 results

---

## Conclusion

The MA Vuln experiments have multiple compounding issues:
1. Technical bug: JSON parsing fails on markdown-wrapped responses
2. Logic bug: Fallback always triggers on "vulnerability" keyword
3. Prompt bug: Decision values not specified in prompt
4. Design issue: Review Board evaluates discussion, not vulnerability presence

The results should be considered unreliable. Re-running with fixes would address issues 1-3, but issue 4 suggests the MA Vuln design may need fundamental revision to accurately predict vulnerability presence.
