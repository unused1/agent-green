"""
Faithfulness Metrics for RQ3 Explanation Evaluation

This module implements automated faithfulness metrics to assess how well
explanations align with actual evidence and execution outcomes.

Metrics include:
- Basic structural metrics (length, structure compliance)
- Citation/reference metrics (code span mentions)
- Consistency metrics (claim-outcome alignment)
"""

import re
import json
from typing import Dict, List, Tuple, Any


# --- Basic Structural Metrics ---

def compute_explanation_length(reasoning: str) -> int:
    """
    Compute character length of explanation.

    Args:
        reasoning: The REASONING section text

    Returns:
        Character count
    """
    return len(reasoning) if reasoning else 0


def compute_word_count(reasoning: str) -> int:
    """
    Compute word count of explanation.

    Args:
        reasoning: The REASONING section text

    Returns:
        Word count
    """
    if not reasoning:
        return 0
    return len(reasoning.split())


def check_structure_compliance(response_text: str, expected_format: str = "REASONING-DECISION") -> Dict[str, bool]:
    """
    Check if response follows expected structured format.

    Args:
        response_text: Full model response
        expected_format: Either "REASONING-DECISION" (vuln) or "REASONING-CODE" (codegen)

    Returns:
        Dict with compliance flags:
        - has_reasoning_section: Boolean
        - has_output_section: Boolean (DECISION or CODE)
        - fully_compliant: Boolean
    """
    response_lower = response_text.lower()

    has_reasoning = "reasoning:" in response_lower

    if expected_format == "REASONING-DECISION":
        has_output = "decision:" in response_lower
    elif expected_format == "REASONING-CODE":
        has_output = "code:" in response_lower
    else:
        has_output = False

    return {
        "has_reasoning_section": has_reasoning,
        "has_output_section": has_output,
        "fully_compliant": has_reasoning and has_output
    }


# --- Citation and Reference Metrics ---

def extract_code_references(reasoning: str) -> List[str]:
    """
    Extract code references from reasoning text.

    Looks for patterns like:
    - `code_snippet`
    - function_name()
    - variable_name
    - Line X

    Args:
        reasoning: The REASONING section text

    Returns:
        List of extracted code references
    """
    if not reasoning:
        return []

    references = []

    # Extract backtick-quoted code
    backtick_pattern = r'`([^`]+)`'
    references.extend(re.findall(backtick_pattern, reasoning))

    # Extract function calls (word followed by parentheses)
    function_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)'
    references.extend(re.findall(function_pattern, reasoning))

    # Extract line number references
    line_pattern = r'[Ll]ine\s+(\d+)'
    line_refs = re.findall(line_pattern, reasoning)
    references.extend([f"Line {line}" for line in line_refs])

    return list(set(references))  # Remove duplicates


def compute_citation_density(reasoning: str) -> float:
    """
    Compute citation density (code references per 100 words).

    Args:
        reasoning: The REASONING section text

    Returns:
        Citations per 100 words
    """
    if not reasoning:
        return 0.0

    word_count = compute_word_count(reasoning)
    if word_count == 0:
        return 0.0

    references = extract_code_references(reasoning)
    return (len(references) / word_count) * 100


def check_code_reference_validity(reasoning: str, actual_code: str) -> Dict[str, Any]:
    """
    Check if code references in reasoning actually exist in the code.

    Args:
        reasoning: The REASONING section text
        actual_code: The actual code being analyzed

    Returns:
        Dict with:
        - total_references: int
        - valid_references: int
        - invalid_references: List[str]
        - validity_rate: float (0-1)
    """
    references = extract_code_references(reasoning)

    if not references:
        return {
            "total_references": 0,
            "valid_references": 0,
            "invalid_references": [],
            "validity_rate": 1.0  # No references = no invalid references
        }

    valid = []
    invalid = []

    for ref in references:
        # Skip line number references (harder to validate)
        if ref.startswith("Line "):
            continue

        # Check if reference appears in code
        if ref in actual_code:
            valid.append(ref)
        else:
            invalid.append(ref)

    total = len(valid) + len(invalid)
    validity_rate = len(valid) / total if total > 0 else 1.0

    return {
        "total_references": len(references),
        "valid_references": len(valid),
        "invalid_references": invalid,
        "validity_rate": validity_rate
    }


# --- Consistency Metrics for Vulnerability Detection ---

def check_decision_consistency(reasoning: str, decision: int, keywords: Dict[str, List[str]] = None) -> Dict[str, Any]:
    """
    Check if reasoning is consistent with the final decision.

    For vulnerability detection:
    - DECISION: YES should have vulnerability-related keywords in reasoning
    - DECISION: NO should have safety-related keywords in reasoning

    Args:
        reasoning: The REASONING section text
        decision: 1 for vulnerable, 0 for safe
        keywords: Optional custom keyword dict with 'vulnerable' and 'safe' lists

    Returns:
        Dict with consistency analysis
    """
    if keywords is None:
        keywords = {
            "vulnerable": [
                "vulnerability", "vulnerable", "security issue", "exploit",
                "injection", "overflow", "unsafe", "risk", "attack",
                "malicious", "compromise", "breach"
            ],
            "safe": [
                "safe", "secure", "no vulnerability", "no issue", "protected",
                "validated", "sanitized", "no risk", "not vulnerable"
            ]
        }

    reasoning_lower = reasoning.lower()

    # Count vulnerability keywords
    vuln_count = sum(1 for keyword in keywords["vulnerable"] if keyword in reasoning_lower)
    safe_count = sum(1 for keyword in keywords["safe"] if keyword in reasoning_lower)

    # Determine if reasoning aligns with decision
    if decision == 1:  # Vulnerable
        is_consistent = vuln_count > safe_count
        expected = "vulnerability indicators"
        actual_dominant = "vulnerable" if vuln_count > safe_count else "safe"
    else:  # Safe
        is_consistent = safe_count >= vuln_count
        expected = "safety indicators"
        actual_dominant = "safe" if safe_count >= vuln_count else "vulnerable"

    return {
        "is_consistent": is_consistent,
        "vulnerability_keyword_count": vuln_count,
        "safety_keyword_count": safe_count,
        "expected_sentiment": expected,
        "actual_dominant_sentiment": actual_dominant
    }


# --- Consistency Metrics for Code Generation ---

def check_implementation_consistency(reasoning: str, generated_code: str) -> Dict[str, Any]:
    """
    Check if generated code is consistent with the reasoning/plan.

    Looks for:
    - Function/variable names mentioned in reasoning appear in code
    - Steps mentioned in reasoning are reflected in code structure

    Args:
        reasoning: The REASONING section text
        generated_code: The generated code

    Returns:
        Dict with consistency analysis
    """
    if not reasoning or not generated_code:
        return {
            "mentioned_in_plan": [],
            "implemented_in_code": [],
            "consistency_rate": 0.0
        }

    # Extract potential function/variable names from reasoning
    # Look for words that might be identifiers
    identifier_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]{2,})\b'
    mentioned = set(re.findall(identifier_pattern, reasoning.lower()))

    # Filter out common English words (simple heuristic)
    common_words = {
        "the", "and", "for", "that", "with", "this", "will", "should",
        "can", "use", "return", "check", "from", "function", "variable",
        "code", "implement", "create", "make", "need", "each", "then"
    }
    mentioned = mentioned - common_words

    # Check which mentioned items appear in code
    implemented = []
    for item in mentioned:
        if item in generated_code.lower():
            implemented.append(item)

    consistency_rate = len(implemented) / len(mentioned) if mentioned else 1.0

    return {
        "mentioned_in_plan": list(mentioned),
        "implemented_in_code": implemented,
        "consistency_rate": consistency_rate
    }


# --- Aggregate Metrics ---

def compute_faithfulness_metrics_vuln(result: Dict[str, Any], include_code_validation: bool = True) -> Dict[str, Any]:
    """
    Compute all faithfulness metrics for a vulnerability detection result.

    Args:
        result: Dict with keys 'reasoning', 'vuln', 'func' (code)
        include_code_validation: Whether to validate code references

    Returns:
        Dict with all faithfulness metrics
    """
    reasoning = result.get('reasoning', '')
    decision = result.get('vuln', 0)
    code = result.get('func', '')

    metrics = {
        # Basic metrics
        "explanation_length": compute_explanation_length(reasoning),
        "word_count": compute_word_count(reasoning),

        # Structure compliance
        "structure_compliance": check_structure_compliance(
            result.get('response_text', reasoning),
            expected_format="REASONING-DECISION"
        ),

        # Citation metrics
        "code_references": extract_code_references(reasoning),
        "citation_density": compute_citation_density(reasoning),

        # Consistency metrics
        "decision_consistency": check_decision_consistency(reasoning, decision)
    }

    # Add code reference validation if requested
    if include_code_validation and code:
        metrics["reference_validity"] = check_code_reference_validity(reasoning, code)

    return metrics


def compute_faithfulness_metrics_codegen(result: Dict[str, Any], include_code_validation: bool = True) -> Dict[str, Any]:
    """
    Compute all faithfulness metrics for a code generation result.

    Args:
        result: Dict with keys 'reasoning', 'generated_solution', 'prompt'
        include_code_validation: Whether to check implementation consistency

    Returns:
        Dict with all faithfulness metrics
    """
    reasoning = result.get('reasoning', '')
    generated_code = result.get('generated_solution', '')

    metrics = {
        # Basic metrics
        "explanation_length": compute_explanation_length(reasoning),
        "word_count": compute_word_count(reasoning),

        # Structure compliance
        "structure_compliance": check_structure_compliance(
            result.get('response_text', reasoning),
            expected_format="REASONING-CODE"
        ),

        # Citation metrics
        "code_references": extract_code_references(reasoning),
        "citation_density": compute_citation_density(reasoning),
    }

    # Add implementation consistency if requested
    if include_code_validation and generated_code:
        metrics["implementation_consistency"] = check_implementation_consistency(reasoning, generated_code)

    return metrics


# --- Batch Processing ---

def compute_faithfulness_for_experiment(results_file: str, task_type: str = "vuln") -> Dict[str, Any]:
    """
    Compute faithfulness metrics for all results in an experiment.

    Args:
        results_file: Path to JSONL results file
        task_type: Either "vuln" or "codegen"

    Returns:
        Dict with:
        - per_sample_metrics: List of metrics for each sample
        - aggregate_metrics: Summary statistics
    """
    results = []

    # Read results file
    with open(results_file, 'r') as f:
        for line in f:
            results.append(json.loads(line.strip()))

    # Compute metrics for each sample
    per_sample_metrics = []

    for result in results:
        if task_type == "vuln":
            metrics = compute_faithfulness_metrics_vuln(result)
        else:  # codegen
            metrics = compute_faithfulness_metrics_codegen(result)

        per_sample_metrics.append({
            "task_id": result.get('task_id', result.get('sample_id', 'unknown')),
            "metrics": metrics
        })

    # Compute aggregate statistics
    aggregate = compute_aggregate_statistics(per_sample_metrics)

    return {
        "per_sample_metrics": per_sample_metrics,
        "aggregate_metrics": aggregate,
        "total_samples": len(results)
    }


def compute_aggregate_statistics(per_sample_metrics: List[Dict]) -> Dict[str, Any]:
    """
    Compute aggregate statistics across all samples.

    Args:
        per_sample_metrics: List of per-sample metric dicts

    Returns:
        Dict with aggregate statistics
    """
    if not per_sample_metrics:
        return {}

    # Collect values for averaging
    lengths = []
    word_counts = []
    citation_densities = []
    compliance_rates = []

    for sample in per_sample_metrics:
        metrics = sample["metrics"]
        lengths.append(metrics.get("explanation_length", 0))
        word_counts.append(metrics.get("word_count", 0))
        citation_densities.append(metrics.get("citation_density", 0))

        structure = metrics.get("structure_compliance", {})
        if structure.get("fully_compliant"):
            compliance_rates.append(1.0)
        else:
            compliance_rates.append(0.0)

    return {
        "mean_explanation_length": sum(lengths) / len(lengths) if lengths else 0,
        "mean_word_count": sum(word_counts) / len(word_counts) if word_counts else 0,
        "mean_citation_density": sum(citation_densities) / len(citation_densities) if citation_densities else 0,
        "structure_compliance_rate": sum(compliance_rates) / len(compliance_rates) if compliance_rates else 0
    }


if __name__ == "__main__":
    # Example usage
    print("Faithfulness Metrics Module")
    print("=" * 60)
    print("\nThis module provides functions to compute faithfulness metrics")
    print("for RQ3 explanation evaluation.")
    print("\nExample usage:")
    print("  from faithfulness_metrics import compute_faithfulness_metrics_vuln")
    print("  metrics = compute_faithfulness_metrics_vuln(result)")
