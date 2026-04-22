#!/bin/bash
# Agent-Green Replication Container — Entrypoint
# Starts the inference backend (vLLM or ollama), waits for readiness, dispatches
# to the appropriate runner, and supports deterministic exp_name for auto-resume.
set -euo pipefail

# When container runs with --user <host-UID>, the UID may not have an /etc/passwd
# entry, breaking pwd.getpwuid() calls by torch/codecarbon/etc. Setting USER + HOME
# makes getpass.getuser() pick them up via its env-var fallback path.
export USER="${USER:-replication}"
export HOME="${HOME:-/tmp}"

# Cache dirs are set via Dockerfile ENV (defaulting to /tmp/...) so they're user-writable
# when the container runs with --user <host-UID>. Team members can override at runtime
# with -e HF_HOME=/mnt/persistent/... for persistent caching across invocations.
mkdir -p "$HF_HOME" "$XDG_CACHE_HOME" "$OLLAMA_MODELS"

# === Required env vars ===
: "${DESIGN:?DESIGN required: NA | SA | DA | MA}"
: "${MODE:?MODE required: instruct | thinking}"
: "${MODEL:?MODEL required: qwen3-4b | qwen3-30b | nemotron-nano-8b | nemotron-super-49b}"
: "${PROMPTING:?PROMPTING required: zero | few}"

# === Optional env vars ===
SEED="${SEED:-1}"
SMOKE_TEST="${SMOKE_TEST:-0}"
HF_TOKEN="${HF_TOKEN:-}"
INFERENCE_BACKEND="${INFERENCE_BACKEND:-vllm}"

# vLLM-specific
MAX_MODEL_LEN="${MAX_MODEL_LEN:-65536}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.9}"
VLLM_DTYPE="${VLLM_DTYPE:-auto}"
VLLM_READY_TIMEOUT="${VLLM_READY_TIMEOUT:-900}"

# Ollama-specific
OLLAMA_MODEL="${OLLAMA_MODEL:-}"
OLLAMA_NUM_CTX="${OLLAMA_NUM_CTX:-65536}"
OLLAMA_READY_TIMEOUT="${OLLAMA_READY_TIMEOUT:-1800}"

# === Validate INFERENCE_BACKEND ===
case "$INFERENCE_BACKEND" in
  vllm|ollama) ;;
  *)
    echo "[ERROR] Unknown INFERENCE_BACKEND: $INFERENCE_BACKEND (must be vllm or ollama)" >&2
    exit 1
    ;;
esac

# === Ollama extra validation ===
if [[ "$INFERENCE_BACKEND" == "ollama" && -z "$OLLAMA_MODEL" ]]; then
  echo "[ERROR] OLLAMA_MODEL required when INFERENCE_BACKEND=ollama (e.g., qwen3:4b, qwen3:4b-instruct-q8_0)" >&2
  exit 1
fi

# === MODEL → HF identifier + vLLM args + tensor-parallel size + model family ===
# MODEL is used for exp_name/results dir naming and selecting the right config module
# (config_nemotron for nemotron-* models, config for qwen3-*). For ollama, the actual
# served model is OLLAMA_MODEL; HF IDs here are only used for the vllm backend path.
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

# === MODE → reasoning toggle + HF model selection ===
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
# Format uses the served model's effective ID, so vllm/ollama runs land in different exp_names
if [[ "$INFERENCE_BACKEND" == "ollama" ]]; then
  SERVED_MODEL="$OLLAMA_MODEL"
else
  SERVED_MODEL="$HF_MODEL"
fi
MODEL_SLUG=$(echo "$SERVED_MODEL" | tr '/:' '__')
EXP_NAME_VAL="${DESIGN}-vuln-${PROMPT_TYPE}_${MODEL_SLUG}_seed${SEED}"
[[ "$SMOKE_TEST" == "1" ]] && EXP_NAME_VAL="${EXP_NAME_VAL}_smoke"

# === Output directory ===
RESULTS_BASE="${RESULTS_DIR:-/workspace/results}"
CONFIG_SUBDIR="run${SEED}/${INFERENCE_BACKEND}_${DESIGN}_${MODE}_${MODEL}_${PROMPTING}"
[[ "$SMOKE_TEST" == "1" ]] && CONFIG_SUBDIR="${CONFIG_SUBDIR}_smoke"
FULL_RESULTS_DIR="${RESULTS_BASE}/${CONFIG_SUBDIR}"
mkdir -p "$FULL_RESULTS_DIR"

# === Export env vars consumed by src/config*.py and patched runners ===
export MODEL_FAMILY="$MODEL_FAMILY_VAL"
export ENABLE_REASONING="$ENABLE_REASONING_VAL"
export VULN_DATASET="$VULN_DATASET_PATH"
export RESULTS_DIR="$FULL_RESULTS_DIR"
export EXP_NAME="$EXP_NAME_VAL"
export HF_HUB_ENABLE_HF_TRANSFER=1
[[ -n "$HF_TOKEN" ]] && export HF_TOKEN

if [[ "$INFERENCE_BACKEND" == "vllm" ]]; then
  # vLLM + OpenAI-compatible API at localhost:8000
  export USE_RUNPOD=true
  export LLM_SERVICE=openai
  export REASONING_ENDPOINT="http://localhost:8000/v1"
  export BASELINE_ENDPOINT="http://localhost:8000/v1"
  export REASONING_MODEL="$HF_MODEL"
  export BASELINE_MODEL="$HF_MODEL"
  export LLM_MODEL="$HF_MODEL"
else
  # Ollama at localhost:11434 (config.py Ollama path reads LLM_MODEL + LLM_API_BASE)
  export USE_RUNPOD=false
  export LLM_SERVICE=ollama
  export LLM_MODEL="$OLLAMA_MODEL"
  export LLM_API_BASE="http://localhost:11434"
  # config_nemotron.py reads REASONING_MODEL/BASELINE_MODEL when USE_RUNPOD path is used;
  # also set these for consistency in case any runner paths reference them.
  export REASONING_MODEL="$OLLAMA_MODEL"
  export BASELINE_MODEL="$OLLAMA_MODEL"
  export REASONING_ENDPOINT="http://localhost:11434"
  export BASELINE_ENDPOINT="http://localhost:11434"
fi

# === Log configuration ===
cat <<EOF
========================================
  AGENT-GREEN REPLICATION CONTAINER v1.1
========================================
INFERENCE_BACKEND = $INFERENCE_BACKEND
DESIGN            = $DESIGN
MODE              = $MODE  (ENABLE_REASONING=$ENABLE_REASONING_VAL)
MODEL             = $MODEL
  served as       = $SERVED_MODEL
PROMPTING         = $PROMPTING  ($PROMPT_TYPE)
SEED              = $SEED
SMOKE_TEST        = $SMOKE_TEST
DATASET           = $VULN_DATASET_PATH
RESULTS_DIR       = $FULL_RESULTS_DIR
EXP_NAME          = $EXP_NAME_VAL
MODEL_FAMILY      = $MODEL_FAMILY_VAL
EOF

if [[ "$INFERENCE_BACKEND" == "vllm" ]]; then
cat <<EOF
TP_SIZE           = $TP
MAX_MODEL_LEN     = $MAX_MODEL_LEN
GPU_MEM_UTIL      = $GPU_MEM_UTIL
VLLM_DTYPE        = $VLLM_DTYPE
EOF
else
cat <<EOF
OLLAMA_NUM_CTX    = $OLLAMA_NUM_CTX
EOF
fi
echo "========================================"

# === Start inference backend ===
if [[ "$INFERENCE_BACKEND" == "vllm" ]]; then
  echo "[vLLM] Starting server for $HF_MODEL (TP=$TP, dtype=$VLLM_DTYPE)..."
  nohup python -m vllm.entrypoints.openai.api_server \
    --model "$HF_MODEL" \
    --served-model-name "$HF_MODEL" \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype "$VLLM_DTYPE" \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization "$GPU_MEM_UTIL" \
    --tensor-parallel-size "$TP" \
    $VLLM_EXTRA \
    > "$FULL_RESULTS_DIR/vllm.log" 2>&1 &
  BACKEND_PID=$!
  HEALTH_URL="http://localhost:8000/v1/models"
  READY_TIMEOUT="$VLLM_READY_TIMEOUT"
  BACKEND_LOG="$FULL_RESULTS_DIR/vllm.log"
  BACKEND_LABEL=vLLM
else
  echo "[Ollama] Starting ollama server..."
  nohup ollama serve > "$FULL_RESULTS_DIR/ollama.log" 2>&1 &
  BACKEND_PID=$!
  HEALTH_URL="http://localhost:11434/api/tags"
  READY_TIMEOUT="$OLLAMA_READY_TIMEOUT"
  BACKEND_LOG="$FULL_RESULTS_DIR/ollama.log"
  BACKEND_LABEL=Ollama
fi

# Ensure backend is shut down on exit
trap 'echo "[Cleanup] Stopping $BACKEND_LABEL (PID $BACKEND_PID)..."; kill $BACKEND_PID 2>/dev/null || true; wait $BACKEND_PID 2>/dev/null || true' EXIT

# === Wait for backend readiness ===
echo "[$BACKEND_LABEL] Waiting for server (timeout ${READY_TIMEOUT}s)..."
WAIT_START=$(date +%s)
until curl -sf "$HEALTH_URL" > /dev/null 2>&1; do
  if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "[ERROR] $BACKEND_LABEL process died during startup. Last 100 lines of log:" >&2
    tail -100 "$BACKEND_LOG" >&2
    exit 1
  fi
  ELAPSED=$(( $(date +%s) - WAIT_START ))
  if [[ $ELAPSED -gt $READY_TIMEOUT ]]; then
    echo "[ERROR] $BACKEND_LABEL startup timeout (${READY_TIMEOUT}s). Last 100 lines of log:" >&2
    tail -100 "$BACKEND_LOG" >&2
    exit 1
  fi
  sleep 5
done
echo "[$BACKEND_LABEL] Server ready after $(( $(date +%s) - WAIT_START ))s"

# === Ollama: pull model on first run (cached in /root/.ollama across runs) ===
if [[ "$INFERENCE_BACKEND" == "ollama" ]]; then
  echo "[Ollama] Ensuring model $OLLAMA_MODEL is available (pull if missing)..."
  PULL_START=$(date +%s)
  ollama pull "$OLLAMA_MODEL"
  echo "[Ollama] Model ready after $(( $(date +%s) - PULL_START ))s"
fi

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
