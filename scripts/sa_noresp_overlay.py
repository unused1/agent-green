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
    """True if the record carries no usable model output (NA/SA `reasoning`)."""
    return str(rec.get("reasoning", "")).strip().lower() in NORESP_STRINGS
