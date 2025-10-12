# RQ1 Analysis Notebooks

This directory contains Jupyter notebooks for analyzing the Qwen RQ1 vulnerability detection experiments.

## Notebooks Overview

### 1. `rq1_analysis.ipynb` - Main Performance & Energy Analysis

**Purpose**: Primary analysis of model performance and energy consumption

**Outputs**:
- Performance comparison tables (accuracy, precision, recall, F1)
- Confusion matrices for all experiments
- Error analysis (timeouts, skipped samples)
- Energy consumption overview (CO2 emissions, execution time)
- Model comparison charts (Baseline vs Thinking)
- Prompting strategy comparison (Zero-shot vs Few-shot)

**Key Visualizations**:
- `performance_comparison.png` - Side-by-side metric comparison
- `confusion_matrices.png` - 2x2 grid of all experiment confusion matrices
- `energy_comparison.png` - CO2 emissions and execution time charts

**Export Files**:
- `rq1_metrics_summary.xlsx` - Complete metrics in Excel format
- `detailed_metrics.csv` - Detailed performance metrics
- `energy_summary.csv` - Energy consumption summary

### 2. `rq1_codecarbon_analysis.ipynb` - Hardware-Level Energy Analysis

**Purpose**: Detailed hardware component breakdown using CodeCarbon data

**Outputs**:
- Cross-validation: energy_tracking.json vs emissions.csv
- Hardware component energy consumption (CPU, GPU, RAM)
- Power consumption analysis (Watts per component)
- Component energy distribution percentages
- Session-level tracking details

**Key Visualizations**:
- `energy_by_component.png` - Stacked bar chart (CPU/GPU/RAM)
- `power_consumption.png` - Average power and total energy comparison
- `energy_distribution_pies.png` - 4 pie charts showing component breakdown

**Export Files**:
- `rq1_codecarbon_detailed.xlsx` - Hardware metrics and cross-validation
- `hardware_energy_summary.csv` - Component-level energy data
- `energy_cross_validation.csv` - Validation results

## Usage

### Prerequisites

```bash
pip install pandas numpy matplotlib seaborn openpyxl
```

### Running the Analysis

1. **Navigate to project root**:
```bash
cd /Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green
```

2. **Start Jupyter**:
```bash
jupyter notebook notebooks/
```

3. **Run notebooks in order**:
   - First: `rq1_analysis.ipynb` (main analysis)
   - Then: `rq1_codecarbon_analysis.ipynb` (hardware details)

4. **View outputs**:
```bash
ls -lh results/analysis/
```

## Data Sources

### Input Files
- `results/mars/*_detailed_results.jsonl` - Experiment results (384 samples each)
- `results/mars/*_energy_tracking.json` - Custom energy tracking summaries
- `results/mars/codecarbon_*/emissions.csv` - CodeCarbon hardware metrics

### Experiment Mapping
| Experiment Key | Name | CodeCarbon Directory | Result File Prefix |
|---|---|---|---|
| baseline_zero | Baseline Zero-shot | codecarbon_baseline_sa-zero | Sa-zero_Qwen-Qwen3-4B-Instruct-2507 |
| baseline_few | Baseline Few-shot | codecarbon_baseline_sa-few | Sa-few_Qwen-Qwen3-4B-Instruct-2507 |
| thinking_zero | Thinking Zero-shot | codecarbon_thinking_sa-zero | Sa-zero_Qwen-Qwen3-4B-Thinking-2507 |
| thinking_few | Thinking Few-shot | codecarbon_thinking_sa-few | Sa-few_Qwen-Qwen3-4B-Thinking-2507 |

## Dataset Information

- **Total lines**: 386
- **Unique samples**: 384
- **Duplicates**: 2 (indices 349259, 439495)
- **Problematic sample**: 344242 (skipped in Thinking Zero-shot)

See `docs/dataset_duplicate_analysis.md` for details.

## Key Findings

Run the notebooks to generate:

1. **Performance Metrics**: Accuracy, precision, recall, F1 scores
2. **Energy Impact**: Thinking model uses ~X.XX times more energy than Baseline
3. **GPU Dominance**: GPU accounts for ~XX% of total energy consumption
4. **Data Validation**: energy_tracking.json matches emissions.csv (< 0.01% difference)

## Analysis Workflow

```
┌─────────────────────────────────────┐
│  Experiment Results (.jsonl)         │
│  + Energy Tracking (.json)           │
│  + CodeCarbon Data (.csv)            │
└──────────────┬──────────────────────┘
               │
               ├─────────────────────┐
               │                     │
               ▼                     ▼
┌──────────────────────┐  ┌──────────────────────┐
│  rq1_analysis.ipynb  │  │ rq1_codecarbon_      │
│  - Performance       │  │   analysis.ipynb     │
│  - Metrics           │  │ - Hardware breakdown │
│  - Overview energy   │  │ - Power consumption  │
└──────────┬───────────┘  └──────────┬───────────┘
           │                         │
           ▼                         ▼
┌──────────────────────────────────────────┐
│  results/analysis/                       │
│  - Charts (.png)                         │
│  - Tables (.xlsx, .csv)                  │
│  - Summary statistics                    │
└──────────────────────────────────────────┘
```

## Troubleshooting

### Issue: "KeyError: 'error'"
**Solution**: Run `scripts/standardize_results.py` to add missing error columns

### Issue: "CO2 values showing as 0"
**Solution**: Verify energy_tracking.json files exist and use correct field name (`total_emissions`)

### Issue: "File not found"
**Solution**: Ensure you downloaded all results from Mars server using `scripts/download_mars_results.sh`

## Next Steps

After running both notebooks:

1. Review all generated visualizations in `results/analysis/`
2. Check Excel files for complete data tables
3. Verify cross-validation shows < 0.01% difference
4. Use outputs for research paper/report

---

**Last Updated**: 2025-10-12
**Experiments Completed**: 2025-10-11
**Analysis Framework**: Pandas + Matplotlib + Seaborn
