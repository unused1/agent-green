# RQ2 Experiment Design: Agentic Moderation

**Research Question**: How do multi-agent setups (planner–executor, proposer–reviewer) compare to single-agent execution in accuracy and robustness under matched toolchains and budgets, and do these effects differ between reasoning and non-reasoning models?

**Date Created**: 2025-11-10
**Last Updated**: 2025-11-10
**Status**: Design Phase - Ready for Review

## Key Design Decisions

✅ **Full Scope Approved**: All 32 experiments (16 dual-agent + 16 multi-agent)
✅ **Execution Strategy**: Start with dual-agent first, then multi-agent
✅ **Hardware**: All experiments on RunPod H100 SXM 80GB (for fair comparison)
✅ **Baseline**: RQ1 single-agent experiments already complete (4B + 30B on H100)
✅ **Model Coverage**:
   - Qwen3-4B-Instruct + Qwen3-4B-Thinking
   - Qwen3-30B-A3B-Instruct + Qwen3-30B-A3B-Thinking
✅ **Prompting**: Zero-shot + Few-shot for all configurations
✅ **Tasks**: Vulnerability Detection + Code Generation
✅ **Estimated Cost**: ~$150 (with spot instances: ~$100-120)
✅ **Timeline**: 6 weeks

### Changes from Initial Design

**Updated (2025-11-10):**
1. ✅ **Removed Mars experiments** - All on H100 for consistent hardware comparison
2. ✅ **Included 4B H100 baseline** - Phase 2c (vuln) and Phase 3b (code gen) already complete
3. ✅ **Simplified hardware variable** - Single platform (H100) instead of two (Mars + H100)
4. ✅ **Updated cost estimate** - $150 instead of $60-80 (all RunPod, no free Mars)
5. ✅ **Shorter timeline** - 6 weeks instead of 7 (no Mars phase needed)

**Benefits:**
- ✅ Fairer comparison (all same hardware)
- ✅ Cleaner experiment design (one platform)
- ✅ Complete baseline (4B and 30B already on H100)
- ✅ Faster execution (no hardware switching)

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

**RQ1 Baseline (Already Complete)**: 8 single-agent configs × 2 tasks = 16 experiments ✅
**RQ2 New Experiments**: 16 configs × 2 tasks = 32 experiments ❌

### Experiment Breakdown by Phase

| Phase | Agent Config | Tasks | Experiments | Status |
|---|---|---|---|---|
| **RQ1 (Baseline)** | Single-agent | Vuln + Code | 16 | ✅ Complete |
| **RQ2 Phase 1** | Dual-agent | Vuln + Code | 16 | ⭐ Start Here |
| **RQ2 Phase 2** | Multi-agent | Vuln + Code | 16 | ⭐ After Phase 1 |

**Execution Strategy:**
1. Complete all 16 dual-agent experiments first
2. Analyze dual-agent results
3. Proceed with 16 multi-agent experiments
4. Comprehensive comparison analysis

**Notes:**
- Phase 2c: 4B models vulnerability detection on H100 (prompt comparison)
- Phase 3b: 4B + 30B models code generation on H100
- All experiments use same hardware (H100) for fair comparison
- No Mars experiments needed - full H100 matrix

---

## 3. Implementation Requirements

### 3.1 Missing Features to Add

**Resume/Restart Functionality** (Priority: HIGH)
- ✅ Already implemented in `single_agent_vuln.py`
- ❌ Not yet in `dual_agent_vuln.py`
- ❌ Not yet in `multi_agent_vuln_detection_four_agents.py`
- ❌ Not yet in dual/multi code generation scripts

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

### Phase 3: Main Experiments - RunPod H100 (Weeks 3-5)

**All Experiments on RunPod H100 SXM 80GB:**

**4B Models (16 experiments):**
- 8 dual-agent experiments (4 vuln + 4 code gen)
- 8 multi-agent experiments (4 vuln + 4 code gen)

**30B Models (16 experiments):**
- 8 dual-agent experiments (4 vuln + 4 code gen)
- 8 multi-agent experiments (4 vuln + 4 code gen)

**Estimated Runtime per Experiment:**
- Single-agent baseline: ~30-40 min (RQ1 reference)
- Dual-agent: ~60-90 min (2-3× more API calls)
- Multi-agent: ~120-180 min (4-6× more API calls)

**Total Runtime Estimate:**
- 16 dual-agent: 16 × 75 min = 20 hours
- 16 multi-agent: 16 × 150 min = 40 hours
- **Total: ~60 hours**

**Estimated Cost:**
- RunPod H100: $2.49/hr × 60 hours = **~$150**
- With spot instances (if available): ~$100-120

### Phase 4: Analysis & Visualization (Week 6)

**Tasks:**
1. Collect all RQ2 results
2. Create master datasets (SA vs DA vs MA comparison)
3. Generate comparison visualizations
4. Statistical significance testing
5. Robustness analysis
6. Cost-benefit analysis

**Deliverables:**
- RQ2 comprehensive analysis notebook
- Comparison scatter plots (SA vs DA vs MA)
- Agent interaction analysis
- Robustness metrics report
- Updated research findings document

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
