#!/usr/bin/env python3
"""
Analyze CodeCarbon sessions and reconcile with energy tracking data

This script helps understand how multiple CodeCarbon sessions relate to the
experiment results, especially when there were interruptions and resumes.
"""

import json
import pandas as pd
from pathlib import Path

# Experiments to analyze
EXPERIMENTS = [
    {
        'name': 'Baseline Zero-shot',
        'base': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251011-083716',
        'codecarbon': 'codecarbon_baseline_sa-zero'
    },
    {
        'name': 'Baseline Few-shot',
        'base': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251011-102915',
        'codecarbon': 'codecarbon_baseline_sa-few'
    },
    {
        'name': 'Thinking Zero-shot',
        'base': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-095820',
        'codecarbon': 'codecarbon_thinking_sa-zero'
    },
    {
        'name': 'Thinking Few-shot',
        'base': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251011-103534',
        'codecarbon': 'codecarbon_thinking_sa-few'
    }
]

RESULTS_DIR = Path('results/mars')

print("=" * 80)
print("CODECARBON SESSION ANALYSIS")
print("=" * 80)
print()

for exp in EXPERIMENTS:
    print(f"{'='*80}")
    print(f"{exp['name']}")
    print(f"{'='*80}")

    # Load results
    results_file = RESULTS_DIR / f"{exp['base']}_detailed_results.jsonl"
    if results_file.exists():
        with open(results_file, 'r') as f:
            total_samples = sum(1 for line in f if line.strip())
        print(f"Total samples in results: {total_samples}")
    else:
        print(f"⚠️  Results file not found")
        total_samples = 0

    # Load energy tracking
    energy_file = RESULTS_DIR / f"{exp['base']}_energy_tracking.json"
    if energy_file.exists():
        with open(energy_file, 'r') as f:
            energy_data = json.load(f)

        print(f"\nEnergy Tracking JSON (custom accumulation):")
        print(f"  Total emissions: {energy_data['total_emissions']:.8f} kg CO2")
        print(f"  Sessions: {energy_data['sessions']}")
        print(f"  Session history:")

        cumulative_samples = 0
        for session in energy_data['session_history']:
            cumulative_samples += session['samples_processed']
            print(f"    Session {session['session']}:")
            print(f"      Start: {session['start_time']}")
            print(f"      Samples: {session['samples_processed']}")
            print(f"      Emissions: {session['session_emissions']:.8f} kg CO2")

        print(f"  Total samples from sessions: {cumulative_samples}")

        # Note: cumulative_samples may be > total_samples due to resume/retry logic
        if cumulative_samples > total_samples:
            print(f"  ⚠️  Note: Cumulative > total due to resume/retry (some samples processed multiple times)")

    # Load CodeCarbon emissions
    cc_file = RESULTS_DIR / exp['codecarbon'] / 'emissions.csv'
    if cc_file.exists():
        cc_df = pd.read_csv(cc_file)

        print(f"\nCodeCarbon emissions.csv:")
        print(f"  Total rows: {len(cc_df)}")
        print(f"  Total emissions (sum): {cc_df['emissions'].sum():.8f} kg CO2")
        print(f"  Sessions:")

        for idx, row in cc_df.iterrows():
            print(f"    {idx+1}. {row['timestamp']}")
            print(f"       Project: {row['project_name']}")
            print(f"       Duration: {row['duration']:.1f} seconds ({row['duration']/3600:.2f} hours)")
            print(f"       Emissions: {row['emissions']:.8f} kg CO2")
            print(f"       Energy: {row['energy_consumed']:.4f} kWh")

        # Check if project names match the experiment
        exp_base = exp['base'].split('_')[0]  # Sa-zero or Sa-few
        matching_sessions = cc_df[cc_df['project_name'].str.contains(exp['base'][:40], na=False)]

        if len(matching_sessions) < len(cc_df):
            print(f"\n  ⚠️  WARNING: emissions.csv contains {len(cc_df) - len(matching_sessions)} sessions from OTHER experiments!")
            print(f"     Only {len(matching_sessions)} sessions match this experiment")
            print(f"     For accurate reporting, use only matching sessions")
            print(f"\n     Matching sessions total: {matching_sessions['emissions'].sum():.8f} kg CO2")

        # Cross-validation
        if energy_file.exists():
            diff = abs(energy_data['total_emissions'] - matching_sessions['emissions'].sum())
            diff_pct = (diff / energy_data['total_emissions'] * 100) if energy_data['total_emissions'] > 0 else 0

            print(f"\n  Cross-validation (matching sessions only):")
            print(f"    energy_tracking.json: {energy_data['total_emissions']:.8f} kg CO2")
            print(f"    emissions.csv (matched): {matching_sessions['emissions'].sum():.8f} kg CO2")
            print(f"    Difference: {diff:.10f} kg ({diff_pct:.6f}%)")

            if diff_pct < 0.01:
                print(f"    ✓ MATCH (< 0.01%)")
            else:
                print(f"    ⚠️  DIFFERENCE (> 0.01%)")

    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("Key Insights:")
print("1. Each 'session' represents a period of continuous tracking (start to Ctrl+C or completion)")
print("2. When you resume an experiment, a new session is created")
print("3. The 'samples_processed' in each session may include retries/skips")
print("4. CodeCarbon emissions.csv may contain rows from test runs or other experiments")
print("5. For accurate reporting: filter emissions.csv by project_name matching the experiment")
print()
print("Recommendation:")
print("- Use emissions.csv filtered by project_name for component-level analysis")
print("- Use energy_tracking.json for high-level summary")
print("- Both should match when sessions are properly filtered")
print()
