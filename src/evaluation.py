import csv
import Levenshtein
from difflib import SequenceMatcher
import pandas as pd
import config
import os

def load_ground_truth(file_path):
    ground_truth = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ground_truth[int(row["LineId"])] = row["EventTemplate"]
    return ground_truth

def calculate_edit_distance(str1, str2):
    return Levenshtein.distance(str1, str2)

def calculate_lcs(str1, str2):
    matcher = SequenceMatcher(None, str1, str2)
    return sum(block.size for block in matcher.get_matching_blocks())

def load_ground_truth_list(file_path):
    templates = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            templates.append(row["EventTemplate"])
    return templates

def evaluate_parsing(parsed_templates, ground_truth_templates):
    total_logs = len(ground_truth_templates)
    correct_parses = 0
    total_edit_distance = 0
    total_lcs_length = 0

    line_metrics = []

    for idx, (parsed_template, ground_truth_template) in enumerate(zip(parsed_templates, ground_truth_templates), start=1):
        edit_distance = calculate_edit_distance(parsed_template, ground_truth_template)
        total_edit_distance += edit_distance

        lcs_length = calculate_lcs(parsed_template, ground_truth_template)
        total_lcs_length += lcs_length

        is_correct = parsed_template == ground_truth_template

        if is_correct:
            correct_parses += 1

        print(f"Log Line {idx}:")
        print(f"  Parsed:    {parsed_template}")
        print(f"  Ground:    {ground_truth_template}")
        print(f"  Edit Dist: {edit_distance}")
        print(f"  LCS:       {lcs_length}")
        print("-" * 50)

        line_metrics.append({
            "Line Number": idx,
            "Parsed": parsed_template,
            "Ground Truth": ground_truth_template,
            "Edit Distance": edit_distance,
            "LCS Length": lcs_length,
            "Is Correct": is_correct
        })


    avg_edit_distance = total_edit_distance / total_logs
    avg_lcs_length = total_lcs_length / total_logs
    parsing_accuracy = correct_parses / total_logs
    

    print("\nEvaluation Summary:")
    print(f"  Parsing Accuracy: {parsing_accuracy:.2%}")
    print(f"  Average Edit Distance: {avg_edit_distance:.2f}")
    print(f"  Average LCS Length: {avg_lcs_length:.2f}")

    return {
        "Parsing Accuracy": parsing_accuracy,
        "Average Edit Distance": avg_edit_distance,
        "Average LCS Length": avg_lcs_length,
        "Per-Line Metrics": line_metrics
    }

def save_per_line_metrics(results, design, results_dir=config.RESULT_DIR):
    filename = os.path.join(results_dir, f"{design}_per_line_metrics.csv")
    df_metrics = pd.DataFrame(results["Per-Line Metrics"])
    df_metrics.to_csv(filename, index=False)
    print(f"Per-line metrics saved to: {filename}")

def save_summary_metrics(results, design, results_dir=config.RESULT_DIR):
    filename = os.path.join(results_dir, f"{design}_summary_metrics.csv")
    summary_df = pd.DataFrame([{
        "Parsing Accuracy": results["Parsing Accuracy"],
        "Average Edit Distance": results["Average Edit Distance"],
        "Average LCS Length": results["Average LCS Length"]
    }])
    summary_df.to_csv(filename, index=False)
    print(f"Summary metrics saved to: {filename}")

# --- Evaluate all ---
def evaluate_and_save(normalize_fn, parsed_templates, ground_truth_file_path, exp_name):
    normalized_templates = [normalize_fn(t) for t in parsed_templates]
    ground_truth_templates = load_ground_truth_list(ground_truth_file_path)
    results = evaluate_parsing(normalized_templates, ground_truth_templates)
    save_per_line_metrics(results, exp_name)
    save_summary_metrics(results, exp_name)
    return results