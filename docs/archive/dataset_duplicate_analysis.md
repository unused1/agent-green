# Dataset Duplicate Analysis

## Discovery

During the Qwen RQ1 experiments on Mars server (2025-10-11), we discovered that the dataset `VulTrial_386_samples_balanced.jsonl` contains duplicate entries.

## Dataset Statistics

- **Total lines**: 386
- **Unique samples**: 384
- **Duplicate samples**: 2

## Duplicate Entries

The following sample indices appear twice in the dataset:

| Index  | Occurrences | Project        | CVE            | CWE      | Ground Truth | Line Numbers |
|--------|-------------|----------------|----------------|----------|--------------|--------------|
| 349259 | 2           | squashfs-tools | CVE-2021-41072 | CWE-200  | 0 (Not Vuln) | 12, 79       |
| 439495 | 2           | squashfs-tools | CVE-2021-40153 | CWE-22   | 0 (Not Vuln) | 22, 75       |

**Notes:**
- Both duplicate samples are from the **squashfs-tools** project
- Both are labeled as **non-vulnerable** (target = 0)
- All occurrences of each duplicate are **identical** (byte-for-byte match)
- The duplicates appear at different positions in the file (not consecutive)

## Impact on Experiments

### Experiment Execution
- The `single_agent_vuln.py` script processes samples by unique `idx`
- When a duplicate `idx` is encountered, it is skipped (already in `processed_indices` set)
- This means **only the first occurrence** of each duplicate is processed
- The second occurrence is silently skipped

### Results Files
- All results files contain **384 unique samples** (not 386)
- Sample counts in results:
  - Baseline SA-zero: 384 samples
  - Baseline SA-few: 384 samples
  - Thinking SA-zero: 384 samples (383 successful + 1 skipped)
  - Thinking SA-few: 384 samples (all successful after retry)

### Metrics Calculation
The duplicate entries do **not** affect metrics because:
1. Only unique samples are processed
2. Evaluation functions count actual predictions vs ground truth
3. No double-counting occurs

## Verification Script

```python
import json
from collections import Counter

# Count all indices in dataset
indices = []
with open('vuln_database/VulTrial_386_samples_balanced.jsonl', 'r') as f:
    for line in f:
        sample = json.loads(line)
        indices.append(sample['idx'])

# Check for duplicates
counter = Counter(indices)
duplicates = {idx: count for idx, count in counter.items() if count > 1}

print(f'Total lines: {len(indices)}')
print(f'Unique indices: {len(set(indices))}')
print(f'Duplicates: {duplicates}')
```

## Recommendations for Analysis

### 1. Report Actual Sample Count
- State clearly: "We processed **384 unique samples** from the dataset"
- Explain the duplicate discovery in methodology section
- Reference this document for transparency

### 2. Adjust Metrics Reporting
All metrics should be calculated as:
```
Metric = (Value / 384) * 100%
```
Not based on 386.

### 3. Sample Coverage
For completeness reporting:
- "384/384 unique samples processed (100%)"
- Not "384/386 samples processed (99.5%)"

### 4. Dataset Cleanup (Optional)
For future experiments, consider creating a deduplicated version:
```bash
# Create deduplicated dataset
python3 -c "
import json
seen = set()
with open('vuln_database/VulTrial_386_samples_balanced.jsonl', 'r') as fin:
    with open('vuln_database/VulTrial_384_samples_balanced_deduplicated.jsonl', 'w') as fout:
        for line in fin:
            sample = json.loads(line)
            if sample['idx'] not in seen:
                fout.write(line)
                seen.add(sample['idx'])
"
```

## Files Affected

All experiment result files:
- `Sa-zero_Qwen-Qwen3-4B-Instruct-2507_*_detailed_results.jsonl` (384 samples)
- `Sa-few_Qwen-Qwen3-4B-Instruct-2507_*_detailed_results.jsonl` (384 samples)
- `Sa-zero_Qwen-Qwen3-4B-Thinking-2507_*_detailed_results.jsonl` (384 samples)
- `Sa-few_Qwen-Qwen3-4B-Thinking-2507_*_detailed_results.jsonl` (384 samples)

All classification reports and metrics files based on these results.

## Timeline

- **2025-10-11**: Duplicate discovery during results analysis
- **2025-10-11**: Documented in this file
- **2025-10-11**: Verified all experiments processed 384 unique samples correctly

## Conclusion

The duplicate entries in the dataset do **not** invalidate the experimental results. All experiments correctly processed 384 unique samples, and metrics are accurate. However, reporting should explicitly state the actual sample count (384) for transparency and reproducibility.

## Problematic Sample: 344242

### Discovery
During the Qwen RQ1 experiments, sample 344242 consistently failed to complete with the thinking model across multiple attempts.

### Sample Details
- **Index**: 344242
- **Project**: lua
- **CVE**: CVE-2022-33099
- **CWE**: CWE-787
- **Ground Truth**: 0 (Not Vulnerable)
- **Function**: `luaG_runerror` (error handling code)
- **Code Length**: 531 characters

### Failure Pattern
| Experiment       | Model Type | Attempt | Result                           |
|------------------|------------|---------|----------------------------------|
| SA-few           | Thinking   | 1       | Manually skipped (stuck)         |
| SA-few           | Thinking   | Retry   | Completed after 5.5 minutes      |
| SA-zero          | Thinking   | 1       | Manually skipped (stuck)         |
| SA-zero          | Thinking   | Retry   | Stuck for 14+ minutes, killed    |
| SA-zero          | Baseline   | 1       | ✓ Completed successfully         |
| SA-few           | Baseline   | 1       | ✓ Completed successfully         |

### Analysis
- **Baseline model**: Processes this sample without issues
- **Thinking model**: Consistently gets stuck or takes excessive time (5-14+ minutes)
- **Root cause**: Likely recursive reasoning about error-handling code
- **Note**: The function is literally about handling recursive errors, which may trigger problematic reasoning loops in the thinking model

### Impact on Results
- **Thinking SA-zero**: 383/384 samples (99.74% completion rate)
- **Thinking SA-few**: 384/384 samples (100% after extended retry)
- **Baseline models**: 384/384 samples (100%)

### Decision
Sample 344242 is marked as "skipped" in Thinking SA-zero experiment and accepted as a known limitation of the thinking model when processing recursive error-handling code.

---

**Last Updated**: 2025-10-12
**Verified By**: Automated analysis during Qwen RQ1 experiments
