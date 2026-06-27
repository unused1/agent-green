#!/usr/bin/env bash
# Option B — VulTrial-faithful constrained Multi-Agent re-inference (RunPod).
#
# Re-runs MA on VulTrial-870 with the constrained Review Board verdict scheme
# (decision in {valid, invalid, partially valid}) and binarises the live label
# via parse_ma_constrained(strict). Outputs go to a SEPARATE folder with FRESH
# emissions; the submitted runs are never touched.
#
# RESUMABLE: re-running the same command resumes (fixed EXP_NAME + per-sample
# durable append in ExperimentResume). Safe to Ctrl-C and relaunch.
#
# Prerequisite: a vLLM server for the target model is already serving at
# $ENDPOINT. The served model must match:
#   super49b           -> nvidia/Llama-3_3-Nemotron-Super-49B-v1_5 (both modes, toggle)
#   qwen30b instruct   -> Qwen/Qwen3-30B-A3B-Instruct-2507
#   qwen30b thinking   -> Qwen/Qwen3-30B-A3B-Thinking-2507
#
# Usage:
#   bash scripts/run_option_b_ma.sh super49b [instruct|thinking]
#   bash scripts/run_option_b_ma.sh qwen30b  [instruct|thinking]
# (mode defaults to instruct)
set -euo pipefail

CFG="${1:-}"
MODE="${2:-instruct}"
export PROJECT_ROOT="${PROJECT_ROOT:-/workspace/agent-green}"
ENDPOINT="${ENDPOINT:-http://localhost:8000/v1}"

export USE_RUNPOD=true
export ENABLE_CODECARBON=true                 # fresh, separate emissions
export VULN_DATASET="${PROJECT_ROOT}/vuln_database/VulTrial_870_samples_balanced.jsonl"
export RESULTS_DIR="${PROJECT_ROOT}/results/runpod_vuln_870_constrained"
export BASELINE_ENDPOINT="$ENDPOINT"
export REASONING_ENDPOINT="$ENDPOINT"
export BASELINE_API_KEY="${BASELINE_API_KEY:-dummy-key}"
export REASONING_API_KEY="${REASONING_API_KEY:-dummy-key}"

case "$MODE" in
  instruct) export ENABLE_REASONING=false ;;
  thinking) export ENABLE_REASONING=true ;;
  *) echo "usage: $0 {super49b|qwen30b} [instruct|thinking]" >&2; exit 1 ;;
esac

case "$CFG" in
  super49b)
    export MODEL_FAMILY=nemotron
    SERVED="nvidia/Llama-3_3-Nemotron-Super-49B-v1_5"   # same checkpoint, mode via /no_think toggle
    MODELTAG="nvidia-Llama-3_3-Nemotron-Super-49B-v1_5"
    ;;
  qwen30b)
    export MODEL_FAMILY=                                # empty -> Qwen3 (base config)
    if [ "$MODE" = thinking ]; then
      SERVED="Qwen/Qwen3-30B-A3B-Thinking-2507"; MODELTAG="Qwen-Qwen3-30B-A3B-Thinking-2507"
    else
      SERVED="Qwen/Qwen3-30B-A3B-Instruct-2507"; MODELTAG="Qwen-Qwen3-30B-A3B-Instruct-2507"
    fi
    ;;
  *)
    echo "usage: $0 {super49b|qwen30b} [instruct|thinking]" >&2; exit 1 ;;
esac

# Point the active mode's model var at the served model (config reads BASELINE_*
# when ENABLE_REASONING=false, REASONING_* when true). Either can be overridden.
if [ "$MODE" = thinking ]; then
  export REASONING_MODEL="${REASONING_MODEL:-$SERVED}"; ACTIVE="$REASONING_MODEL"
else
  export BASELINE_MODEL="${BASELINE_MODEL:-$SERVED}"; ACTIVE="$BASELINE_MODEL"
fi

# Append _thinking only for thinking, so instruct EXP_NAME is unchanged and the
# already-running instruct pods stay resume-safe.
SUFFIX=""; [ "$MODE" = thinking ] && SUFFIX="_thinking"
export EXP_NAME="MA-vuln-four-zero_shot-constrained_${MODELTAG}${SUFFIX}"

echo "================ Option B: ${CFG} / ${MODE} ================"
echo "  model    : ${ACTIVE}  (ENABLE_REASONING=${ENABLE_REASONING})"
echo "  endpoint : ${ENDPOINT}"
echo "  dataset  : ${VULN_DATASET}"
echo "  results  : ${RESULTS_DIR}"
echo "  exp_name : ${EXP_NAME}  (resumable)"
echo "==========================================================="

cd "${PROJECT_ROOT}"
python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot --constrained
