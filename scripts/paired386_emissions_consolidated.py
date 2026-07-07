#!/usr/bin/env python3
"""Build a consolidated-emissions-schema table for the paired-386 Item 5/9 runs.

Reads each config's per-config codecarbon emissions CSV (one or more session
rows; sharded/interrupted configs already aggregated, bogus 404 sessions
excluded upstream) and emits one row per config using the SAME columns as
results/consolidated_emissions.csv, so the Item 5/9 energy is directly
comparable / concatenable with the main catalogue.

Output: results/paired386_item5_9_emissions.csv
"""
import csv, glob, json, os, re

DIRS = {"budget": "results/runpod_vuln_386paired_budget",
        "vulagent": "results/runpod_vuln_386paired_vulagent"}
OUT = "results/paired386_item5_9_emissions.csv"

COLS = ["model", "model_family", "parameters_b", "design", "task", "dataset",
        "mode", "prompting", "thinking_enabled", "num_sessions", "total_duration_s",
        "duration_hours", "total_emissions_kg", "emissions_g", "total_energy_kwh",
        "total_cpu_energy_kwh", "total_gpu_energy_kwh", "total_ram_energy_kwh",
        "avg_cpu_power_w", "avg_gpu_power_w", "avg_ram_power_w", "gpu_model",
        "gpu_count", "cpu_model", "country", "source_note", "variant", "label_rule"]


def _f(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0


def parse_config(stem):
    mode = "thinking" if stem.endswith("_thinking") else "instruct"
    core = stem[:-9] if mode == "thinking" else stem
    if core.startswith("VulAgentLite"):
        method, rest, design = "vulagent-lite", core[len("VulAgentLite") + 1:], "MA"
    else:
        m = re.match(r"SA-budget-([a-z0-9]+)_(.*)", core)
        method, rest, design = f"budget-{m.group(1)}", m.group(2), "SA"
    if rest.startswith("Qwen"):
        family, params, model = "Qwen", "30", "Qwen3-30B-A3B-" + ("Thinking" if mode == "thinking" else "Instruct")
    else:
        family, params, model = "Nemotron", "49", "Nemotron-Super-49B"
    return method, design, family, params, model, mode


def main():
    out = []
    for kind, d in DIRS.items():
        for f in sorted(glob.glob(os.path.join(d, "*_detailed_results.jsonl"))):
            stem = os.path.basename(f).replace("_detailed_results.jsonl", "")
            ef = os.path.join(d, "emissions", f"emissions_{stem}.csv")
            if not os.path.exists(ef):
                print(f"WARN no emissions for {stem}"); continue
            rows = list(csv.DictReader(open(ef)))
            method, design, family, params, model, mode = parse_config(stem)
            dur = sum(_f(r.get("duration")) for r in rows) or 1.0
            def wmean(col):  # duration-weighted
                return sum(_f(r.get(col)) * _f(r.get("duration")) for r in rows) / dur
            r0 = rows[-1]
            kg = sum(_f(r.get("emissions")) for r in rows)
            out.append({
                "model": model, "model_family": family, "parameters_b": params,
                "design": design, "task": "vulnerability_detection",
                "dataset": "VulTrial-386-paired", "mode": mode, "prompting": "zero-shot",
                "thinking_enabled": (mode == "thinking"),
                "num_sessions": len(rows),
                "total_duration_s": round(dur, 1), "duration_hours": round(dur / 3600, 3),
                "total_emissions_kg": round(kg, 4), "emissions_g": round(kg * 1000, 1),
                "total_energy_kwh": round(sum(_f(r.get("energy_consumed")) for r in rows), 4),
                "total_cpu_energy_kwh": round(sum(_f(r.get("cpu_energy")) for r in rows), 4),
                "total_gpu_energy_kwh": round(sum(_f(r.get("gpu_energy")) for r in rows), 4),
                "total_ram_energy_kwh": round(sum(_f(r.get("ram_energy")) for r in rows), 4),
                "avg_cpu_power_w": round(wmean("cpu_power"), 1),
                "avg_gpu_power_w": round(wmean("gpu_power"), 1),
                "avg_ram_power_w": round(wmean("ram_power"), 1),
                "gpu_model": r0.get("gpu_model", ""), "gpu_count": r0.get("gpu_count", ""),
                "cpu_model": r0.get("cpu_model", ""), "country": r0.get("country_name", ""),
                "source_note": f"paired386 {('Item5' if design=='SA' else 'Item9')} {method}; {len(rows)} session(s) summed",
                "variant": method, "label_rule": "paired386",
            })
    with open(OUT, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=COLS); w.writeheader()
        for r in out: w.writerow(r)
    print(f"wrote {OUT}: {len(out)} configs")
    hdr = f'{"design":6}{"variant":16}{"family":10}{"mode":9}{"kWh":>9}{"kg":>8}{"hours":>8}{"sess":>5}'
    print(hdr); print("-" * len(hdr))
    for r in sorted(out, key=lambda x: (x["design"], x["variant"], x["model_family"], x["mode"])):
        print(f'{r["design"]:6}{r["variant"]:16}{r["model_family"]:10}{r["mode"]:9}'
              f'{r["total_energy_kwh"]:9.2f}{r["total_emissions_kg"]:8.2f}{r["duration_hours"]:8.2f}{r["num_sessions"]:5}')


if __name__ == "__main__":
    main()
