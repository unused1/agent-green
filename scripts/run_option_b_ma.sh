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
# $ENDPOINT (provision the pod as in previous runs). BASELINE_MODEL must match
# the server's --served-model-name.
#
# Usage:
#   bash scripts/run_option_b_ma.sh super49b
#   bash scripts/run_option_b_ma.sh qwen30b
set -euo pipefail

CFG="${1:-}"
export PROJECT_ROOT="${PROJECT_ROOT:-/workspace/agent-green}"
ENDPOINT="${ENDPOINT:-http://localhost:8000/v1}"

export USE_RUNPOD=true
export ENABLE_REASONING=false                 # instruct pilot (no thinking)
export ENABLE_CODECARBON=true                 # fresh, separate emissions
export VULN_DATASET="${PROJECT_ROOT}/vuln_database/VulTrial_870_samples_balanced.jsonl"
export RESULTS_DIR="${PROJECT_ROOT}/results/runpod_vuln_870_constrained"
export BASELINE_ENDPOINT="$ENDPOINT"
export REASONING_ENDPOINT="$ENDPOINT"
export BASELINE_API_KEY="${BASELINE_API_KEY:-dummy-key}"
export REASONING_API_KEY="${REASONING_API_KEY:-dummy-key}"

case "$CFG" in
  super49b)
    export MODEL_FAMILY=nemotron
    # Must match the vLLM --served-model-name (see RunPod_Nemotron_49B_Setup_Guide.md).
    export BASELINE_MODEL="${BASELINE_MODEL:-nvidia/Llama-3_3-Nemotron-Super-49B-v1_5}"
    MODELTAG="nvidia-Llama-3_3-Nemotron-Super-49B-v1_5"
    ;;
  qwen30b)
    export MODEL_FAMILY=                       # empty -> Qwen3 (base config)
    export BASELINE_MODEL="${BASELINE_MODEL:-Qwen/Qwen3-30B-A3B-Instruct-2507}"
    MODELTAG="Qwen-Qwen3-30B-A3B-Instruct-2507"
    ;;
  *)
    echo "usage: $0 {super49b|qwen30b}" >&2; exit 1 ;;
esac

# Fixed EXP_NAME => resume on relaunch.
export EXP_NAME="MA-vuln-four-zero_shot-constrained_${MODELTAG}"

echo "================ Option B pilot: ${CFG} ================"
echo "  model    : ${BASELINE_MODEL}"
echo "  endpoint : ${ENDPOINT}"
echo "  dataset  : ${VULN_DATASET}"
echo "  results  : ${RESULTS_DIR}"
echo "  exp_name : ${EXP_NAME}  (resumable)"
echo "========================================================"

cd "${PROJECT_ROOT}"
python src/multi_agent_vuln_detection_four_agents.py --prompt_type zero_shot --constrained
