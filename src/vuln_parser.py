"""Canonical vulnerability-verdict parser — single source of truth.

This module is imported by the NA / SA / DA / MA inference scripts AND by the
offline re-parser (scripts/reparse_vuln_870.py), so the live inference path and
any re-parse of stored raw outputs can never diverge. Previously each agent
script carried its own inlined parser; those copies drifted and produced
inconsistent verdicts across designs (the original SA/DA/MA parser-variance
bug). Consolidating to one module removes that failure mode.

Core fix (2026-06): **last-decisive-marker-wins** for the text path.

The earlier per-design parsers used *first-match-wins* with NO checked before
YES. That misclassified two real patterns:

  1. Responses that walk through several "No vulnerability found here" section
     headers before a final "(1) YES: Vulnerability detected" verdict — the
     first "no vulnerability" match returned 0 even though the model concluded
     YES (e.g. entry 216515, Nemotron-Super-49B SA zero-shot).
  2. Thinking-mode responses that conclude with "Final Answer: YES" rather than
     the template's "(1) YES" marker (e.g. entry 264657, Qwen3-30B SA thinking).

The fix scans for the *last* decisive verdict marker and uses its polarity.
Decisive markers (explicit answer formats requested by the prompt) take
absolute precedence; soft keyword phrasings are consulted only when no decisive
marker is present.

Public API:
    final_text_verdict(text) -> Optional[int]   # 1 / 0 / None(undetermined)
    parse_na_sa(response_text) -> (int, str)
    parse_da(response)         -> (int, str)
    parse_ma(board_response)   -> (int, str)

All design wrappers return (decision, reasoning) where decision is 1
(vulnerable) or 0 (safe); undetermined defaults to 0, matching the historical
convention. Callers that need the tri-state (for auditing) should call
final_text_verdict directly.
"""

import ast
import json
import re
from typing import Optional, Tuple

__all__ = [
    "strip_think_block",
    "strip_markdown_fences",
    "final_text_verdict",
    "parse_na_sa",
    "parse_da",
    "parse_ma",
    "parse_ma_affirm",
    "parse_ma_constrained",
    "classify",
]


def _try_literal(s):
    return ast.literal_eval(s)


# ---------------------------------------------------------------------------
# Pre-cleaning helpers
# ---------------------------------------------------------------------------
def strip_think_block(text: str) -> str:
    """Return only the model's *communicated output* — the text after </think>.

    Three cases, by tag convention observed across models:
      1. </think> present  -> return the portion after it (the final response).
         Covers paired <think>...</think> (Nemotron-Super-49B) and
         opening-tag-stripped content</think> (Qwen thinking models).
      2. <think> present but </think> absent -> the thinking block was TRUNCATED
         at the token limit and NO final answer was emitted. Return "" so the
         verdict is treated as undetermined rather than parsing in-progress
         reasoning as if it were the output. (Observed in ~29 entries: 1 SA,
         28 MA review-board responses.)
      3. Neither tag -> the model produced no separate thinking block; the whole
         text is the output (e.g. Nemotron-Nano-8B SA, which emits structured
         prose without tags). Return it unchanged.
    """
    if text is None:
        return ""
    if "</think>" in text:
        return text.split("</think>", 1)[1].strip()
    if "<think>" in text:
        return ""  # truncated thinking: no communicated output
    return text


def strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` / ``` ... ``` fences so JSON can be located."""
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Core text verdict — last-decisive-marker-wins
# ---------------------------------------------------------------------------
# Tier 1: decisive verdict markers. These are the explicit answer formats the
# VulTrial prompt requests, plus common equivalents. When present they are
# authoritative regardless of how many section-header phrasings precede them.
_DECISIVE_YES = [
    r"\(1\)\s*\*{0,2}\s*yes",                       # (1) YES, (1) **YES**
    r"final\s+answer\s*[:\-]?\s*\*{0,2}\s*\(?1?\)?\s*\*{0,2}\s*yes",
    r"final\s+answer\s*[:\-]?\s*\*{0,2}\s*vulnerab",
    r"final\s+(?:verdict|decision)\s*[:\-]?\s*\*{0,2}\s*(?:yes|vulnerab)",
    r"\banswer\s*[:\-]\s*\*{0,2}\s*yes\b",
    r"\bconclusion\s*[:\-]?\s*\*{0,2}\s*(?:yes\b|the code is vulnerab|vulnerab)",
    r"\byes\s*[:\-]\s*vulnerab",
    r"\byes,\s*the code\b",
]
_DECISIVE_NO = [
    r"\(2\)\s*\*{0,2}\s*no\b",                      # (2) NO, (2) **NO**
    r"final\s+answer\s*[:\-]?\s*\*{0,2}\s*\(?2?\)?\s*\*{0,2}\s*no\b",
    r"final\s+answer\s*[:\-]?\s*\*{0,2}\s*(?:not\s+vulnerab|no\s+vulnerab|safe)",
    r"final\s+(?:verdict|decision)\s*[:\-]?\s*\*{0,2}\s*(?:no\b|not\s+vulnerab|safe)",
    r"\banswer\s*[:\-]\s*\*{0,2}\s*no\b",
    r"\bconclusion\s*[:\-]?\s*\*{0,2}\s*(?:no\b|the code is (?:safe|not vulnerab)|not vulnerab|safe\b)",
    r"\bno,\s*the code\b",
]

# Tier 2: soft phrasings, consulted only if no decisive marker exists.
_SOFT_YES = [
    r"\bvulnerability detected\b",
    r"\bis vulnerable\b",
    r"\bcontains a vulnerability\b",
    r"\bsecurity vulnerability exists\b",
    r"\bcan be exploited\b",
]
_SOFT_NO = [
    r"\bno vulnerability\b",
    r"\bno security vulnerability\b",
    r"\bnot vulnerable\b",
    r"\bno security issue\b",
    r"\bis safe\b",
    r"\bis benign\b",
]


def _last_pos(patterns, text: str) -> int:
    """Return the start index of the last match across all patterns, or -1."""
    last = -1
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            if m.start() > last:
                last = m.start()
    return last


def final_text_verdict(text: str) -> Optional[int]:
    """Parse a free-text response into 1 (vulnerable), 0 (safe), or None.

    Strips the <think> block first, then applies last-decisive-marker-wins:
      Tier 1 (decisive answer markers) — last occurrence wins.
      Tier 2 (soft phrasings)          — consulted only if no decisive marker.
    Returns None when neither tier yields a signal (caller decides the default).
    """
    if not text:
        return None
    t = strip_think_block(text)

    last_yes = _last_pos(_DECISIVE_YES, t)
    last_no = _last_pos(_DECISIVE_NO, t)
    if last_yes >= 0 or last_no >= 0:
        return 1 if last_yes > last_no else 0

    last_syes = _last_pos(_SOFT_YES, t)
    last_sno = _last_pos(_SOFT_NO, t)
    if last_syes >= 0 or last_sno >= 0:
        return 1 if last_syes > last_sno else 0

    return None


# ---------------------------------------------------------------------------
# Design entry points
# ---------------------------------------------------------------------------
def parse_na_sa(response_text: str) -> Tuple[int, str]:
    """NA / SA: pure-text YES/NO response. Undetermined -> 0 (safe)."""
    verdict = final_text_verdict(response_text)
    return (verdict if verdict is not None else 0), (response_text or "")


def parse_da(response: str) -> Tuple[int, str]:
    """DA: Security-Analyst output. Prefer JSON `vulnerability_detected`; fall
    back to the canonical text verdict when JSON is absent/unparseable."""
    if response is None:
        return 0, ""
    cleaned = strip_markdown_fences(strip_think_block(response))
    # JSON path (object or array)
    if cleaned.startswith("{") or cleaned.startswith("["):
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                decision = bool(data.get("vulnerability_detected", False))
                reasoning = data.get("analysis", data.get("reasoning", cleaned))
                return (1 if decision else 0), reasoning
            if isinstance(data, list):
                decision = any(
                    isinstance(d, dict) and d.get("vulnerability_detected", False)
                    for d in data
                )
                reasoning = "; ".join(
                    str(d.get("analysis", d.get("reasoning", "")))
                    for d in data if isinstance(d, dict)
                )
                return (1 if decision else 0), reasoning
        except (json.JSONDecodeError, ValueError, TypeError):
            pass  # fall through to text verdict
    # Text fallback
    verdict = final_text_verdict(response)
    return (verdict if verdict is not None else 0), response


# MA Review-Board decision keyword polarity (preserved from the fork's
# 2026-03-11 fix: "mitigated/resolved/fixed" means the issue was addressed ->
# SAFE; "confirmed/valid/exploitable" -> VULNERABLE).
_MA_SAFE_DECISION = [
    "no vulnerability", "no_vulnerability", "reject", "invalid",
    "safe", "not exploitable", "mitigated", "resolved", "fixed", "patched",
]
_MA_VULN_DECISION_STRONG = [
    "confirmed", "vulnerable", "exploitable", "valid", "partially valid",
]
_MA_VULN_SEVERITY_STRONG = ["critical", "high", "high severity", "critical severity"]
_MA_VULN_SEVERITY_WEAK = ["medium", "low", "moderate", "medium severity", "low severity"]


def _score_ma_verdicts(verdicts) -> Optional[int]:
    """Weighted vote over a list of review-board verdict dicts. Returns 1/0,
    or None if no signal was found."""
    vuln_signals = 0
    safe_signals = 0
    for v in verdicts:
        if not isinstance(v, dict):
            continue
        decision = str(v.get("decision", "")).lower().strip()
        severity = str(v.get("severity", "")).lower().strip()
        if any(k in decision for k in _MA_SAFE_DECISION):
            safe_signals += 2
            continue
        if any(k in decision for k in _MA_VULN_DECISION_STRONG):
            vuln_signals += 2
            continue
        if "accept" in decision:
            vuln_signals += 2
            continue
        if decision in _MA_VULN_SEVERITY_STRONG:
            vuln_signals += 2
            continue
        if any(k in decision for k in ["fix required", "action required", "requires fix"]):
            vuln_signals += 1
            continue
        if decision in _MA_VULN_SEVERITY_WEAK:
            vuln_signals += 1
            continue
        # Ambiguous decision — use severity as tiebreaker
        if severity in ("critical", "high"):
            vuln_signals += 1
        elif severity in ("low", "medium", "moderate"):
            safe_signals += 1
    if vuln_signals == 0 and safe_signals == 0:
        return None
    # Tie goes to vulnerable (security-conservative), matching the fork.
    return 1 if vuln_signals >= safe_signals and vuln_signals > 0 else 0


def parse_ma(board_response: str) -> Tuple[int, str]:
    """MA: Review-Board final verdict. Prefer JSON `decision` field scoring;
    fall back to the canonical text verdict when JSON is absent/unparseable."""
    if board_response is None:
        return 0, ""
    cleaned = strip_markdown_fences(strip_think_block(board_response))

    # Direct boolean object form: {"vulnerability_detected": true} / {"vulnerability": true}
    match_array = re.search(r"(\[[\s\S]*\])", cleaned)
    match_object = re.search(r"(\{[\s\S]*\})", cleaned)
    json_str = None
    if match_array:
        json_str = match_array.group(1)
    elif match_object:
        json_str = match_object.group(1)

    if json_str is not None:
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                if "vulnerability_detected" in parsed:
                    return (1 if parsed.get("vulnerability_detected") else 0), board_response
                if "vulnerability" in parsed and isinstance(parsed["vulnerability"], bool):
                    return (1 if parsed["vulnerability"] else 0), board_response
                verdicts = [parsed]
            elif isinstance(parsed, list):
                verdicts = parsed
            else:
                verdicts = []
            scored = _score_ma_verdicts(verdicts)
            if scored is not None:
                return scored, board_response
        except (json.JSONDecodeError, ValueError, TypeError):
            pass  # fall through to text verdict

    # Text fallback
    verdict = final_text_verdict(board_response)
    return (verdict if verdict is not None else 0), board_response


# ---------------------------------------------------------------------------
# Unified design dispatch with determination flag (for the reparser/audit)
# ---------------------------------------------------------------------------
def _da_signal(response: str) -> Optional[int]:
    """DA verdict if determinable (JSON vulnerability_detected or text), else None."""
    if not response:
        return None
    cleaned = strip_markdown_fences(strip_think_block(response))
    if cleaned.startswith("{") or cleaned.startswith("["):
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and "vulnerability_detected" in data:
                return 1 if data.get("vulnerability_detected") else 0
            if isinstance(data, list):
                if any(isinstance(d, dict) and "vulnerability_detected" in d for d in data):
                    return 1 if any(
                        isinstance(d, dict) and d.get("vulnerability_detected") for d in data
                    ) else 0
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return final_text_verdict(response)


def _ma_signal(board_response: str) -> Optional[int]:
    """MA verdict if determinable (JSON decision scoring or text), else None."""
    if not board_response:
        return None
    cleaned = strip_markdown_fences(strip_think_block(board_response))
    match_array = re.search(r"(\[[\s\S]*\])", cleaned)
    match_object = re.search(r"(\{[\s\S]*\})", cleaned)
    json_str = match_array.group(1) if match_array else (match_object.group(1) if match_object else None)
    if json_str is not None:
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                if "vulnerability_detected" in parsed:
                    return 1 if parsed.get("vulnerability_detected") else 0
                if "vulnerability" in parsed and isinstance(parsed["vulnerability"], bool):
                    return 1 if parsed["vulnerability"] else 0
                verdicts = [parsed]
            elif isinstance(parsed, list):
                verdicts = parsed
            else:
                verdicts = []
            scored = _score_ma_verdicts(verdicts)
            if scored is not None:
                return scored
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return final_text_verdict(board_response)


# ---------------------------------------------------------------------------
# MA deterministic "affirm-unless-rejected" rule (Option A, P0 RQ2 correction)
# ---------------------------------------------------------------------------
# The MA Review Board over-affirms: it routinely "accepts/confirms" the
# researcher's findings (often "accepted and mitigated") even on benign code.
# The submission parser mapped "mitigated/resolved -> safe", which inverted
# these affirmations into "safe" and manufactured MA's apparent P-C strength.
# This rule restores the correct, reproducible reading:
#   VULNERABLE  if the board affirms ANY finding (valid/confirmed/accepted,
#               including "accepted and mitigated", or assigns a severity).
#   SAFE        only if it rejects all findings (invalid / no vulnerability /
#               not exploitable / rejected) with no affirmation.
# Deterministic, no LLM judge; designed to match VulTrial's "valid/partially
# valid = vulnerable" intent.
# Affirmation substrings (safe to match as substrings; none collide with a reject).
_MA_AFFIRM_KW = [
    "confirmed", "accept", "approved", "partially valid", "mitigat", "resolved",
    "fixed", "patched", "remediat", "fix required", "action required",
    "requires fix", "critical", "high severity", "severity_high", "severity high",
]
# Reject phrases. Word-boundary forms handled separately to avoid substring traps
# (e.g. "invalid" contains "valid", "not vulnerable" contains "vulnerable").
_MA_REJECT_KW = [
    "no vulnerability", "no_vulnerability", "no vulnerabilities", "not vulnerable",
    "not exploitable", "no security", "no issue", "benign", "is safe",
    "no risk", "no exploit",
]


def _decision_is_affirm(decision: str):
    """Classify a single decision string: 1=affirm, 0=reject, None=ambiguous.

    Word boundaries guard the substring traps: `\\bvalid\\b` so "invalid" is not
    read as affirm; explicit reject phrases ("not vulnerable", "not exploitable",
    "invalid", "reject") win over the bare "vulnerable"/"exploitable" substrings
    they contain.
    """
    d = decision.lower().strip()
    if not d:
        return None
    reject = (bool(re.search(r"\binvalid\b|\breject", d))
              or any(k in d for k in _MA_REJECT_KW))
    affirm = (bool(re.search(r"\bvalid\b", d))
              or bool(re.search(r"\bvulnerable\b", d))
              or bool(re.search(r"\bexploitable\b", d))
              or any(k in d for k in _MA_AFFIRM_KW))
    if reject and not affirm:
        return 0
    if affirm and not reject:
        return 1
    if reject and affirm:
        # Both fired (e.g. "not vulnerable" sets reject + the \bvulnerable\b affirm).
        # An explicit negation/rejection dominates.
        if re.search(r"\binvalid\b|\breject|no vulnerab|not vulnerable|not exploitable", d):
            return 0
        return 1
    return None


def parse_ma_affirm(board_response: str) -> Tuple[int, bool]:
    """Deterministic MA verdict (Option A). Returns (verdict, determined).

    Primary: classify every `"decision": "..."` in the board verdict; VULNERABLE
    if any affirms, SAFE if all reject. Fallback: whole-text affirm-unless-reject.
    """
    if not board_response:
        return 0, False
    text = strip_markdown_fences(strip_think_block(board_response))
    decisions = re.findall(r'"decision"\s*:\s*"([^"]*)"', text, flags=re.IGNORECASE)
    if decisions:
        votes = [_decision_is_affirm(d) for d in decisions]
        if any(v == 1 for v in votes):
            return 1, True
        if any(v == 0 for v in votes):  # at least one explicit reject, none affirm
            return 0, True
        # decisions present but all ambiguous -> fall through to text
    # Whole-text fallback (mirror the decision-level word-boundary logic).
    low = text.lower()
    has_reject = (bool(re.search(r"\binvalid\b|\breject", low))
                  or any(k in low for k in _MA_REJECT_KW))
    has_affirm = (bool(re.search(r"\bvalid\b", low))
                  or bool(re.search(r"\bvulnerable\b", low))
                  or bool(re.search(r"\bexploitable\b", low))
                  or any(k in low for k in _MA_AFFIRM_KW))
    if has_reject and not has_affirm:
        return 0, True
    if has_affirm:
        return 1, True
    return 0, False  # no signal -> safe default, undetermined


def _ma_verdict_fields(board_response: str):
    """Extract structured Review Board verdicts as (decision, severity, action) tuples.

    For the VulTrial-faithful constrained prompt, the board emits a JSON array of
    objects with a closed-vocabulary `decision` (valid / invalid / partially valid),
    a `severity`, and a `recommended_action`. Returns [] if nothing parseable.
    """
    if not board_response:
        return []
    text = strip_markdown_fences(strip_think_block(board_response))
    m = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', text)
    cand = m.group(1) if m else text.strip()
    obj = None
    for ld in (json.loads, _try_literal):
        try:
            obj = ld(cand)
            break
        except Exception:  # noqa: BLE001
            continue
    if obj is None:
        # Field-by-field regex fallback (objects in textual order).
        decs = re.findall(r'"decision"\s*:\s*"([^"]*)"', text, flags=re.I)
        sevs = re.findall(r'"severity"\s*:\s*"([^"]*)"', text, flags=re.I)
        acts = re.findall(r'"recommended_action"\s*:\s*"([^"]*)"', text, flags=re.I)
        out = []
        for i, d in enumerate(decs):
            out.append((d, sevs[i] if i < len(sevs) else "",
                        acts[i] if i < len(acts) else ""))
        return out
    if isinstance(obj, dict):
        for k in ("verdicts", "review_board", "findings", "results"):
            if isinstance(obj.get(k), list):
                obj = obj[k]
                break
        else:
            obj = [obj]
    if not isinstance(obj, list):
        return []
    out = []
    for v in obj:
        if isinstance(v, dict):
            out.append((str(v.get("decision", "")), str(v.get("severity", "")),
                        str(v.get("recommended_action", v.get("recommended action", "")))))
    return out


def _is_valid_decision(d: str) -> bool:
    """VulTrial 'valid' (full validity): excludes 'invalid' and 'partially valid'."""
    s = d.lower()
    if "invalid" in s or "partial" in s:
        return False
    return "valid" in s


def parse_ma_constrained(board_response: str, rule: str = "strict") -> Tuple[int, bool]:
    """VulTrial-faithful MA binarization from the constrained Review Board verdicts.

    A function is VULNERABLE iff at least one finding meets the rule's criteria,
    applied to the closed-vocabulary fields. Returns (verdict, determined).
    The label is a pure function of the stored board verdicts, so the binarization
    can be changed and re-run with NO re-inference.

    rule:
      "strict"     valid AND high severity AND fix-immediately  (VulTrial paper)
      "valid_high" valid AND high severity
      "valid_any"  valid (any severity)
      "incl_partial" valid OR partially valid (any severity)
    """
    verdicts = _ma_verdict_fields(board_response)
    if not verdicts:
        return 0, False
    for dec, sev, act in verdicts:
        valid = _is_valid_decision(dec)
        partial = "partial" in dec.lower() and "invalid" not in dec.lower()
        high = "high" in sev.lower() or "critical" in sev.lower()
        immediate = "immediat" in act.lower() or "urgent" in act.lower()
        if rule == "strict" and valid and high and immediate:
            return 1, True
        if rule == "valid_high" and valid and high:
            return 1, True
        if rule == "valid_any" and valid:
            return 1, True
        if rule == "incl_partial" and (valid or partial):
            return 1, True
    return 0, True


def classify(design: str, raw_text: str) -> Tuple[int, bool]:
    """Dispatch to the right design parser and report determination.

    Returns (verdict, determined):
      verdict    — 1 (vulnerable) / 0 (safe); undetermined defaults to 0.
      determined — True if a verdict signal was found, False if it defaulted.

    design accepts: 'NA', 'NoAgent', 'SA', 'DA', 'MA' (case-insensitive).
    raw_text is the design-appropriate raw field (reasoning for NA/SA/DA,
    review-board text for MA).
    """
    d = (design or "").upper()
    if d in ("NA", "NOAGENT", "SA"):
        v = final_text_verdict(raw_text)
    elif d == "DA":
        v = _da_signal(raw_text)
    elif d == "MA":
        v = _ma_signal(raw_text)
    else:
        raise ValueError(f"Unknown design: {design!r}")
    return (v if v is not None else 0), (v is not None)
