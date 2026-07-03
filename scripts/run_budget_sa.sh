#!/usr/bin/env bash
# Item 5 — Budget-matched single-agent baselines (RA1), RunPod.
#
# Spends DA/MA's call budget on a SINGLE agent (no roles) to test whether DA/MA
# gains come from collaboration or just more compute. Runs on VulTrial-386 with
# FRESH emissions in a separate folder; submitted runs are never touched.
#
# RESUMABLE: re-running the same command resumes (fixed EXP_NAME + idx-append).
#
# Prerequisite: a vLLM server for the target model is serving at $ENDPOINT.
#   super49b           -> nvidia/Llama-3_3-Nemotron-Super-49B-v1_5 (both modes, toggle)
#   qwen30b instruct   -> Qwen/Qwen3-30B-A3B-Instruct-2507
#   qwen30b thinking   -> Qwen/Qwen3-30B-A3B-Thinking-2507
#
# Usage:
#   bash scripts/run_budget_sa.sh {super49b|qwen30b} [instruct|thinking] {selfrev2|selfrev4|bon4}
#   (reasoning mode defaults to instruct; budget defaults to selfrev2)
#     selfrev2 -> self-revision, 2 calls  (matches DA)
#     selfrev4 -> self-revision, 4 calls  (matches MA)
#     bon4     -> best-of-4 self-consistency (matches MA)
set -euo pipefail

CFG="${1:-}"
RUN_MODE="${2:-instruct}"       # instruct | thinking  (reasoning toggle)
BUDGET="${3:-selfrev2}"         # selfrev2 | selfrev4 | bon4
export PROJECT_ROOT="${PROJECT_ROOT:-/workspace/agent-green}"
ENDPOINT="${ENDPOINT:-http://localhost:8000/v1}"

export USE_RUNPOD=true
export ENABLE_CODECARBON=true
export VULN_DATASET="${VULN_DATASET:-${PROJECT_ROOT}/vuln_database/VulTrial_386_samples_balanced.jsonl}"
export RESULTS_DIR="${PROJECT_ROOT}/results/runpod_vuln_386_budget"
export BASELINE_ENDPOINT="$ENDPOINT"
export REASONING_ENDPOINT="$ENDPOINT"
export BASELINE_API_KEY="${BASELINE_API_KEY:-dummy-key}"
export REASONING_API_KEY="${REASONING_API_KEY:-dummy-key}"

# Reasoning toggle (config reads BASELINE_* when off, REASONING_* when on).
case "$RUN_MODE" in
  instruct) export ENABLE_REASONING=false ;;
  thinking) export ENABLE_REASONING=true ;;
  *) echo "usage: $0 {super49b|qwen30b} [instruct|thinking] {selfrev2|selfrev4|bon4}" >&2; exit 1 ;;
esac

# Budget mode -> the harness's MODE / N_CALLS env.
case "$BUDGET" in
  selfrev2) export MODE=self_revision; export N_CALLS=2 ;;
  selfrev4) export MODE=self_revision; export N_CALLS=4 ;;
  bon4)     export MODE=best_of_n;     export N_CALLS=4 ;;
  *) echo "budget must be selfrev2|selfrev4|bon4" >&2; exit 1 ;;
esac

# Model selection.
case "$CFG" in
  super49b)
    export MODEL_FAMILY=nemotron
    SERVED="nvidia/Llama-3_3-Nemotron-Super-49B-v1_5"; MODELTAG="nvidia-Llama-3_3-Nemotron-Super-49B-v1_5" ;;
  qwen30b)
    export MODEL_FAMILY=
    if [ "$RUN_MODE" = thinking ]; then
      SERVED="Qwen/Qwen3-30B-A3B-Thinking-2507"; MODELTAG="Qwen-Qwen3-30B-A3B-Thinking-2507"
    else
      SERVED="Qwen/Qwen3-30B-A3B-Instruct-2507"; MODELTAG="Qwen-Qwen3-30B-A3B-Instruct-2507"
    fi ;;
  *) echo "usage: $0 {super49b|qwen30b} [instruct|thinking] {selfrev2|selfrev4|bon4}" >&2; exit 1 ;;
esac

if [ "$RUN_MODE" = thinking ]; then
  export REASONING_MODEL="${REASONING_MODEL:-$SERVED}"; ACTIVE="$REASONING_MODEL"
else
  export BASELINE_MODEL="${BASELINE_MODEL:-$SERVED}"; ACTIVE="$BASELINE_MODEL"
fi

SUFFIX=""; [ "$RUN_MODE" = thinking ] && SUFFIX="_thinking"
export EXP_NAME="${EXP_NAME:-SA-budget-${BUDGET}_${MODELTAG}${SUFFIX}}"

echo "================ Item 5 budget SA: ${CFG} / ${RUN_MODE} / ${BUDGET} ================"
echo "  model    : ${ACTIVE}  (ENABLE_REASONING=${ENABLE_REASONING})"
echo "  budget   : MODE=${MODE} N_CALLS=${N_CALLS}"
echo "  endpoint : ${ENDPOINT}"
echo "  dataset  : ${VULN_DATASET}"
echo "  results  : ${RESULTS_DIR}"
echo "  exp_name : ${EXP_NAME}  (resumable)"
echo "=============================================================================="

cd "${PROJECT_ROOT}"
python src/single_agent_budget_vuln.py SA-zero
