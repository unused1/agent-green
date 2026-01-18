import csv
import Levenshtein
from difflib import SequenceMatcher
import pandas as pd
import os

# Dynamic config selection based on MODEL_FAMILY environment variable
_model_family = os.getenv('MODEL_FAMILY', '').lower()
if _model_family == 'deepseek':
    import config_deepseek as config
elif _model_family == 'nemotron':
    import config_nemotron as config
else:
    import config

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


# --- Log Analysis Evaluation ---
def evaluate_and_save_log_analysis(gt, predictions, exp_name, result_dir):
    """
    Evaluate log analysis (anomaly detection) predictions against ground truth.

    Args:
        gt: dict {block_id: "0"/"1"} ground truth labels
        predictions: list of {"block_id": ..., "normalized": "0"/"1"}
        exp_name: experiment name for file naming
        result_dir: directory to save results

    Returns:
        dict with evaluation metrics
    """
    # Build prediction dict
    pred_dict = {item["block_id"]: item["normalized"] for item in predictions}

    # Align predictions with ground truth
    tp, tn, fp, fn = 0, 0, 0, 0
    per_session_results = []

    for block_id, gt_label in gt.items():
        pred_label = pred_dict.get(block_id, "0")  # default to normal if missing

        gt_int = int(gt_label)
        pred_int = int(pred_label)

        if gt_int == 1 and pred_int == 1:
            tp += 1
            result = "TP"
        elif gt_int == 0 and pred_int == 0:
            tn += 1
            result = "TN"
        elif gt_int == 0 and pred_int == 1:
            fp += 1
            result = "FP"
        else:  # gt_int == 1 and pred_int == 0
            fn += 1
            result = "FN"

        per_session_results.append({
            "block_id": block_id,
            "ground_truth": gt_label,
            "prediction": pred_label,
            "result": result
        })

    # Calculate metrics
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # Print summary
    print("\n" + "=" * 50)
    print("Log Analysis Evaluation Summary")
    print("=" * 50)
    print(f"Total Sessions: {total}")
    print(f"  True Positives (TP):  {tp}")
    print(f"  True Negatives (TN):  {tn}")
    print(f"  False Positives (FP): {fp}")
    print(f"  False Negatives (FN): {fn}")
    print("-" * 50)
    print(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print("=" * 50 + "\n")

    # Save per-session results
    os.makedirs(result_dir, exist_ok=True)
    per_session_path = os.path.join(result_dir, f"{exp_name}_per_session_metrics.csv")
    df_per_session = pd.DataFrame(per_session_results)
    df_per_session.to_csv(per_session_path, index=False)
    print(f"Per-session metrics saved to: {per_session_path}")

    # Save summary metrics
    summary_path = os.path.join(result_dir, f"{exp_name}_summary_metrics.csv")
    summary_df = pd.DataFrame([{
        "Total": total,
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1
    }])
    summary_df.to_csv(summary_path, index=False)
    print(f"Summary metrics saved to: {summary_path}")

    return {
        "total": total,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "per_session": per_session_results
    }