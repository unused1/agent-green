# CodeCarbon Session Interpretation Guide

**Date**: 2025-10-12
**Purpose**: Understanding how to interpret CodeCarbon emissions.csv with multiple sessions

---

## Understanding Sessions

### What is a Session?

A **session** is a period of continuous energy tracking from when `tracker.start()` is called until `tracker.stop()` is executed. A new session is created when:

1. You start the experiment
2. You press Ctrl+C and then resume (new session_N)
3. An error occurs and you retry (new run with new timestamp)

### Session Data Sources

We have TWO complementary data sources:

1. **`energy_tracking.json`** (custom code)
   - Tracks sessions for ONE experiment run (identified by timestamp)
   - Accumulates emissions across resume/retry within that run
   - Stored with experiment results

2. **`emissions.csv`** (CodeCarbon library)
   - Appends ALL sessions to one shared CSV file per `codecarbon_*` directory
   - May contain sessions from MULTIPLE experiment runs (including failed/test runs)
   - Contains detailed hardware metrics

---

## Experiment Session Analysis

### Baseline Zero-shot

**Results**: 386 samples processed successfully

**Energy Tracking JSON** (Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251011-083716):
- 1 session (no interruptions)
- Start: 08:37:16
- Total: **0.154753 kg CO2**

**CodeCarbon emissions.csv**:
- 4 rows total
- **Only 1 row matches this experiment** (timestamp: 10:20:20, project contains "083716")
- Other 3 rows are from EARLIER FAILED RUNS:
  - 06:07:02 (experiment 060641): 0.000285 kg CO2
  - 06:09:44 (experiment 060924): 0.000271 kg CO2
  - 07:47:59 (experiment 061002): 0.088325 kg CO2
  - **10:20:20 (experiment 083716)**: **0.154753 kg CO2** ← THIS ONE

**Conclusion**: Use only the matching session (row 4) for this experiment.

### Baseline Few-shot

**Results**: 386 samples processed successfully

**Energy Tracking JSON** (Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251011-102915):
- 3 sessions (2 Ctrl+C interruptions, then resumed)
- Starts: 10:29:15, 11:02:58, 16:51:40
- Total: **0.113401 kg CO2**

**CodeCarbon emissions.csv**:
- 3 rows total
- ALL 3 rows match this experiment (timestamps: 10:55:48, 11:51:57, 16:51:41)
- All project names contain "102915" (the experiment timestamp)
- Total: **0.113401 kg CO2** ✓ PERFECT MATCH

**Conclusion**: Sum all 3 sessions for this experiment.

### Thinking Zero-shot

**Results**: 383 samples processed (1 skipped)

**Energy Tracking JSON** (Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-095820):
- 6 sessions (multiple Ctrl+C, resume, skip)
- Starts: 09:58:20, 10:20:16, 10:25:44, 10:44:27, 11:02:31, 18:08:06
- Total: **0.731428 kg CO2**

**CodeCarbon emissions.csv**:
- 13 rows total
- **Only 6 rows match this experiment** (project names contain "095820" or later session numbers)
- Other 7 rows are from EARLIER FAILED RUNS (experiments 060557, 060901, 080556, etc.)

**Matching sessions**:
- 10:20:07 (session_1, contains "095820"): 0.032715 kg CO2
- 10:25:24 (session_2): 0.007678 kg CO2
- 10:43:56 (session_3): 0.027320 kg CO2
- 10:55:41 (session_4): 0.016842 kg CO2
- 17:58:49 (session_5): 0.625706 kg CO2
- 18:22:13 (session_6): 0.021167 kg CO2
- **Total**: **0.731428 kg CO2** ✓ PERFECT MATCH

**Conclusion**: Filter by project_name containing "095820" to get accurate sessions.

### Thinking Few-shot

**Results**: 386 samples processed successfully

**Energy Tracking JSON** (Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251011-103534):
- 4 sessions (3 Ctrl+C interruptions, then resumed)
- Starts: 10:35:34, 11:02:46, 11:09:39, 16:59:28
- Total: **0.446900 kg CO2**

**CodeCarbon emissions.csv**:
- 4 rows total
- ALL 4 rows match this experiment (all project names contain "103534")
- Total: **0.446900 kg CO2** ✓ PERFECT MATCH

**Conclusion**: Sum all 4 sessions for this experiment.

---

## How to Filter emissions.csv Correctly

### Method 1: Filter by Project Name (Recommended)

Each experiment run has a unique timestamp in its name. Extract it and filter:

```python
# Example: Baseline Zero-shot
exp_timestamp = "083716"  # From Sa-zero_..._20251011-083716
cc_df = pd.read_csv('codecarbon_baseline_sa-zero/emissions.csv')

# Filter to only matching sessions
matching = cc_df[cc_df['project_name'].str.contains(exp_timestamp)]
total_emissions = matching['emissions'].sum()
```

### Method 2: Match by Session Start Times

Compare session start times in energy_tracking.json with timestamps in emissions.csv:

```python
import json
from datetime import datetime

# Load energy tracking
with open('Sa-zero_..._energy_tracking.json') as f:
    energy = json.load(f)

session_starts = [s['start_time'] for s in energy['session_history']]

# Filter emissions.csv by matching timestamps (within 5 minutes)
# ... implementation ...
```

---

## Summary Table

| Experiment | Total Rows in CSV | Matching Rows | Other Rows (Failed/Test) | Cross-Validation |
|---|---|---|---|---|
| Baseline Zero-shot | 4 | 1 | 3 (06:07, 06:09, 07:48) | ✓ MATCH |
| Baseline Few-shot | 3 | 3 | 0 | ✓ MATCH |
| Thinking Zero-shot | 13 | 6 | 7 (06:07, 06:45, 08:06, etc.) | ✓ MATCH |
| Thinking Few-shot | 4 | 4 | 0 | ✓ MATCH |

---

## Reporting Guidelines for Research Paper

### For Total Emissions

**Option 1: Use energy_tracking.json** (Simpler)
- Directly reports the total for each experiment
- Already filtered to the successful run
- Matches the result files

**Option 2: Use filtered emissions.csv** (More rigorous)
- Filter by project_name containing experiment timestamp
- Sum the matching sessions
- Cross-validate with energy_tracking.json
- Advantage: Can cite CodeCarbon directly

### For Hardware Component Breakdown

**Must use emissions.csv** (with filtering):
- CodeCarbon is the authoritative source for CPU/GPU/RAM metrics
- Filter to matching sessions ONLY
- Report: CPU Energy, GPU Energy, RAM Energy, Power Consumption

### Recommended Approach

1. **Main results**: Use energy_tracking.json for total emissions
2. **Hardware details**: Use filtered emissions.csv for component breakdown
3. **Cross-validation**: Show both match (builds confidence)
4. **Transparency**: Document the filtering process in methodology

### Example Methodology Text

> "Energy consumption was tracked using CodeCarbon v2.7.1 (OfflineEmissionsTracker).
> Each experiment run generated multiple sessions due to resume functionality after
> interruptions. The emissions.csv file contains historical data from all runs; we
> filtered sessions by matching the experiment timestamp in the project_name field.
> We cross-validated filtered CodeCarbon data with our custom energy_tracking.json
> accumulator, confirming < 0.01% difference for all experiments."

---

## Why the Discrepancy Occurred

The initial cross-validation showed differences because:

1. **emissions.csv accumulates ALL runs** in the same directory
2. **Earlier test runs** (before 08:00, 09:00) were NOT deleted
3. **Our filter was missing** - we summed ALL rows instead of matching ones

The fix:
- Filter emissions.csv by project_name containing the experiment timestamp
- Then sum only the matching sessions
- Result: Perfect match with energy_tracking.json

---

**Key Takeaway**: Always filter CodeCarbon emissions.csv by project_name to isolate the specific experiment run. The CSV is append-only and contains historical data from all runs in that directory.

---

*Last Updated: 2025-10-12*
*Verified by: scripts/analyze_sessions.py*
