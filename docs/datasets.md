# Datasets

This document catalogs datasets relevant to the agent-green research project, covering code generation, vulnerability detection, log analysis, and technical debt detection tasks.

---

## Datasets Used in This Project

The following datasets are actively used in experiments.

### HumanEval (Code Generation)

| Attribute | Value |
|-----------|-------|
| **Task** | Code Generation |
| **Description** | Evaluates code generation by measuring functional correctness for synthesizing programs from docstrings. Contains 164 Python programming problems with unit tests. |
| **Samples Used** | 164 |
| **Location** | `vuln_database/HumanEval.jsonl` |
| **Paper** | [Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374) (Jul 2021) |
| **Source** | [github.com/openai/human-eval](https://github.com/openai/human-eval) |
| **Notes** | Widely-used benchmark; dataset is from 2021 so may have contamination in newer models. |

---

### VulTrial (Vulnerability Detection)

| Attribute | Value |
|-----------|-------|
| **Task** | Vulnerability Detection |
| **Description** | Balanced dataset of vulnerable and benign code samples with CWE (Common Weakness Enumeration) labels for binary classification. Sourced from PrimeVul v0.1. |
| **Samples Used** | 486 (balanced: 243 vuln + 243 safe) |
| **Location** | `vuln_database/VulTrial_486_samples_balanced.jsonl` |
| **Notes** | Combined dataset used for final RQ1 and RQ2 vulnerability detection experiments. Created by expanding the original 386-sample set with 100 incremental samples (50 vuln + 50 safe) drawn from VulTrial-870. |

**Dataset lineage:**
- `VulTrial_386_samples_balanced.jsonl` — Original 386 balanced samples (193 vuln + 193 safe). Used for initial experiment runs.
- `VulTrial_870_samples_balanced.jsonl` — Full pool of 870 balanced samples (435 vuln + 435 safe) from PrimeVul v0.1.
- `VulTrial_100_incremental.jsonl` — 100 incremental samples (50 vuln + 50 safe), stratified random sample from the 484-sample set difference (870 − 386), seed=42. Used for incremental inference runs.
- `VulTrial_486_samples_balanced.jsonl` — Combined dataset (386 + 100 = 486 samples). Used as ground truth for final evaluation.

---

### LogHub / HDFS (Log Analysis)

| Attribute | Value |
|-----------|-------|
| **Task** | Log Analysis / Anomaly Detection |
| **Description** | A large collection of system log datasets from distributed systems, supercomputers, operating systems, and more. The HDFS subset contains Hadoop Distributed File System logs with anomaly labels at the block/session level. |
| **Samples Used** | 385 sessions (sampled from HDFS_2k) |
| **Location** | `data/HDFS_385_sampled_sessions/` |
| **Labels** | `data/HDFS_anomaly_label_385_session_sampled.csv` |
| **Paper** | [Loghub: A Large Collection of System Log Datasets](https://arxiv.org/abs/2008.06448) (Sep 2023) |
| **Source** | [github.com/logpai/loghub](https://github.com/logpai/loghub) |
| **Notes** | Binary classification (normal vs anomalous session). 373 normal, 12 anomalous in sampled subset. |

---

### MLCQ (Technical Debt / Code Smell Detection)

| Attribute | Value |
|-----------|-------|
| **Task** | Technical Debt Detection |
| **Description** | Nearly 15,000 code samples reviewed by professional software developers for code smells. Captures industry-relevant, contemporary understanding of code smells from Java open-source projects. |
| **Code Smells** | Blob (God Class), Data Class, Feature Envy, Long Method |
| **Severity Levels** | none, minor, major, critical |
| **Samples Used** | 385 (cleaned and pruned subset) |
| **Location** | `data/mlcq_cleaned_and_pruned_dataset_385.csv` |
| **Paper** | [MLCQ: Industry-Relevant Code Smell Data Set](https://dl.acm.org/doi/10.1145/3383219.3383264) (EASE 2020, Apr 2020) |
| **Source** | [zenodo.org/records/3666840](https://zenodo.org/records/3666840) |
| **Citation** | Madeyski, L. and Lewowski, T. (2020). MLCQ: Industry-Relevant Code Smell Data Set. In EASE 2020, Trondheim, Norway. ACM. |

---

## Alternative / Future Datasets

The following datasets are potential alternatives or candidates for future experiments.

### PrimeVul (Vulnerability Detection)

| Attribute | Value |
|-----------|-------|
| **Task** | Vulnerability Detection |
| **Description** | Dataset for training and evaluating code LMs for vulnerability detection. Incorporates novel data labeling techniques achieving comparable accuracy to human-verified benchmarks while significantly expanding the dataset. Implements rigorous de-duplication and chronological data splitting to mitigate data leakage. |
| **Paper** | [PrimeVul: A Comprehensive Vulnerability Dataset](https://arxiv.org/abs/2403.18624) (Jul 2024) |
| **Source** | [github.com/DLVulDet/PrimeVul](https://github.com/DLVulDet/PrimeVul?tab=readme-ov-file#-primevul-dataset) |
| **Notes** | More recent and rigorous than many vulnerability datasets; addresses common data leakage issues. |

---

### BigCodeBench (Code Generation)

| Attribute | Value |
|-----------|-------|
| **Task** | Code Generation |
| **Description** | Challenges LLMs to invoke multiple function calls as tools from 139 libraries across 7 domains for 1,140 fine-grained tasks. Each task has 5.6 test cases on average with 99% branch coverage. Includes BigCodeBench-Instruct variant with natural language instructions. |
| **Samples** | 1,140 tasks |
| **Paper** | [BigCodeBench: Benchmarking Code Generation](https://arxiv.org/pdf/2406.15877) (Apr 2025) |
| **Source** | [huggingface.co/datasets/bigcode/bigcodebench](https://huggingface.co/datasets/bigcode/bigcodebench) |
| **Notes** | More challenging than HumanEval; tests realistic multi-library usage. |

---

### SecureAgentBench (Secure Code Generation)

| Attribute | Value |
|-----------|-------|
| **Task** | Secure Code Generation |
| **Description** | 105 coding tasks evaluating code agents' secure code generation capabilities. Features realistic multi-file edits in large repositories, contexts based on real-world open-source vulnerabilities, and comprehensive evaluation combining functionality testing, vulnerability checking via proof-of-concept exploits, and static analysis. |
| **Samples** | 105 tasks |
| **Paper** | [SecureAgentBench](https://arxiv.org/abs/2509.22097) (Sep 2025) |
| **Source** | Not yet available for download |
| **Notes** | Combines security and functionality evaluation; awaiting public release. |

---

## Dataset Summary

| Dataset | Task | Samples | Status |
|---------|------|---------|--------|
| HumanEval | Code Generation | 164 | In use |
| VulTrial | Vulnerability Detection | 486 | In use |
| HDFS (LogHub) | Log Analysis | 385 | In use |
| MLCQ | Technical Debt Detection | 385 | In use |
| PrimeVul | Vulnerability Detection | - | Alternative |
| BigCodeBench | Code Generation | 1,140 | Alternative |
| SecureAgentBench | Secure Code Generation | 105 | Future (not released) |

---

## References

1. Chen, M., et al. (2021). Evaluating Large Language Models Trained on Code. arXiv:2107.03374
2. He, J., et al. (2023). Loghub: A Large Collection of System Log Datasets. arXiv:2008.06448
3. Madeyski, L. and Lewowski, T. (2020). MLCQ: Industry-Relevant Code Smell Data Set. EASE 2020.
4. Ding, Y., et al. (2024). PrimeVul: A Comprehensive Vulnerability Dataset. arXiv:2403.18624
5. Zhuo, T.Y., et al. (2025). BigCodeBench: Benchmarking Code Generation. arXiv:2406.15877
