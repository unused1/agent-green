"""
Context Overflow Logger - Captures details when multi-agent conversations hit context limits
"""

import json
import os
from datetime import datetime
from pathlib import Path


class ContextOverflowLogger:
    """Logs context overflow errors with conversation details for research analysis"""

    def __init__(self, log_file="context_overflow_log.jsonl"):
        self.log_file = log_file

    def log_overflow(self,
                     sample_idx,
                     sample_num,
                     total_samples,
                     phase,
                     phase_name,
                     error_message,
                     conversation_history=None,
                     last_response=None,
                     experiment_name=None):
        """
        Log a context overflow error with full details

        Args:
            sample_idx: Sample index in dataset
            sample_num: Current sample number (1-indexed)
            total_samples: Total samples in experiment
            phase: Phase number (1-4)
            phase_name: Name of the phase (e.g., "Security Researcher", "Code Author")
            error_message: Full error message from exception
            conversation_history: Dict with all prior agent responses
            last_response: The response that caused overflow (last 10000 chars)
            experiment_name: Name of the experiment
        """

        overflow_record = {
            "timestamp": datetime.now().isoformat(),
            "experiment": experiment_name,
            "sample_idx": sample_idx,
            "sample_num": sample_num,
            "total_samples": total_samples,
            "phase": phase,
            "phase_name": phase_name,
            "error_message": error_message,
            "conversation_history": conversation_history or {},
            "last_response_tail": last_response[-10000:] if last_response else None,
            "last_response_length": len(last_response) if last_response else 0,
        }

        # Append to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(overflow_record) + '\n')

        print(f"\n⚠️ Context overflow logged to {self.log_file}")
        print(f"   Sample {sample_num}/{total_samples}, idx: {sample_idx}")
        print(f"   Phase {phase}/4: {phase_name}")
        print(f"   Last response length: {len(last_response) if last_response else 0} chars")

        # Extract and print repeating pattern if detectable
        if last_response and len(last_response) > 1000:
            tail = last_response[-1000:]
            if self._detect_repetition(tail):
                print(f"   ⚠️ REPETITION DETECTED in last 1000 chars")

    def _detect_repetition(self, text, min_pattern_len=50):
        """Simple repetition detection - check if last N chars repeat"""
        if len(text) < min_pattern_len * 2:
            return False

        # Check if last quarter repeats in previous quarter
        quarter_len = len(text) // 4
        last_quarter = text[-quarter_len:]
        prev_quarter = text[-quarter_len*2:-quarter_len]

        # If 80% similarity, likely repetition
        if last_quarter == prev_quarter:
            return True

        return False

    def get_overflow_summary(self):
        """Get summary statistics of context overflows"""
        if not os.path.exists(self.log_file):
            return {"total_overflows": 0}

        overflows = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                overflows.append(json.loads(line))

        # Summary stats
        phase_counts = {}
        sample_counts = {}

        for overflow in overflows:
            phase = overflow['phase_name']
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

            sample_idx = overflow['sample_idx']
            sample_counts[sample_idx] = sample_counts.get(sample_idx, 0) + 1

        return {
            "total_overflows": len(overflows),
            "phase_breakdown": phase_counts,
            "repeated_samples": {k: v for k, v in sample_counts.items() if v > 1},
            "unique_problematic_samples": len(sample_counts)
        }
