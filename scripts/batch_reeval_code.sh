#!/bin/bash
# Batch re-evaluate all code generation results
# Run this on Pod 1 after uploading results
# Usage: ./scripts/batch_reeval_code.sh

cd /workspace/agent-green

REEVAL_DIR="results_reeval"
OUTPUT_LOG="$REEVAL_DIR/reeval_summary.txt"

echo "=== Batch Code Re-evaluation ===" | tee $OUTPUT_LOG
echo "Started: $(date)" | tee -a $OUTPUT_LOG
echo "" | tee -a $OUTPUT_LOG

# Count files
TOTAL=$(find $REEVAL_DIR -name "*.jsonl" | wc -l)
echo "Total files to evaluate: $TOTAL" | tee -a $OUTPUT_LOG
echo "" | tee -a $OUTPUT_LOG

COUNT=0
for f in $REEVAL_DIR/**/*.jsonl; do
    if [ -f "$f" ]; then
        COUNT=$((COUNT + 1))
        filename=$(basename "$f")
        echo "[$COUNT/$TOTAL] Evaluating: $filename" | tee -a $OUTPUT_LOG

        # Run evaluation and capture Pass@1
        result=$(python src/evaluate_code_generation.py "$f" 2>&1)
        pass_at_1=$(echo "$result" | grep -o "Pass@1: [0-9.]*" | head -1)

        if [ -n "$pass_at_1" ]; then
            echo "  -> $pass_at_1" | tee -a $OUTPUT_LOG
        else
            echo "  -> FAILED or no result" | tee -a $OUTPUT_LOG
        fi
        echo "" | tee -a $OUTPUT_LOG
    fi
done

echo "=== Re-evaluation Complete ===" | tee -a $OUTPUT_LOG
echo "Finished: $(date)" | tee -a $OUTPUT_LOG
echo ""
echo "Summary saved to: $OUTPUT_LOG"
