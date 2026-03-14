#!/usr/bin/env python3
"""Split combined emissions.csv into codecarbon subdirectories"""

import csv
import os
from collections import defaultdict

# Read the combined emissions file
input_file = "results/mars_codegen/emissions_combined.csv"
output_base = "results/mars_codegen"

# Dictionary to store rows for each subdirectory
emissions_by_dir = defaultdict(list)

# Read and categorize emissions
with open(input_file, 'r') as f:
    reader = csv.DictReader(f)
    header = reader.fieldnames

    for row in reader:
        project_name = row['project_name']

        # Determine model type and design from project_name
        if 'Thinking' in project_name:
            model_type = 'thinking'
        elif 'Instruct' in project_name:
            model_type = 'baseline'
        else:
            print(f"Warning: Unknown model type in {project_name}")
            continue

        if 'Sa-zero' in project_name or 'sa-zero' in project_name:
            design = 'sa-zero'
        elif 'Sa-few' in project_name or 'sa-few' in project_name:
            design = 'sa-few'
        else:
            print(f"Warning: Unknown design in {project_name}")
            continue

        # Add to appropriate subdirectory
        subdir = f"codecarbon_{model_type}_{design}"
        emissions_by_dir[subdir].append(row)

# Write split emissions files
for subdir, rows in emissions_by_dir.items():
    subdir_path = os.path.join(output_base, subdir)
    os.makedirs(subdir_path, exist_ok=True)

    output_file = os.path.join(subdir_path, "emissions.csv")

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_file}")

print("\nEmissions split complete!")
