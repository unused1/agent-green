# RQ2 Experiment Design: Agentic Moderation

**Research Question**: How do multi-agent setups (planner–executor, proposer–reviewer) compare to single-agent execution in accuracy and robustness under matched toolchains and budgets, and do these effects differ between reasoning and non-reasoning models?

**Date Created**: 2025-11-10
**Last Updated**: 2025-11-14
**Status**: Design Phase - Updated with Replication Requirements

## Key Design Decisions

✅ **Full Scope Approved**: All 32 experiments (16 dual-agent + 16 multi-agent)
✅ **Phased Execution Strategy**: Preliminary results first, replication if time permits
✅ **Priority 1 (Required)**: 32 experiments × 1 run = **32 runs** (preliminary results)
✅ **Priority 2 (If time permits)**: +2 runs per experiment = **+64 runs** (statistical significance)
✅ **Priority 3 (Optional)**: RQ1 replication = **+56 runs** (baseline variance)
✅ **Execution Order**: Start with dual-agent first, then multi-agent
✅ **Hardware**: All experiments on RunPod H100 SXM 80GB (for fair comparison)
✅ **Baseline**: RQ1 single-agent experiments already complete (4B + 30B on H100, 1 run each)
✅ **Model Coverage**:
   - Qwen3-4B-Instruct + Qwen3-4B-Thinking
   - Qwen3-30B-A3B-Instruct + Qwen3-30B-A3B-Thinking
✅ **Prompting**: Zero-shot + Few-shot for all configurations
✅ **Tasks**: Vulnerability Detection + Code Generation
✅ **Estimated Cost**:
   - Priority 1 (32 runs): ~$150
   - Priority 1+2 (96 runs): ~$450
   - All priorities (152 runs): ~$532
✅ **Timeline**:
   - Priority 1: 6 weeks
   - Priority 1+2: 8-10 weeks
   - All priorities: 10-12 weeks

### Changes from Initial Design

**Updated (2025-11-14 - v2 Phased Approach):**
1. ✅ **Phased execution strategy** - Preliminary results first (Priority 1), replication if time permits (Priority 2+3)
2. ✅ **Priority 1 (Required)**: 32 experiments × 1 run = 32 runs (~$150, 6 weeks)
3. ✅ **Priority 2 (Recommended)**: +2 runs per RQ2 experiment = +64 runs (~$300, +2-4 weeks)
4. ✅ **Priority 3 (Optional)**: +2 runs per RQ1 baseline = +56 runs (~$82, +2 weeks)
5. ✅ **Pragmatic approach** - Guarantees complete RQ2 preliminary results, adds replication if feasible

**Updated (2025-11-10):**
1. ✅ **Removed Mars experiments** - All on H100 for consistent hardware comparison
2. ✅ **Included 4B H100 baseline** - Phase 2c (vuln) and Phase 3b (code gen) already complete
3. ✅ **Simplified hardware variable** - Single platform (H100) instead of two (Mars + H100)

**Benefits of Phased Approach:**
- ✅ **Risk mitigation** - Guarantees complete preliminary results (32 experiments)
- ✅ **Flexibility** - Can stop after Priority 1 if time/budget constrained
- ✅ **Informed decisions** - Preliminary results guide replication priorities
- ✅ **Progressive rigor** - Can replicate high-variance or surprising results first
- ✅ **Publishable at any stage**:
  - Priority 1 alone: Valid preliminary findings
  - Priority 1+2: Full RQ2 with statistical significance
  - All priorities: Complete study with baseline variance

### Replication Strategy (Priority 2 & 3)

**If Time Permits - Why 3 Runs Total?**
1. **Statistical Validity**: Enables calculation of mean, standard deviation, and confidence intervals
2. **Variance Detection**: Identifies unstable/non-deterministic agent behaviors
3. **Outlier Detection**: Can identify and handle anomalous runs (3 is minimum for this)
4. **Academic Standard**: Most ML/AI research requires ≥3 runs for publication
5. **Robustness Claims**: Can make stronger claims about consistency (RQ2 hypothesis H4)

**What We Can Measure with 3 Runs:**
- Mean performance (accuracy, F1, pass@1) ± standard deviation
- Performance stability across agent configurations
- Statistical significance testing (t-tests, ANOVA)
- Confidence intervals (95% CI with 3 runs)
- Coefficient of variation (CV) to compare robustness

**Replication Priority Order (if time limited):**
1. Dual-agent experiments (easier to replicate, 2-3× time vs SA)
2. High-variance or surprising results from Priority 1
3. Multi-agent experiments (harder to replicate, 4-6× time vs SA)
4. RQ1 baseline (for statistical comparison)

---

## 1. Existing Code Architecture

### Available Implementations

**Vulnerability Detection:**
- `single_agent_vuln.py` - Baseline single-agent (RQ1 ✅)
- `dual_agent_vuln.py` - 2 agents: Code Author + Security Analyst
- `multi_agent_vuln_detection_three_agents.py` - 3 agents
- `multi_agent_vuln_detection_four_agents.py` - 4 agents: Security Researcher + Code Author + Moderator + Review Board
- `no_agent_vuln_detection.py` - Direct prompting baseline

**Code Generation:**
- `single_agent_code_generation.py` - Baseline single-agent (RQ1 ✅)
- `dual_agent_code_generation.py` - 2 agents: Programmer + Critic
- `multi_agent_code_generation.py` - Multi-agent workflow
- `no_agent_code_generation.py` - Direct prompting baseline

### Agent Architectures

#### Dual Agent (2 Agents)

**Vulnerability Detection:**
1. **Code Author Agent**: Generates/revises code based on feedback
2. **Security Analyst Agent**: Analyzes vulnerabilities, provides feedback, makes final decision

**Code Generation:**
1. **Programmer Agent**: Generates/revises Python code
2. **Critic Agent**: Reviews quality and correctness, provides feedback

**Workflow**: Iterative feedback loop → Code Author/Programmer generates → Security Analyst/Critic reviews → Iterate → Final decision

#### Multi-Agent (4 Agents)

**Vulnerability Detection:**
1. **Security Researcher Agent**: Identifies potential vulnerabilities
2. **Code Author Agent**: Defends code or proposes mitigations
3. **Moderator Agent**: Provides neutral summaries
4. **Review Board Agent**: Makes final decisions on validity and severity

**Workflow**: Adversarial deliberation → Security Researcher flags issues → Code Author defends → Moderator summarizes → Review Board decides

---

## 2. RQ2 Experiment Design

### 2.1 Research Hypotheses

**H1**: Multi-agent setups improve accuracy compared to single-agent
**H2**: Reasoning models benefit MORE from multi-agent collaboration than non-reasoning models
**H3**: 4-agent setup outperforms 2-agent which outperforms 1-agent (more deliberation = better)
**H4**: Multi-agent robustness (consistency across samples) is higher than single-agent

### 2.2 Experimental Variables

**Independent Variables:**
1. **Agent Configuration** (3 levels):
   - Single-agent (SA) - RQ1 baseline
   - Dual-agent (DA) - 2 agents
   - Multi-agent (MA) - 4 agents

2. **Model Type** (2 levels):
   - Instruct (non-reasoning)
   - Thinking (reasoning-enabled)

3. **Model Size** (2 levels):
   - 4B (Qwen3-4B)
   - 30B (Qwen3-30B-A3B MoE)

4. **Prompting Strategy** (2 levels):
   - Zero-shot
   - Few-shot

5. **Hardware** (1 level):
   - RunPod (H100 SXM 80GB) - All experiments for fair comparison

6. **Model Precision** (1 level):
   - BF16 (bfloat16) - No quantization applied
   - vLLM `--dtype bfloat16` or `--dtype auto` (defaults to BF16 on H100)

7. **Temperature** (1 level):
   - **0.0** (deterministic/greedy decoding)
   - Ensures reproducibility and consistent outputs across runs
   - Configured in `src/config.py`: `TEMPERATURE = 0.0`

**Dependent Variables:**
1. **Performance Metrics**:
   - Vulnerability Detection: Accuracy, Precision, Recall, F1 Score
   - Code Generation: Pass@1, Pass Rate %

2. **Energy Metrics**:
   - Total energy consumed (kWh)
   - CO2 emissions (kg)
   - Duration (seconds)
   - Energy per sample

3. **Robustness Metrics** (new):
   - Prediction variance across samples
   - Consistency score
   - Error rate stability

4. **Collaboration Metrics** (new):
   - Number of agent interactions
   - Token overhead (vs single-agent)
   - Deliberation quality (qualitative analysis)

### 2.3 Experiment Matrix

**All Experiments on RunPod H100 SXM 80GB**

**Per Task (Vulnerability Detection + Code Generation):**

| Agent Config | Model Type | Model Size | Prompting | RQ1 Done | RQ2 Needed |
|---|---|---|---|---|---|
| **Single-agent** | Instruct | 4B | Zero-shot | ✅ (Phase 2c/3b) | Baseline |
| **Single-agent** | Instruct | 4B | Few-shot | ✅ (Phase 2c/3b) | Baseline |
| **Single-agent** | Thinking | 4B | Zero-shot | ✅ (Phase 2c/3b) | Baseline |
| **Single-agent** | Thinking | 4B | Few-shot | ✅ (Phase 2c/3b) | Baseline |
| **Single-agent** | Instruct | 30B | Zero-shot | ✅ (Phase 2a/3b) | Baseline |
| **Single-agent** | Instruct | 30B | Few-shot | ✅ (Phase 2a/3b) | Baseline |
| **Single-agent** | Thinking | 30B | Zero-shot | ✅ (Phase 2a/3b) | Baseline |
| **Single-agent** | Thinking | 30B | Few-shot | ✅ (Phase 2a/3b) | Baseline |
| **Dual-agent** | Instruct | 4B | Zero-shot | ❌ | **NEW** ⭐ |
| **Dual-agent** | Instruct | 4B | Few-shot | ❌ | **NEW** ⭐ |
| **Dual-agent** | Thinking | 4B | Zero-shot | ❌ | **NEW** ⭐ |
| **Dual-agent** | Thinking | 4B | Few-shot | ❌ | **NEW** ⭐ |
| **Dual-agent** | Instruct | 30B | Zero-shot | ❌ | **NEW** ⭐ |
| **Dual-agent** | Instruct | 30B | Few-shot | ❌ | **NEW** ⭐ |
| **Dual-agent** | Thinking | 30B | Zero-shot | ❌ | **NEW** ⭐ |
| **Dual-agent** | Thinking | 30B | Few-shot | ❌ | **NEW** ⭐ |
| **Multi-agent** | Instruct | 4B | Zero-shot | ❌ | **NEW** ⭐ |
| **Multi-agent** | Instruct | 4B | Few-shot | ❌ | **NEW** ⭐ |
| **Multi-agent** | Thinking | 4B | Zero-shot | ❌ | **NEW** ⭐ |
| **Multi-agent** | Thinking | 4B | Few-shot | ❌ | **NEW** ⭐ |
| **Multi-agent** | Instruct | 30B | Zero-shot | ❌ | **NEW** ⭐ |
| **Multi-agent** | Instruct | 30B | Few-shot | ❌ | **NEW** ⭐ |
| **Multi-agent** | Thinking | 30B | Zero-shot | ❌ | **NEW** ⭐ |
| **Multi-agent** | Thinking | 30B | Few-shot | ❌ | **NEW** ⭐ |

**RQ1 Baseline (Already Complete)**: 8 single-agent configs × 2 tasks = 16 experiments (1 run each) ✅
**RQ2 New Experiments**: 16 configs × 2 tasks = 32 unique experiments ❌

### Experiment Breakdown by Priority

| Priority | Phase | Agent Config | Tasks | Configs | Runs | Total Runs | Status |
|---|---|---|---|---|---|---|---|
| **RQ1** | Baseline | Single-agent | Vuln + Code | 16 | 1 | 16 | ✅ Complete |
| **Priority 1** | RQ2 Prelim | Dual-agent | Vuln + Code | 16 | 1 | **16** | ⭐ Start Here |
| **Priority 1** | RQ2 Prelim | Multi-agent | Vuln + Code | 16 | 1 | **16** | ⭐ After DA |
| | | | | | **P1 Subtotal** | **32** | |
| **Priority 2** | RQ2 Replication | Dual-agent | Vuln + Code | 16 | +2 | **+32** | If time permits |
| **Priority 2** | RQ2 Replication | Multi-agent | Vuln + Code | 16 | +2 | **+32** | If time permits |
| | | | | | **P2 Subtotal** | **+64** | |
| **Priority 3** | RQ1 Replication | Single-agent | Vuln + Code | 16 | +2 | **+32** | Optional |
| **Priority 3** | RQ1 Replication | Single-agent | Code only | 12 | +2 | **+24** | Optional |
| | | | | | **P3 Subtotal** | **+56** | |
| | | | | | **GRAND TOTAL** | **152** | |

### Execution Strategy (Phased)

**Priority 1 (Required - 6 weeks, ~$150):**
1. Run all 16 dual-agent configs once (16 runs: 8 vuln + 8 code gen)
2. Quick preliminary analysis
3. Run all 16 multi-agent configs once (16 runs: 8 vuln + 8 code gen)
4. Preliminary RQ2 comparison analysis (SA vs DA vs MA)
5. **Decision point**: Assess timeline and decide on replication

**Priority 2 (If time permits - +2-4 weeks, +~$300):**
6. Replicate all dual-agent configs (2 more runs each = +32 runs)
7. Replicate all multi-agent configs (2 more runs each = +32 runs)
8. Full variance analysis with 3 runs per experiment
9. Statistical significance testing (t-tests, ANOVA)

**Priority 3 (Optional - +2 weeks, +~$82):**
10. Replicate RQ1 baselines for statistical comparison (2 more runs each = +56 runs)
11. Complete variance analysis across all agent configurations

**Run Naming Convention:**
- Priority 1: `DA-vuln_Qwen3-4B-Instruct_zero-shot_20251114-120000`
- Priority 2+: `DA-vuln_Qwen3-4B-Instruct_zero-shot_20251114-120000_run1` (retroactively rename P1)
- Priority 2+: `DA-vuln_Qwen3-4B-Instruct_zero-shot_20251114-130000_run2`
- Priority 2+: `DA-vuln_Qwen3-4B-Instruct_zero-shot_20251114-140000_run3`

**Notes:**
- Phase 2c: 4B models vulnerability detection on H100 (prompt comparison)
- Phase 3b: 4B + 30B models code generation on H100
- All experiments use same hardware (H100) for fair comparison
- No Mars experiments needed - full H100 matrix

---

## 3. Implementation Requirements

### 3.1 Features to Add/Update

**Resume/Restart Functionality** (Priority: HIGH)
- ✅ Already implemented in `single_agent_vuln.py`
- ✅ **DONE** - `dual_agent_vuln.py` (2025-11-14)
- ✅ **DONE** - `dual_agent_code_generation.py` (2025-11-14)
- ❌ Not yet in `multi_agent_vuln_detection_four_agents.py`
- ❌ Not yet in `multi_agent_code_generation.py`

**Run Tracking for Replication** (Priority: HIGH - NEW)
- Add run number tracking (run1, run2, run3) to experiment names
- Automated run management: loop through 3 runs per config
- Aggregate results across runs for variance analysis
- Prevent duplicate runs (check if all 3 runs exist before re-running)

**Required Implementation:**
```python
def find_most_recent_results(result_dir, design, model):
    """Find most recent experiment with same design and model"""
    # Scan for existing files matching pattern
    # Return exp_name if found, None otherwise

def initialize_results_files(exp_name, result_dir, design, model):
    """Initialize or resume experiment"""
    skip_next_sample = False

    existing_base = find_most_recent_results(result_dir, design, model)
    if existing_base:
        print(f"\n[FOUND] Existing experiment: {existing_base}")
        print("Options:")
        print("  1. Resume from last completed sample")
        print("  2. Skip next sample (if problematic)")
        print("  3. Start fresh")

        response = input("Enter choice (1/2/3): ").strip()
        # Handle choice...

    return detailed_file, csv_file, energy_file, skip_next_sample
```

**Why This Matters for Multi-Agent:**
- Multi-agent experiments take LONGER (more API calls)
- Higher risk of interruption/timeout
- Resume capability is CRITICAL for cost control

### 3.2 Configuration Standardization

**Ensure Consistent LLM Config:**
- Same API endpoint
- Same generation parameters (temperature, max_tokens, etc.)
- Same system prompts (where appropriate)
- Fair comparison across agent configurations

**Matched Budgets:**
- Single-agent: 1 API call per sample
- Dual-agent: 2-3 API calls per sample (initial + feedback + final)
- Multi-agent: 4-6 API calls per sample (all agents participate)
- Track token usage for fair cost comparison

### 3.3 Additional Metrics Collection

**Agent Interaction Tracking:**
```python
{
    "sample_id": 123,
    "agent_config": "dual-agent",
    "interactions": [
        {"agent": "code_author", "tokens": 150, "role": "initial_generation"},
        {"agent": "security_analyst", "tokens": 200, "role": "feedback"},
        {"agent": "code_author", "tokens": 180, "role": "revision"},
        {"agent": "security_analyst", "tokens": 100, "role": "final_decision"}
    ],
    "total_tokens": 630,
    "num_iterations": 2
}
```

**Robustness Metrics:**
```python
# Calculate prediction variance across similar samples
# Measure consistency of agent decisions
# Track error patterns by agent configuration
```

---

## 4. Execution Plan

### Phase 1: Infrastructure Preparation (Week 1)

**Tasks:**
1. Add resume/restart functionality to all multi-agent scripts
2. Standardize configuration management
3. Add interaction tracking to all agent scripts
4. Create unified result collection scripts
5. Update evaluation scripts for robustness metrics

**Deliverables:**
- ✅ All scripts support resume
- ✅ Consistent config across all agent types
- ✅ Enhanced logging for agent interactions
- ✅ Test runs validate functionality

### Phase 2: Pilot Experiments (Week 2)

**Objective**: Validate infrastructure with small-scale test

**Experiments on RunPod H100:**
- 2 dual-agent experiments (1 vuln, 1 code gen)
- 2 multi-agent experiments (1 vuln, 1 code gen)
- Use 4B Instruct Zero-shot

**Validation Checklist:**
- [ ] Resume functionality works correctly
- [ ] Energy tracking accurate
- [ ] Agent interactions logged
- [ ] Results format consistent with RQ1
- [ ] No crashes or hangs

**Estimated Cost:**
- RunPod H100: $2.49/hr
- Pilot runtime: ~2-4 hours
- Budget: ~$5-10

### Phase 3: Main Experiments - RunPod H100 (Weeks 3-6+)

**All Experiments on RunPod H100 SXM 80GB:**

**Estimated Runtime per Single Run:**
- Single-agent baseline: ~30-40 min (RQ1 reference)
- Dual-agent: ~60-90 min (2-3× more API calls)
- Multi-agent: ~120-180 min (4-6× more API calls)

#### Priority 1: Preliminary Results (Required - Weeks 3-6)

**4B Models (16 unique experiments × 1 run = 16 runs):**
- 8 dual-agent configs × 1 run = 8 runs (4 vuln + 4 code gen)
- 8 multi-agent configs × 1 run = 8 runs (4 vuln + 4 code gen)

**30B Models (16 unique experiments × 1 run = 16 runs):**
- 8 dual-agent configs × 1 run = 8 runs (4 vuln + 4 code gen)
- 8 multi-agent configs × 1 run = 8 runs (4 vuln + 4 code gen)

**Priority 1 Runtime:**
- 16 dual-agent: 16 × 75 min = **20 hours**
- 16 multi-agent: 16 × 150 min = **40 hours**
- **Total: ~60 hours**

**Priority 1 Cost:**
- RunPod H100: $2.49/hr × 60 hours = **~$150**
- With spot instances: ~$100-120

**Priority 1 Execution Plan:**
- Week 3-4: Dual-agent (16 runs, ~20 hours, ~$50)
- Week 5-6: Multi-agent (16 runs, ~40 hours, ~$100)
- **Checkpoint**: Preliminary analysis → Decide on replication

#### Priority 2: Replication (If time permits - Weeks 7-10)

**Replicate all RQ2 configs (32 configs × 2 additional runs = 64 runs):**
- 16 dual-agent × 2 runs = 32 runs
- 16 multi-agent × 2 runs = 32 runs

**Priority 2 Runtime:**
- 32 dual-agent: 32 × 75 min = **40 hours**
- 32 multi-agent: 32 × 150 min = **80 hours**
- **Total: ~120 hours**

**Priority 2 Cost:**
- RunPod H100: $2.49/hr × 120 hours = **~$300**
- With spot instances: ~$200-240

**Priority 2 Execution Plan:**
- Week 7-8: Dual-agent replication (32 runs, ~40 hours, ~$100)
- Week 9-10: Multi-agent replication (32 runs, ~80 hours, ~$200)

#### Priority 3: RQ1 Baseline Replication (Optional - Weeks 11-12)

**Replicate RQ1 configs (28 configs × 2 additional runs = 56 runs):**
- 16 vuln detection (4B + 30B) × 2 runs = 32 runs
- 12 code generation (4B + 30B) × 2 runs = 24 runs

**Priority 3 Runtime:**
- 56 single-agent: 56 × 35 min = **33 hours**

**Priority 3 Cost:**
- RunPod H100: $2.49/hr × 33 hours = **~$82**
- With spot instances: ~$55-65

### Phase 4: Analysis & Visualization

#### Phase 4a: Preliminary Analysis (After Priority 1 - Week 6)

**Tasks:**
1. Collect Priority 1 results (32 runs: 16 DA + 16 MA)
2. Create preliminary datasets (SA vs DA vs MA comparison)
3. **Preliminary analysis** (no variance yet):
   - Direct performance comparison (point estimates)
   - Energy consumption comparison
   - Agent interaction patterns
   - Cost-benefit analysis (preliminary)
4. Generate comparison visualizations (no error bars yet)
5. **Decision point**: Assess need for replication

**Deliverables:**
- Preliminary RQ2 analysis notebook
- Comparison plots (SA vs DA vs MA) - point estimates
- Agent interaction summary
- Cost-benefit analysis (preliminary)
- **Go/No-go decision** on Priority 2 replication

#### Phase 4b: Statistical Analysis (After Priority 2 - Weeks 10-11)

**Tasks (if Priority 2 completed):**
1. Collect all Priority 1+2 results (96 runs: 48 DA + 48 MA)
2. Create complete datasets with replication data
3. **Full statistical analysis** (enabled by 3 runs):
   - Calculate mean ± std dev for each configuration
   - Perform t-tests / ANOVA for significance testing
   - Compute 95% confidence intervals
   - Variance analysis across runs
4. Generate comparison visualizations with error bars
5. Robustness analysis (coefficient of variation, outlier detection)
6. Cost-benefit analysis with confidence intervals

**Deliverables:**
- Complete RQ2 analysis notebook with statistical tests
- Comparison scatter plots (SA vs DA vs MA) with error bars
- Agent interaction analysis (with variance)
- Robustness metrics report (variance, CV, stability)
- Statistical significance tables (p-values, effect sizes)
- Publication-ready findings document

#### Phase 4c: Complete Variance Analysis (After Priority 3 - Week 12)

**Tasks (if Priority 3 completed):**
1. Add RQ1 replication data (56 additional runs)
2. Complete variance analysis across all agent configurations
3. Full statistical comparison with baseline variance
4. Enhanced robustness claims with complete variance data

**Deliverables:**
- Complete statistical comparison across all configurations
- Enhanced robustness analysis with baseline variance
- Publication-quality results with full replication

---

## 5. Expected Outcomes

### Performance Expectations

**Optimistic Scenario:**
- Multi-agent improves F1 by 5-10pp over single-agent
- Thinking models benefit more from collaboration
- 4-agent > 2-agent > 1-agent hierarchy holds

**Realistic Scenario:**
- Multi-agent improves F1 by 2-5pp
- Improvement task-dependent (vuln > code gen)
- Diminishing returns from 2-agent to 4-agent

**Pessimistic Scenario:**
- No significant improvement (added complexity = added noise)
- Energy cost outweighs small accuracy gains
- Single-agent remains most efficient

### Energy-Performance Trade-offs

**Expected Energy Ratios:**
- Dual-agent: 2-3× single-agent (more API calls)
- Multi-agent: 4-6× single-agent (many agent interactions)

**Break-even Analysis:**
- If dual-agent costs 2.5× energy but improves F1 by 5pp: Worth it?
- If multi-agent costs 5× energy but improves F1 by 8pp: Worth it?
- Compare to RQ1 finding: Thinking costs 4× for 17pp improvement

### Research Contributions

1. **First systematic comparison** of single vs multi-agent reasoning models
2. **Energy cost analysis** of agentic orchestration
3. **Practical guidance** on when to use multi-agent setups
4. **Robustness insights** for production deployment

---

## 6. Risk Mitigation

### Technical Risks

**Risk 1**: Multi-agent experiments crash/hang
- **Mitigation**: Resume functionality (HIGH PRIORITY)
- **Mitigation**: Timeout mechanisms
- **Mitigation**: Incremental saving after each sample

**Risk 2**: Budget overruns on RunPod
- **Mitigation**: Run Mars experiments first (free)
- **Mitigation**: Pilot test to estimate actual runtime
- **Mitigation**: Use spot instances where possible

**Risk 3**: Agent collaboration doesn't converge
- **Mitigation**: Max iteration limits
- **Mitigation**: Fallback to single-agent decision if stuck
- **Mitigation**: Monitor and adjust prompts

### Scientific Risks

**Risk 1**: No significant improvement from multi-agent
- **Outcome**: Still a valid finding (negative result)
- **Paper angle**: "Multi-agent complexity not justified for these tasks"

**Risk 2**: Results inconsistent across runs
- **Mitigation**: Multiple random seeds
- **Mitigation**: Robustness metrics to quantify variance
- **Mitigation**: Statistical significance testing

---

## 7. Success Criteria

### Minimum Viable RQ2

**Must Have:**
- [ ] All 32 new experiments completed
- [ ] Resume functionality working
- [ ] Energy tracking for all experiments
- [ ] Performance metrics comparable to RQ1
- [ ] Statistical comparison (SA vs DA vs MA)

### Complete RQ2

**Should Have:**
- [ ] Robustness metrics calculated
- [ ] Agent interaction analysis
- [ ] Token overhead quantified
- [ ] Cost-benefit recommendations
- [ ] Publication-ready visualizations

### Stretch Goals

**Nice to Have:**
- [ ] Qualitative analysis of agent deliberations
- [ ] Failure case analysis
- [ ] Agent prompt optimization
- [ ] Cross-task generalization insights

---

## 8. Timeline Summary

| Week | Activities | Deliverables |
|---|---|---|
| 1 | Infrastructure prep | Resume functionality, enhanced logging |
| 2 | Pilot experiments (H100) | Validated infrastructure (~$5-10) |
| 3-5 | Main experiments (H100) | 32 experiments (16 DA + 16 MA) |
| 6 | Analysis | RQ2 comprehensive report |

**Total Duration**: 6 weeks
**Total Budget**: ~$150 (RunPod H100 only)

---

## 9. Next Steps

### Immediate Actions (This Week)

1. **Review this design document** with supervisor
2. **Prioritize experiments** if time/budget constrained
3. **Start infrastructure prep** (resume functionality)
4. **Create pilot experiment plan**

### Decision Points

**Q1**: Do we need all 32 experiments, or can we reduce scope?
- Option A: Full matrix (32 experiments) - **Comprehensive** (~$150, 6 weeks)
- Option B: 4B only (16 experiments) - **Faster, cheaper** (~$60, 4 weeks)
- Option C: Zero-shot only (16 experiments) - **Focus on pure reasoning** (~$75, 5 weeks)
- Option D: Vuln detection only (16 experiments) - **Focus on complex task** (~$75, 5 weeks)
- Option E: Dual-agent only (16 experiments) - **Simpler collaboration** (~$50, 4 weeks)

**Q2**: Which agent configuration to prioritize?
- Dual-agent first (simpler, faster to validate, then decide on multi-agent)
- Multi-agent first (more ambitious, if fails we still have baseline)
- Both in parallel (if confident in infrastructure)

---

**Status**: Ready for supervisor review and approval to proceed
