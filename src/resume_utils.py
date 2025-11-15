"""
Resume/Restart Utilities for Agent Experiments

This module provides standardized functionality for resuming interrupted experiments,
tracking energy consumption across sessions, and managing experimental state.

Usage:
    from resume_utils import ExperimentResume

    # Initialize with experiment parameters
    resume = ExperimentResume(
        result_dir="./results",
        design="DA-vuln",
        model="qwen3-4b-instruct",
        exp_name="DA-vuln_qwen3-4b-instruct_20251115-120000"
    )

    # Check for existing experiments and prompt user
    exp_name, detailed_file, energy_file, skip_next = resume.initialize()

    # Load existing results
    existing_results = resume.load_results(detailed_file)
    energy_data = resume.load_energy(energy_file)

    # Filter remaining samples
    remaining = resume.filter_remaining_samples(samples, existing_results, id_field='idx')

    # Save energy after experiment
    resume.save_energy(energy_data, energy_file, emissions, len(remaining))
"""

import os
import json
import glob
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class ExperimentResume:
    """Handles experiment resume/restart functionality"""

    def __init__(self, result_dir: str, design: str, model: str, exp_name: str):
        """
        Initialize ExperimentResume

        Args:
            result_dir: Directory where results are saved
            design: Experiment design identifier (e.g., "DA-vuln", "MA-code")
            model: Model name (e.g., "qwen3-4b-instruct")
            exp_name: Base experiment name
        """
        self.result_dir = result_dir
        self.design = design
        self.model = model
        self.exp_name = exp_name
        os.makedirs(result_dir, exist_ok=True)

    def find_most_recent_results(self) -> Optional[str]:
        """
        Find the most recent result files for this design/model combination

        Returns:
            Base name of most recent experiment, or None if not found
        """
        pattern = f"{self.design}_{self.model}_*_detailed_results.jsonl"
        matching_files = glob.glob(os.path.join(self.result_dir, pattern))

        if matching_files:
            most_recent = max(matching_files, key=os.path.getmtime)
            base_name = os.path.basename(most_recent).replace('_detailed_results.jsonl', '')
            print(f"[RESUME] Found existing results: {most_recent}")
            return base_name
        return None

    def prompt_resume_options(self, existing_base: str) -> Tuple[str, bool]:
        """
        Prompt user for resume options

        Args:
            existing_base: Base name of existing experiment

        Returns:
            Tuple of (experiment_name, skip_next_sample)
        """
        print(f"\n[FOUND] Existing experiment: {existing_base}")
        print("Options:")
        print("  1. Resume from last completed sample (continue normally)")
        print("  2. Skip the next sample and mark as failed (if it's problematic)")
        print("  3. Start a fresh new experiment")

        response = input("\nEnter choice (1/2/3): ").strip()

        if response == '1':
            print(f"[RESUME] Continuing with experiment: {existing_base}")
            return existing_base, False
        elif response == '2':
            print(f"[RESUME] Will skip the next problematic sample and mark as FAILED")
            return existing_base, True
        else:
            print(f"[NEW] Starting fresh experiment: {self.exp_name}")
            return self.exp_name, False

    def initialize(self) -> Tuple[str, str, str, bool]:
        """
        Initialize experiment with resume capability

        Returns:
            Tuple of (exp_name, detailed_file, energy_file, skip_next_sample)
        """
        skip_next_sample = False
        exp_name = self.exp_name

        # Check for existing experiment
        existing_base = self.find_most_recent_results()
        if existing_base:
            exp_name, skip_next_sample = self.prompt_resume_options(existing_base)

        # Construct file paths
        detailed_file = os.path.join(self.result_dir, f"{exp_name}_detailed_results.jsonl")
        energy_file = os.path.join(self.result_dir, f"{exp_name}_energy_tracking.json")

        return exp_name, detailed_file, energy_file, skip_next_sample

    @staticmethod
    def load_results(detailed_file: str) -> List[Dict[str, Any]]:
        """
        Load existing results if the script was interrupted

        Args:
            detailed_file: Path to detailed results JSONL file

        Returns:
            List of existing result dictionaries
        """
        results = []
        if os.path.exists(detailed_file):
            print(f"Found existing results file: {detailed_file}")
            with open(detailed_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            results.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
            print(f"Loaded {len(results)} existing results")
        return results

    @staticmethod
    def load_energy(energy_file: str) -> Dict[str, Any]:
        """
        Load existing energy consumption data

        Args:
            energy_file: Path to energy tracking JSON file

        Returns:
            Dictionary with energy data (total_emissions, sessions, session_history)
        """
        if os.path.exists(energy_file):
            with open(energy_file, 'r') as f:
                energy_data = json.load(f)
            print(f"Loaded existing energy data: {energy_data['total_emissions']:.6f} kg CO2 from {energy_data['sessions']} sessions")
            return energy_data
        else:
            return {
                "total_emissions": 0.0,
                "sessions": 0,
                "session_history": []
            }

    @staticmethod
    def save_energy(energy_data: Dict[str, Any], energy_file: str, emissions: float, samples_processed: int):
        """
        Update and save energy consumption data

        Args:
            energy_data: Current energy data dictionary
            energy_file: Path to energy tracking JSON file
            emissions: Emissions from this session (kg CO2)
            samples_processed: Number of samples processed in this session
        """
        energy_data['total_emissions'] += emissions
        energy_data['sessions'] += 1
        energy_data['session_history'].append({
            'timestamp': datetime.now().isoformat(),
            'emissions_kg_co2': emissions,
            'samples_processed': samples_processed
        })

        with open(energy_file, 'w') as f:
            json.dump(energy_data, f, indent=2)

        print(f"Total emissions (all sessions): {energy_data['total_emissions']:.6f} kg CO2")

    @staticmethod
    def filter_remaining_samples(
        samples: List[Dict[str, Any]],
        existing_results: List[Dict[str, Any]],
        id_field: str = 'idx'
    ) -> List[Dict[str, Any]]:
        """
        Filter out already processed samples

        Args:
            samples: Full list of samples
            existing_results: List of already processed results
            id_field: Field name for sample ID (default: 'idx', could be 'task_id')

        Returns:
            List of remaining unprocessed samples
        """
        processed_ids = {r.get(id_field, r.get('id', -1)) for r in existing_results}
        remaining = [s for s in samples if s.get(id_field, s.get('id', -1)) not in processed_ids]

        print(f"\nProcessing {len(remaining)} remaining samples (out of {len(samples)} total)")
        print(f"Already completed: {len(processed_ids)} samples\n")

        return remaining

    @staticmethod
    def create_skip_result(sample: Dict[str, Any], id_field: str = 'idx') -> Dict[str, Any]:
        """
        Create a failed result for a skipped sample

        Args:
            sample: Sample to skip
            id_field: Field name for sample ID

        Returns:
            Dictionary representing skipped result
        """
        result = dict(sample)
        result.update({
            'error': 'USER_SKIP',
            'timestamp': datetime.now().isoformat(),
            'skipped': True
        })

        # Add task-specific skip markers
        if 'vuln' in sample or 'target' in sample:
            result['vuln'] = -1
            result['reasoning'] = 'SKIPPED - Sample marked as problematic by user'
        elif 'generated_solution' in sample or 'task_id' in sample:
            result['generated_solution'] = ''
            result['prompt'] = sample.get('prompt', '')

        return result
