# RQ1 Analysis Summary

**Date**: 2025-10-12  
**Status**: Analysis framework complete, ready for execution

---

## Overview

This document summarizes the complete analysis setup for RQ1 (Thinking vs Baseline models for vulnerability detection).

---

## Key Understanding: CodeCarbon Session Filtering

### The Problem We Discovered

CodeCarbon's `emissions.csv` is **append-only** and contains data from ALL experiment runs in the same directory, including:
- Failed runs
- Test runs  
- Abandoned runs
- The successful run

### The Solution

We must **filter sessions by experiment timestamp** to isolate only the sessions belonging to the successful experiment run.

**Example** (Baseline Zero-shot):
- Raw emissions.csv: 4 rows, 0.2436 kg CO2
- After filtering by "083716": 1 row, 0.1548 kg CO2 ✓ MATCHES energy_tracking.json

### Implementation

```python
# Filter CodeCarbon data by experiment timestamp
exp_timestamp = '083716'  # From filename Sa-zero_..._20251011-083716
cc_df_all = pd.read_csv('emissions.csv')
cc_df = cc_df_all[cc_df_all['project_name'].str.contains(exp_timestamp)]
```

---

## Data Sources

### 1. Custom Energy Tracking (`energy_tracking.json`)

**Source**: Our code in `src/single_agent_vuln.py`

**How it works**:
```python
# Start tracking
tracker = OfflineEmissionsTracker(project_name=f"{exp_name}_session_{N}")
tracker.start()

# Run inference...

# Stop and accumulate
session_emissions = tracker.stop()
energy_data['total_emissions'] += session_emissions  # Cumulative sum
```

**Structure**:
```json
{
  "total_emissions": 0.154753,  // Sum across all sessions
  "sessions": 1,
  "session_history": [
    {
      "session": 1,
      "start_time": "2025-10-11T08:37:16",
      "samples_processed": 386,
      "session_emissions": 0.154753
    }
  ]
}
```

**Use case**: High-level summary, already filtered to successful run

### 2. CodeCarbon Emissions CSV (`emissions.csv`)

**Source**: CodeCarbon library (automatic)

**How it works**:
- Appends one row per `tracker.stop()` call
- Includes detailed hardware metrics
- Stored in shared directory (one CSV per reasoning mode + design)

**Structure** (each row):
```csv
timestamp,project_name,duration,emissions,cpu_energy,gpu_energy,ram_energy,cpu_power,gpu_power,ram_power,...
```

**Use case**: Hardware component breakdown, power analysis (MUST be filtered)

---

## Cross-Validation Results

After proper filtering (verified 2025-10-12):

| Experiment | JSON (kg) | CSV (kg) | Difference | Status |
|---|---|---|---|---|
| Baseline Zero-shot | 0.154753 | 0.154753 | < 0.001% | ✓ MATCH |
| Baseline Few-shot | 0.113401 | 0.113401 | < 0.001% | ✓ MATCH |
| Thinking Zero-shot | 0.731428 | 0.731428 | < 0.001% | ✓ MATCH |
| Thinking Few-shot | 0.446900 | 0.446900 | < 0.001% | ✓ MATCH |

All experiments show **perfect match** (< 0.01% difference) after filtering.

**Key Metrics Confirmed**:
- Baseline models: 0.268 kg CO2 total (average: 0.134 kg)
- Thinking models: 1.178 kg CO2 total (average: 0.589 kg)
- **Thinking uses 4.4x more energy** than Baseline

---

## Analysis Notebooks

### 1. `rq1_analysis.ipynb` - Main Performance Analysis

**Purpose**: Vulnerability detection performance metrics

**Inputs**:
- `*_detailed_results.jsonl` - Per-sample predictions
- `*_energy_tracking.json` - Total emissions

**Outputs**:
- Performance metrics (accuracy, precision, recall, F1)
- Confusion matrices
- Energy consumption overview
- Model comparison charts

**Run**: Complete the TBD values in `docs/rq1_findings.md`

### 2. `rq1_codecarbon_analysis.ipynb` - Hardware-Level Analysis

**Purpose**: Detailed hardware component breakdown

**Inputs**:
- `emissions.csv` (filtered by timestamp!)
- `*_energy_tracking.json` - For cross-validation

**Outputs**:
- CPU/GPU/RAM energy breakdown
- Power consumption analysis
- Component distribution percentages
- Cross-validation table

**Key change**: Now properly filters CodeCarbon sessions

---

## Documentation Created

### Core Findings
- `docs/rq1_findings.md` - Complete findings template (fill in TBD values)

### Technical Details
- `docs/codecarbon_session_interpretation.md` - How to interpret sessions
- `docs/dataset_duplicate_analysis.md` - Dataset issues and validation
- `docs/ANALYSIS_SUMMARY.md` - This document

### Analysis Tools
- `scripts/analyze_sessions.py` - Session filtering validation
- `notebooks/README.md` - Notebook usage guide

---

## How to Complete the Analysis

### Step 1: Run Main Analysis
```bash
jupyter notebook notebooks/rq1_analysis.ipynb
```

This will generate:
- Performance comparison charts
- Confusion matrices  
- Energy visualizations
- Excel/CSV exports

### Step 2: Run CodeCarbon Analysis
```bash
jupyter notebook notebooks/rq1_codecarbon_analysis.ipynb
```

This will generate:
- Hardware component breakdowns
- Power consumption charts
- Cross-validation tables
- Component distribution pies

### Step 3: Update Findings Document

Open `docs/rq1_findings.md` and fill in all TBD values with results from the notebooks.

### Step 4: Verify Cross-Validation

Check that all experiments show < 0.01% difference between energy_tracking.json and filtered emissions.csv.

---

## For the Research Paper

### Energy Data Reporting

**Recommendation**: Use CodeCarbon emissions.csv as the primary source

**Methodology text** (example):
> "Energy consumption was measured using CodeCarbon v2.7.1 (OfflineEmissionsTracker) 
> running on an NVIDIA RTX A5000 GPU. Each experiment generated multiple tracking sessions 
> due to resume functionality after interruptions. We filtered the emissions data by 
> matching the experiment timestamp in the project name to isolate sessions belonging 
> to the successful run (see Supplementary Materials for session analysis). 
> Cross-validation with our custom energy accumulator confirmed < 0.01% difference 
> for all experiments."

**Tables to include**:
1. Total energy consumption (from filtered emissions.csv)
2. Hardware component breakdown (CPU/GPU/RAM)
3. Cross-validation results (showing both sources match)

**Charts to include**:
1. Stacked bar chart of energy by component
2. Power consumption comparison
3. Thinking vs Baseline energy ratio

### Citing CodeCarbon

Proper attribution:
> Benoit Courty, Victor Schmidt, Sasha Luccioni, and others. (2021). 
> CodeCarbon: Estimate and Track Carbon Emissions from Machine Learning Computing. 
> https://github.com/mlco2/codecarbon

---

## Session Counts by Experiment

| Experiment | Sessions | Reason |
|---|---|---|
| Baseline Zero-shot | 1 | Completed without interruption |
| Baseline Few-shot | 3 | 2x Ctrl+C, resumed |
| Thinking Zero-shot | 6 | Multiple Ctrl+C, skip problematic sample |
| Thinking Few-shot | 4 | 3x Ctrl+C, resumed |

**Note**: Multiple sessions are expected and correct. CodeCarbon properly tracks each continuous period and we sum them for total consumption.

---

## Key Takeaways

1. **CodeCarbon emissions.csv requires filtering** by experiment timestamp
2. **energy_tracking.json is pre-filtered** and ready to use
3. **Both sources must match** after proper filtering (validates data quality)
4. **Multiple sessions are normal** due to resume/retry functionality
5. **For papers**: Cite CodeCarbon, explain filtering methodology, show cross-validation

---

## Checks for Submission

- [ ] `docs/rq1_findings.md`
- [ ] `results/analysis/*.png`
- [ ] `results/analysis/*.xlsx`
- [ ] Cross-validation shows < 0.01% difference for all experiments
- [ ] Hardware component percentages look reasonable (GPU dominant)

---

**Status**: ✓ Framework complete, ready to run notebooks and populate findings

**Next**: Execute both notebooks and complete rq1_findings.md
