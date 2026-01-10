# Vulnerability Detection Extraction Reliability Analysis

**Date:** December 29, 2025
**Status:** Analysis Complete

---

## Executive Summary

Investigation of vuln detection extraction reliability across all designs (SA, DA, MA) reveals systematic issues that affect the reliability of recorded predictions. The core problem is that extraction logic varies significantly between designs, and fallback keyword matching introduces bias.

**Key Finding:** Ground truth is balanced (50% vulnerable, 50% safe), but predictions vary wildly from 0% to 100% vulnerable depending on:
1. Design (SA, DA, MA)
2. Prompt type (zero-shot, few-shot)
3. Model family (Qwen3, Nemotron)
4. Response format (clean JSON vs markdown-wrapped vs text)
5. Extraction fallback behavior

---

## Extraction Logic Summary

| Design | Primary Extraction | Fallback Keywords | Default Behavior |
|--------|-------------------|-------------------|------------------|
| SA | Looks for "(1) yes" / "(2) no" format | "vulnerable", "attack", "exploit" | **SAFE** |
| DA | JSON with `vulnerability_detected` boolean | "vulnerable", "unsafe", "security issue" | **SAFE** |
| MA | JSON array with `decision` field | "vulnerability" (too broad!) | **VULNERABLE** |

### Critical Difference

- **SA/DA default to SAFE** when parsing fails → Conservative bias
- **MA defaults to VULNERABLE** when parsing fails → Aggressive bias

This explains why MA experiments show ~100% vuln predictions when JSON parsing fails.

---

## Prediction Distribution by Design

### Single-Agent (SA) Vuln Detection

| Model | Config | Vuln % | Notes |
|-------|--------|--------|-------|
| Qwen3 4B | zero-shot Instruct | 11-17% | Conservative |
| Qwen3 4B | zero-shot Thinking | 27-51% | Variable |
| Qwen3 4B | few-shot Instruct | 4-27% | Conservative |
| Qwen3 4B | few-shot Thinking | 17-65% | Variable |
| Qwen3 30B | zero-shot | 44-55% | Near balanced |
| Qwen3 30B | few-shot | 22-62% | Variable |
| Nemotron 8B | zero-shot | 10-16% | Very conservative |
| Nemotron 8B | few-shot | 45-46% | Near balanced |
| Nemotron 49B | zero-shot Instruct | 48% | Near balanced |
| Nemotron 49B | zero-shot Thinking | 79% | Aggressive |
| Nemotron 49B | few-shot | 58-72% | Moderate-aggressive |

**SA Summary:** Range from 4% to 79% vuln predictions. Generally conservative due to SAFE default.

---

### Dual-Agent (DA) Vuln Detection

| Model | Config | Vuln % | Notes |
|-------|--------|--------|-------|
| Qwen3 4B | zero-shot Instruct | 0% or 68% | 0% was API error (404) |
| Qwen3 4B | zero-shot Thinking | 89% | High bias |
| Qwen3 4B | few-shot Instruct | 42% | Near balanced |
| Qwen3 4B | few-shot Thinking | 71% | High bias |
| Qwen3 30B | zero-shot | 67-79% | High bias |
| Qwen3 30B | few-shot | 65-68% | High bias |
| Nemotron 8B | All configs | 87-93% | Very high bias |
| Nemotron 49B | zero-shot Instruct | 30% | Conservative |
| Nemotron 49B | zero-shot Thinking | 58% | Moderate |
| Nemotron 49B | few-shot | 62-69% | High bias |

**DA Summary:** Range from 30% to 93% vuln predictions. Generally aggressive bias, especially for Nemotron 8B.

---

### Multi-Agent (MA) Vuln Detection

| Model | Config | Vuln % | Notes |
|-------|--------|--------|-------|
| Qwen3 4B | zero-shot Instruct | 97-98% | Fallback triggered |
| Qwen3 4B | zero-shot Thinking | 97% | Fallback triggered |
| Qwen3 4B | few-shot Instruct | 11% | Only config that parses correctly |
| Qwen3 4B | few-shot Thinking | 97% | Fallback triggered |
| Nemotron 49B | All configs | 100% | Always fallback (markdown-wrapped JSON) |
| Nemotron 8B | All configs | 89-100% | Always fallback |

**MA Summary:** Range from 11% to 100% vuln predictions. Extremely aggressive bias due to "vulnerability" keyword in fallback.

---

## Root Causes

### Issue 1: Response Format Inconsistency

Models return different formats depending on:
- **Instruct vs Thinking**: Thinking models add preamble text
- **Zero-shot vs Few-shot**: Few-shot examples guide format
- **Model family**: Nemotron wraps JSON in markdown code blocks (100% of responses)

### Issue 2: Fallback Keyword Selection

| Design | Fallback Keywords | Problem |
|--------|------------------|---------|
| MA | "vulnerability" | Always present in security context |
| DA | "vulnerable", "unsafe" | Common but not universal |
| SA | "vulnerable", "attack" | More specific |

The MA fallback using "vulnerability" is catastrophic because every response discusses "vulnerability" in some form.

### Issue 3: JSON Parsing Failures

| Model | Markdown-wrapped % | Clean JSON % |
|-------|-------------------|--------------|
| Qwen3 4B | 11% | 89% |
| Nemotron 49B | 100% | 0% |
| Nemotron 8B | ~100% | ~0% |

Nemotron consistently wraps JSON in markdown code blocks (`\`\`\`json ... \`\`\``), which causes `json.loads()` to fail.

### Issue 4: Design Philosophy Mismatch

- **SA/DA**: Evaluate whether code IS vulnerable (binary decision)
- **MA**: Evaluate whether a DISCUSSION about vulnerabilities is valid (meta-level decision)

The MA Review Board's "Accepted" or "Confirmed" decisions mean "the discussion is reasonable," not "there is a real vulnerability." This fundamental mismatch explains why even correctly parsed MA results don't correlate with ground truth.

---

## Extraction Code Fixes Applied

### MA Vuln (both 3-agent and 4-agent)

Updated `extract_vulnerability_decision()` in:
- `src/multi_agent_vuln_detection_four_agents.py` (lines 194-292)
- `src/multi_agent_vuln_detection_three_agents.py` (lines 183-268)

Changes:
1. Strip markdown code blocks before JSON parsing
2. Model-agnostic decision interpretation based on MA workflow context
3. Stronger fallback keywords (not just "vulnerability")
4. Default to SAFE when uncertain

### Decision Interpretation Logic (Updated Dec 30, 2025)

Based on MA workflow analysis:
- Security Researcher → Reports vulnerabilities
- Code Author → Responds/disputes
- Moderator → Summarizes
- **Review Board → Issues FINAL VERDICT** (this is what we parse)

| Review Board Decision | Interpretation | Prediction |
|----------------------|----------------|------------|
| "confirmed", "accept", "valid", "partially valid" | RB accepts the vulnerability claim | **1 (vuln)** |
| "critical", "high", "vulnerable", "accept with mitigation" | RB validates severity | **1 (vuln)** |
| "mitigated", "resolved", "fixed", "patched" | Issue was addressed | **0 (safe)** |
| "no vulnerability", "reject", "invalid", "safe" | RB rejects the claim | **0 (safe)** |

### SA/DA Vuln

**No fixes applied.** These designs already default to SAFE when uncertain, which is less problematic than defaulting to VULNERABLE.

---

## Re-evaluation Results (Dec 30, 2025)

All 15 canonical MA Vuln experiments were re-evaluated using corrected extraction logic.

### Summary

| Metric | Before | After |
|--------|--------|-------|
| Files processed | 15 | 15 |
| Total samples | 5,627 | 5,627 |
| Predictions changed | - | 3,721 (66.1%) |
| Average accuracy | 50.5% | 50.1% |

### Per-Experiment Results (Corrected)

| Model | Config | Original Vuln % | Corrected Vuln % | Accuracy |
|-------|--------|-----------------|------------------|----------|
| Nemotron 49B | few-shot Instruct | 100% | 22.3% | 48.4% |
| Nemotron 49B | few-shot Thinking | 97.4% | 65.0% | 54.6% |
| Nemotron 49B | zero-shot Instruct | 100% | 47.9% | 49.2% |
| Nemotron 8B | few-shot Instruct | 98.9% | 73.6% | 51.0% |
| Nemotron 8B | few-shot Thinking | 98.3% | 58.6% | 53.1% |
| Nemotron 8B | zero-shot Instruct | 100% | 13.9% | 49.6% |
| Nemotron 8B | zero-shot Thinking | 98.6% | 13.3% | 51.0% |
| Qwen3 4B | few-shot Instruct | 11.4% | 78.0% | 49.7% |
| Qwen3 4B | few-shot Thinking | 99.5% | 23.3% | 52.3% |
| Qwen3 4B | zero-shot Instruct | 100% | 5.5% | 49.7% |
| Qwen3 4B | zero-shot Thinking | 99.2% | 26.5% | 47.1% |
| Qwen3 30B | few-shot Instruct | 74.9% | 82.1% | 48.7% |
| Qwen3 30B | few-shot Thinking | 99.5% | 22.0% | 50.8% |
| Qwen3 30B | zero-shot Instruct | 100% | 9.6% | 47.2% |
| Qwen3 30B | zero-shot Thinking | 99.7% | 25.3% | 50.0% |

### Files Generated

For each experiment, the re-evaluation script regenerated:
- `*_corrected.jsonl` - Results with corrected predictions
- `*_reeval_metrics.json` - Comparison metrics
- `*_classification_report.csv` - Updated classification report
- `*_classification_report.txt` - Human-readable report
- `*_per_sample_vulnerability_metrics.csv` - Per-sample metrics
- `*_summary_vulnerability_metrics.csv` - Summary metrics

---

## Remaining Risks and Limitations

> **⚠️ IMPORTANT CAVEAT**: The decision interpretation logic is based on general semantic understanding of terms like "accept", "confirmed", "mitigated". **Detailed per-sample analysis was NOT performed** to validate that these interpretations are correct in every context.

### Known Risks

1. **Ambiguous "accept" decisions**: "Accept" may have different meanings depending on context:
   - "Accept the vulnerability claim as valid" → should predict vuln
   - "Accept the code author's defense" → should predict safe
   - Without reading each sample's full discussion, we cannot be certain

2. **Context-dependent "confirmed"**: "Confirmed" typically means the vulnerability is real, but could also mean "confirmed the discussion is valid" in the MA workflow context

3. **High fallback rates**: Some experiments have >90% fallback to keyword matching:
   - Qwen3 30B zero-shot Instruct: 100% fallback (0 parsed)
   - Qwen3 4B zero-shot Instruct: 99.7% fallback
   - This means extraction relies heavily on keyword heuristics, not structured parsing

4. **Accuracy remains ~50%**: Even with corrected extraction, accuracy hovers around random chance, confirming the fundamental design issue (MA evaluates discussion quality, not vulnerability presence)

### Recommended Validation Steps

For critical analysis, consider:
1. Manually reviewing a sample of predictions to validate interpretation
2. Cross-referencing with SA/DA predictions for the same samples
3. Treating MA Vuln results as supplementary rather than primary evidence

---

## Recommendations

### Short-term (For RQ2/RQ3 Analysis)

1. **Flag affected experiments**: All MA Vuln results should be marked as unreliable
2. **Use corrected extraction**: Re-evaluate MA Vuln logs with fixed extraction code
3. **Focus on SA/DA for vuln analysis**: These designs have more reliable extraction

### Long-term (For Future Work)

1. **Standardize response format**: Add explicit format specification in prompts
2. **Remove keyword fallback**: If parsing fails, mark as UNKNOWN, not vuln/safe
3. **Add validation step**: Ask model to confirm decision in structured format
4. **Reconsider MA design**: The multi-agent discussion evaluates discussion quality, not vulnerability presence

---

## Files Involved

### Extraction Code
- `src/single_agent_vuln_detection.py` - SA extraction (lines 326-349)
- `src/dual_agent_vuln.py` - DA extraction (lines 63-84)
- `src/multi_agent_vuln_detection_three_agents.py` - MA 3-agent extraction (lines 183-268)
- `src/multi_agent_vuln_detection_four_agents.py` - MA 4-agent extraction (lines 194-268)

### Related Documentation
- `docs/MA_Vuln_Investigation_NM25_NM26.md` - Detailed MA investigation
- `docs/Cross_Architecture_Validation_Plan.md` - Updated with warnings

---

## Conclusion

The extraction reliability varies significantly across designs:

| Design | Reliability | Main Issue |
|--------|------------|------------|
| SA | Moderate | Conservative bias (defaults to safe) |
| DA | Low-Moderate | High bias for some models (87-93% vuln for Nemotron 8B) |
| MA | Very Low | Catastrophic fallback (100% vuln for Nemotron) |

For RQ2/RQ3 analysis, SA experiments provide the most reliable predictions. DA experiments should be interpreted with caution. MA experiments should be considered unreliable without re-extraction using corrected code.

**Critical Note:** Even with fixed extraction, MA Vuln design fundamentally evaluates "is this discussion reasonable?" rather than "is this code vulnerable?" This design issue cannot be fixed by extraction code changes alone.
