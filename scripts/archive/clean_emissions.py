#!/usr/bin/env python3
"""Clean emissions CSV files to keep only valid experiment records"""

import csv
import os

# Define valid project_name prefixes for each experiment
valid_records = {
    'results/mars_codegen/codecarbon_baseline_sa-zero/emissions.csv': [
        'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251106-210151',  # Initial attempt
        'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251106-210549',  # Actual complete run
    ],
    'results/mars_codegen/codecarbon_baseline_sa-few/emissions.csv': [
        'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251106-221304',  # Main run + resume
    ],
    'results/mars_codegen/codecarbon_thinking_sa-zero/emissions.csv': [
        'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251106-210015',  # Actual complete run
    ],
}

for file_path, valid_project_names in valid_records.items():
    print(f"\nProcessing {file_path}...")

    # Read all rows
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        all_rows = list(reader)

    # Filter to keep only valid records
    filtered_rows = []
    removed_count = 0

    for row in all_rows:
        project_name = row['project_name']
        # Check if this project_name starts with any valid prefix
        is_valid = any(project_name.startswith(valid) for valid in valid_project_names)

        if is_valid:
            filtered_rows.append(row)
        else:
            removed_count += 1
            print(f"  Removing: {project_name}")

    # Write back filtered rows
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(filtered_rows)

    print(f"  Kept {len(filtered_rows)} rows, removed {removed_count} rows")

print("\nEmissions files cleaned!")
