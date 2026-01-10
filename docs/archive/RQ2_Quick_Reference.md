# RQ2 Parallel Execution - Quick Reference

**Master guide for executing RQ2 experiments on RunPod H100 pods in parallel**

---

## 📋 At a Glance

| Metric | Test Run | Full Run (8 Pods) | Full Run (4 Pods) |
|--------|----------|-------------------|-------------------|
| **Experiments** | 4 | 32 | 32 |
| **Pods Required** | 4 | 8 | 4 |
| **Samples per Exp** | 10 | 386 (vuln) / 164 (code) | 386 / 164 |
| **Wall-Clock Time** | ~1 hour | ~5 hours | ~10 hours |
| **Cost (Spot)** | ~$10 | ~$100 | ~$100 |
| **Purpose** | Validate scripts | Full RQ2 data | Full RQ2 data |

---

## 🚀 Quick Start

### For Test Run (Recommended First Step):
```bash
# 1. Read detailed instructions
open docs/RQ2_Test_Run_Commands.md

# 2. Deploy 4 pods, upload code, run 4 test experiments
# Follow copy-paste commands in the test run doc

# 3. Validate results
bash scripts/validate_test_results.sh
```

### For Full Run (After Test Success):
```bash
# 1. Read detailed instructions
open docs/RQ2_Full_Run_Commands.md

# 2. Deploy 8 pods, upload code, run 32 experiments
# Follow copy-paste commands in the full run doc

# 3. Monitor progress
bash scripts/quick_check_all_pods.sh
```

---

## 📚 Documentation Index

### Core Execution Guides
- **[RQ2_Test_Run_Commands.md](RQ2_Test_Run_Commands.md)** - 4 experiments, 10 samples, validation
- **[RQ2_Full_Run_Commands.md](RQ2_Full_Run_Commands.md)** - All 32 experiments, full datasets, production
- **[RQ2_Monitoring_and_Troubleshooting.md](RQ2_Monitoring_and_Troubleshooting.md)** - Monitor progress, debug issues

### Supporting Documentation
- **[rq2_experiment_design.md](rq2_experiment_design.md)** - RQ2 experiment scope and design
- **[RunPod_Setup_Guide.md](RunPod_Setup_Guide.md)** - RunPod infrastructure setup
- **[mars_docker_workflow.md](mars_docker_workflow.md)** - Previous parallel execution reference

---

## 🎯 Execution Workflow

### Phase 1: Test Run (Day 1)
```
┌─────────────────────────────────────────┐
│ 1. Deploy 4 Pods (4B models)           │
│    - 2 × 4B-Instruct                   │
│    - 2 × 4B-Thinking                   │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 2. Upload Code & Setup Env              │
│    - bash upload_to_runpod.sh          │
│    - bash setup_runpod_env.sh          │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 3. Run 4 Test Experiments (10 samples)  │
│    - DA-vuln-zero (Pod 1)              │
│    - DA-vuln-few (Pod 2)               │
│    - MA-code-zero (Pod 3)              │
│    - MA-code-few (Pod 4)               │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 4. Validate Results                     │
│    - Check all 4 completed             │
│    - Verify 10 samples each            │
│    - Test resume functionality         │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 5. Decision Point                       │
│    ✅ Success → Proceed to Full Run   │
│    ❌ Issues → Debug & Re-run         │
└─────────────────────────────────────────┘
```

### Phase 2: Full Run (Week 1-2)
```
┌─────────────────────────────────────────┐
│ 1. Deploy 8 Pods                        │
│    - 4 × 4B models (Instruct/Thinking) │
│    - 4 × 30B models (Instruct/Thinking)│
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 2. Upload Code & Setup (All 8 Pods)    │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 3. Start All 32 Experiments in Parallel │
│    - Each pod runs 4 experiments       │
│    - All pods run simultaneously       │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 4. Monitor Progress (~5 hours)         │
│    - bash quick_check_all_pods.sh      │
│    - Check logs via SSH                │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 5. Download All Results                 │
│    - 32 result files                   │
│    - Energy tracking data              │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 6. Analysis & Visualization             │
│    - RQ2 comprehensive analysis        │
│    - Compare SA vs DA vs MA            │
└─────────────────────────────────────────┘
```

---

## 🔢 Experiment Matrix

### Complete RQ2 Experiment List (32 Total)

#### Dual-Agent (16 Experiments)
```
4B-Instruct  × Zero-Shot × Vuln → DA-vuln-two-zero_shot (Pod 1)
4B-Instruct  × Zero-Shot × Code → DA-code-zero_shot (Pod 1)
4B-Instruct  × Few-Shot  × Vuln → DA-vuln-two-few_shot (Pod 3)
4B-Instruct  × Few-Shot  × Code → DA-code-few_shot (Pod 3)

4B-Thinking  × Zero-Shot × Vuln → DA-vuln-two-zero_shot (Pod 2)
4B-Thinking  × Zero-Shot × Code → DA-code-zero_shot (Pod 2)
4B-Thinking  × Few-Shot  × Vuln → DA-vuln-two-few_shot (Pod 4)
4B-Thinking  × Few-Shot  × Code → DA-code-few_shot (Pod 4)

30B-Instruct × Zero-Shot × Vuln → DA-vuln-two-zero_shot (Pod 5)
30B-Instruct × Zero-Shot × Code → DA-code-zero_shot (Pod 5)
30B-Instruct × Few-Shot  × Vuln → DA-vuln-two-few_shot (Pod 7)
30B-Instruct × Few-Shot  × Code → DA-code-few_shot (Pod 7)

30B-Thinking × Zero-Shot × Vuln → DA-vuln-two-zero_shot (Pod 6)
30B-Thinking × Zero-Shot × Code → DA-code-zero_shot (Pod 6)
30B-Thinking × Few-Shot  × Vuln → DA-vuln-two-few_shot (Pod 8)
30B-Thinking × Few-Shot  × Code → DA-code-few_shot (Pod 8)
```

#### Multi-Agent (16 Experiments)
```
Same pattern as Dual-Agent, but using:
- MA-vuln-four-{zero_shot|few_shot} (4-agent vulnerability detection)
- MA-code-{zero_shot|few_shot} (4-agent code generation)
```

---

## 📊 Expected Results Structure

```
results/
├── pod1_full_results/
│   ├── DA-vuln-two-zero_shot_qwen3-4b-instruct_<timestamp>_detailed_results.jsonl
│   ├── DA-vuln-two-zero_shot_qwen3-4b-instruct_<timestamp>_energy_tracking.json
│   ├── DA-code-zero_shot_qwen3-4b-instruct_<timestamp>_detailed_results.jsonl
│   ├── DA-code-zero_shot_qwen3-4b-instruct_<timestamp>_summary.json
│   ├── MA-vuln-four-zero_shot_qwen3-4b-instruct_<timestamp>_detailed_results.jsonl
│   └── MA-code-zero_shot_qwen3-4b-instruct_<timestamp>_detailed_results.jsonl
├── pod2_full_results/
│   └── ... (4 experiments with qwen3-4b-thinking)
├── pod3_full_results/
│   └── ... (4 experiments with qwen3-4b-instruct, few-shot)
...
└── pod8_full_results/
    └── ... (4 experiments with qwen3-30b-thinking, few-shot)
```

**Total Files**: ~128 files (32 experiments × 4 file types)

---

## ⏱️ Time Estimates

### Per Experiment Type

| Experiment Type | Samples | Est. Time |
|----------------|---------|-----------|
| DA-vuln | 386 | 60-90 min |
| DA-code | 164 | 30-45 min |
| MA-vuln | 386 | 120-180 min |
| MA-code | 164 | 60-90 min |

### Per Pod (4 Experiments Sequential)

| Pod | Experiments | Total Time |
|-----|------------|-----------|
| Pod 1 | DA-vuln-zero + DA-code-zero + MA-vuln-zero + MA-code-zero | ~5 hours |
| Pod 2-8 | Same pattern | ~5 hours each |

**Parallel Execution**: All 8 pods finish in ~5 hours (wall-clock time)

---

## 💰 Cost Breakdown

### RunPod H100 Pricing
- **Spot Instances**: $2.49/hr per pod
- **On-Demand**: $2.89/hr per pod

### Test Run Cost
```
4 pods × 1 hour × $2.49/hr = ~$10
```

### Full Run Cost (8 Pods)
```
8 pods × 5 hours × $2.49/hr = ~$100
```

### Full Run Cost (4 Pods)
```
4 pods × 10 hours × $2.49/hr = ~$100
```

**Total Budget for RQ2 (Test + Full)**: ~$110

---

## ✅ Pre-Flight Checklist

Before starting execution:

### Code Readiness
- [ ] All scripts tested and validated
- [ ] Resume functionality working
- [ ] Energy tracking enabled
- [ ] Datasets available (VulTrial_386, HumanEval)
- [ ] Config.py correctly configured
- [ ] All prompts in config.py

### Infrastructure
- [ ] RunPod account funded ($120+ recommended)
- [ ] SSH key generated (`~/.ssh/runpod_ed25519`)
- [ ] Upload/download scripts tested
- [ ] Monitoring scripts prepared

### Execution Plan
- [ ] Test run planned (4 pods, 4 experiments)
- [ ] Full run strategy decided (4 or 8 pods)
- [ ] Monitoring schedule set
- [ ] Download plan ready

---

## 🆘 Emergency Contacts

### If Things Go Wrong

1. **Check**: [RQ2_Monitoring_and_Troubleshooting.md](RQ2_Monitoring_and_Troubleshooting.md)
2. **Emergency Stop**: `pkill -f "python src/"` on each pod
3. **Download Partial Results**: `bash scripts/download_from_runpod.sh`
4. **Resume**: Scripts auto-detect existing results

### Support Resources
- RunPod Discord: https://discord.gg/runpod
- RunPod Docs: https://docs.runpod.io/
- AutoGen Docs: https://microsoft.github.io/autogen/

---

## 📝 Post-Execution Checklist

After all experiments complete:

- [ ] Download all results from 8 pods
- [ ] Verify 32 experiments completed
- [ ] Check sample counts (386 vuln, 164 code)
- [ ] Validate energy tracking data
- [ ] Organize results by model/prompt type
- [ ] Terminate all pods (stop billing!)
- [ ] Backup results to cloud storage
- [ ] Run comprehensive RQ2 analysis
- [ ] Generate visualizations
- [ ] Document findings

---

## 🎓 Next Steps After RQ2

1. **Analyze Results**
   - Compare single vs dual vs multi-agent performance
   - Evaluate accuracy and robustness metrics
   - Assess computational efficiency

2. **Write RQ2 Findings**
   - Document performance differences
   - Identify optimal agent configurations
   - Compare against RQ1 baselines

3. **Prepare for RQ3** (if applicable)
   - Explanation prompting experiments
   - Using insights from RQ2

4. **Prepare for RQ4** (if applicable)
   - Cost-efficiency analysis
   - Quality-cost trade-offs
   - Use API tracking data (if implemented)

---

## 📌 Key Reminders

1. **Test Before Full Run**: Always validate with test run first
2. **Monitor Progress**: Check pods every 30-60 minutes
3. **Resume Works**: Don't panic if interrupted - resume functionality will recover
4. **Terminate Pods**: Remember to stop pods after download to avoid charges
5. **Backup Results**: Keep multiple copies of result files
6. **Document Issues**: Note any anomalies for paper discussion

---

## 🔗 Quick Links

- [Test Run Commands →](RQ2_Test_Run_Commands.md)
- [Full Run Commands →](RQ2_Full_Run_Commands.md)
- [Monitoring Guide →](RQ2_Monitoring_and_Troubleshooting.md)
- [Experiment Design →](rq2_experiment_design.md)
- [RunPod Setup →](RunPod_Setup_Guide.md)

---

**Good luck with your RQ2 experiments! 🚀**

**Estimated Timeline**: Test (Day 1) + Full Run (Day 2) + Analysis (Week 2-3) = **3-4 weeks total**
