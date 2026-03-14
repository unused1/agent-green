#!/usr/bin/env python3
"""
RQ2 Pod Monitor - Monitors all 4 active RunPod experiments
Detects context overflows, stuck processes, and documents issues
"""

import subprocess
import json
import re
from datetime import datetime
from pathlib import Path

# Pod configuration
PODS = {
    2: {"ip": "205.196.17.138", "port": 12500, "experiment": "MA-vuln-zero", "name": "4B-Thinking Zero-Shot"},
    4: {"ip": "205.196.17.123", "port": 11670, "experiment": "MA-vuln-few", "name": "4B-Thinking Few-Shot"},
    6: {"ip": "63.141.33.85", "port": 22145, "experiment": "MA-vuln-zero", "name": "30B-Thinking Zero-Shot"},
    8: {"ip": "213.181.122.251", "port": 15454, "experiment": "MA-vuln-few", "name": "30B-Thinking Few-Shot"},
}

SSH_KEY = "~/.ssh/runpod_ed25519"
TRACKING_FILE = "docs/RQ2_Experiment_Tracking.md"
MONITOR_LOG = "pod_monitor.log"

def log_message(message):
    """Log message to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(MONITOR_LOG, "a") as f:
        f.write(log_entry + "\n")

def ssh_command(pod_id, command):
    """Execute SSH command on a pod"""
    pod = PODS[pod_id]
    ssh_cmd = f"ssh root@{pod['ip']} -p {pod['port']} -i {SSH_KEY} '{command}'"
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return None, "SSH command timed out"

def check_process_running(pod_id):
    """Check if experiment process is running"""
    stdout, stderr = ssh_command(pod_id, "ps aux | grep 'multi_agent.*\.py' | grep -v grep")
    if stdout:
        # Extract CPU usage and runtime
        parts = stdout.split()
        cpu_usage = parts[2] if len(parts) > 2 else "N/A"
        return True, cpu_usage
    return False, None

def get_last_completed_sample(pod_id):
    """Get the last completed sample from results file"""
    exp = PODS[pod_id]["experiment"]
    stdout, _ = ssh_command(pod_id, f"tail -1 /workspace/agent-green/results/*{exp}*detailed_results.jsonl 2>/dev/null")

    if stdout:
        try:
            result = json.loads(stdout)
            return result.get("idx"), result.get("vulnerability_detected"), result.get("reasoning", "")[:100]
        except json.JSONDecodeError:
            return None, None, None
    return None, None, None

def check_for_context_overflow(pod_id):
    """Check recent output for context overflow errors"""
    # Check if process is consuming high CPU but not progressing
    stdout, _ = ssh_command(pod_id, "tail -100 /workspace/agent-green/*.log 2>/dev/null | grep -i 'maximum context length\\|65536\\|overflow' | tail -5")

    if "maximum context length" in stdout.lower():
        # Try to extract sample info from recent output
        sample_match = re.search(r'Sample (\d+)/(\d+).*idx[:\s]+(\d+)', stdout)
        if sample_match:
            return True, {
                "sample_num": sample_match.group(1),
                "total": sample_match.group(2),
                "idx": sample_match.group(3)
            }
        return True, None
    return False, None

def get_current_sample_from_output(pod_id):
    """Get current sample being processed from output logs"""
    # Look for the sample info in recent output
    stdout, _ = ssh_command(pod_id, "tail -200 /workspace/agent-green/*.log 2>/dev/null | grep -E 'Processing.*idx:|\\[Sample.*idx:' | tail -1")

    if stdout:
        # Try to extract sample number and idx
        match = re.search(r'Sample (\d+)/(\d+).*idx[:\s]+(\d+)', stdout) or \
                re.search(r'Processing.*(\d+)/(\d+).*idx[:\s]+(\d+)', stdout)
        if match:
            return {
                "sample_num": match.group(1),
                "total": match.group(2),
                "idx": match.group(3)
            }
    return None

def monitor_all_pods():
    """Monitor all pods and return status"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message(f"\n{'='*80}")
    log_message(f"POD MONITORING CYCLE - {timestamp}")
    log_message(f"{'='*80}")

    status_summary = []
    issues_found = []

    for pod_id, config in PODS.items():
        log_message(f"\n--- Pod {pod_id} ({config['name']}) ---")

        # Check if process is running
        is_running, cpu_usage = check_process_running(pod_id)

        if not is_running:
            log_message(f"  ⚠️ WARNING: Process not running!")
            issues_found.append({
                "pod": pod_id,
                "issue": "Process not running",
                "action": "Check if experiment completed or crashed"
            })
            continue

        log_message(f"  ✓ Process running (CPU: {cpu_usage}%)")

        # Get last completed sample
        last_idx, vuln_detected, reasoning = get_last_completed_sample(pod_id)
        if last_idx:
            log_message(f"  Last completed: idx {last_idx} (vuln: {vuln_detected})")

        # Get current sample from output
        current_sample = get_current_sample_from_output(pod_id)
        if current_sample:
            log_message(f"  Current: Sample {current_sample['sample_num']}/{current_sample['total']}, idx: {current_sample['idx']}")

        # Check for context overflow
        has_overflow, overflow_info = check_for_context_overflow(pod_id)
        if has_overflow:
            if overflow_info:
                log_message(f"  🔴 CONTEXT OVERFLOW DETECTED!")
                log_message(f"     Sample {overflow_info['sample_num']}/{overflow_info['total']}, idx: {overflow_info['idx']}")
                issues_found.append({
                    "pod": pod_id,
                    "issue": "Context overflow",
                    "sample": overflow_info,
                    "action": "Resume with skip option 2"
                })
            else:
                log_message(f"  ⚠️ Possible context overflow (need to check manually)")

        status_summary.append({
            "pod": pod_id,
            "running": is_running,
            "cpu": cpu_usage,
            "last_idx": last_idx,
            "current": current_sample,
            "overflow": has_overflow
        })

    # Summary
    log_message(f"\n{'='*80}")
    log_message(f"SUMMARY")
    log_message(f"{'='*80}")
    log_message(f"Pods monitored: {len(PODS)}")
    log_message(f"Running normally: {sum(1 for s in status_summary if s['running'] and not s['overflow'])}")
    log_message(f"Issues detected: {len(issues_found)}")

    if issues_found:
        log_message(f"\n🚨 ISSUES REQUIRING ATTENTION:")
        for issue in issues_found:
            log_message(f"  Pod {issue['pod']}: {issue['issue']}")
            if 'sample' in issue:
                log_message(f"    Sample {issue['sample']['sample_num']}, idx: {issue['sample']['idx']}")
            log_message(f"    Action: {issue['action']}")

    return status_summary, issues_found

def document_issue_in_tracker(pod_id, sample_info, overflow_pattern):
    """
    Document a context overflow issue in the tracking file

    Args:
        pod_id: Pod number
        sample_info: Dict with sample_num, total, idx
        overflow_pattern: Brief description of the overflow pattern
    """
    log_message(f"\n📝 Documenting issue in tracker...")
    log_message(f"   Pod {pod_id}, Sample {sample_info['sample_num']}/{sample_info['total']}, idx: {sample_info['idx']}")
    log_message(f"   Pattern: {overflow_pattern}")
    log_message(f"   Update {TRACKING_FILE} manually with this information")

if __name__ == "__main__":
    print("RQ2 Pod Monitor - Starting monitoring cycle...")
    print(f"Monitoring {len(PODS)} active pods")
    print("-" * 80)

    status, issues = monitor_all_pods()

    print("\n" + "="*80)
    if issues:
        print("⚠️  MANUAL INTERVENTION REQUIRED")
        print("See pod_monitor.log for details")
    else:
        print("✓ All pods running normally")
    print("="*80)
