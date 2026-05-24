# CleanVul — Local Provenance

## Source

- Upstream repository: https://github.com/yikun-li/CleanVul
- Paper: *CleanVul: Toward High-Quality Function-Level Vulnerability Datasets via LLM-Based Noise Reduction*
- Upstream commit at time of clone: `f3a3e44061edcf3a09ae0251e1650374d968b5f5` (2026-03-25)
- Cloned: 2026-05-24 (shallow, `--depth 1`)
- The `.git` directory was removed after cloning to avoid nesting a git repo inside `agent-green`.

## Local modifications

- Removed `vulnerability_score_0.csv` (51 MB, ~1.15M low-confidence rows; not used in our experiments).
- Retained `vulnerability_score_2.csv`, `vulnerability_score_3.csv`, `vulnerability_score_4.csv` locally but excluded from version control via `.gitignore` (`vuln_database/CleanVul/vulnerability_score_*.csv`).
- Retained `README.md` and `src/` (committed).

## Reproducing the local checkout

```bash
cd vuln_database/CleanVul
git clone --depth 1 https://github.com/yikun-li/CleanVul.git /tmp/cleanvul_tmp
cp /tmp/cleanvul_tmp/vulnerability_score_{2,3,4}.csv .
rm -rf /tmp/cleanvul_tmp
```

## Dataset row counts (after upstream heuristic filtering)

| File | Pairs | Confidence |
|---|---|---|
| `vulnerability_score_4.csv` | 6,051 | 97.3% correctness (threshold 4) |
| `vulnerability_score_3.csv` | 2,041 | combine with score_4 for threshold ≥3 → 8,092 pairs, 90.6% |
| `vulnerability_score_2.csv` | 2,444 | combine with score_3+4 for threshold ≥2 → 10,536 pairs, 49.4% |

## Schema

Per row (each row is one vulnerable/fixed function pair):

| Column | Notes |
|---|---|
| `func_before` | Vulnerable version of the function |
| `func_after`  | Fixed version of the function |
| `commit_msg`  | Commit message |
| `commit_url`  | GitHub commit URL |
| `cve_id`      | CVE identifier if available |
| `cwe_id`      | CWE identifier if available |
| `file_name`   | Source file containing the function |
| `vulnerability_score` | LLM confidence score (2, 3, or 4) |
| `extension`   | Source language: c, java, py, js, cs, cpp |
| `is_test`     | Test-related flag (heuristic) — all rows in shipped CSVs are False |
| `date`        | Commit date (may be empty) |

## License

The upstream repository does not ship a top-level LICENSE file. Licensing terms must be confirmed against the CleanVul paper and/or by contacting the authors before redistributing any subset of this data.
