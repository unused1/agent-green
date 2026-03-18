#!/bin/bash
# ============================================================================
# VulTrial-870 Expansion — Batch 2: SA Thinking (4 models × 2 shots)
# ============================================================================
#
# Batch 2 scope: SA thinking × {zero-shot, few-shot} × 4 models = 8 configs
# Each config runs 384 incremental samples (192 vuln + 192 safe).
#
# Pod assignments:
#   Pod 1: Qwen3-4B-Thinking          (1× H100)  — SA-zero, SA-few
#   Pod 2: Qwen3-30B-A3B-Thinking     (1× H100)  — SA-zero, SA-few
#   Pod 3: Nemotron-Nano-8B thinking   (1× H100)  — SA-zero, SA-few
#   Pod 4: Nemotron-Super-49B thinking (2× H100)  — SA-zero, SA-few
#
# Key difference from Batch 1: ENABLE_REASONING=true
#   - Qwen models: requires different vLLM model (Thinking variant)
#   - Nemotron models: same vLLM model, toggle via system prompt
#     (can run Batch 2 right after Batch 1 without restarting vLLM)
#
# Features:
#   - Auto-resume: on crash/timeout, restarts and resumes from checkpoint
#   - Completion detection: checks JSONL line count (≥380 = done)
#   - Pre-run check: skips configs that are already complete
#
# Usage (run ON the RunPod pod after vLLM is serving):
#   bash scripts/run_vuln_870_batch2.sh [pod1|pod2|pod3|pod4]
#
# Prerequisites:
#   - vLLM server running with the correct model
#   - vuln_database/VulTrial_384_incremental.jsonl uploaded
# ============================================================================

# Do NOT set -e — the auto-resume loop handles failures

POD="${1:?Usage: bash scripts/run_vuln_870_batch2.sh [pod1|pod2|pod3|pod4]}"

# Get project root (relative to this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Common environment (all pods)
# ---------------------------------------------------------------------------
export PROJECT_ROOT="$PROJECT_ROOT"
export VULN_DATASET="$PROJECT_ROOT/vuln_database/VulTrial_384_incremental.jsonl"
export ENABLE_REASONING=true    # thinking mode
export USE_RUNPOD=true
export RESULTS_DIR="$PROJECT_ROOT/results"
export TEMPERATURE=0.0
export BASELINE_ENDPOINT="http://localhost:8000/v1"
export BASELINE_API_KEY="dummy-key"
export REASONING_ENDPOINT="http://localhost:8000/v1"
export REASONING_API_KEY="dummy-key"

# Source .env if it exists (user overrides take precedence)
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Sourcing .env..."
    set -a && source "$PROJECT_ROOT/.env" && set +a
fi

# Override critical vars that the batch script controls
# (re-export after .env sourcing to ensure correctness)
export VULN_DATASET="$PROJECT_ROOT/vuln_database/VulTrial_384_incremental.jsonl"
export ENABLE_REASONING=true
export USE_RUNPOD=true

# Target sample count (384 samples, use 380 as threshold to handle edge cases)
TARGET_SAMPLES=384
COMPLETION_THRESHOLD=380

echo "============================================================"
echo "VulTrial-870 Expansion — Batch 2: SA Thinking"
echo "============================================================"
echo ""
echo "Pod:              $POD"
echo "Dataset:          $VULN_DATASET"
echo "Reasoning:        $ENABLE_REASONING (thinking)"
echo "Results dir:      $RESULTS_DIR"
echo "Project root:     $PROJECT_ROOT"
echo "Python:           $(which python3)"
echo ""

# Verify dataset exists
if [ ! -f "$VULN_DATASET" ]; then
    echo "ERROR: Dataset not found: $VULN_DATASET"
    echo "Upload VulTrial_384_incremental.jsonl to the pod first."
    exit 1
fi

SAMPLE_COUNT=$(wc -l < "$VULN_DATASET" | tr -d ' ')
echo "Dataset samples:  $SAMPLE_COUNT"
echo ""

# ---------------------------------------------------------------------------
# Auto-resume wrapper: runs the experiment in a loop until completion
# ---------------------------------------------------------------------------
run_sa_with_resume() {
    local design=$1   # SA-zero or SA-few
    local exp_num=$2
    local exp_total=$3

    echo "============================================================"
    echo "[$exp_num/$exp_total] $design (thinking mode) — with auto-resume"
    echo "============================================================"

    # Check if already complete BEFORE running (skip entirely if done)
    # Note: single_agent_vuln_detection.py uses DESIGN.capitalize() for filenames,
    # so "SA-zero" becomes "Sa-zero" in the filename. Use case-insensitive grep.
    RESULTS_FILE=$(ls -t "$RESULTS_DIR"/*_detailed_results.jsonl 2>/dev/null | grep -i "${design}" | head -1)
    if [ -n "$RESULTS_FILE" ]; then
        COMPLETED=$(wc -l < "$RESULTS_FILE" | tr -d ' ')
        if [ "$COMPLETED" -ge "$COMPLETION_THRESHOLD" ]; then
            echo ""
            echo "  ALREADY COMPLETE ($COMPLETED/$TARGET_SAMPLES samples)"
            echo "  Results: $RESULTS_FILE"
            echo "  Skipping to next config."
            echo ""
            return 0
        fi
    fi

    while true; do
        echo ""
        echo "  Start: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "  Running: python3 src/single_agent_vuln_detection.py $design"
        echo ""

        python3 src/single_agent_vuln_detection.py "$design"
        EXIT_CODE=$?

        echo ""
        echo "  End:   $(date '+%Y-%m-%d %H:%M:%S')"
        echo "  Exit code: $EXIT_CODE"

        # Check completion
        RESULTS_FILE=$(ls -t "$RESULTS_DIR"/*_detailed_results.jsonl 2>/dev/null | grep -i "${design}" | head -1)
        if [ -n "$RESULTS_FILE" ]; then
            COMPLETED=$(wc -l < "$RESULTS_FILE" | tr -d ' ')
        else
            COMPLETED=0
        fi

        echo "  Completed samples: $COMPLETED / $TARGET_SAMPLES"

        if [ "$COMPLETED" -ge "$COMPLETION_THRESHOLD" ]; then
            echo ""
            echo "  COMPLETED ($COMPLETED/$TARGET_SAMPLES samples)"
            echo "  Results: $RESULTS_FILE"
            break
        fi

        echo ""
        echo "  Not yet complete. Auto-resuming in 5 seconds..."
        echo "  (The script will resume from sample $COMPLETED)"
        sleep 5
    done
    echo ""
}

# ---------------------------------------------------------------------------
# Pod-specific configuration and execution
# ---------------------------------------------------------------------------
case "$POD" in
    "pod1")
        # Qwen3-4B-Thinking (requires vLLM with Thinking model)
        unset MODEL_FAMILY
        export REASONING_MODEL="Qwen/Qwen3-4B-Thinking-2507"
        echo "Model:            Qwen3-4B-Thinking"
        echo "REASONING_MODEL:  $REASONING_MODEL"
        echo ""
        echo "NOTE: vLLM must be serving Qwen/Qwen3-4B-Thinking-2507"
        echo ""
        run_sa_with_resume "SA-zero" 1 2
        run_sa_with_resume "SA-few"  2 2
        ;;

    "pod2")
        # Qwen3-30B-A3B-Thinking (requires vLLM with Thinking model)
        unset MODEL_FAMILY
        export REASONING_MODEL="Qwen/Qwen3-30B-A3B-Thinking-2507"
        echo "Model:            Qwen3-30B-A3B-Thinking"
        echo "REASONING_MODEL:  $REASONING_MODEL"
        echo ""
        echo "NOTE: vLLM must be serving Qwen/Qwen3-30B-A3B-Thinking-2507"
        echo ""
        run_sa_with_resume "SA-zero" 1 2
        run_sa_with_resume "SA-few"  2 2
        ;;

    "pod3")
        # Nemotron-Nano-8B thinking (same model, toggle via system prompt)
        export MODEL_FAMILY=nemotron
        export REASONING_MODEL="nvidia/Llama-3.1-Nemotron-Nano-8B-v1"
        echo "Model:            Nemotron-Nano-8B (thinking)"
        echo "MODEL_FAMILY:     $MODEL_FAMILY"
        echo "REASONING_MODEL:  $REASONING_MODEL"
        echo ""
        echo "NOTE: Same vLLM server as instruct — thinking toggled via system prompt"
        echo ""
        run_sa_with_resume "SA-zero" 1 2
        run_sa_with_resume "SA-few"  2 2
        ;;

    "pod4")
        # Nemotron-Super-49B thinking (same model, toggle via system prompt)
        export MODEL_FAMILY=nemotron
        export REASONING_MODEL="nvidia/Llama-3_3-Nemotron-Super-49B-v1_5"
        echo "Model:            Nemotron-Super-49B (thinking)"
        echo "MODEL_FAMILY:     $MODEL_FAMILY"
        echo "REASONING_MODEL:  $REASONING_MODEL"
        echo ""
        echo "NOTE: Same vLLM server as instruct — thinking toggled via system prompt"
        echo ""
        run_sa_with_resume "SA-zero" 1 2
        run_sa_with_resume "SA-few"  2 2
        ;;

    *)
        echo "ERROR: Unknown pod '$POD'"
        echo "Usage: bash scripts/run_vuln_870_batch2.sh [pod1|pod2|pod3|pod4]"
        exit 1
        ;;
esac

echo "============================================================"
echo "Batch 2 complete for $POD"
echo "============================================================"
echo ""
echo "Results in: $RESULTS_DIR/"
echo ""
echo "Next steps:"
echo "  1. Download results to local machine"
echo "  2. Place in results/runpod_870_batch2_raw/"
echo "  3. Run: python scripts/merge_vuln_870.py"
echo ""
