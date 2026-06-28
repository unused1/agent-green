"""Regression tests for the canonical vulnerability parser (src/vuln_parser.py).

Run:  /opt/anaconda3/envs/erp_i/bin/python -m pytest scripts/test_vuln_parser.py -q
  or:  /opt/anaconda3/envs/erp_i/bin/python scripts/test_vuln_parser.py   (self-run)

Anchored on the two real misclassifications that motivated the P0 parser fix:
  - entry 216515: many "No vulnerability found here" section headers followed
    by a final "(1) YES: Vulnerability detected" — first-match-wins returned 0.
  - entry 264657: thinking-mode "Final Answer: YES" phrasing not matched by the
    template-only "(1) YES" check.
Plus synthetic coverage for NA/SA text, DA/MA JSON, malformed JSON, MA
mitigated->safe polarity, and contradictory verdict/rationale text.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from vuln_parser import (  # noqa: E402
    final_text_verdict,
    parse_na_sa,
    parse_da,
    parse_ma,
    parse_ma_affirm,
    parse_ma_constrained,
    classify,
)


# ---------------------------------------------------------------------------
# Named regression cases (the bugs that motivated the fix)
# ---------------------------------------------------------------------------
def test_entry_216515_multi_no_then_final_yes():
    """Many 'No vulnerability found here' sections then a final (1) YES."""
    text = (
        "**Step-by-Step Analysis**\n"
        "1. Message reception. **No vulnerability found here.**\n"
        "2. Length checks. **No vulnerability found here.**\n"
        "3. Parsing. **No vulnerability found here.**\n"
        "**Conclusion**\nBased on the analysis, there is a potential vulnerability "
        "in the memory allocation path.\n\n"
        "**Result:**\n(1) **YES: Vulnerability detected.**\n"
        "**Recommendation:** Validate ticklen before allocation."
    )
    assert final_text_verdict(text) == 1
    assert parse_na_sa(text)[0] == 1


def test_entry_264657_final_answer_yes_format():
    """Thinking-mode 'Final Answer: YES' rather than '(1) YES'."""
    text = (
        "Let me check the global quantizer. So that part is safe.\n"
        "...lots of analysis...\n"
        "Step: Make the final decision. The double-free is exploitable.\n\n"
        "Final Answer: YES\n"
        "Reasoning: The code contains a double-free vulnerability."
    )
    assert final_text_verdict(text) == 1
    assert parse_na_sa(text)[0] == 1


# ---------------------------------------------------------------------------
# NA / SA text path
# ---------------------------------------------------------------------------
def test_na_sa_clean_no():
    text = "**Step-by-Step Analysis:**\n...\n(2) NO: No vulnerability."
    assert parse_na_sa(text)[0] == 0


def test_na_sa_clean_yes():
    text = "Analysis...\n(1) YES: Vulnerability detected."
    assert parse_na_sa(text)[0] == 1


def test_na_sa_no_vulnerability_phrasing():
    text = "After review, the code is safe. No vulnerability is present."
    assert parse_na_sa(text)[0] == 0


def test_na_sa_decisive_overrides_soft():
    """A passing 'is vulnerable' mention but a decisive (2) NO conclusion."""
    text = "One might think this is vulnerable, but on review it is fine.\n(2) NO: No vulnerability."
    assert parse_na_sa(text)[0] == 0


def test_na_sa_think_block_stripped():
    text = "<think>maybe vulnerable? (1) YES could apply</think>\n(2) NO: No vulnerability."
    # The decisive marker inside <think> must be ignored; only post-think counts.
    assert parse_na_sa(text)[0] == 0


def test_na_sa_undetermined_defaults_safe():
    text = "This function processes input and returns a value."
    assert final_text_verdict(text) is None
    assert parse_na_sa(text)[0] == 0


def test_truncated_thinking_no_output_is_undetermined():
    """<think> opened, cut off before </think>: no final answer was emitted.
    Must NOT parse the in-progress reasoning (which mentions 'vulnerable')."""
    text = "<think> Let me analyze. This strcpy looks vulnerable, the buffer could overflow if"
    assert final_text_verdict(text) is None
    assert parse_na_sa(text)[0] == 0


def test_result_marker_no_vuln_detected():
    """Human-review case (sid 33): 'Result: NO (No vulnerability detected)' -> 0.
    Soft 'vulnerability detected' must not win over the decisive NO."""
    text = "Analysis...\n**Result:** **NO** (No vulnerability detected in the snippet)"
    assert parse_na_sa(text)[0] == 0


def test_markdown_answer_no():
    """Human-review case (sid 86): '**Answer**: **NO**' (markdown) -> 0."""
    text = "...discussion of buffer overflow risks...\n**Answer**: **NO**"
    assert parse_na_sa(text)[0] == 0


def test_no_direct_vulnerability_detected():
    """Human-review case (sid 96): 'NO (No direct vulnerability detected)' -> 0."""
    text = "Review...\n**NO** (No direct vulnerability detected in the provided snippet)"
    assert parse_na_sa(text)[0] == 0


def test_bare_vulnerable_conclusion_is_yes():
    """Human-review case (sid 189): concludes 'making the code vulnerable' -> 1."""
    text = "These issues could trigger memory corruption, making the code vulnerable."
    assert parse_na_sa(text)[0] == 1


def test_code_is_not_vulnerable_guard():
    """Negation guard: 'the code is not vulnerable' must stay 0, not match YES."""
    text = "After review, the code is not vulnerable to the reported issue."
    assert parse_na_sa(text)[0] == 0


def test_no_tags_whole_text_is_output():
    """No think tags at all (e.g. Nemotron-Nano-8B): parse the full text."""
    text = "Step-by-step analysis of the function.\n(1) YES: Vulnerability detected."
    assert parse_na_sa(text)[0] == 1


# ---------------------------------------------------------------------------
# DA JSON path
# ---------------------------------------------------------------------------
def test_da_json_true():
    resp = '{"vulnerability_detected": true, "analysis": "strcpy overflow"}'
    assert parse_da(resp)[0] == 1


def test_da_json_false():
    resp = '{"vulnerability_detected": false, "analysis": "bounded copy"}'
    assert parse_da(resp)[0] == 0


def test_da_json_in_markdown_fence():
    resp = '```json\n{"vulnerability_detected": true, "analysis": "x"}\n```'
    assert parse_da(resp)[0] == 1


def test_da_malformed_json_falls_back_to_text():
    resp = '{"vulnerability_detected": true,,, broken\n(2) NO: No vulnerability.'
    # JSON parse fails -> text fallback -> decisive (2) NO
    assert parse_da(resp)[0] == 0


def test_da_array_any_true():
    resp = '[{"vulnerability_detected": false}, {"vulnerability_detected": true}]'
    assert parse_da(resp)[0] == 1


# ---------------------------------------------------------------------------
# MA JSON path + polarity
# ---------------------------------------------------------------------------
def test_ma_decision_confirmed_is_vuln():
    resp = '{"vulnerability": "BOF", "decision": "Confirmed", "severity": "High"}'
    assert parse_ma(resp)[0] == 1


def test_ma_decision_mitigated_is_safe():
    """The 2026-03-11 polarity fix: 'mitigated' means addressed -> SAFE."""
    resp = '{"vulnerability": "BOF", "decision": "Mitigated", "severity": "Medium"}'
    assert parse_ma(resp)[0] == 0


def test_ma_decision_rejected_is_safe():
    resp = '[{"vulnerability": "X", "decision": "Rejected", "severity": "none"}]'
    assert parse_ma(resp)[0] == 0


def test_ma_decision_valid_is_vuln():
    resp = '[{"vulnerability": "X", "decision": "valid", "severity": "high"}]'
    assert parse_ma(resp)[0] == 1


def test_ma_summary_vulnerabilities_found_bool():
    resp = '{"vulnerability_detected": false}'
    assert parse_ma(resp)[0] == 0


def test_ma_markdown_wrapped_object():
    resp = '```json\n{"vulnerability": "UAF", "decision": "Confirmed", "severity": "Critical"}\n```'
    assert parse_ma(resp)[0] == 1


def test_ma_text_fallback_when_no_json():
    resp = "After deliberation the board concludes (2) NO: No vulnerability."
    assert parse_ma(resp)[0] == 0


# ---------------------------------------------------------------------------
# Contradiction guard: decisive marker beats earlier opposite phrasing
# ---------------------------------------------------------------------------
def test_contradiction_last_decisive_wins():
    text = "(1) YES initially considered.\nOn reflection, final answer: NO."
    # last decisive: "final answer: no" appears after "(1) yes"
    assert final_text_verdict(text) == 0


# ---------------------------------------------------------------------------
# classify() dispatch + determination flag
# ---------------------------------------------------------------------------
def test_classify_sa_determined():
    v, det = classify("SA", "Analysis...\n(1) YES: Vulnerability detected.")
    assert v == 1 and det is True


def test_classify_sa_undetermined():
    v, det = classify("SA", "This function processes input.")
    assert v == 0 and det is False


def test_classify_noagent_alias():
    v, det = classify("NoAgent", "(2) NO: No vulnerability.")
    assert v == 0 and det is True


def test_classify_da_json_determined():
    v, det = classify("DA", '{"vulnerability_detected": false, "analysis": "x"}')
    assert v == 0 and det is True


def test_classify_ma_mitigated_determined_safe():
    v, det = classify("MA", '{"vulnerability": "X", "decision": "Mitigated", "severity": "Medium"}')
    assert v == 0 and det is True


def test_classify_truncated_undetermined():
    v, det = classify("SA", "<think> looks vulnerable but cut off")
    assert v == 0 and det is False


def test_classify_unknown_design_raises():
    try:
        classify("XX", "text")
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown design")


# ---------------------------------------------------------------------------
# parse_ma_affirm — deterministic "affirm-unless-rejected" rule (Option A)
# ---------------------------------------------------------------------------
def test_affirm_accepted_and_mitigated_is_vuln():
    """The core polarity fix: 'accepted and mitigated' = board affirmed -> vuln."""
    resp = '{"vulnerability": "BOF", "decision": "Accepted and Mitigated", "severity": "High"}'
    assert parse_ma_affirm(resp) == (1, True)


def test_affirm_confirmed_is_vuln():
    assert parse_ma_affirm('[{"decision": "Confirmed", "severity": "Critical"}]') == (1, True)


def test_affirm_bare_mitigated_is_vuln():
    """Bare 'Mitigated' (board acknowledged a real finding) -> vuln under the rule."""
    assert parse_ma_affirm('{"decision": "Mitigated", "severity": "Medium"}') == (1, True)


def test_affirm_invalid_is_safe():
    assert parse_ma_affirm('[{"decision": "Invalid", "severity": "none"}]') == (0, True)


def test_affirm_no_vulnerability_is_safe():
    assert parse_ma_affirm('{"decision": "No vulnerability found", "severity": "none"}') == (0, True)


def test_affirm_any_finding_affirmed_wins():
    """Multiple findings: one rejected, one accepted -> vuln (any affirm wins)."""
    resp = ('[{"decision": "Invalid"}, '
            '{"decision": "Accepted with mitigation", "severity": "High"}]')
    assert parse_ma_affirm(resp) == (1, True)


def test_affirm_all_rejected_is_safe():
    resp = '[{"decision": "Invalid"}, {"decision": "Not exploitable"}]'
    assert parse_ma_affirm(resp) == (0, True)


def test_affirm_text_fallback_no_json():
    assert parse_ma_affirm("The board confirmed a critical buffer overflow.")[0] == 1
    assert parse_ma_affirm("The board found no vulnerability in the code.")[0] == 0


def test_affirm_empty_is_safe_undetermined():
    assert parse_ma_affirm("") == (0, False)


# ---------------------------------------------------------------------------
# parse_ma_constrained — VulTrial strict binarization (Option B)
# ---------------------------------------------------------------------------
_VT_STRICT = ('[{"vulnerability": "BOF", "decision": "valid", "severity": "high", '
              '"recommended_action": "fix immediately", "reason": "x"}]')
_VT_PARTIAL = ('[{"vulnerability": "X", "decision": "partially valid", "severity": "high", '
               '"recommended_action": "fix immediately"}]')
_VT_VALID_LOW = ('[{"vulnerability": "X", "decision": "valid", "severity": "low", '
                 '"recommended_action": "monitor"}]')
_VT_INVALID = ('[{"vulnerability": "X", "decision": "invalid", "severity": "none", '
               '"recommended_action": "no action needed"}]')


def test_constrained_strict_valid_high_immediate_is_vuln():
    assert parse_ma_constrained(_VT_STRICT, "strict") == (1, True)


def test_constrained_strict_partially_valid_is_safe():
    """VulTrial excludes partially valid from the strict vulnerable set."""
    assert parse_ma_constrained(_VT_PARTIAL, "strict") == (0, True)


def test_constrained_strict_valid_low_is_safe():
    """valid but low severity -> not vulnerable under strict."""
    assert parse_ma_constrained(_VT_VALID_LOW, "strict") == (0, True)


def test_constrained_invalid_is_safe_all_rules():
    for rule in ("strict", "valid_high", "valid_any", "incl_partial"):
        assert parse_ma_constrained(_VT_INVALID, rule) == (0, True)


def test_constrained_any_finding_meets_rule_wins():
    resp = ('[{"decision": "invalid", "severity": "none", "recommended_action": "none"}, '
            '{"decision": "valid", "severity": "high", "recommended_action": "fix immediately"}]')
    assert parse_ma_constrained(resp, "strict") == (1, True)


def test_constrained_rule_sensitivity_same_input():
    """Same verdict, different rule -> different label (the reparse lever)."""
    assert parse_ma_constrained(_VT_VALID_LOW, "strict") == (0, True)
    assert parse_ma_constrained(_VT_VALID_LOW, "valid_any") == (1, True)
    assert parse_ma_constrained(_VT_PARTIAL, "strict") == (0, True)
    assert parse_ma_constrained(_VT_PARTIAL, "incl_partial") == (1, True)


def test_constrained_markdown_fenced_array():
    resp = "```json\n" + _VT_STRICT + "\n```"
    assert parse_ma_constrained(resp, "strict") == (1, True)


def test_constrained_empty_array_is_determined_safe():
    """An explicit empty array = determinate 'no findings' -> safe (0, True),
    not undetermined. Covers the Review-Board 'no vulnerabilities' case."""
    assert parse_ma_constrained("```json\n[]\n```", "strict") == (0, True)
    assert parse_ma_constrained("...analysis...</think>\n\n[]", "strict") == (0, True)


def test_constrained_unparseable_is_undetermined():
    """No verdict array and no explicit empty array -> undetermined (0, False)."""
    assert parse_ma_constrained("the board did not return a verdict", "strict") == (0, False)


def test_constrained_empty_is_undetermined():
    assert parse_ma_constrained("", "strict") == (0, False)


def _run_self():
    """Run all test_* functions in this module without pytest."""
    fns = [g for name, g in sorted(globals().items())
           if name.startswith("test_") and callable(g)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"FAIL: {fn.__name__}  {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR: {fn.__name__}  {type(e).__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed (of {len(fns)})")
    return failed


if __name__ == "__main__":
    sys.exit(1 if _run_self() else 0)
