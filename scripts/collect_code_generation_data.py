#!/usr/bin/env python3
"""
Data Collection Script for Code Generation Experiments

This script collects all code generation experiment data from mars_codegen and runpod_codegen
directories, including HumanEval Pass@1 scores and energy consumption metrics.

Author: Agent Green
Date: November 2025
"""

import pandas as pd
import json
from pathlib import Path
import re
from datetime import datetime

# Manual experiment mappings (similar to vuln detection)
EXPERIMENT_MAPPINGS = {
    'results/mars_codegen': {
        'Sa-zero_Qwen-Qwen3-4B-Instruct-2507': {
            'evaluation_file': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251106-210549_detailed_results_evaluation.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251106-210549',
            'codecarbon_dir': 'codecarbon_baseline_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-4B-Instruct-2507': {
            'evaluation_file': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251106-221304_detailed_results_evaluation.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251106-221304',
            'codecarbon_dir': 'codecarbon_baseline_sa-few'
        },
        'Sa-zero_Qwen-Qwen3-4B-Thinking-2507': {
            'evaluation_file': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251106-210015_detailed_results_evaluation.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251106-210015',
            'codecarbon_dir': 'codecarbon_thinking_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-4B-Thinking-2507': {
            'evaluation_file': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-220000_detailed_results_evaluation.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-220000',
            'codecarbon_dir': 'codecarbon_thinking_sa-few'
        },
    },
    'results/runpod_codegen': {
        'Sa-zero_Qwen-Qwen3-4B-Instruct-2507': {
            'evaluation_file': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251107-131154_detailed_results_evaluation.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251107-131154',
            'codecarbon_dir': 'codecarbon_baseline_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-4B-Instruct-2507': {
            'evaluation_file': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251107-133348_detailed_results_evaluation.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251107-133348',
            'codecarbon_dir': 'codecarbon_baseline_sa-few'
        },
        'Sa-zero_Qwen-Qwen3-4B-Thinking-2507': {
            'evaluation_file': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251107-133841_detailed_results_evaluation.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251107-133841',
            'codecarbon_dir': 'codecarbon_thinking_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-4B-Thinking-2507': {
            'evaluation_file': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-144419_detailed_results_evaluation.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-144419',
            'codecarbon_dir': 'codecarbon_thinking_sa-few'
        },
        'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507': {
            'evaluation_file': 'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_20251107-123658_detailed_results_evaluation.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_20251107-123658',
            'codecarbon_dir': 'codecarbon_baseline_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507': {
            'evaluation_file': 'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_20251107-130505_detailed_results_evaluation.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_20251107-130505',
            'codecarbon_dir': 'codecarbon_baseline_sa-few'
        },
        'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507': {
            'evaluation_file': 'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20251107-123611_detailed_results_evaluation.json',
            'exp_base': 'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20251107-123611',
            'codecarbon_dir': 'codecarbon_thinking_sa-zero'
        },
        'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507': {
            'evaluation_file': 'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20251107-132927_detailed_results_evaluation.json',
            'exp_base': 'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20251107-132927',
            'codecarbon_dir': 'codecarbon_thinking_sa-few'
        },
    }
}

# Phase mapping for each directory
PHASE_MAPPING = {
    'results/mars_codegen': 'Phase 3a (Mars Code Gen)',
    'results/runpod_codegen': 'Phase 3b (RunPod Code Gen)'
}

# Hardware mapping
HARDWARE_MAPPING = {
    'results/mars_codegen': 'Mars (RTX A5000)',
    'results/runpod_codegen': 'RunPod (H100)'
}


def extract_model_metadata(exp_name):
    """Extract model metadata from experiment name"""
    metadata = {
        'model_size': None,
        'model_type': None,
        'prompting': None
    }

    # Extract model size
    if '4B' in exp_name:
        metadata['model_size'] = '4B'
    elif '30B' in exp_name:
        metadata['model_size'] = '30B'

    # Extract model type
    if 'Thinking' in exp_name:
        metadata['model_type'] = 'Thinking'
    elif 'Instruct' in exp_name:
        metadata['model_type'] = 'Instruct'

    # Extract prompting strategy
    if 'Sa-zero' in exp_name or 'zero' in exp_name.lower():
        metadata['prompting'] = 'Zero-shot'
    elif 'Sa-few' in exp_name or 'few' in exp_name.lower():
        metadata['prompting'] = 'Few-shot'

    return metadata


def load_evaluation_results(eval_file):
    """Load evaluation results from JSON"""
    with open(eval_file, 'r') as f:
        data = json.load(f)

    metrics = data.get('metrics', {})
    return {
        'pass_at_1': metrics.get('pass@1', 0),
        'pass_rate_pct': metrics.get('pass_rate_percentage', 0),
        'total_samples': metrics.get('total_samples', 0),
        'passed_samples': metrics.get('passed_samples', 0),
        'failed_samples': metrics.get('failed_samples', 0),
        'timestamp': data.get('timestamp', '')
    }


def load_codecarbon_data(emissions_file, exp_base):
    """Load and sum CodeCarbon data for multi-session experiments"""
    if not emissions_file.exists():
        print(f"  ⚠️  CodeCarbon file not found: {emissions_file}")
        return None

    emissions_df = pd.read_csv(emissions_file)

    # Extract date and model pattern for matching
    match_prefix = '_'.join(exp_base.split('_')[:-1])  # Everything except timestamp
    time_part = exp_base.split('_')[-1].split('-')[-1]  # Gets time like "123658"

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

            # For code gen, most are single session, but check project_name for session count
            # e.g., "Sa-zero_..._session_1" means 1 session
            project_name = same_date_df.iloc[pos]['project_name']
            if '_session_' in project_name:
                session_num = int(project_name.split('_session_')[-1])
                expected_sessions = session_num
            else:
                expected_sessions = 1

            # Take initial session + next (expected_sessions - 1)
            matching_rows = same_date_df.iloc[pos:pos+expected_sessions]

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
                    'start_time': matching_rows.iloc[0]['timestamp'],
                    'end_time': matching_rows.iloc[-1]['timestamp']
                }

                print(f"  ✓ CodeCarbon: {len(matching_rows)} session(s), {emissions_data['energy_consumed_kwh']:.4f} kWh")
                return emissions_data

    print(f"  ⚠️  No matching sessions found in CodeCarbon")
    return None


def collect_all_experiments():
    """Collect all code generation experiment data"""
    print("=" * 80)
    print("CODE GENERATION DATA COLLECTION")
    print("=" * 80)

    all_data = []

    for result_dir, experiments in EXPERIMENT_MAPPINGS.items():
        result_path = Path(result_dir)
        print(f"\n📂 Processing directory: {result_dir}")
        print(f"   Phase: {PHASE_MAPPING[result_dir]}")
        print(f"   Hardware: {HARDWARE_MAPPING[result_dir]}")

        for exp_name, config in experiments.items():
            print(f"\n📊 Processing {exp_name}")

            # Load evaluation results
            eval_file = result_path / config['evaluation_file']
            if not eval_file.exists():
                print(f"  ⚠️  Evaluation file not found: {eval_file}")
                continue

            eval_results = load_evaluation_results(eval_file)
            print(f"  ✓ Evaluation: Pass@1 = {eval_results['pass_at_1']*100:.2f}%, {eval_results['passed_samples']}/{eval_results['total_samples']} passed")

            # Load CodeCarbon data
            codecarbon_dir = result_path / config['codecarbon_dir']
            emissions_file = codecarbon_dir / 'emissions.csv'
            emissions_data = load_codecarbon_data(emissions_file, config['exp_base'])

            # Extract metadata
            metadata = extract_model_metadata(exp_name)

            # Construct full model name from exp_base
            full_model_name = '_'.join(config['exp_base'].split('_')[1:-1])

            # Create experiment ID
            experiment_id = f"{metadata['model_size']}_{metadata['model_type']}_{metadata['prompting']}_{PHASE_MAPPING[result_dir]}"

            # Combine all data
            experiment_data = {
                'experiment_id': experiment_id,
                'phase': PHASE_MAPPING[result_dir],
                'hardware': HARDWARE_MAPPING[result_dir],
                'model_size': metadata['model_size'],
                'model_type': metadata['model_type'],
                'prompting': metadata['prompting'],
                'full_model_name': full_model_name,
                'timestamp': config['exp_base'].split('_')[-1],
                'result_directory': result_dir,
                **eval_results
            }

            # Add emissions data if available
            if emissions_data:
                experiment_data.update(emissions_data)

            all_data.append(experiment_data)
            print(f"  ✅ Collected: {experiment_id}")

    return all_data


def main():
    """Main execution function"""
    # Collect all data
    all_data = collect_all_experiments()

    # Create DataFrame
    df = pd.DataFrame(all_data)

    # Save to CSV
    output_dir = Path('results/analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'code_generation_master_dataset.csv'

    df.to_csv(output_file, index=False)

    print("\n" + "=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print(f"\n✅ Collected {len(df)} code generation experiments")
    print(f"📊 Output file: {output_file}")

    # Display summary
    print("\n📈 Summary Statistics:")
    print(f"   Average Pass@1: {df['pass_at_1'].mean()*100:.2f}%")
    print(f"   Average Energy: {df['energy_consumed_kwh'].mean():.3f} kWh")
    print(f"   Average Emissions: {df['emissions_kg_codecarbon'].mean():.3f} kg CO2")

    print("\n📊 Breakdown:")
    print(f"   By Model Size: {dict(df['model_size'].value_counts())}")
    print(f"   By Model Type: {dict(df['model_type'].value_counts())}")
    print(f"   By Prompting: {dict(df['prompting'].value_counts())}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
