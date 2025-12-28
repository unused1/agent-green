#!/bin/bash
# Auto-resume wrapper for DA Code Generation experiments
# Usage: ./auto_resume_da_code.sh <prompt_type> <thinking_mode>
# Example: ./auto_resume_da_code.sh few_shot true
#          ./auto_resume_da_code.sh zero_shot false

PROMPT_TYPE=${1:-few_shot}
ENABLE_THINKING=${2:-true}

cd /workspace/agent-green
set -a && source .env && set +a
export MODEL_FAMILY=nemotron
export ENABLE_REASONING=$ENABLE_THINKING

echo "Starting DA Code Generation experiment with:"
echo "  Prompt type: $PROMPT_TYPE"
echo "  Thinking mode: $ENABLE_REASONING"
echo ""

while true; do
    # Pipe "2" to auto-select "skip next sample" on resume prompt
    echo "2" | python src/dual_agent_code_generation.py --prompt_type $PROMPT_TYPE
    EXIT_CODE=$?

    # Check sample count for robust completion detection
    SAMPLES=$(wc -l < results/DA-*_detailed_results.jsonl 2>/dev/null | tr -d ' ' || echo "0")

    if [ $EXIT_CODE -eq 0 ] || [ "$SAMPLES" -ge 160 ]; then
        echo "========================================"
        echo "Experiment completed! ($SAMPLES/164 samples)"
        echo "========================================"
        break
    fi
    echo "Error encountered (exit code: $EXIT_CODE). $SAMPLES/164 samples completed."
    echo "Restarting in 5 seconds..."
    sleep 5
done
