#!/bin/bash

# Download Mars Results - Interactive download with per-experiment prompts
# Run from project root: bash scripts/download_mars_results.sh

MARS_USER="huabengtan"
MARS_HOST="10.193.104.137"
MARS_PATH="/mnt/hdd2/huabengtan/agent-green/results"
LOCAL_DIR="./results/mars"

echo "=== Download Mars Results ==="
echo "Source: ${MARS_USER}@${MARS_HOST}:${MARS_PATH}"
echo "Destination: ${LOCAL_DIR}"
echo ""
echo "This script will prompt you for each experiment type."
echo "Press Ctrl+C at any time to cancel."
echo ""

# Create local directory
mkdir -p "${LOCAL_DIR}"

# Function to prompt for download
prompt_download() {
    local experiment_name=$1
    echo "----------------------------------------"
    read -p "Download ${experiment_name}? (y/n): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
    else
        echo "⊘ Skipping ${experiment_name}"
        return 1
    fi
}

# Function to download experiment files
download_experiment() {
    local exp_type=$1
    local model=$2
    local codecarbon_dir=$3

    echo "Downloading ${exp_type} results..."

    # Download files with both lowercase (Sa-) and uppercase (SA-) prefixes
    scp "${MARS_USER}@${MARS_HOST}:${MARS_PATH}/${exp_type}_${model}_*" "${LOCAL_DIR}/" 2>/dev/null
    local files_status1=$?

    # Try uppercase version (SA-zero/SA-few for predictions.json files)
    local exp_type_upper=$(echo "$exp_type" | sed 's/Sa-/SA-/')
    scp "${MARS_USER}@${MARS_HOST}:${MARS_PATH}/${exp_type_upper}_${model}_*" "${LOCAL_DIR}/" 2>/dev/null
    local files_status2=$?

    # Download CodeCarbon directory
    scp -r "${MARS_USER}@${MARS_HOST}:${MARS_PATH}/${codecarbon_dir}" "${LOCAL_DIR}/" 2>/dev/null
    local codecarbon_status=$?

    if [ $files_status1 -eq 0 ] || [ $files_status2 -eq 0 ] || [ $codecarbon_status -eq 0 ]; then
        echo "✓ ${exp_type} downloaded"

        # Show file count and size
        local file_count=$(ls "${LOCAL_DIR}"/${exp_type}_${model}_* "${LOCAL_DIR}"/${exp_type_upper}_${model}_* 2>/dev/null | wc -l)
        if [ $file_count -gt 0 ]; then
            echo "  Files: ${file_count}"
            local detailed_file="${LOCAL_DIR}/${exp_type}_${model}_"*"_detailed_results.jsonl"
            if [ -f ${detailed_file} 2>/dev/null ]; then
                local sample_count=$(wc -l < ${detailed_file})
                echo "  Samples completed: ${sample_count}"
            fi
        fi

        if [ -d "${LOCAL_DIR}/${codecarbon_dir}" ]; then
            echo "  CodeCarbon: ✓"
        fi
    else
        echo "⚠ No files found for ${exp_type}"
    fi
    echo ""
}

# Experiment 1: Baseline SA-zero (Non-thinking Zero-shot)
if prompt_download "Baseline SA-zero (non-thinking zero-shot)"; then
    download_experiment "Sa-zero" "Qwen-Qwen3-4B-Instruct-2507" "codecarbon_baseline_sa-zero"
fi

# Experiment 2: Baseline SA-few (Non-thinking Few-shot)
if prompt_download "Baseline SA-few (non-thinking few-shot)"; then
    download_experiment "Sa-few" "Qwen-Qwen3-4B-Instruct-2507" "codecarbon_baseline_sa-few"
fi

# Experiment 3: Thinking SA-zero (Thinking Zero-shot) - May be incomplete
echo "----------------------------------------"
echo "⚠ NOTE: Thinking SA-zero may still be running (incomplete)"
if prompt_download "Thinking SA-zero (thinking zero-shot)"; then
    download_experiment "Sa-zero" "Qwen-Qwen3-4B-Thinking-2507" "codecarbon_thinking_sa-zero"
fi

# Experiment 4: Thinking SA-few (Thinking Few-shot) - May be incomplete
echo "----------------------------------------"
echo "⚠ NOTE: Thinking SA-few may still be running (incomplete)"
if prompt_download "Thinking SA-few (thinking few-shot)"; then
    download_experiment "Sa-few" "Qwen-Qwen3-4B-Thinking-2507" "codecarbon_thinking_sa-few"
fi

# Download legacy/misc files
echo "----------------------------------------"
if prompt_download "Legacy CodeCarbon directories and emissions.csv"; then
    echo "Downloading legacy CodeCarbon directories..."
    scp -r "${MARS_USER}@${MARS_HOST}:${MARS_PATH}/codecarbon_baseline" "${LOCAL_DIR}/" 2>/dev/null
    scp -r "${MARS_USER}@${MARS_HOST}:${MARS_PATH}/codecarbon_thinking" "${LOCAL_DIR}/" 2>/dev/null
    scp "${MARS_USER}@${MARS_HOST}:${MARS_PATH}/emissions.csv" "${LOCAL_DIR}/" 2>/dev/null
    echo "✓ Legacy files downloaded"
    echo ""
fi

echo "========================================"
echo "=== Download Complete ==="
echo ""
echo "Downloaded files:"
ls -lh "${LOCAL_DIR}/" | grep -v "^d" | tail -n +2
echo ""
echo "Downloaded directories:"
ls -ld "${LOCAL_DIR}"/codecarbon_* 2>/dev/null
echo ""
echo "Total size:"
du -sh "${LOCAL_DIR}/"

echo ""
echo "=== Summary by Experiment ==="
for exp_file in "${LOCAL_DIR}"/*_detailed_results.jsonl; do
    if [ -f "$exp_file" ]; then
        count=$(wc -l < "$exp_file")
        file_basename=$(basename "$exp_file")
        echo "  ${file_basename}: ${count} samples"
    fi
done

echo ""
echo "=== Verifying Download ==="
echo "Comparing local files with Mars server..."
echo ""

# Get list of files on Mars server
echo "Fetching file list from Mars..."
REMOTE_FILES=$(ssh "${MARS_USER}@${MARS_HOST}" "ls -1 ${MARS_PATH}/*.{csv,jsonl,json,txt} 2>/dev/null" | sort)
REMOTE_DIRS=$(ssh "${MARS_USER}@${MARS_HOST}" "ls -1d ${MARS_PATH}/codecarbon_* 2>/dev/null" | sort)

# Get list of local files
LOCAL_FILES=$(ls -1 "${LOCAL_DIR}"/*.{csv,jsonl,json,txt} 2>/dev/null | xargs -n1 basename | sort)
LOCAL_DIRS=$(ls -1d "${LOCAL_DIR}"/codecarbon_* 2>/dev/null | xargs -n1 basename | sort)

# Count files
REMOTE_FILE_COUNT=$(echo "$REMOTE_FILES" | grep -v '^$' | wc -l | tr -d ' ')
LOCAL_FILE_COUNT=$(echo "$LOCAL_FILES" | grep -v '^$' | wc -l | tr -d ' ')
REMOTE_DIR_COUNT=$(echo "$REMOTE_DIRS" | grep -v '^$' | wc -l | tr -d ' ')
LOCAL_DIR_COUNT=$(echo "$LOCAL_DIRS" | grep -v '^$' | wc -l | tr -d ' ')

echo "Files on Mars: ${REMOTE_FILE_COUNT}"
echo "Files locally: ${LOCAL_FILE_COUNT}"
echo "CodeCarbon dirs on Mars: ${REMOTE_DIR_COUNT}"
echo "CodeCarbon dirs locally: ${LOCAL_DIR_COUNT}"
echo ""

# Check for missing files
echo "Checking for missing files..."
MISSING_COUNT=0
for remote_file in $REMOTE_FILES; do
    filename=$(basename "$remote_file")
    if ! echo "$LOCAL_FILES" | grep -q "^${filename}$"; then
        if [ $MISSING_COUNT -eq 0 ]; then
            echo ""
            echo "Missing files (not downloaded):"
        fi
        echo "  ⚠ ${filename}"
        MISSING_COUNT=$((MISSING_COUNT + 1))
    fi
done

# Check for missing directories
for remote_dir in $REMOTE_DIRS; do
    dirname=$(basename "$remote_dir")
    if ! echo "$LOCAL_DIRS" | grep -q "^${dirname}$"; then
        if [ $MISSING_COUNT -eq 0 ]; then
            echo ""
            echo "Missing directories (not downloaded):"
        fi
        echo "  ⚠ ${dirname}/"
        MISSING_COUNT=$((MISSING_COUNT + 1))
    fi
done

if [ $MISSING_COUNT -eq 0 ]; then
    echo "✓ All files downloaded successfully!"
else
    echo ""
    echo "⚠ ${MISSING_COUNT} items not downloaded"
    echo ""
    echo "To download missing files, re-run:"
    echo "  bash scripts/download_mars_results.sh"
fi

echo ""
echo "=== Re-run Download Script ==="
echo "You can re-run this script anytime to get updated results:"
echo "  bash scripts/download_mars_results.sh"
