# Context Overflow Analysis - RQ2 Experiments

## Current Situation (Data Gap)

### What's NOT Being Captured:
1. **Full repeating output patterns** - Only visible in terminal, not saved
2. **Complete error messages** - BadRequestError details lost when script crashes
3. **Conversation history** - All 4 agent responses leading to overflow
4. **Response length metrics** - Token counts, character counts
5. **Timing information** - When overflow occurred during experiment

### What IS Being Captured:
1. **Manual documentation** in `RQ2_Experiment_Tracking.md`
   - Sample number and idx
   - Phase where overflow occurred
   - Brief description of pattern (e.g., "Endless 000...", "Repetitive enumeration")
2. **Experiment progress** - Results up to the failed sample are saved

## Impact on Research

### Lost Information:
- Cannot systematically analyze WHAT causes agents to get stuck
- Cannot measure response length progression across phases
- Cannot identify common patterns in problematic code
- Cannot do quantitative analysis of overflow characteristics

### What We Know (From Manual Observation):
- **Frequency**: ~4.9% of samples (19 unique, 20 total occurrences)
- **Pod-specific rates**:
  - Pod 4 (4B-Thinking, Few-Shot): 9 failures (2.3% of samples)
  - Pod 2 (4B-Thinking, Zero-Shot): 6 failures (1.6%)
  - Pod 1 (4B-Instruct, Zero-Shot): 3 failures (0.8%)
  - Pod 8 (30B-Thinking, Few-Shot): 2 failures (0.5%)
  - Pod 6 (30B-Thinking, Zero-Shot): 1 failure (0.3%)

- **Phase distribution**:
  - Phase 1 (Security Researcher): Several failures
  - Phase 2 (Code Author): 2 failures (Pod 2 idx: 217551, Pod 6 idx: 443152)
  - Phase 3 (Moderator): Some failures
  - Phase 4 (Review Board): 5+ failures (Pod 2 idx: 440872, Pod 4 idx: 210692, 195026, 201382, Pod 8 idx: 389760)

- **Common patterns**:
  1. Endless number generation (999..., 000...)
  2. Repetitive vulnerability enumeration (Vulnerability 1, 2, 3, ..., 155, 156, ...)
  3. Repetitive "no vulnerability" loops
  4. Code repetition (e.g., `i_data.nrpages = 0` repeated endlessly)
  5. Commit ID overflow (`0d0d0d0d...`)

## Problematic Samples (idx)

### Repeated Across Pods:
- **389760**: Failed on Pod 1 (4B-Instruct, Zero-Shot) AND Pod 8 (30B-Thinking, Few-Shot)
  - Same vulnerable code (atoi/r_num_math integer overflow)
  - Different output patterns (Pod 1: 999..., Pod 8: 000...)
  - **Insight**: Some code samples inherently problematic across configurations

### Unique Failures:
See `RQ2_Experiment_Tracking.md` for complete list

## Recommendations for Future Experiments

### 1. Implement Error Logging
Use `src/utils/context_overflow_logger.py` to capture:
- Full conversation history (all 4 agent responses)
- Last 10,000 characters of problematic response
- Error message and timestamp
- Metrics (response length, phase, sample info)

### 2. Modify Experiment Scripts
Add try-catch blocks around `initiate_chat()`:
```python
try:
    response = user_proxy.initiate_chat(...)
except BadRequestError as e:
    # Log overflow details
    overflow_logger.log_overflow(
        sample_idx=sample['idx'],
        sample_num=i+1,
        total_samples=len(remaining_samples),
        phase=phase_num,
        phase_name=phase_name,
        error_message=str(e),
        conversation_history={...},
        last_response=get_last_response(),
        experiment_name=exp_name
    )
    # Re-raise or handle
    raise
```

### 3. Post-Processing Analysis
After experiments complete, analyze `context_overflow_log.jsonl`:
- Extract common repeating patterns
- Measure average response length per phase
- Identify which vulnerability types cause overflows
- Correlate with code complexity metrics (LOC, cyclomatic complexity)

### 4. Prevention Strategies
Based on analysis, implement:
- **Max response length per phase** (e.g., 20,000 tokens)
- **Conversation truncation** after each phase
- **Early stopping** if response shows repetition
- **Output validation** to detect loops

## Current Workaround

**Manual intervention required:**
1. User monitors terminal output
2. When overflow detected, user identifies:
   - Sample number and idx
   - Phase where it occurred
   - Type of repetition pattern
3. User resumes experiment with skip option 2
4. User informs assistant to document in tracking file

**Limitation**: Only brief descriptions captured, full data lost

## RQ2 Specific Findings

### Configuration Impact:
- **4B-Thinking + Few-Shot** (Pod 4): Highest risk (2.3% failure rate)
  - Thinking model generates verbose reasoning
  - Few-shot examples use more initial context
  - Combined effect: frequent context overflows

- **4B-Thinking + Zero-Shot** (Pod 2): Moderate risk (1.6%)
  - Thinking model verbose, but no examples

- **30B models**: Lower risk (0.3-0.5%)
  - More capable at staying concise
  - Better at following instructions

### Research Value:
This context overflow pattern reveals important trade-offs:
- **More capable models** (Thinking) generate more detailed analysis but hit limits
- **Few-shot prompting** improves quality but reduces available context
- **Multi-agent architectures** accumulate context across phases
- Need for **adaptive context management** strategies
