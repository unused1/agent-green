"""Shared overlay + no-output exclusion for the VulTrial-870 Option-A metrics.

The submitted SA runs contain a small number of transient "No response from
agent" samples. For the 4 SA-zero configs (Super-49B + Qwen-30B, both modes)
these were re-inferred (the gap-fill patch) and their corrected labels live in
`results/sa_noresp_patch/patched_labels.csv` — applied here as an OVERLAY so the
original JSONLs stay pristine. Any remaining no-output samples (other SA configs
with no patch) are EXCLUDED from metrics (decision: exclude no-output everywhere;
`vuln=-1`/safe-default would mis-score a non-prediction).

Keyed by (model, mode, idx) so it composes with the per-config metric loops.
"""

import csv
import os
import sys

csv.field_size_limit(sys.maxsize)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OVERLAY_CSV = os.path.join(_ROOT, "results", "sa_noresp_patch", "patched_labels.csv")

# A record whose raw output is one of these is a non-prediction (no model output).
NORESP_STRINGS = {"", "no response from agent"}

_overlay = None


def load_overlay():
    """Return {(model, mode, idx): vuln} from the gap-fill patch (cached)."""
    global _overlay
    if _overlay is None:
        _overlay = {}
        if os.path.exists(_OVERLAY_CSV):
            with open(_OVERLAY_CSV) as f:
                for r in csv.DictReader(f):
                    _overlay[(r["model"], r["mode"], int(r["idx"]))] = int(r["vuln"])
    return _overlay


def is_noresp(rec):
    """True if the record carries no usable model output (NA/SA `reasoning`).

    Covers both the transient 'No response from agent' cases and skip markers
    (e.g. 'SKIPPED: timeout' from a thinking-mode runaway) — neither is a real
    prediction, so both are excluded / must be patched.
    """
    t = str(rec.get("reasoning", "")).strip().lower()
    return t in NORESP_STRINGS or t.startswith("skipped")


# Full overlay (label + re-inferred response) for consumers that need the patched
# RESPONSE text, e.g. the FP/FN rater frame. Keyed (model, mode, idx).
_OUT_DIR = os.path.join(_ROOT, "results", "sa_noresp_patch", "out")
_OUT_FMAP = {
    "sa_noresp_super49b_instruct": ("Nemotron-Super-49B", "instruct"),
    "sa_noresp_super49b_thinking": ("Nemotron-Super-49B", "thinking"),
    "sa_noresp_qwen_instruct": ("Qwen3-30B-A3B-Instruct", "instruct"),
    "sa_noresp_qwen_thinking": ("Qwen3-30B-A3B-Thinking", "thinking"),
}
_overlay_full = None


def load_overlay_full():
    """Return {(model, mode, idx): (vuln, response_text)} from the patch outputs.

    Label is re-parsed from the re-inferred response with the canonical parser
    (matches patched_labels.csv); response is the raw re-inferred text.
    """
    global _overlay_full
    if _overlay_full is None:
        import glob
        import json
        from vuln_parser import classify
        _overlay_full = {}
        for f in glob.glob(os.path.join(_OUT_DIR, "*detailed_results.jsonl")):
            tag = os.path.basename(f).replace("_detailed_results.jsonl", "")
            mm = _OUT_FMAP.get(tag)
            if not mm:
                continue
            with open(f) as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    resp = r.get("reasoning", "") or ""
                    v, _ = classify("SA", resp)
                    _overlay_full[(mm[0], mm[1], int(r["idx"]))] = (v, resp)
    return _overlay_full
