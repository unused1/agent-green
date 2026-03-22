#!/bin/bash
# ============================================================================
# VulTrial-870 Expansion — Batch 7: NA Instruct (4 models × 2 shots)
# ============================================================================
#
# Batch 7 scope: NA instruct × {zero-shot, few-shot} × 4 models = 8 configs
# Each config runs 384 incremental samples (192 vuln + 192 safe).
# NA = No Agent (direct LLM call without AutoGen framework)
#
# Pod assignments:
#   Pod 1: Qwen3-4B-Instruct         (1× H100)  — NA-zero, NA-few
#   Pod 2: Qwen3-30B-A3B-Instruct    (1× H100)  — NA-zero, NA-few
#   Pod 3: Nemotron-Nano-8B instruct  (1× H100)  — NA-zero, NA-few
#   Pod 4: Nemotron-Super-49B instruct(2× H100)  — NA-zero, NA-few
#
# Features:
#   - Auto-resume with skip: restarts on crash, resumes from checkpoint
#   - Completion detection: checks JSONL line count (≥380 = done)
#   - Pre-run check: skips configs that are already complete
#
# Usage (run ON the RunPod pod after vLLM is serving):
#   bash scripts/run_vuln_870_batch7.sh [pod1|pod2|pod3|pod4]
#
# Prerequisites:
#   - vLLM server running with the correct model
#   - vuln_database/VulTrial_384_incremental.jsonl uploaded
# ============================================================================

# Do NOT set -e — the auto-resume loop handles failures

POD="${1:?Usage: bash scripts/run_vuln_870_batch7.sh [pod1|pod2|pod3|pod4]}"

# Get project root (relative to this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Common environment (all pods)
# ---------------------------------------------------------------------------
export PROJECT_ROOT="$PROJECT_ROOT"
export VULN_DATASET="$PROJECT_ROOT/vuln_database/VulTrial_384_incremental.jsonl"
export ENABLE_REASONING=false   # instruct mode
export USE_RUNPOD=true
export RESULTS_DIR="$PROJECT_ROOT/results"
export TEMPERATURE=0.0
export BASELINE_ENDPOINT="http://localhost:8000/v1"
export BASELINE_API_KEY="dummy-key"

# Source .env if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Sourcing .env..."
    set -a && source "$PROJECT_ROOT/.env" && set +a
fi

# Override critical vars
export VULN_DATASET="$PROJECT_ROOT/vuln_database/VulTrial_384_incremental.jsonl"
export ENABLE_REASONING=false
export USE_RUNPOD=true

# Target sample count
TARGET_SAMPLES=384
COMPLETION_THRESHOLD=380

echo "============================================================"
echo "VulTrial-870 Expansion — Batch 7: NA Instruct"
echo "============================================================"
echo ""
echo "Pod:              $POD"
echo "Dataset:          $VULN_DATASET"
echo "Reasoning:        $ENABLE_REASONING (instruct)"
echo "Results dir:      $RESULTS_DIR"
echo "Project root:     $PROJECT_ROOT"
echo "Python:           $(which python3)"
echo ""

# Verify dataset exists
if [ ! -f "$VULN_DATASET" ]; then
    echo "ERROR: Dataset not found: $VULN_DATASET"
    exit 1
fi

SAMPLE_COUNT=$(wc -l < "$VULN_DATASET" | tr -d ' ')
echo "Dataset samples:  $SAMPLE_COUNT"
echo ""

# ---------------------------------------------------------------------------
# Auto-resume wrapper for NA experiments
# ---------------------------------------------------------------------------
run_na_with_resume() {
    local prompt_type=$1   # zero_shot or few_shot
    local exp_num=$2
    local exp_total=$3

    echo "============================================================"
    echo "[$exp_num/$exp_total] NA $prompt_type (instruct mode) — with auto-resume"
    echo "============================================================"

    # Check if already complete BEFORE running
    RESULTS_FILE=$(ls -t "$RESULTS_DIR"/*_detailed_results.jsonl 2>/dev/null | grep -i "NA-vuln.*${prompt_type}" | head -1)
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
        echo "  Running: python3 src/no_agent_vuln_detection.py --prompt_type $prompt_type"
        echo ""

        python3 src/no_agent_vuln_detection.py --prompt_type "$prompt_type"
        EXIT_CODE=$?

        echo ""
        echo "  End:   $(date '+%Y-%m-%d %H:%M:%S')"
        echo "  Exit code: $EXIT_CODE"

        # Check completion
        RESULTS_FILE=$(ls -t "$RESULTS_DIR"/*_detailed_results.jsonl 2>/dev/null | grep -i "NA-vuln.*${prompt_type}" | head -1)
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
        # Qwen3-4B-Instruct
        unset MODEL_FAMILY
        export BASELINE_MODEL="Qwen/Qwen3-4B-Instruct-2507"
        echo "Model:            Qwen3-4B-Instruct"
        echo "BASELINE_MODEL:   $BASELINE_MODEL"
        echo ""
        run_na_with_resume "zero_shot" 1 2
        run_na_with_resume "few_shot"  2 2
        ;;

    "pod2")
        # Qwen3-30B-A3B-Instruct
        unset MODEL_FAMILY
        export BASELINE_MODEL="Qwen/Qwen3-30B-A3B-Instruct-2507"
        echo "Model:            Qwen3-30B-A3B-Instruct"
        echo "BASELINE_MODEL:   $BASELINE_MODEL"
        echo ""
        run_na_with_resume "zero_shot" 1 2
        run_na_with_resume "few_shot"  2 2
        ;;

    "pod3")
        # Nemotron-Nano-8B instruct
        export MODEL_FAMILY=nemotron
        export BASELINE_MODEL="nvidia/Llama-3.1-Nemotron-Nano-8B-v1"
        echo "Model:            Nemotron-Nano-8B (instruct)"
        echo "MODEL_FAMILY:     $MODEL_FAMILY"
        echo "BASELINE_MODEL:   $BASELINE_MODEL"
        echo ""
        run_na_with_resume "zero_shot" 1 2
        run_na_with_resume "few_shot"  2 2
        ;;

    "pod4")
        # Nemotron-Super-49B instruct (2× H100)
        export MODEL_FAMILY=nemotron
        export BASELINE_MODEL="nvidia/Llama-3_3-Nemotron-Super-49B-v1_5"
        echo "Model:            Nemotron-Super-49B (instruct)"
        echo "MODEL_FAMILY:     $MODEL_FAMILY"
        echo "BASELINE_MODEL:   $BASELINE_MODEL"
        echo ""
        run_na_with_resume "zero_shot" 1 2
        run_na_with_resume "few_shot"  2 2
        ;;

    *)
        echo "ERROR: Unknown pod '$POD'"
        echo "Usage: bash scripts/run_vuln_870_batch7.sh [pod1|pod2|pod3|pod4]"
        exit 1
        ;;
esac

echo "============================================================"
echo "Batch 7 complete for $POD"
echo "============================================================"
echo ""
echo "Results in: $RESULTS_DIR/"
echo ""
