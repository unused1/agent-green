# RQ1 Analysis - Completion Status

**Last Updated**: 2025-10-20
**Phase 1 (4B Models)**: Complete ✅
**Phase 2a (30B-A3B Models)**: Experiments Complete ✅ | Analysis Pending 🔄

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

## Phase 2a: Qwen3-30B-A3B Models (Experiments Complete ✅)

**Date**: October 20, 2025

### 1. Experiment Execution ✅
- [x] 4 experiments completed successfully (386 samples each)
- [x] RunPod H100 SXM 80GB infrastructure (4 pods in parallel)
- [x] Clean experimental isolation (fresh vLLM per experiment)
- [x] CodeCarbon energy tracking for all experiments
- [x] All results downloaded and verified

**Models:**
- Qwen3-30B-A3B-Instruct-2507 (Baseline MoE: 30B total, 3B active)
- Qwen3-30B-A3B-Thinking-2507 (Reasoning MoE: 30B total, 3B active)

**Configurations:**
- Pod 1: Thinking zero-shot (0.224 kg CO2, 1 session)
- Pod 2: Instruct zero-shot (0.059 kg CO2, 1 session)
- Pod 3: Thinking few-shot (0.194 kg CO2, 2 sessions)
- Pod 4: Instruct few-shot (0.047 kg CO2, 1 session)

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

### 2. Energy Observations (Preliminary)
- [x] Thinking models use 3-4× more energy than Instruct (0.21 avg vs 0.053 avg kg CO2)
- [x] Few-shot reduced energy for both models (13-20% reduction)
- [x] 30B-A3B MoE uses ~60% less energy than 4B dense models (despite larger total parameters)
- [x] File sizes correlate with energy: Thinking produces 3-4× larger results

### 3. Pending Analysis 🔄
- [ ] Classification performance metrics (precision, recall, F1)
- [ ] Compare 30B-A3B vs 4B to test scale-dependent few-shot hypothesis
- [ ] Energy-performance tradeoff analysis for MoE models
- [ ] Decide on Phase 2b (235B-A22B) based on findings

---

*Phase 1: Analysis complete, ready for research paper*
*Phase 2a: Experiments complete, analysis pending*
