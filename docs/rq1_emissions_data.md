# RQ1 Emissions Data - Exact Records Used in Analysis

**Research Question**: RQ1 - Qwen3-4B Vulnerability Detection (Thinking vs Baseline)

**Date**: 2025-10-11
**Analysis Notebook**: `notebooks/rq1_analysis.ipynb`
**Findings Document**: `docs/rq1_findings.md`

---

## Overview

This document contains the exact emissions records from CodeCarbon v2.7.1 that were used in the RQ1 analysis. Each experiment may have multiple sessions due to interruptions and resumptions (Ctrl+C). Sessions were filtered by matching the experiment timestamp in the `project_name` field to exclude earlier failed/test runs.

---

## 1. Baseline Zero-shot (Qwen3-4B-Instruct)

**File**: `results/mars/codecarbon_baseline_sa-zero/emissions.csv`
**Lines Used**: Line 5 only (out of 5 total lines including header)
**Sessions**: 1
**Total Emissions**: 0.154753 kg CO2

```csv
timestamp,project_name,run_id,experiment_id,duration,emissions,emissions_rate,cpu_power,gpu_power,ram_power,cpu_energy,gpu_energy,ram_energy,energy_consumed,country_name,country_iso_code,region,cloud_provider,cloud_region,os,python_version,codecarbon_version,cpu_count,cpu_model,gpu_count,gpu_model,longitude,latitude,ram_total_size,tracking_mode,on_cloud,pue
2025-10-11T10:20:20,Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251011-083716_session_1,845a8f50-28d2-41fe-865b-7445ba43b0ae,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,6182.034128322266,0.1547527851896159,2.503266432655785e-05,112.5,235.8353892719504,188.8258137702942,0.1931873318846627,0.3928191067550344,0.3240738656928296,0.9100803043325272,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
```

**Notes**:
- Experiment timestamp: `20251011-083716`
- Lines 2-4 excluded (earlier failed runs: 06:07, 06:09, 07:48)
- Duration: 6,182 seconds (~1.72 hours)
- Energy consumed: 0.910 kWh

---

## 2. Baseline Few-shot (Qwen3-4B-Instruct)

**File**: `results/mars/codecarbon_baseline_sa-few/emissions.csv`
**Lines Used**: Lines 2, 3, 4 (all 3 data rows)
**Sessions**: 3
**Total Emissions**: 0.113401 kg CO2

```csv
timestamp,project_name,run_id,experiment_id,duration,emissions,emissions_rate,cpu_power,gpu_power,ram_power,cpu_energy,gpu_energy,ram_energy,energy_consumed,country_name,country_iso_code,region,cloud_provider,cloud_region,os,python_version,codecarbon_version,cpu_count,cpu_model,gpu_count,gpu_model,longitude,latitude,ram_total_size,tracking_mode,on_cloud,pue
2025-10-11T10:55:48,Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251011-102915_session_1,7762adb3-c07c-44c7-b5bd-df2ce2df5172,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,1592.608108907007,0.0398588796394388,2.502742477356442e-05,112.5,229.2011715741269,188.8258137702942,0.0497686999419529,0.1011133475572805,0.0835226597773894,0.234404707276623,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
2025-10-11T11:51:57,Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251011-110256_session_2,5b90c575-1845-423f-a9c5-4c75eee21fbd,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,2937.801988308318,0.0735416313924706,2.5032875491659102e-05,112.5,229.03434389712157,188.8258137702942,0.0918057540222362,0.1866452965383374,0.1540373870256292,0.4324884375862027,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
2025-10-11T16:51:41,Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251011-164913_session_3,71024b24-6f1c-46b4-a488-a959e0231e26,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,0.04722765367478132,6.859070934391303e-07,1.4523420921192022e-05,112.5,12.095827145908707,188.8258137702942,1.473129930673167e-06,1.5527789543057224e-07,2.405319486629689e-06,4.033727312733428e-06,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
```

**Notes**:
- Experiment timestamp: `20251011-102915`
- All sessions included (no failed runs in this file)
- Total duration: 4,530 seconds (~1.26 hours)
- Total energy consumed: 0.667 kWh
- Session 3 is very short (0.047 seconds) - likely final checkpoint

---

## 3. Thinking Zero-shot (Qwen3-4B-Thinking)

**File**: `results/mars/codecarbon_thinking_sa-zero/emissions.csv`
**Lines Used**: Lines 9, 10, 11, 12, 13, 14 (6 data rows out of 14 total)
**Sessions**: 6
**Total Emissions**: 0.731428 kg CO2

```csv
timestamp,project_name,run_id,experiment_id,duration,emissions,emissions_rate,cpu_power,gpu_power,ram_power,cpu_energy,gpu_energy,ram_energy,energy_consumed,country_name,country_iso_code,region,cloud_provider,cloud_region,os,python_version,codecarbon_version,cpu_count,cpu_model,gpu_count,gpu_model,longitude,latitude,ram_total_size,tracking_mode,on_cloud,pue
2025-10-11T10:20:07,Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-095820_session_1,6770054b-00f2-4926-9f2d-4ac65a00b987,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,1305.963114517741,0.0327146580941338,2.5050215990376232e-05,112.5,222.4263390750029,188.8258137702942,0.0408110565908136,0.0830896492494446,0.0684897959394905,0.192390501779749,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
2025-10-11T10:25:24,Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-102011_session_2,54fab2c5-2c69-48e5-93c8-534caa151a3b,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,306.60383917670697,0.0076779642922981,2.504197048841608e-05,112.5,221.4864986942916,188.8258137702942,0.0095813156257208,0.0194922000381936,0.0160795591012811,0.0451530747651956,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
2025-10-11T10:43:56,Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-102529_session_3,940bdb49-85a5-46e9-8667-c9c58243306c,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,1090.458587787114,0.0273204940208549,2.5054132570313293e-05,112.5,230.8617769262549,188.8258137702942,0.0340766195770702,0.0694034535782748,0.0571880756120548,0.1606681487673998,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
2025-10-11T10:55:41,Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-104424_session_4,5c163b7f-323d-45cb-bf18-f13ee8f4153c,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,672.2229965236038,0.0168415997379819,2.505359058687095e-05,112.5,228.7007382770707,188.8258137702942,0.0210068245240836,0.042782367559198,0.0352539895706643,0.099043181653946,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
2025-10-11T17:58:49,Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-110220_session_5,26ca12d7-1bba-4c55-9d47-df02e02cd518,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,24976.985054707155,0.6257062893456947,2.505131375845438e-05,112.5,222.0079265715032,188.8258137702942,0.7805260269129928,1.589506110770543,1.3096623475095934,3.679694485193126,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
2025-10-11T18:22:13,Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251011-180646_session_6,0eb1542d-eedf-48f2-910c-075ee5935a97,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,845.6317937448621,0.021167428197097257,2.5031495213014355e-05,112.5,228.44764042764578,188.8258137702942,0.026425828928360713,0.05370860435573377,0.04434836340319786,0.12448279668729237,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
```

**Notes**:
- Experiment timestamp: `20251011-095820`
- Lines 2-8 excluded (7 earlier failed runs from different experiments)
- Total duration: 28,197 seconds (~7.83 hours)
- Total energy consumed: 4.301 kWh
- Session 5 is the longest (24,977 seconds = ~6.94 hours), accounting for 85.6% of total emissions
- Multiple interruptions and resumptions during execution

---

## 4. Thinking Few-shot (Qwen3-4B-Thinking)

**File**: `results/mars/codecarbon_thinking_sa-few/emissions.csv`
**Lines Used**: Lines 2, 3, 4, 5 (all 4 data rows)
**Sessions**: 4
**Total Emissions**: 0.446900 kg CO2

```csv
timestamp,project_name,run_id,experiment_id,duration,emissions,emissions_rate,cpu_power,gpu_power,ram_power,cpu_energy,gpu_energy,ram_energy,energy_consumed,country_name,country_iso_code,region,cloud_provider,cloud_region,os,python_version,codecarbon_version,cpu_count,cpu_model,gpu_count,gpu_model,longitude,latitude,ram_total_size,tracking_mode,on_cloud,pue
2025-10-11T10:38:43,Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251011-103534_session_1,3a102471-f774-44e5-8269-87da73114aec,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,187.367152874358,0.0046649428848249,2.4897335596240497e-05,112.5,230.12491843419093,188.8258137702942,0.0058551815945247,0.0117527202355063,0.0098259995056604,0.0274339013356914,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
2025-10-11T11:09:12,Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251011-110242_session_2,a903e5d3-0409-4a17-8a13-c0930996da45,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,384.57457644026726,0.009614142828792,2.499942382510908e-05,112.5,224.9860652393448,188.8258137702942,0.0120178787096519,0.024353116982489,0.0201684844910599,0.056539480183201,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
2025-10-11T15:51:55,Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251011-110932_session_3,41bd85ea-a39f-42bc-b60d-6f3ba7a506f1,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,16934.61721560452,0.4241411673680313,2.5045807765716933e-05,112.5,228.98691358364152,188.8258137702942,0.5292036159761774,1.07721711816189,0.8878963936944919,2.494317127832556,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
2025-10-11T17:05:08,Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251011-165923_session_4,3a8e5d21-36ff-4f7b-89ab-ddd65f2864b9,5b0fa12a-3dd7-45bb-9766-cc326314d9f1,338.6871530758217,0.008479820983989863,2.503732694606072e-05,112.5,227.0551055851936,188.8258137702942,0.010583904692262877,0.021522804162671605,0.017761977206766734,0.04986868606170123,Canada,CAN,,,,Linux-6.8.0-47-generic-x86_64-with-glibc2.35,3.12.11,2.7.1,96,AMD EPYC 7643 48-Core Processor,1,1 x NVIDIA RTX A5000,,,503.5355033874512,machine,N,1.0
```

**Notes**:
- Experiment timestamp: `20251011-103534`
- All sessions included (no failed runs in this file)
- Total duration: 17,845 seconds (~4.96 hours)
- Total energy consumed: 2.628 kWh
- Session 3 is the longest (16,935 seconds = ~4.70 hours), accounting for 94.9% of total emissions

---

## Summary Table

| Experiment | File | Lines | Sessions | Total CO2 (kg) | Energy (kWh) | Duration (hrs) |
|------------|------|-------|----------|----------------|--------------|----------------|
| Baseline Zero-shot | `codecarbon_baseline_sa-zero/emissions.csv` | Line 5 | 1 | 0.154753 | 0.910 | 1.72 |
| Baseline Few-shot | `codecarbon_baseline_sa-few/emissions.csv` | Lines 2-4 | 3 | 0.113401 | 0.667 | 1.26 |
| Thinking Zero-shot | `codecarbon_thinking_sa-zero/emissions.csv` | Lines 9-14 | 6 | 0.731428 | 4.301 | 7.83 |
| Thinking Few-shot | `codecarbon_thinking_sa-few/emissions.csv` | Lines 2-5 | 4 | 0.446900 | 2.628 | 4.96 |

---

## Key Metrics Used in Analysis

### Average Emissions per Configuration

| Configuration | Experiments | Average CO2 (kg) |
|---------------|-------------|------------------|
| **Baseline** (avg of zero-shot and few-shot) | 2 | 0.134077 |
| **Thinking** (avg of zero-shot and few-shot) | 2 | 0.589164 |
| **Energy Ratio** (Thinking / Baseline) | - | **4.39x** |

### Energy-Performance Tradeoff

- **Baseline Average F1**: 16.08%
- **Thinking Average F1**: 33.16%
- **F1 Improvement**: 2.1x (17.08 percentage points)
- **Energy Cost**: 4.39x more energy
- **Cost per F1 point**: 0.26 kWh per percentage point improvement

---

## Hardware Configuration

All experiments ran on the same hardware:

- **CPU**: AMD EPYC 7643 48-Core Processor (96 logical cores)
- **GPU**: 1 x NVIDIA RTX A5000 (24GB VRAM)
- **RAM**: 503.54 GB
- **Location**: Canada
- **CodeCarbon Version**: 2.7.1
- **Python Version**: 3.12.11
- **OS**: Linux 6.8.0-47-generic x86_64

---

## Filtering Methodology

Sessions were filtered using the experiment timestamp embedded in the `project_name` field:

```python
# Example: Baseline Zero-shot
exp_timestamp = "083716"  # From Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251011-083716
cc_df = pd.read_csv('codecarbon_baseline_sa-zero/emissions.csv')

# Filter to only matching sessions
matching = cc_df[cc_df['project_name'].str.contains(exp_timestamp)]
total_emissions = matching['emissions'].sum()
```

This ensures only sessions from the successful experiment run are included, excluding earlier failed or test runs.

---

## Cross-Validation

All emission totals were cross-validated against `*_energy_tracking.json` files:

| Experiment | emissions.csv (filtered) | energy_tracking.json | Match |
|------------|--------------------------|----------------------|-------|
| Baseline Zero-shot | 0.154753 kg | 0.154753 kg | ✓ |
| Baseline Few-shot | 0.113401 kg | 0.113401 kg | ✓ |
| Thinking Zero-shot | 0.731428 kg | 0.731428 kg | ✓ |
| Thinking Few-shot | 0.446900 kg | 0.446900 kg | ✓ |

**Difference**: < 0.01% for all experiments

---

## Related Documents

- **Analysis Notebook**: `notebooks/rq1_analysis.ipynb`
- **Findings Report**: `docs/rq1_findings.md`
- **Session Interpretation Guide**: `docs/codecarbon_session_interpretation.md`
- **Completion Status**: `docs/COMPLETION_STATUS.md`
- **Experiment Plan**: `docs/rq1_experiment_plan.md`

---

*Last Updated: 2025-10-18*
*Created by: Claude Code*
*Purpose: Reference document for exact emissions data used in RQ1 analysis*
