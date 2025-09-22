import csv
import json
import pandas as pd
import config
import os
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

# Normalization Functions (moved from config.py)
def normalize_vulnerability_basic(prediction):
    """Basic normalization for vulnerability predictions"""
    if prediction is None:
        return 1  # Default to vulnerable if unclear
    return int(prediction)

def normalize_vulnerability_conservative(prediction):
    """Conservative normalization - defaults to vulnerable"""
    if prediction is None or prediction == "":
        return 1
    try:
        return int(prediction)
    except (ValueError, TypeError):
        return 1  # Default to vulnerable

def normalize_vulnerability_strict(prediction):
    """Strict normalization - defaults to not vulnerable"""
    if prediction is None or prediction == "":
        return 0
    try:
        return int(prediction)
    except (ValueError, TypeError):
        return 0  # Default to not vulnerable

def load_ground_truth_vulnerability(file_path):
    """Load ground truth vulnerability labels from JSONL file"""
    ground_truth = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip():
                data = json.loads(line.strip())
                if 'idx' in data and 'target' in data:
                    ground_truth[data['idx']] = data['target']
    return ground_truth

def load_ground_truth_list_vulnerability(file_path):
    """Load ground truth vulnerability labels as list (maintaining order)"""
    labels = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip():
                data = json.loads(line.strip())
                if 'target' in data:
                    labels.append(data['target'])
    return labels

def evaluate_vulnerability_detection(predictions, ground_truth_labels):
    """Evaluate vulnerability detection performance"""
    total_samples = len(ground_truth_labels)
    
    # Basic metrics
    accuracy = accuracy_score(ground_truth_labels, predictions)
    precision = precision_score(ground_truth_labels, predictions, zero_division=0)
    recall = recall_score(ground_truth_labels, predictions, zero_division=0)
    f1 = f1_score(ground_truth_labels, predictions, zero_division=0)
    
    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(ground_truth_labels, predictions).ravel()
    
    # Per-sample metrics
    sample_metrics = []
    correct_predictions = 0
    
    for idx, (pred, truth) in enumerate(zip(predictions, ground_truth_labels), start=1):
        is_correct = pred == truth
        if is_correct:
            correct_predictions += 1
            
        # Determine prediction type
        if pred == 1 and truth == 1:
            prediction_type = "True Positive"
        elif pred == 1 and truth == 0:
            prediction_type = "False Positive"
        elif pred == 0 and truth == 1:
            prediction_type = "False Negative"
        else:  # pred == 0 and truth == 0
            prediction_type = "True Negative"
        
        sample_metrics.append({
            "Sample Number": idx,
            "Predicted": pred,
            "Ground Truth": truth,
            "Prediction Type": prediction_type,
            "Is Correct": is_correct
        })
    
    print("\nEvaluation Summary:")
    print(f" Accuracy: {accuracy:.4f} ({accuracy:.2%})")
    print(f" Precision: {precision:.4f}")
    print(f" Recall: {recall:.4f}")
    print(f" F1-Score: {f1:.4f}")
    print(f" True Positives: {tp}")
    print(f" True Negatives: {tn}")
    print(f" False Positives: {fp}")
    print(f" False Negatives: {fn}")
    
    return {
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1_Score": f1,
        "True_Positives": tp,
        "True_Negatives": tn,
        "False_Positives": fp,
        "False_Negatives": fn,
        "Total_Samples": total_samples,
        "Correct_Predictions": correct_predictions,
        "Per_Sample_Metrics": sample_metrics
    }

def save_per_sample_metrics_vulnerability(results, design, results_dir=config.RESULT_DIR):
    """Save per-sample vulnerability detection metrics"""
    filename = os.path.join(results_dir, f"{design}_per_sample_vulnerability_metrics.csv")
    df_metrics = pd.DataFrame(results["Per_Sample_Metrics"])
    df_metrics.to_csv(filename, index=False)
    print(f"Per-sample vulnerability metrics saved to: {filename}")

def save_summary_metrics_vulnerability(results, design, results_dir=config.RESULT_DIR):
    """Save summary vulnerability detection metrics"""
    filename = os.path.join(results_dir, f"{design}_summary_vulnerability_metrics.csv")
    summary_df = pd.DataFrame([{
        "Accuracy": results["Accuracy"],
        "Precision": results["Precision"],
        "Recall": results["Recall"],
        "F1_Score": results["F1_Score"],
        "True_Positives": results["True_Positives"],
        "True_Negatives": results["True_Negatives"],
        "False_Positives": results["False_Positives"],
        "False_Negatives": results["False_Negatives"],
        "Total_Samples": results["Total_Samples"],
        "Correct_Predictions": results["Correct_Predictions"]
    }])
    summary_df.to_csv(filename, index=False)
    print(f"Summary vulnerability metrics saved to: {filename}")

def save_classification_report(predictions, ground_truth_labels, design, results_dir=config.RESULT_DIR):
    """Save detailed classification report"""
    report = classification_report(
        ground_truth_labels, 
        predictions, 
        target_names=['Not Vulnerable', 'Vulnerable'],
        output_dict=True
    )
    
    # Convert to DataFrame for better formatting
    report_df = pd.DataFrame(report).transpose()
    
    filename = os.path.join(results_dir, f"{design}_classification_report.csv")
    report_df.to_csv(filename)
    print(f"Classification report saved to: {filename}")
    
    # Also save as human-readable text
    text_filename = os.path.join(results_dir, f"{design}_classification_report.txt")
    with open(text_filename, 'w') as f:
        f.write(classification_report(
            ground_truth_labels, 
            predictions, 
            target_names=['Not Vulnerable', 'Vulnerable']
        ))
    print(f"Classification report (text) saved to: {text_filename}")

# --- Main Evaluation Function (following original pattern) ---
def evaluate_and_save_vulnerability(normalize_fn, predictions, ground_truth_file_path, exp_name):
    """Main evaluation function for vulnerability detection (following original pattern)"""
    
    # Normalize predictions using the provided function
    normalized_predictions = [normalize_fn(p) for p in predictions]
    
    # Load ground truth labels
    ground_truth_labels = load_ground_truth_list_vulnerability(ground_truth_file_path)
    
    # Ensure same length
    if len(normalized_predictions) != len(ground_truth_labels):
        min_length = min(len(normalized_predictions), len(ground_truth_labels))
        normalized_predictions = normalized_predictions[:min_length]
        ground_truth_labels = ground_truth_labels[:min_length]
        print(f"Warning: Truncated to {min_length} samples to match lengths")
    
    # Evaluate vulnerability detection
    results = evaluate_vulnerability_detection(normalized_predictions, ground_truth_labels)
    
    # Save results (following original pattern)
    save_per_sample_metrics_vulnerability(results, exp_name)
    save_summary_metrics_vulnerability(results, exp_name)
    save_classification_report(normalized_predictions, ground_truth_labels, exp_name)
    
    return results

# Alias for backward compatibility with original naming
evaluate_and_save = evaluate_and_save_vulnerability