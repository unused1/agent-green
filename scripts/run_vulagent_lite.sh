#!/usr/bin/env bash
# Item 9 — VulAgent-lite role-sensitivity variant (RA7), RunPod.
#
# A materially different multi-agent role/coordination scheme (perspective
# specialists -> aggregator -> validator; anchored on VulAgent, LLM-only) run under
# the SAME conditions as our VulTrial-MA so the role design is the only variable.
# VulTrial-386, FRESH emissions in a separate folder; submitted runs untouched.
#
# RESUMABLE: re-running the same command resumes (fixed EXP_NAME + idx-append).
#
# Prerequisite: a vLLM server for the target model is serving at $ENDPOINT.
#   super49b           -> nvidia/Llama-3_3-Nemotron-Super-49B-v1_5 (both modes, toggle)
#   qwen30b instruct   -> Qwen/Qwen3-30B-A3B-Instruct-2507
#   qwen30b thinking   -> Qwen/Qwen3-30B-A3B-Thinking-2507
#
# Usage:
#   bash scripts/run_vulagent_lite.sh {super49b|qwen30b} [instruct|thinking]
set -euo pipefail

CFG="${1:-}"
RUN_MODE="${2:-instruct}"
export PROJECT_ROOT="${PROJECT_ROOT:-/workspace/agent-green}"
ENDPOINT="${ENDPOINT:-http://localhost:8000/v1}"

export USE_RUNPOD=true
export ENABLE_CODECARBON=true
export VULN_DATASET="${VULN_DATASET:-${PROJECT_ROOT}/vuln_database/VulTrial_386_paired.jsonl}"
export RESULTS_DIR="${PROJECT_ROOT}/results/runpod_vuln_386paired_vulagent"
export BASELINE_ENDPOINT="$ENDPOINT"
export REASONING_ENDPOINT="$ENDPOINT"
export BASELINE_API_KEY="${BASELINE_API_KEY:-dummy-key}"
export REASONING_API_KEY="${REASONING_API_KEY:-dummy-key}"

case "$RUN_MODE" in
  instruct) export ENABLE_REASONING=false ;;
  thinking) export ENABLE_REASONING=true ;;
  *) echo "usage: $0 {super49b|qwen30b} [instruct|thinking]" >&2; exit 1 ;;
esac

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
  *) echo "usage: $0 {super49b|qwen30b} [instruct|thinking]" >&2; exit 1 ;;
esac

if [ "$RUN_MODE" = thinking ]; then
  export REASONING_MODEL="${REASONING_MODEL:-$SERVED}"; ACTIVE="$REASONING_MODEL"
else
  export BASELINE_MODEL="${BASELINE_MODEL:-$SERVED}"; ACTIVE="$BASELINE_MODEL"
fi

SUFFIX=""; [ "$RUN_MODE" = thinking ] && SUFFIX="_thinking"
export EXP_NAME="${EXP_NAME:-VulAgentLite_${MODELTAG}${SUFFIX}}"

echo "================ Item 9 VulAgent-lite: ${CFG} / ${RUN_MODE} ================"
echo "  model    : ${ACTIVE}  (ENABLE_REASONING=${ENABLE_REASONING})"
echo "  pipeline : 4 specialists -> aggregator -> validator (6 calls/sample)"
echo "  endpoint : ${ENDPOINT}"
echo "  dataset  : ${VULN_DATASET}"
echo "  results  : ${RESULTS_DIR}"
echo "  exp_name : ${EXP_NAME}  (resumable)"
echo "=========================================================================="

cd "${PROJECT_ROOT}"
python src/multi_agent_vulagent_lite.py
