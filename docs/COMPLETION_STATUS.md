# RQ1 Analysis - Completion Status

**Last Updated**: 2025-10-20
**Phase 1 (4B Models)**: Complete ✅
**Phase 2a (30B-A3B Models)**: Complete ✅

---

## Phase 1: Qwen3-4B Models (COMPLETE ✅)

### 1. Data Collection & Validation
- [x] 4 experiments completed successfully (384 samples each, except 383 for Thinking Zero-shot)
- [x] CodeCarbon energy tracking for all experiments
- [x] Custom energy_tracking.json accumulator
- [x] Cross-validation: Perfect match (< 0.001% difference)

### 2. Session Filtering Solution
- [x] Identified issue: emissions.csv contains ALL runs (test + successful)
- [x] Identified issue: Resume sessions get new timestamps
- [x] Solution implemented: Filter by initial timestamp + take N consecutive sessions
- [x] Validation: All experiments now match between sources

### 3. Energy Analysis (COMPLETE)
- [x] Hardware component breakdown (CPU/GPU/RAM)
- [x] Total energy consumption calculated
- [x] Energy efficiency metrics computed
- [x] Cross-validation verified
- [x] Visualizations generated:
  - Energy by component (stacked bars)
  - Power consumption comparison
  - Component distribution (pie charts)

### 4. Documentation
- [x] `docs/rq1_findings.md` - Energy sections complete
- [x] `docs/ANALYSIS_SUMMARY.md` - Updated with actual results
- [x] `docs/codecarbon_session_interpretation.md` - Session filtering explained
- [x] `docs/dataset_duplicate_analysis.md` - Dataset issues documented
- [x] `notebooks/rq1_codecarbon_analysis.ipynb` - Working correctly

---

## ✅ Completed (Update: 2025-10-12)

### Performance Analysis (COMPLETE)
- [x] Run `notebooks/rq1_analysis.ipynb` - DONE
- [x] Generated all performance metrics:
  - Accuracy, Precision, Recall, F1 scores ✓
  - Confusion matrices ✓
  - Error analysis ✓
  - Model comparison charts ✓

- [x] Updated `docs/rq1_findings.md`:
  - Section 1.1: Overall Results table ✓
  - Section 1.2: Model Comparison metrics ✓
  - Section 5.1: Performance findings ✓
  - Section 5.3: Complete energy-performance tradeoff analysis ✓

### Still Pending (Optional)
- [ ] Section 3.2: Programming Language Distribution (requires dataset analysis)
- [ ] Section 3.3: Vulnerability Distribution (requires dataset analysis)

---

## 📊 Confirmed Results

### Performance Metrics

| Metric | Baseline Avg | Thinking Avg | Improvement |
|---|---|---|---|
| Accuracy | 50.65% | 52.15% | +1.50pp |
| Precision | 56.71% | 55.08% | -1.63pp |
| Recall | 9.85% | 24.09% | +14.24pp |
| F1 Score | 16.08% | 33.16% | +17.08pp (2.1x) |

**Best Configuration**: Thinking Zero-shot (F1: 39.19%, Accuracy: 53.00%)

### Energy Consumption

| Metric | Baseline Avg | Thinking Avg | Ratio |
|---|---|---|---|
| CO2 per experiment (kg) | 0.134 | 0.589 | 4.39x |
| Energy per experiment (kWh) | 0.789 | 3.465 | 4.39x |
| Per sample (kg CO2) | 0.00070 | 0.00307 | 4.39x |
| Avg duration (hours) | 1.49 | 6.54 | 4.39x |

### Hardware Breakdown

| Component | % of Total | Avg Power (W) |
|---|---|---|
| CPU | 21.2% | 112.5 |
| GPU | 43.2% | 217.5 |
| RAM | 35.6% | 188.8 |

### Cross-Validation

All experiments: ✓ PERFECT MATCH (< 0.001% difference)

---

## 🔍 Key Insights

### Performance
1. **Thinking improves F1 by 2.1x** (33.16% vs 16.08%)
2. **Thinking doubles recall** (+14.24pp) - better at finding vulnerabilities
3. **Few-shot paradox**: Few-shot prompting WORSENS performance for thinking model
4. **Best configuration**: Thinking Zero-shot (F1: 39.19%)

### Energy
5. **Thinking mode has 4.39x energy cost** compared to Baseline
6. **GPU is the dominant component** (43% of total energy)
7. **Energy-performance tradeoff**: 0.16 kWh per percentage point F1 improvement
8. **Data validation successful** - two independent sources match perfectly

### Technical
9. **Session filtering challenge solved** - can now accurately track multi-session experiments
10. **Few-shot is more energy-efficient** but doesn't improve accuracy

---

## 📁 Generated Files

### Analysis Outputs (`results/analysis/`)
- `energy_by_component.png` - Stacked bar chart
- `power_consumption.png` - Power comparison
- `energy_distribution_pies.png` - Component breakdown
- `rq1_codecarbon_detailed.xlsx` - Complete data tables
- `hardware_energy_summary.csv` - Hardware metrics
- `energy_cross_validation.csv` - Validation results

### Documentation (`docs/`)
- `rq1_findings.md` - Main findings document (energy complete)
- `ANALYSIS_SUMMARY.md` - Technical guide (updated with results)
- `codecarbon_session_interpretation.md` - Session filtering guide
- `dataset_duplicate_analysis.md` - Dataset issues
- `COMPLETION_STATUS.md` - This document

### Scripts (`scripts/`)
- `analyze_sessions.py` - Session validation tool
- `standardize_results.py` - Add error column to results

---

## 🎯 Next Steps

1. **Run performance analysis** notebook:
   ```bash
   jupyter notebook notebooks/rq1_analysis.ipynb
   ```

2. **Complete rq1_findings.md**:
   - Fill in all TBD values with performance metrics
   - Add final conclusions about energy-performance tradeoff

3. **Prepare for paper**:
   - Use energy data from `docs/rq1_findings.md`
   - Include visualizations from `results/analysis/`
   - Reference CodeCarbon methodology
   - Explain session filtering in supplementary materials

---

## ✨ Success Metrics

- [x] All experiments completed successfully
- [x] All energy data validated and cross-checked
- [x] Hardware component analysis complete
- [x] Session filtering methodology documented
- [x] Performance metrics calculated
- [x] Complete findings document ready for paper
- [x] Energy-performance tradeoff analyzed

---

**Energy Analysis: COMPLETE ✓**
**Performance Analysis: COMPLETE ✓**
**Overall Progress: 100%** 🎉

---

## 📝 Paper-Ready Findings

**Main Result**: Thinking mode achieves 2.1x higher F1 score but at 4.39x energy cost

**Key Trade-off**: 0.16 kWh per percentage point F1 improvement

**Recommendation**:
- Use Thinking Zero-shot for high-stakes vulnerability detection
- Use Baseline for routine/large-scale scanning
- Avoid Few-shot prompting (no benefit, wastes energy)

---

---

## Phase 2a: Qwen3-30B-A3B Models (COMPLETE ✅)

**Date**: October 20, 2025
**Status**: Experiments Complete ✅ | Analysis Complete ✅

### 1. Experiment Execution ✅
- [x] 4 experiments completed successfully (386 samples each)
- [x] RunPod H100 SXM 80GB infrastructure (4 pods in parallel)
- [x] Clean experimental isolation (fresh vLLM per experiment)
- [x] CodeCarbon energy tracking for all experiments
- [x] All results downloaded and verified

**Models:**
- Qwen3-30B-A3B-Instruct-2507 (Instruct MoE: 30B total, 3B active)
- Qwen3-30B-A3B-Thinking-2507 (Reasoning MoE: 30B total, 3B active)

**Configurations:**
- Pod 1: Thinking zero-shot (0.224 kg CO2, 1.316 kWh, 1 session)
- Pod 2: Instruct zero-shot (0.059 kg CO2, 0.349 kWh, 1 session)
- Pod 3: Thinking few-shot (0.194 kg CO2, 1.138 kWh, 2 sessions)
- Pod 4: Instruct few-shot (0.047 kg CO2, 0.278 kWh, 1 session)

**Infrastructure:**
- Platform: RunPod H100 SXM 80GB
- Cost: ~$9.96 total (4 pods × ~1 hr @ $2.49/hr)
- vLLM config: max-model-len 65536, dtype auto, gpu-memory-utilization 0.90
- Storage: 100GB Volume Disk per pod

**Downloaded Results:**
```
results/runpod/
├── thinking_zero_20251020_215332/   (17 files, 6.5M detailed results)
├── instruct_zero_20251020_194844/   (17 files, 1.9M detailed results)
├── thinking_few_20251020_214835/    (17 files, 5.9M detailed results)
└── instruct_few_20251020_200040/    (17 files, 1.6M detailed results)
```

### 2. Performance Metrics ✅

| Configuration | Accuracy | Precision | Recall | F1-Score |
|---|---|---|---|---|
| **Thinking Zero-shot** | **52.59%** | **52.36%** | **57.51%** | **54.81%** ⭐ |
| Instruct Zero-shot | 54.15% | 54.71% | 48.19% | 51.24% |
| Thinking Few-shot | 51.82% | 52.35% | 46.11% | 49.04% |
| Instruct Few-shot | 55.18% | 61.63% | 27.46% | 37.99% |

**Best Configuration**: Thinking Zero-shot (F1: 54.81%, Accuracy: 52.59%)

### 3. Energy Analysis ✅

| Configuration | CO2 (kg) | Energy (kWh) | Duration (hrs) | CO2/sample (g) |
|---|---|---|---|---|
| Thinking Zero-shot | 0.224 | 1.316 | 3.08 | 0.580 |
| Thinking Few-shot | 0.194 | 1.138 | 2.54 | 0.504 |
| Instruct Zero-shot | 0.059 | 0.349 | 0.86 | 0.154 |
| Instruct Few-shot | 0.047 | 0.278 | 0.66 | 0.123 |

**Hardware Breakdown (H100 SXM 80GB):**
- GPU: ~68-70% of total energy (dominant component)
- CPU: ~13-19% of total energy
- RAM: ~13-16% of total energy

### 4. Key Findings ✅

**Performance:**
1. **Thinking Zero-shot wins**: 54.81% F1 (best across all Phase 2a configurations)
2. **Few-shot paradox persists**: Few-shot hurts both models
   - Thinking: 54.81% → 49.04% F1 (-5.77pp)
   - Instruct: 51.24% → 37.99% F1 (-13.25pp)
3. **30B-A3B improves over 4B**: Thinking Zero 54.81% vs 4B 39.19% (+15.62pp F1)

**Energy:**
4. **Thinking uses 3.8× more energy** than Instruct (avg: 0.209 kg vs 0.053 kg CO2)
5. **MoE is highly efficient**: 30B-A3B uses 69% less CO2/sample than 4B dense
   - 30B-A3B Thinking Zero: 0.580 g/sample
   - 4B Thinking Zero: 1.910 g/sample
6. **Few-shot reduces energy** by 13-17% for both models

**Scale-Dependent Hypothesis:**
7. **REJECTED**: Few-shot still hurts performance with larger models
8. **Unexpected finding**: MoE architecture is far more energy-efficient than dense models

### 5. Generated Artifacts ✅

**Analysis Outputs (`results/analysis_phase2a/`):**
- `rq1_phase2a_summary_table.csv` - Performance metrics table
- `rq1_phase2a_complete_results.xlsx` - Detailed results
- `confusion_matrices.png` - Confusion matrices for all 4 experiments
- `phase2a_metrics_comparison.png` - Performance metrics comparison
- `accuracy_comparison.png` - Accuracy visualization
- `energy_consumption.png` - Energy consumption comparison
- `phase2a_energy_by_component.png` - Hardware component breakdown
- `phase2a_power_consumption.png` - Power usage analysis
- `phase2a_energy_distribution_pies.png` - Component distribution
- `phase2a_energy_performance_tradeoff.png` - F1 vs Energy scatter plot

**Documentation:**
- `notebooks/rq1_phase2a_analysis.ipynb` - Performance analysis (executed)
- `notebooks/rq1_phase2a_codecarbon_analysis.ipynb` - Energy analysis (executed)

---

*Phase 1 (4B Models): Complete ✅*
*Phase 2a (30B-A3B Models): Complete ✅*
*Phase 2b (235B-A22B Models): Decision pending based on Phase 2a findings*
