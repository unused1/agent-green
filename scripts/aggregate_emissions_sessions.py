#!/usr/bin/env python3
"""Collapse a multi-session codecarbon emissions CSV into a single aggregated row.

Sharded / interrupted-and-resumed runs produce one emissions row per codecarbon
session. For a per-config energy figure it is convenient to have a single row.
This tool sums the extensive quantities (duration, emissions, the per-component
and total energy, water), duration-weights the intensive ones (power draw and
utilisation percentages), and recomputes the emissions rate from the summed
totals. Shared machine/experiment metadata is carried through unchanged.

The original per-session file is preserved (written next to the output with a
``_persession`` suffix, or left in place when ``--out`` differs from the input),
so no provenance is lost.

Usage:
    python scripts/aggregate_emissions_sessions.py INPUT.csv \
        --project-name CONFIG_NAME [--out OUTPUT.csv]
"""
import argparse
import csv
import os
import shutil
import sys

csv.field_size_limit(2**27)

# Columns summed across sessions (extensive: total over the whole run).
SUM_COLS = [
    "duration", "emissions", "water_consumed",
    "cpu_energy", "gpu_energy", "ram_energy", "energy_consumed",
]
# Columns averaged, weighted by session duration (intensive: rates/levels).
WEIGHTED_MEAN_COLS = [
    "cpu_power", "gpu_power", "ram_power",
    "cpu_utilization_percent", "gpu_utilization_percent",
    "ram_utilization_percent", "ram_used_gb", "ram_total_size",
]


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def aggregate(rows, project_name):
    """Return a single dict row aggregating all input rows."""
    fields = list(rows[0].keys())
    total_dur = sum(_f(r.get("duration")) for r in rows) or 1.0
    out = dict(rows[-1])  # start from the last session (latest timestamp, shared metadata)

    for c in SUM_COLS:
        if c in fields:
            out[c] = sum(_f(r.get(c)) for r in rows)
    for c in WEIGHTED_MEAN_COLS:
        if c in fields:
            out[c] = sum(_f(r.get(c)) * _f(r.get("duration")) for r in rows) / total_dur
    if "emissions_rate" in fields:
        out["emissions_rate"] = (out.get("emissions", 0.0) / total_dur) if total_dur else 0.0

    out["project_name"] = project_name
    if "run_id" in fields:
        # Anchor to the first (originating) session's run_id so the aggregated
        # row keeps a real UUID; timestamp above is carried from the last
        # session, marking completion of the run.
        out["run_id"] = rows[0].get("run_id")
    return fields, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--project-name", required=True,
                    help="project_name for the aggregated row (config-level id)")
    ap.add_argument("--out", default=None,
                    help="output CSV (default: overwrite input, keeping a _persession backup)")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.input)))
    if not rows:
        sys.exit(f"no rows in {args.input}")

    fields, agg = aggregate(rows, args.project_name)
    out_path = args.out or args.input

    # Preserve the per-session detail when overwriting in place.
    if out_path == args.input:
        backup = args.input.replace(".csv", "_persession.csv")
        shutil.copyfile(args.input, backup)
        print(f"per-session detail preserved -> {os.path.basename(backup)}")

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerow(agg)

    print(f"aggregated {len(rows)} sessions -> {os.path.basename(out_path)} (1 row)")
    print(f"  duration        = {_f(agg.get('duration')):.0f} s")
    print(f"  energy_consumed = {_f(agg.get('energy_consumed')):.3f} kWh")
    print(f"  emissions       = {_f(agg.get('emissions')):.4f} kg CO2")


if __name__ == "__main__":
    main()
