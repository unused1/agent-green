#!/bin/bash

# Retry Failed Samples - Wrapper script for easy use
# Run from project root or inside Docker container

# Usage examples:
#   bash scripts/retry_failed.sh                           # Interactive: lists experiments and prompts
#   bash scripts/retry_failed.sh results/file.jsonl        # Retry specific file
#   bash scripts/retry_failed.sh results/file.jsonl timeout # Retry only timeouts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# If no arguments, show available experiments with errors
if [ $# -eq 0 ]; then
    echo "=== Experiments with Failed Samples ==="
    echo ""

    found_errors=false
    for file in results/*_detailed_results.jsonl; do
        if [ -f "$file" ]; then
            error_count=$(grep '"error":' "$file" 2>/dev/null | wc -l | tr -d ' ')
            if [ "$error_count" -gt 0 ] 2>/dev/null; then
                found_errors=true
                basename=$(basename "$file")
                echo "📁 $basename"
                echo "   Failed samples: $error_count"

                # Show error types
                echo "   Error types:"
                grep -o '"error": "[^"]*"' "$file" | sed 's/"error": "//;s/"$//' | sort | uniq -c | while read count type; do
                    echo "     - $type: $count"
                done
                echo ""
            fi
        fi
    done

    if [ "$found_errors" = false ]; then
        echo "✓ No failed samples found in any experiments"
        exit 0
    fi

    echo "=== Retry Failed Samples ==="
    echo ""
    read -p "Enter results filename (or full path, or 'q' to quit): " results_file

    if [ "$results_file" = "q" ]; then
        echo "Exiting"
        exit 0
    fi

    # If user provided just filename, prepend results/
    if [[ ! "$results_file" =~ ^results/ ]] && [[ ! "$results_file" =~ ^/ ]]; then
        results_file="results/$results_file"
    fi

    if [ ! -f "$results_file" ]; then
        echo "❌ File not found: $results_file"
        exit 1
    fi

    echo ""
    echo "Error type options:"
    echo "  1. All errors (default)"
    echo "  2. Timeout only"
    echo "  3. Skipped only"
    echo ""
    read -p "Select error type (1/2/3): " error_choice

    case $error_choice in
        2) error_type="timeout" ;;
        3) error_type="skipped" ;;
        *) error_type="all" ;;
    esac

else
    # Use provided arguments
    results_file="$1"
    error_type="${2:-all}"
fi

# Validate file exists
if [ ! -f "$results_file" ]; then
    echo "❌ Error: Results file not found: $results_file"
    exit 1
fi

# Run retry script
echo ""
echo "Running retry with:"
echo "  File: $results_file"
echo "  Error type: $error_type"
echo ""

python3 scripts/retry_failed_samples.py "$results_file" --error-type "$error_type"
