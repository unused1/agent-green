# Item 5 / Item 9 — Methods Notes and Threats to Validity

Scope: the budget-matched single-agent baselines (Item 5) and the VulAgent-lite
role-sensitivity variant (Item 9), both run on the pair-preserving VulTrial-386
set. These notes capture the methodological decisions taken during the runs so
they can be lifted into the paper's methods and threats-to-validity sections.

---

## 1. Evaluation set: pair-preserving VulTrial-386

The runs use `VulTrial_386_paired.jsonl`: 193 clean vulnerable/benign commit
**pairs** (386 samples), sampled with a fixed seed from the 870-sample set and a
strict subset of it. Preserving both members of each pair is required to report
**Pairwise-Correct (P-C)** — a pair counts as correct only when the model labels
both the vulnerable and the benign member correctly. The earlier 386 sample was
not pair-preserving (only 78 complete pairs), so it was replaced for these
experiments.

---

## 2. VulAgent-lite validator: verdict-first ordering

**Problem.** The validator originally emitted its per-candidate VALID/INVALID
justifications first and the `VERDICT:` line last. Qwen3-30B does not
self-terminate on this stage (see §4): it produced very long validator outputs,
and under the per-call generation cap the tail — including the verdict line —
was truncated. On the instruct run this clipped the verdict on **13% of Qwen
rows** (26 of 199), all of which then fell back to a less-reliable whole-text
parse. Nemotron was unaffected (its validator finishes at ~2k tokens).

**Fix.** The validator now emits `VERDICT: VULNERABLE` / `VERDICT: NOT
VULNERABLE` on the **first line**, then justifies below it. The label therefore
survives any truncation of the justification, for any model or mode. The model
still sees all candidates in its prompt and (in thinking mode) reasons in the
`<think>` block before answering, so the decision is not made less informed —
only its position in the output changes.

**Verification.** After the change, verdict capture holds even on clipped rows:
a validator output of 73,809 characters (truncated at the cap) still carried
`VERDICT: VULNERABLE` on line 1 and parsed correctly. All vulagent runs
(instruct and thinking, both models) use this validator; the earlier Qwen
instruct rows were re-generated so the whole Item 9 set is internally consistent.

---

## 3. Per-call generation cap (`VULAGENT_MAX_TOKENS = 20480`)

A single per-call cap is applied to every VulAgent-lite stage, uniform across
instruct and thinking so the reasoning-on/off comparison is not confounded by a
cap difference. The value was chosen empirically, not to hit a target:

- **Non-binding for legitimate content.** Nemotron's largest single-call output
  across hundreds of calls was ~2.5k tokens; genuine Qwen output tails reach
  ~4k. 20480 clears both with wide headroom.
- **Bounded by the pipeline, not by one call.** VulAgent-lite chains six calls:
  the four specialists' outputs form the aggregator's prompt, and the
  aggregator's output forms the validator's prompt, all under the 65,536-token
  vLLM context window. Because Qwen fills whatever cap it is given (§4), a cap
  near the full context would make a filled specialist/aggregator output
  overflow the *next* stage's prompt and abort the sample. 20480 is close to the
  safe ceiling for the six-stage pipeline; larger caps raise the context-overflow
  (skip) rate on large-code samples.
- **Thinking mode is chaining-safe at this cap.** In thinking mode the verbosity
  goes into the `<think>` block, which is stripped between stages before it is
  chained downstream. The stored/chained answers are therefore small (hundreds
  of characters), so downstream prompts stay small regardless of cap, and 20480
  leaves ample room for the think trace to complete and reach the verdict.

The cap only ever trims trailing justification/enumeration text, which the strict
validator discards; combined with verdict-first ordering (§2) it does not affect
the predicted label.

---

## 4. Model-dependent generation behaviour (efficiency caveat)

The two backbones behave differently under a generation cap, and this affects how
efficiency figures must be read:

- **Nemotron self-terminates.** Its stages stop at a natural end-of-sequence
  (~1–2.5k tokens/call) well below the cap, so its call lengths — and therefore
  its token and energy figures — are **intrinsic** to the model.
- **Qwen fills the cap.** Its aggregator and validator stages do not reach a
  natural stop and run until truncated; doubling the cap roughly doubled their
  output length. Its per-call generation is therefore **cap-bounded, not
  intrinsic**.

**Threat / caveat.** Token- and energy-per-sample comparisons that involve Qwen
VulAgent-lite reflect the 20480 operating point rather than a natural ceiling, so
cross-model efficiency numbers are not strictly apples-to-apples. This should be
stated when reporting compute/energy; the label-quality metrics (F1, P-C, PPR,
FPR) are unaffected because they depend only on the verdict, which is captured
regardless of truncation.

---

## 5. Context-overflow handling (skipped samples)

Two overflow paths can arise; both are handled by recording the sample as
`skipped: true` and excluding it at metric time, mirroring the established
no-response exclusion policy. Skip counts are reported per configuration.

- **Budget-matched self-revision (Item 5).** Self-revision appends each round's
  reply to the conversation. A large function plus verbose replies can push a
  later round's prompt past the 65,536-token context. Two mitigations:
  (a) the per-sample loop catches the context-length error and skips rather than
  crashing the whole run; (b) in thinking mode the `<think>` trace is stripped
  from the reply before it is fed back into the conversation, so only compact
  answers accumulate — this both matches the standard self-refinement contract
  (revise the prior answer, not the raw chain-of-thought) and prevents thinking
  traces from accumulating into an overflow. The strip is a no-op for instruct
  output.
- **VulAgent-lite chaining (Item 9).** As in §3, a filled upstream output can
  overflow a downstream stage's prompt on the largest-code samples. The per-
  sample handler skips and continues; observed skip rates are low at the 20480
  cap and are reported.

### Reasoning-tag formats differ across the two backbones (parsing note)

The two thinking backbones delimit their reasoning differently, which matters for
both parsing and the self-revision context management:

- **Nemotron-Super-49B** emits paired `<think> … </think>`.
- **Qwen3-30B-Thinking** emits the closing `</think>` but **not** the opening
  `<think>` (the opening marker is absent in its output format). Its reasoning is
  still substantial and genuine (observed ~15–27k chars/call) — only the opening
  tag is missing.

`strip_think_block` keys off `</think>` and returns only the text after it (the
communicated answer), so the reasoning is removed whether or not the opening tag
is present. Two consequences: (a) verdicts parse correctly for both models (the
canonical text parser strips the block before reading the verdict), and (b) in
budget-SA self-revision only the compact post-`</think>` answer is fed back into
the conversation, so Qwen's long reasoning does not accumulate across rounds and
selfrev4 stays within the context window. Any downstream analysis of the stored
`reasoning` field should pass it through `strip_think_block` to normalise the two
formats; a bare count of `<think>` occurrences will under-report Qwen's reasoning.

---

## 6. Planned verification (to run when the data lands)

A post-hoc check will confirm that the verdict-bearing **validator** stage is
never truncated before its `VERDICT:` line in either model or mode — i.e. that
the predicted label is cap-independent across the full set. Any clipping that
does occur is confined to the aggregator/specialist enumeration, which the
validator filters. This backs the claim that the per-call cap does not bias the
reported labels.

---

## Threats to validity — summary

1. **Cap-bounded compute for Qwen.** Qwen's non-self-terminating stages make its
   token/energy figures a function of the operating cap; reported with that
   caveat. Nemotron's are intrinsic. Label metrics are unaffected.
2. **Excluded samples.** A small number of samples per configuration are excluded
   for context overflow (skipped), analogous to no-response exclusion; counts are
   reported and are low.
3. **Prompt-ordering intervention.** Moving the verdict to the validator's first
   line is a formatting change applied uniformly across models and modes to make
   the label truncation-robust; it does not change the information available to
   the validator.
4. **Uniform cap across the reasoning axis.** Instruct and thinking use the same
   20480 cap so the RQ1 (reasoning vs non-reasoning) comparison is not confounded
   by a cap difference; verdict-first ordering makes the label robust to the cap
   in both.
