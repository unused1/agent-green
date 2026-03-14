#!/bin/bash
# Auto-resume wrapper for DA Vuln experiments
# Usage: ./auto_resume_da_vuln.sh <prompt_type> <thinking_mode>
# Example: ./auto_resume_da_vuln.sh few_shot true
#          ./auto_resume_da_vuln.sh zero_shot false

PROMPT_TYPE=${1:-few_shot}
ENABLE_THINKING=${2:-true}

cd /workspace/agent-green
set -a && source .env && set +a
export MODEL_FAMILY=nemotron
export ENABLE_REASONING=$ENABLE_THINKING

echo "Starting DA Vuln experiment with:"
echo "  Prompt type: $PROMPT_TYPE"
echo "  Thinking mode: $ENABLE_REASONING"
echo ""

while true; do
    # Pipe "2" to auto-select "skip next sample" on resume prompt
    echo "2" | python src/dual_agent_vuln.py --prompt_type $PROMPT_TYPE
    EXIT_CODE=$?

    # Check sample count for robust completion detection
    # Use most recent results file to avoid counting old experiments
    RESULTS_FILE=$(ls -t results/DA-vuln-*_detailed_results.jsonl 2>/dev/null | head -1)
    if [ -n "$RESULTS_FILE" ]; then
        SAMPLES=$(wc -l < "$RESULTS_FILE" | tr -d ' ')
    else
        SAMPLES=0
    fi

    # ONLY use sample count for completion detection (exit code 0 is unreliable)
    if [ "$SAMPLES" -ge 380 ]; then
        echo "========================================"
        echo "Experiment completed! ($SAMPLES/386 samples)"
        echo "========================================"
        break
    fi

    echo "Run ended (exit code: $EXIT_CODE). $SAMPLES/386 samples completed."
    echo "Restarting in 5 seconds..."
    sleep 5
done
