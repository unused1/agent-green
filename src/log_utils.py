import os
import csv
import re
import json
from datetime import datetime
from collections import Counter
from typing import List, Optional, Dict, Any, Tuple


def read_log_messages(file_path: str) -> List[str]:
    """Read log messages from a file, one per line."""
    log_messages = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            log_messages = [line.strip() for line in file]
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return log_messages


def slice_log_file(input_path: str, num_lines: int) -> Optional[str]:
    """
    Slices the first `num_lines` from a log file and saves it to a new file.
    Returns the path to the new sliced file.
    """
    if not os.path.exists(input_path):
        print(f"Error: The file '{input_path}' does not exist.")
        return None
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            lines = [next(infile).strip() for _ in range(num_lines)]
        dir_path, filename = os.path.split(input_path)
        name, ext = os.path.splitext(filename)
        new_filename = f"{name}_{num_lines}{ext}"
        new_path = os.path.join(dir_path, new_filename)
        with open(new_path, 'w', encoding='utf-8') as outfile:
            outfile.write('\n'.join(lines) + '\n')
        print(f"Sliced file created: {new_path}")
        return new_path
    except StopIteration:
        print(f"Warning: The file has fewer than {num_lines} lines. All lines were copied.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

def _clean_text(text: str) -> str:
    """Helper to remove extra whitespace and newlines."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = " ".join(lines)
    return re.sub(r"\s+", " ", cleaned).strip()

def normalize_template_old(text: str) -> str:
    """Normalize template output (legacy version)."""
    text = re.sub(r"<\|.*?\|>", "", text)
    text = re.sub(r"You are a helpful assistant\.?", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    text = re.split(
        r"The template you provided is correct|Therefore, no further suggestions",
        text
    )[0]
    return _clean_text(text)

def normalize_template(text: str) -> str:
    """Normalize template output (main version)."""
    text = re.sub(r"<\|.*?\|>", "", text)
    text = re.sub(r"You are a helpful assistant\.?", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    template_match = re.match(r'^([^H]*?<\*>.*?<\*>[^H]*?)(?=Human|$)', text, re.DOTALL | re.IGNORECASE)
    if template_match:
        text = template_match.group(1)
    else:
        text = re.sub(r"Human Compare and refine.*", "", text, flags=re.IGNORECASE | re.DOTALL)
    patterns = [
        r"\*\*Final Refined Template:\*\*.*?(?:\n|$)",
        r"Final Refined Template:.*?(?:\n|$)",
        r"Both templates are correct.*?(?:\n|$)",
        r"Merged and corrected.*?(?:\n|$)",
        r"^(The template is (incorrect|correct)\. (The )?correct template should be:)\s*",
        r"^The template corresponding to the log message is:\s*",
        r"^The template corresponding to the log message would be:\s*",
        r"\s*Here, <\*> represents.*$",
        r'"\s*This means.*$',
        r"```python.*?```",
        r"^python\s+import\s+.*",
        r"(?i)I am an AI model.*?(?=\n|$)",
        r"\*\*Created Question\*\*:.*",
        r"\*\*Created Answer\*\*:.*"
    ]
    for pat in patterns:
        text = re.sub(pat, "", text, flags=re.IGNORECASE | re.DOTALL)
    quoted_match = re.match(r'^[\'"`](.+?)[\'"`]\.\s+This\b.*', text, flags=re.IGNORECASE | re.DOTALL)
    if quoted_match:
        return quoted_match.group(1).strip()
    text = re.split(
        r'\s+(Here,.*?|This means|This can be interpreted|In this case|The angle brackets)\b',
        text,
        maxsplit=1,
        flags=re.IGNORECASE | re.DOTALL
    )[0]
    text = re.sub(r"^['\"](.*?)['\"]$", r"\1", text.strip())
    text = re.sub(r'[.,;:\s]+$', '', text.strip())
    explanation_patterns = [
        r"This template better abstracts.*?parameters?\.",
        r"This template correctly abstracts.*?\.",
        r"This template is more accurate.*?\.",
        r"Both templates are correct.*?preferred\.",
        r"You are a language model.*",
        r"You are Qwen, created by Alibaba Cloud.*",
        r"\*\*Created Question\*\*:*",
        r"The template you provided is correct",
        r"Therefore, no further suggestions",
        r"This template is more accurate.*",
        r"(Merged and corrected to abstract both dynamic parameters)",
        r"(Merged and corrected both templates into a more accurate version)",
        r"This template better abstracts the log message by*",
        r"This template better abstracts the log message by including the dynamic port number in the IP address field\.",
        r"Both templates are correct, but the Parser Agent's template is more abstract as it does not include a specific path\. Therefore, the Parser Agent's template is chosen as the final refined version\.",
        r"Both templates are correct, but the Parser Agent's template is more abstract as it does not specify the path, making it applicable to any similar log message without modification\.", 
        r"Both templates are correct, but the Parser Agent's template is more abstract as it does not specify the path, making it applicable to any path\.",
        r"Both templates are correct, but the Parser Agent's template better abstracts the dynamic parameters\.",
        r"Both templates are correct and abstract the dynamic parameters effectively\. No merging is necessary as they already capture all the essential information from the log message\\."
    ]
    for pattern in explanation_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Keep only the part before any explanatory "Note:" or similar
    text = re.split(r"\bNote:|This template|Thus,|Therefore,|The template reflects", text, maxsplit=1, flags=re.IGNORECASE)[0]

    return _clean_text(text)

def normalize_template_v1(text: str) -> str:
    """Normalize template output (v1)."""
    text = re.sub(r"<\|.*?\|>", "", text)
    text = re.sub(r"You are a helpful assistant\.?", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    patterns = [
        (r"Here is an example of a log message and its corresponding template:.*?Template:\s*([^\n]+)", 1),
        (r"The template remains as it is:\s*([^\n]+)", 1),
        (r"([^\n]+)\s+This is the template corresponding to the log message", 1),
        (r'The template should be ["\']([^"\']+)["\']', 1),
        (r'The template should be\s+([^\n.]+?)(?:\.|$)', 1),
        (r"should indeed be as follows:\s*([^\n]+)", 1),
        (r'print\((?:template\s*=\s*)?[\'"]([^\'"]+)[\'"]\)', 1),
        (r'template\s*=\s*[\'"]([^\'"]+)[\'"]', 1)
    ]
    for pat, group in patterns:
        match = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(group).strip()
    template_match = re.match(r'^([^H]*?<(?:\*|[^>]*)>.*?<(?:\*|[^>]*)>[^H]*?)(?=Human|$)', text, re.DOTALL | re.IGNORECASE)
    if template_match:
        text = template_match.group(1)
    else:
        text = re.sub(r"Human Compare and refine.*", "", text, flags=re.IGNORECASE | re.DOTALL)
    # ...repeat cleaning as above...
    return normalize_template(text)

def normalize_template_v2(text: str) -> str:
    """Normalize template output (v2)."""
    text = re.sub(r"<\|.*?\|>", "", text)
    text = re.sub(r"You are a helpful assistant\.?", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    text = re.sub(
        r"^(I apologize.*?|Yes, (that's|you are|you're) correct.*?|You're right.*?|Indeed,.*?)(?=\s|$)",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )
    patterns = [
        r"Here is an example of a log message and its corresponding template:.*?Template:\s*([^\n]+)",
        r"The template remains as it is:\s*([^\n]+)",
        r"([^\n]+)\s+This is the template corresponding to the log message",
        r'The template should be ["\']([^"\']+)["\']',
        r'The template should be\s+([^\n.]+?)(?:\.|$)',
        r"should indeed be as follows:\s*([^\n]+)",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    inline_backtick_match = re.search(r"`([^`]*<[^`>]*>[^`]*)`", text)
    if inline_backtick_match:
        return inline_backtick_match.group(1).strip()
    quoted_template_match = re.search(r'"([^"]*<[^>]+>[^"]*)"', text)
    if quoted_template_match:
        return quoted_template_match.group(1).strip()
    single_quoted_match = re.search(r"'([^']*<[^>]+>[^']*)'", text)
    if single_quoted_match:
        return single_quoted_match.group(1).strip()
    # ...repeat cleaning as above...
    return normalize_template(text)

def generate_filenames(design: str, llm_model: str, base_dir: str = ".", suffixes: Tuple[str, ...] = ("raw", "normalized")) -> Dict[str, str]:
    """Generate filenames for raw and normalized template outputs."""
    model_name = llm_model.replace(":", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        suffix: os.path.join(base_dir, f"{design}_{model_name}_{timestamp}_{suffix}.txt")
        for suffix in suffixes
    }

def save_templates(parsed_templates: List[str], llm_config: Dict[str, Any], design: str, output_dir: str = "templates_output") -> Tuple[str, str]:
    """Save raw and normalized templates to files."""
    os.makedirs(output_dir, exist_ok=True)
    model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filename = f"{output_dir}/{design}_{model}_{timestamp}_raw.txt"
    normalized_filename = f"{output_dir}/{design}_{model}_{timestamp}_normalized.txt"
    normalized_templates = [normalize_template(t) for t in parsed_templates]
    with open(raw_filename, "w", encoding="utf-8") as f:
        for t in parsed_templates:
            f.write(t.strip() + "\n")
    with open(normalized_filename, "w", encoding="utf-8") as f:
        for t in normalized_templates:
            f.write(t + "\n")
    print(f"Saved {len(parsed_templates)} raw and {len(normalized_templates)} normalized templates.")
    return raw_filename, normalized_filename


def extract_last_template_from_history(history: List[Dict[str, Any]], agent_name: str = 'log_parser_agent') -> Optional[str]:
    """Extract last plausible template message from agent history."""
    TEMPLATE_PATTERN = re.compile(r'<\*>|blk_<\*>|<.*?>')
    for msg in reversed(history):
        if msg['name'] == agent_name and TEMPLATE_PATTERN.search(msg['content'].strip()):
            return msg['content'].strip()
    return None


def extract_last_template_from_history_loose(history: List[Dict[str, Any]], agent_name: str = 'log_parser_agent') -> Optional[str]:
    """Extract last non-empty message from agent history."""
    for msg in reversed(history):
        if msg['name'] == agent_name:
            content = msg['content'].strip()
            if content:
                return content
    return None

def extract_template_from_parser_responses(parser_responses: List[str]) -> str:
    """Extract last valid template from parser responses."""
    for response in reversed(parser_responses):
        content = response.strip()
        if '<*>' in content and not re.search(r'understood|no further feedback|thank|feel free|additional feedback', content, re.IGNORECASE):
            content = re.sub(r"^```|```$", "", content.strip(), flags=re.MULTILINE)
            return content
    return "NONE"

def extract_event_templates(csv_file_path: str) -> List[str]:
    """Extracts a list of all EventTemplates from a CSV file."""
    event_templates = []
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            event_template = row.get("EventTemplate")
            if event_template:
                event_templates.append(event_template.strip())
    return event_templates

def read_log_sessions(input_dir):
    """
    Reads all .log files under input_dir and returns a list of dicts with block_id and log content.
    Each .log file corresponds to one HDFS block session.
    """
    sessions = []
    for fname in sorted(os.listdir(input_dir)):
        if fname.endswith(".log"):
            block_id = fname.replace(".log", "")
            file_path = os.path.join(input_dir, fname)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            sessions.append({
                "block_id": block_id,
                "content": content
            })
    print(f"[INFO] Loaded {len(sessions)} log sessions from {input_dir}")
    return sessions

def save_parsed_sessions(sessions, out_dir, exp_name):
    """
    Saves parsed log sessions to a JSON file for reproducibility.
    """
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{exp_name}_parsed_sessions.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2)
    print(f"[INFO] Saved parsed sessions to {out_path}")
    return out_path


def get_log_analysis_gt(gt_file_path):
    """
    Loads ground truth CSV file with BlockId, Label.
    Returns a dict {block_id: "0"/"1"}.
    """
    gt = {}
    with open(gt_file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row["Label"].strip().lower()
            gt[row["BlockId"]] = "1" if label == "anomaly" else "0"
    print(f"[INFO] Loaded ground truth for {len(gt)} block IDs from {gt_file_path}")
    return gt

def save_log_analysis_results(results, normalize_fn, exp_name, llm_config, out_dir="results"):
    """
    Saves raw and normalized anomaly detection results.
    """
    os.makedirs(out_dir, exist_ok=True)
    model = llm_config["config_list"][0]["model"].replace(":", "-").replace("/", "-")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    raw_path = os.path.join(out_dir, f"{exp_name}_{model}_{timestamp}_raw.txt")
    normalized_path = os.path.join(out_dir, f"{exp_name}_{model}_{timestamp}_normalized.txt")

    normalized = []
    with open(raw_path, "w", encoding="utf-8") as fr, open(normalized_path, "w", encoding="utf-8") as fn:
        for item in results:
            block_id, raw_output = item["block_id"], item["raw_output"]
            #print(f"[DEBUG] Block ID: {block_id}, Raw Output: {raw_output}")
            normalized_label = normalize_fn(raw_output)
            #print(f"[DEBUG] Block ID: {block_id}, Normalized Label: {normalized_label}")
            normalized.append({"block_id": block_id, "normalized": normalized_label})
            fr.write(f"{block_id}\t{raw_output.strip()}\n")
            fn.write(f"{block_id}\t{normalized_label}\n")

    print(f"[INFO] Saved raw results to {raw_path}")
    print(f"[INFO] Saved normalized results to {normalized_path}")
    return normalized


def normalize_log_analysis_result(text):
    """
    Normalize LLM outputs to 0 or 1.
    Removes extra explanations and keeps only a valid binary digit.
    """
    if text is None:
        return "0"

    # Clean unwanted formatting
    text = str(text).strip()
    text = re.sub(r"```[a-z]*|```", "", text)
    text = re.sub(r"[^\d]", " ", text)

    # Extract the first 0 or 1
    match = re.search(r"\b[01]\b", text)
    if match:
        return match.group(0)

    # Fallback: interpret words
    if re.search(r"anomal", text, re.I):
        return "1"
    if re.search(r"normal", text, re.I):
        return "0"
    print("Could not determine label, defaulting to 0")
    return "0"  # default to normal if uncertain