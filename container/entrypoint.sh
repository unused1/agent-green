#!/bin/bash
# Agent-Green Replication Container — Entrypoint
# Starts vLLM server, waits for readiness, dispatches to the appropriate runner,
# and supports deterministic exp_name for auto-resume on re-invocation.
set -euo pipefail

# === Required env vars ===
: "${DESIGN:?DESIGN required: NA | SA | DA | MA}"
: "${MODE:?MODE required: instruct | thinking}"
: "${MODEL:?MODEL required: qwen3-4b | qwen3-30b | nemotron-nano-8b | nemotron-super-49b}"
: "${PROMPTING:?PROMPTING required: zero | few}"

# === Optional env vars ===
SEED="${SEED:-1}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-65536}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.9}"
SMOKE_TEST="${SMOKE_TEST:-0}"
HF_TOKEN="${HF_TOKEN:-}"
VLLM_READY_TIMEOUT="${VLLM_READY_TIMEOUT:-900}"

# === MODEL → HF identifier + vLLM args + tensor-parallel size ===
case "$MODEL" in
  qwen3-4b)
    HF_INSTRUCT="Qwen/Qwen3-4B-Instruct-2507"
    HF_THINKING="Qwen/Qwen3-4B-Thinking-2507"
    VLLM_EXTRA="--enable-auto-tool-choice --tool-call-parser hermes"
    TP=1
    MODEL_FAMILY_VAL=""
    ;;
  qwen3-30b)
    HF_INSTRUCT="Qwen/Qwen3-30B-A3B-Instruct-2507"
    HF_THINKING="Qwen/Qwen3-30B-A3B-Thinking-2507"
    VLLM_EXTRA="--enable-auto-tool-choice --tool-call-parser hermes"
    TP=1
    MODEL_FAMILY_VAL=""
    ;;
  nemotron-nano-8b)
    # Nemotron uses the same checkpoint for instruct/thinking; mode toggled via prompt prefix
    HF_INSTRUCT="nvidia/Llama-3.1-Nemotron-Nano-8B-v1"
    HF_THINKING="nvidia/Llama-3.1-Nemotron-Nano-8B-v1"
    VLLM_EXTRA="--enable-auto-tool-choice --tool-call-parser hermes --trust-remote-code"
    TP=1
    MODEL_FAMILY_VAL="nemotron"
    ;;
  nemotron-super-49b)
    HF_INSTRUCT="nvidia/Llama-3_3-Nemotron-Super-49B-v1_5"
    HF_THINKING="nvidia/Llama-3_3-Nemotron-Super-49B-v1_5"
    VLLM_EXTRA="--enable-auto-tool-choice --tool-call-parser hermes --trust-remote-code"
    TP=2
    MODEL_FAMILY_VAL="nemotron"
    ;;
  *)
    echo "[ERROR] Unknown MODEL: $MODEL" >&2
    exit 1
    ;;
esac

# === MODE → reasoning toggle + model selection ===
case "$MODE" in
  instruct)
    ENABLE_REASONING_VAL="false"
    HF_MODEL="$HF_INSTRUCT"
    ;;
  thinking)
    ENABLE_REASONING_VAL="true"
    HF_MODEL="$HF_THINKING"
    ;;
  *)
    echo "[ERROR] Unknown MODE: $MODE" >&2
    exit 1
    ;;
esac

# === PROMPTING → runner arguments ===
case "$PROMPTING" in
  zero) PROMPT_TYPE="zero_shot"; SA_POS_ARG="SA-zero" ;;
  few)  PROMPT_TYPE="few_shot";  SA_POS_ARG="SA-few"  ;;
  *)
    echo "[ERROR] Unknown PROMPTING: $PROMPTING" >&2
    exit 1
    ;;
esac

# === Smoke-test swap (10 samples instead of 870) ===
if [[ "$SMOKE_TEST" == "1" ]]; then
  VULN_DATASET_PATH=/workspace/vuln_database/VulTrial_10_samples_test.jsonl
  echo "[SMOKE] Using 10-sample dataset for pipeline validation"
else
  VULN_DATASET_PATH=/workspace/vuln_database/VulTrial_870_samples_balanced.jsonl
fi

# === Deterministic experiment name (enables auto-resume on re-invocation) ===
# Format: <DESIGN>-vuln-<prompt_type>_<model_slug>_seed<N>[_smoke]
MODEL_SLUG=$(echo "$HF_MODEL" | tr '/:' '__')
EXP_NAME_VAL="${DESIGN}-vuln-${PROMPT_TYPE}_${MODEL_SLUG}_seed${SEED}"
if [[ "$SMOKE_TEST" == "1" ]]; then
  EXP_NAME_VAL="${EXP_NAME_VAL}_smoke"
fi

# === Output directory (mount this from host via -v /host/path:/workspace/results) ===
RESULTS_BASE="${RESULTS_DIR:-/workspace/results}"
CONFIG_SUBDIR="run${SEED}/${DESIGN}_${MODE}_${MODEL}_${PROMPTING}"
[[ "$SMOKE_TEST" == "1" ]] && CONFIG_SUBDIR="${CONFIG_SUBDIR}_smoke"
FULL_RESULTS_DIR="${RESULTS_BASE}/${CONFIG_SUBDIR}"
mkdir -p "$FULL_RESULTS_DIR"

# === Export env vars consumed by src/config*.py and patched runners ===
# USE_RUNPOD=true selects the vLLM OpenAI-compatible backend (vs local Ollama default in config.py)
export USE_RUNPOD=true
export MODEL_FAMILY="$MODEL_FAMILY_VAL"
export ENABLE_REASONING="$ENABLE_REASONING_VAL"
export VULN_DATASET="$VULN_DATASET_PATH"
export RESULTS_DIR="$FULL_RESULTS_DIR"
export REASONING_ENDPOINT="http://localhost:8000/v1"
export BASELINE_ENDPOINT="http://localhost:8000/v1"
export REASONING_MODEL="$HF_MODEL"
export BASELINE_MODEL="$HF_MODEL"
export LLM_MODEL="$HF_MODEL"
export EXP_NAME="$EXP_NAME_VAL"
export HF_HUB_ENABLE_HF_TRANSFER=1
[[ -n "$HF_TOKEN" ]] && export HF_TOKEN

# === Log configuration ===
cat <<EOF
========================================
  AGENT-GREEN REPLICATION CONTAINER v1.0
========================================
DESIGN        = $DESIGN
MODE          = $MODE  (ENABLE_REASONING=$ENABLE_REASONING_VAL)
MODEL         = $MODEL  -> $HF_MODEL
PROMPTING     = $PROMPTING  ($PROMPT_TYPE)
SEED          = $SEED
SMOKE_TEST    = $SMOKE_TEST
DATASET       = $VULN_DATASET_PATH
RESULTS_DIR   = $FULL_RESULTS_DIR
EXP_NAME      = $EXP_NAME_VAL
TP_SIZE       = $TP
MAX_MODEL_LEN = $MAX_MODEL_LEN
GPU_MEM_UTIL  = $GPU_MEM_UTIL
MODEL_FAMILY  = $MODEL_FAMILY_VAL
========================================
EOF

# === Start vLLM server in background ===
echo "[vLLM] Starting server for $HF_MODEL (TP=$TP)..."
nohup python -m vllm.entrypoints.openai.api_server \
  --model "$HF_MODEL" \
  --served-model-name "$HF_MODEL" \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEM_UTIL" \
  --tensor-parallel-size "$TP" \
  $VLLM_EXTRA \
  > /workspace/vllm.log 2>&1 &
VLLM_PID=$!

# Ensure vLLM is shut down on exit (clean or otherwise)
trap 'echo "[Cleanup] Stopping vLLM (PID $VLLM_PID)..."; kill $VLLM_PID 2>/dev/null || true; wait $VLLM_PID 2>/dev/null || true' EXIT

# === Wait for vLLM readiness ===
echo "[vLLM] Waiting for server (timeout ${VLLM_READY_TIMEOUT}s)..."
WAIT_START=$(date +%s)
until curl -sf http://localhost:8000/v1/models > /dev/null 2>&1; do
  if ! kill -0 $VLLM_PID 2>/dev/null; then
    echo "[ERROR] vLLM process died during startup. Last 100 lines of log:" >&2
    tail -100 /workspace/vllm.log >&2
    exit 1
  fi
  NOW=$(date +%s)
  ELAPSED=$((NOW - WAIT_START))
  if [[ $ELAPSED -gt $VLLM_READY_TIMEOUT ]]; then
    echo "[ERROR] vLLM startup timeout (${VLLM_READY_TIMEOUT}s). Last 100 lines of log:" >&2
    tail -100 /workspace/vllm.log >&2
    exit 1
  fi
  sleep 5
done
WAIT_END=$(date +%s)
echo "[vLLM] Server ready after $((WAIT_END - WAIT_START))s"

# === Dispatch to the appropriate runner ===
cd /workspace
echo "[Runner] Starting $DESIGN runner..."
case "$DESIGN" in
  NA)
    python src/no_agent_vuln_detection.py --prompt_type "$PROMPT_TYPE"
    ;;
  SA)
    python src/single_agent_vuln_detection.py "$SA_POS_ARG"
    ;;
  DA)
    python src/dual_agent_vuln.py --prompt_type "$PROMPT_TYPE"
    ;;
  MA)
    python src/multi_agent_vuln_detection_four_agents.py --prompt_type "$PROMPT_TYPE"
    ;;
  *)
    echo "[ERROR] Unknown DESIGN: $DESIGN" >&2
    exit 1
    ;;
esac

echo "[Done] Experiment complete: $EXP_NAME_VAL"
echo "[Done] Results written to: $FULL_RESULTS_DIR"
