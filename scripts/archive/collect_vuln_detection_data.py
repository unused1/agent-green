#!/usr/bin/env python3
"""
Collect all vulnerability detection experiment data into a master dataset.
Reads summary metrics, energy tracking, and emissions data from all directories.

Uses manual experiment mappings from existing notebooks (rq1_codecarbon_analysis.ipynb,
rq1_phase2a_codecarbon_analysis.ipynb) to correctly handle multi-session experiments.
"""

import json
import pandas as pd
from pathlib import Path
import re

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Manual experiment mappings (from existing notebooks)
# This ensures we correctly match multi-session experiments
EXPERIMENT_MAPPINGS = {
    # Phase 1 (Mars Initial) - from rq1_codecarbon_analysis.ipynb
    'results/mars': {
        'Sa-zero_Qwen-Qwen3-4B-Instruct-2507': {
            'summary_file': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251011-083716_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251011-083716_energy_tracking.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251011-083716',
            'codecarbon_dir': 'codecarbon_baseline_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-4B-Instruct-2507': {
            'summary_file': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251011-110256_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251011-102915_energy_tracking.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251011-102915',
            'codecarbon_dir': 'codecarbon_baseline_sa-few'
        },
        'Sa-zero_Qwen-Qwen3-4B-Thinking-2507': {
            'summary_file': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-110220_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-095820_energy_tracking.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-095820',
            'codecarbon_dir': 'codecarbon_thinking_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-4B-Thinking-2507': {
            'summary_file': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251011-110932_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251011-103534_energy_tracking.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251011-103534',
            'codecarbon_dir': 'codecarbon_thinking_sa-few'
        },
    },
    # Phase 1b (Mars Rerun) - CWE-based prompts
    'results/mars_rerun': {
        'Sa-few_Qwen-Qwen3-4B-Instruct-2507': {
            'summary_file': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251101-200224_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251101-200224_energy_tracking.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251101-200224',
            'codecarbon_dir': 'codecarbon_baseline_sa-few'
        },
        'Sa-few_Qwen-Qwen3-4B-Thinking-2507': {
            'summary_file': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251101-200857_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251101-200857_energy_tracking.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251101-200857',
            'codecarbon_dir': 'codecarbon_thinking_sa-few'
        },
    },
    # Phase 2a (RunPod 30B Initial) - from rq1_phase2a_codecarbon_analysis.ipynb
    'results/runpod/instruct_zero_20251020_194844': {
        'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507': {
            'summary_file': 'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_20251020-104948_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_20251020-104948_energy_tracking.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_20251020-104948',
            'codecarbon_dir': 'codecarbon_baseline_sa-zero'
        },
    },
    'results/runpod/instruct_few_20251020_200040': {
        'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507': {
            'summary_file': 'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_20251020-111953_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_20251020-111953_energy_tracking.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_20251020-111953',
            'codecarbon_dir': 'codecarbon_baseline_sa-few'
        },
    },
    'results/runpod/thinking_zero_20251020_215332': {
        'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507': {
            'summary_file': 'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20251020-104530_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20251020-104530_energy_tracking.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20251020-104530',
            'codecarbon_dir': 'codecarbon_thinking_sa-zero'
        },
    },
    'results/runpod/thinking_few_20251020_214835': {
        'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507': {
            'summary_file': 'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20251020-112644_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20251020-111009_energy_tracking.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20251020-111009',
            'codecarbon_dir': 'codecarbon_thinking_sa-few'
        },
    },
    # Phase 2b & 2c (RunPod Rerun) - 30B rerun + 4B H100 comparison
    'results/runpod_rerun': {
        'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507': {
            'summary_file': 'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_20251102-042128_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_20251102-042128_energy_tracking.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_20251102-042128',
            'codecarbon_dir': 'codecarbon_baseline_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507': {
            'summary_file': 'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_20251102-042208_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_20251102-042208_energy_tracking.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_20251102-042208',
            'codecarbon_dir': 'codecarbon_baseline_sa-few'
        },
        'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507': {
            'summary_file': 'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20251102-042138_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20251102-042138_energy_tracking.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20251102-042138',
            'codecarbon_dir': 'codecarbon_thinking_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507': {
            'summary_file': 'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20251102-042248_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20251102-042248_energy_tracking.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20251102-042248',
            'codecarbon_dir': 'codecarbon_thinking_sa-few'
        },
        # 4B H100 experiments
        'Sa-zero_Qwen-Qwen3-4B-Instruct-2507': {
            'summary_file': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251107-145837_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251107-145837_energy_tracking.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251107-145837',
            'codecarbon_dir': 'codecarbon_baseline_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-4B-Instruct-2507': {
            'summary_file': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251107-171703_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251107-171703_energy_tracking.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251107-171703',
            'codecarbon_dir': 'codecarbon_baseline_sa-few'
        },
        'Sa-zero_Qwen-Qwen3-4B-Thinking-2507': {
            'summary_file': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251107-231443_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251107-231443_energy_tracking.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251107-231443',
            'codecarbon_dir': 'codecarbon_thinking_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-4B-Thinking-2507': {
            'summary_file': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-231419_summary_vulnerability_metrics.csv',
            'energy_json': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-231419_energy_tracking.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-231419',
            'codecarbon_dir': 'codecarbon_thinking_sa-few'
        },
    },
}

def parse_filename(filename):
    """Extract metadata from result filename."""
    # Pattern: {Design}_{Model}_{Timestamp}_...
    pattern = r'(Sa-(?:zero|few))_(Qwen-Qwen3-(?:4B|30B-A3B)-(?:Instruct|Thinking)-2507)_(\d{8}-\d{6})'
    match = re.search(pattern, filename)

    if match:
        design = match.group(1)
        model = match.group(2)
        timestamp = match.group(3)

        # Parse design
        prompting = 'Zero-shot' if 'zero' in design else 'Few-shot'

        # Parse model
        if '4B' in model:
            model_size = '4B'
        elif '30B' in model:
            model_size = '30B'
        else:
            model_size = 'Unknown'

        model_type = 'Thinking' if 'Thinking' in model else 'Instruct'

        return {
            'design': design,
            'full_model_name': model,
            'timestamp': timestamp,
            'prompting': prompting,
            'model_size': model_size,
            'model_type': model_type
        }
    return None

def collect_data():
    """Collect all vulnerability detection data using manual experiment mappings."""
    all_data = []

    for result_dir, experiments in EXPERIMENT_MAPPINGS.items():
        dir_path = PROJECT_ROOT / result_dir
        if not dir_path.exists():
            print(f"Skipping {result_dir} - directory not found")
            continue

        print(f"\n🔍 Scanning {result_dir}")
        print(f"   Configured experiments: {len(experiments)}")

        for exp_key, exp_config in experiments.items():
            print(f"\n   📊 Processing {exp_key}")

            # Build file paths from config
            summary_file = dir_path / exp_config['summary_file']
            energy_file = dir_path / exp_config['energy_json']
            codecarbon_path = dir_path / exp_config['codecarbon_dir'] / 'emissions.csv'
            exp_base = exp_config['exp_base']

            # Extract date prefix from exp_base for matching ALL sessions
            # Multi-session experiments have pattern: {Design}_{Model}_{Date}-{Time}_session_{N}
            # E.g., "Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-095820"
            # We need to match: "Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-*_session_*"
            date_match = re.search(r'(.+_\d{8})-', exp_base)
            if not date_match:
                print(f"      ⚠️  Could not extract prefix from exp_base: {exp_base}")
                continue
            match_prefix = date_match.group(1)  # e.g., "Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011"

            # Parse experiment metadata from exp_key
            metadata = parse_filename(exp_config['summary_file'])
            if not metadata:
                print(f"      ⚠️  Could not parse filename: {exp_config['summary_file']}")
                continue

            # Read performance metrics
            if not summary_file.exists():
                print(f"      ⚠️  Summary file not found: {summary_file}")
                continue

            try:
                metrics_df = pd.read_csv(summary_file)
                if len(metrics_df) == 0:
                    print(f"      ⚠️  Empty metrics file")
                    continue
                metrics = metrics_df.iloc[0].to_dict()
            except Exception as e:
                print(f"      ❌ Error reading metrics: {e}")
                continue

            # Read energy tracking
            energy_data = {}
            if energy_file.exists():
                try:
                    with open(energy_file, 'r') as f:
                        energy_json = json.load(f)
                        energy_data = {
                            'total_emissions_kg': energy_json.get('total_emissions', 0),
                            'num_sessions': energy_json.get('sessions', 0),
                        }
                        if energy_json.get('session_history'):
                            session = energy_json['session_history'][0]
                            energy_data['start_time'] = session.get('start_time', '')
                            energy_data['end_time'] = session.get('end_time', '')
                            energy_data['samples_processed'] = session.get('samples_processed', 0)
                    print(f"      ✓ Energy JSON: {energy_data['num_sessions']} sessions, {energy_data['total_emissions_kg']:.6f} kg CO2")
                except Exception as e:
                    print(f"      ⚠️  Error reading energy tracking: {e}")
            else:
                print(f"      ⚠️  No energy tracking file found: {energy_file}")

            # Read CodeCarbon emissions.csv and sum all matching sessions
            # Strategy from rq1_codecarbon_analysis.ipynb:
            # 1. Find initial session by exp_base timestamp
            # 2. Take that session + next (N-1) chronological sessions
            # This avoids matching failed/abandoned runs
            emissions_data = {}
            if codecarbon_path.exists():
                try:
                    emissions_df = pd.read_csv(codecarbon_path)

                    # Extract the time part from exp_base (e.g., "095820" from "...20251011-095820")
                    time_part = exp_base.split('_')[-1].split('-')[-1]  # Gets "095820"

                    # Filter to same date and sort chronologically
                    same_date_df = emissions_df[
                        emissions_df['project_name'].str.contains(match_prefix, na=False)
                    ].copy()

                    if len(same_date_df) > 0:
                        # Sort by timestamp
                        same_date_df['timestamp'] = pd.to_datetime(same_date_df['timestamp'])
                        same_date_df = same_date_df.sort_values('timestamp')

                        # Find the initial session
                        initial_mask = same_date_df['project_name'].str.contains(time_part, na=False)

                        if initial_mask.any():
                            # Get position of initial session
                            initial_idx = same_date_df[initial_mask].index[0]
                            pos = same_date_df.index.get_loc(initial_idx)

                            # Take initial session + next (expected_sessions - 1)
                            expected_sessions = energy_data.get('num_sessions', 1)
                            matching_rows = same_date_df.iloc[pos:pos+expected_sessions]

                            print(f"      📍 Found initial session at {time_part}, taking {expected_sessions} consecutive sessions")
                        else:
                            # Fallback: couldn't find initial timestamp, take all from this date
                            print(f"      ⚠️  Could not find initial timestamp {time_part}, using all {len(same_date_df)} sessions from date")
                            matching_rows = same_date_df
                    else:
                        matching_rows = pd.DataFrame()

                    if len(matching_rows) > 0:
                        # SUM energy/emissions values across all sessions
                        emissions_data = {
                            'duration_seconds': matching_rows['duration'].sum(),
                            'emissions_kg_codecarbon': matching_rows['emissions'].sum(),
                            'energy_consumed_kwh': matching_rows['energy_consumed'].sum(),
                            'cpu_energy_kwh': matching_rows['cpu_energy'].sum(),
                            'gpu_energy_kwh': matching_rows['gpu_energy'].sum(),
                            'ram_energy_kwh': matching_rows['ram_energy'].sum(),
                            'gpu_model': matching_rows.iloc[0].get('gpu_model', ''),
                            'cpu_model': matching_rows.iloc[0].get('cpu_model', ''),
                            'num_codecarbon_sessions': len(matching_rows),
                        }
                        if len(matching_rows) > 1:
                            print(f"      📝 Multi-session: {len(matching_rows)} sessions summed")
                        print(f"      ✓ CodeCarbon: {emissions_data['energy_consumed_kwh']:.6f} kWh, {emissions_data['emissions_kg_codecarbon']:.6f} kg CO2")
                    else:
                        print(f"      ⚠️  No matching emissions data for prefix {match_prefix}")
                except Exception as e:
                    print(f"      ⚠️  Error reading emissions: {e}")
            else:
                print(f"      ⚠️  No emissions.csv found at {codecarbon_path}")

            # Determine hardware and phase
            if 'mars' in result_dir:
                hardware = 'Mars (RTX A5000)'
                if 'rerun' in result_dir:
                    phase = 'Phase 1b (Mars Rerun)'
                    # Only few-shot experiments have CWE vs LLM distinction
                    if metadata['prompting'] == 'Few-shot':
                        prompt_version = 'CWE-based'
                    else:
                        prompt_version = 'Zero-shot (no examples)'
                else:
                    phase = 'Phase 1 (Mars Initial)'
                    if metadata['prompting'] == 'Few-shot':
                        prompt_version = 'LLM-generated'
                    else:
                        prompt_version = 'Zero-shot (no examples)'
            elif 'runpod' in result_dir:
                hardware = 'RunPod (H100)'
                if 'rerun' in result_dir:
                    if metadata['model_size'] == '30B':
                        phase = 'Phase 2b (RunPod 30B Rerun)'
                    else:
                        phase = 'Phase 2c (RunPod 4B H100)'
                    # Only few-shot experiments have CWE vs LLM distinction
                    if metadata['prompting'] == 'Few-shot':
                        prompt_version = 'CWE-based'
                    else:
                        prompt_version = 'Zero-shot (no examples)'
                else:
                    phase = 'Phase 2a (RunPod 30B Initial)'
                    if metadata['prompting'] == 'Few-shot':
                        prompt_version = 'LLM-generated'
                    else:
                        prompt_version = 'Zero-shot (no examples)'
            else:
                hardware = 'Unknown'
                phase = 'Unknown'
                prompt_version = 'Unknown'

            # Combine all data
            row_data = {
                'experiment_id': f"{metadata['model_size']}_{metadata['model_type']}_{metadata['prompting']}_{phase}",
                'phase': phase,
                'hardware': hardware,
                'model_size': metadata['model_size'],
                'model_type': metadata['model_type'],
                'prompting': metadata['prompting'],
                'prompt_version': prompt_version,
                'full_model_name': metadata['full_model_name'],
                'timestamp': metadata['timestamp'],
                'result_directory': result_dir,
                **metrics,
                **energy_data,
                **emissions_data,
            }

            all_data.append(row_data)
            print(f"      ✅ Collected: {row_data['experiment_id']}")

    return pd.DataFrame(all_data)

if __name__ == '__main__':
    print("=" * 80)
    print("Vulnerability Detection Data Collection")
    print("=" * 80)

    # Collect data
    df = collect_data()

    # Sort by phase, model_size, model_type, prompting
    df = df.sort_values(['phase', 'model_size', 'model_type', 'prompting'])

    # Save to CSV
    output_file = PROJECT_ROOT / 'results' / 'analysis' / 'vuln_detection_master_dataset.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)

    print("\n" + "=" * 80)
    print(f"✅ Data collection complete!")
    print(f"📊 Total experiments: {len(df)}")
    print(f"💾 Saved to: {output_file}")
    print("=" * 80)

    # Print summary
    print("\n📋 Experiment Summary:")
    print(df[['experiment_id', 'Accuracy', 'F1_Score', 'energy_consumed_kwh', 'emissions_kg_codecarbon']].to_string(index=False))
