#!/bin/bash
# Upload all code generation results to Pod 1 for re-evaluation
# Usage: ./scripts/upload_code_results_for_reeval.sh

POD1_HOST="root@213.181.105.211"
POD1_PORT="13695"
REMOTE_DIR="/workspace/agent-green/results_reeval"

echo "=== Uploading Code Results for Re-evaluation ==="
echo "Target: Pod 1 ($POD1_HOST:$POD1_PORT)"
echo ""

# Create remote directory structure
echo "Creating remote directory structure..."
ssh -p $POD1_PORT $POD1_HOST "mkdir -p $REMOTE_DIR/qwen_rq2 $REMOTE_DIR/nemotron"

# Upload Qwen RQ2 results (16 files)
echo ""
echo "Uploading Qwen RQ2 code results..."
find results/runpod_rq2_pod* -name "*code*detailed_results.jsonl" 2>/dev/null | while read f; do
    filename=$(basename "$f")
    echo "  -> $filename"
    scp -P $POD1_PORT "$f" $POD1_HOST:$REMOTE_DIR/qwen_rq2/
done

# Upload Nemotron results (19 files)
echo ""
echo "Uploading Nemotron code results..."
find results/rq2_cross_architecture -name "*code*detailed_results.jsonl" 2>/dev/null | while read f; do
    filename=$(basename "$f")
    echo "  -> $filename"
    scp -P $POD1_PORT "$f" $POD1_HOST:$REMOTE_DIR/nemotron/
done

echo ""
echo "=== Upload Complete ==="
echo ""
echo "Files uploaded to: $REMOTE_DIR"
echo ""
echo "To run re-evaluation on Pod 1:"
echo "  ssh -p $POD1_PORT $POD1_HOST"
echo "  cd /workspace/agent-green"
echo "  for f in results_reeval/**/*.jsonl; do python src/evaluate_code_generation.py \"\$f\"; done"
