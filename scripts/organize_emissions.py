#!/usr/bin/env python3
"""Split a codecarbon emissions.csv into per-config files under an emissions/ subdir.

codecarbon appends every run to a single generically-named emissions.csv per
results directory on each pod. Downloading several pods' emissions.csv into one
local directory would overwrite them. This tool splits a raw emissions.csv by
config (the project_name minus its _session_N suffix) into stable, uniquely-named
per-config files, merging idempotently: re-running with the same or an updated
raw file dedups on the full project_name (config + session), so repeated
downloads never duplicate or clobber rows.

Usage:
    python scripts/organize_emissions.py <raw_emissions.csv> <target_results_dir>
    # writes <target_results_dir>/emissions/emissions_<config>.csv
"""
import csv
import os
import re
import sys

csv.field_size_limit(2**27)


def config_key(project_name: str) -> str:
    return re.sub(r"_session_\d+$", "", project_name or "").strip() or "unknown"


def read_rows(path):
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    raw, results_dir = sys.argv[1], sys.argv[2]
    out_dir = os.path.join(results_dir, "emissions")
    os.makedirs(out_dir, exist_ok=True)

    fields, rows = read_rows(raw)
    groups = {}
    for row in rows:
        groups.setdefault(config_key(row.get("project_name", "")), []).append(row)

    for cfg, new_rows in groups.items():
        target = os.path.join(out_dir, f"emissions_{cfg}.csv")
        merged = {}  # project_name -> row (dedups sessions across re-downloads)
        hdr = fields
        if os.path.exists(target):
            hdr, existing = read_rows(target)
            for row in existing:
                merged[row.get("project_name")] = row
        for row in new_rows:
            merged[row.get("project_name")] = row  # newer download wins
        with open(target, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=hdr)
            w.writeheader()
            for pn in sorted(merged):
                w.writerow(merged[pn])
        print(f"  {os.path.basename(target)}: {len(merged)} session row(s)")


if __name__ == "__main__":
    main()
