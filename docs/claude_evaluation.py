import os
import json
import re
from anthropic import Anthropic

SYSTEM_PROMPT = """
You are an expert in software security and vulnerability detection.
Your task is to evaluate reasoning outputs for a given code function
and provide structured scoring and comparative analysis.
"""


EVAL_TEMPLATE = """
**Code Function:**
{function}
**Ground-Truth Label:**
{label}
**Reasoning Outputs:**
1. Reasoning A:
{reasoning_a}
2. Reasoning B:
{reasoning_b}

**Evaluation Instructions:**
**Score Assignment:** Provide score for each reasoning output on a scale of 1 to 5 for the following criteria:
   - Completeness: Does the reasoning cover the vulnerability mechanism or justify why the code is safe, considering edge cases and attack vectors?
   - Clarity: Is the reasoning logically structured, free of ambiguities, and using precise technical terms?
   - Actionability: Does the reasoning provide actionable insights like highlighting vulnerable lines, suggesting patches, or detailing risks?
   - Informativeness: Does the reasoning provide rich, non-redundant, and technically insightful information beyond superficial observations?
   

**Output Format (STRICT JSON):**
{{
  "scores": {{
    "reasoning_a": {{
      "completeness": int,
      "clarity": int,
      "actionability": int,
      "informativeness": int
    }},
    "reasoning_b": {{
      "completeness": int,
      "clarity": int,
      "actionability": int,
      "informativeness": int
    }}
  }}
}}
"""


ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


CLAUDE_MODEL = "claude-haiku-4-5-20251001"
INPUT_FILE = "output_explanation_synthesis_cot.json" 
OUTPUT_DIR = "evaluations_claudehaiku45"   

os.makedirs(OUTPUT_DIR, exist_ok=True)



def load_examples_from_json_dict(path: str):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    examples = []
    for key, item in raw.items():
        examples.append({
            "id": key,
            "function": item["code"],
            "label": item["vuln"],
            "reasoning_a": item["exp1"],
            "reasoning_b": item["exp2"],
        })
    return examples


def build_eval_prompt(example: dict) -> str:
    return EVAL_TEMPLATE.format(
        function=example["function"],
        label=example["label"],
        reasoning_a=example["reasoning_a"],
        reasoning_b=example["reasoning_b"],
    )

def extract_json_object(text: str) -> str:
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    candidates = re.findall(r"\{.*?\}", text, flags=re.DOTALL)

    candidates = sorted(candidates, key=len, reverse=True)

    for cand in candidates:
        try:
            json.loads(cand)
            return cand
        except json.JSONDecodeError:
            continue

    
    raise ValueError(
        "Could not find a valid JSON object in model output. "
        f"Here is a preview:\n{text[:2000]}"
    )

def call_claude(prompt: str) -> dict:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1048,
        temperature=0.0,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    text = "".join(
        block.text for block in response.content if block.type == "text"
    ) #.strip()
    print(text)
    print("-------------")
    # Extract just the JSON part

     # Remove extra content
    text = "{\n"+text.split("{",1)[-1].strip()
    clean_text = text.split("\nHuman:")[0].strip()
    clean_text = clean_text.split("Human:")[0].strip()
    clean_text = clean_text.split("Detailed Rationale:")[0].strip()
    clean_text = clean_text.rsplit("}\n```",1)[0]+"}"
    clean_text = clean_text.rsplit("}",1)[0] +"}"
    print(clean_text)
    return json.loads(clean_text)



def evaluate_file(input_path: str, output_path: str = None):
    examples = load_examples_from_json_dict(input_path)
    results = []

    for idx, ex in enumerate(examples, start=1):
        if os.path.exists(OUTPUT_DIR+"/"+str(ex['id'])+".txt"):
            print(f"Skipping ({idx}/{len(examples)}): file already exists.")
            continue
        print(f"Evaluating example {idx}/{len(examples)} (ID={ex['id']})...")

        prompt = build_eval_prompt(ex)
        eval_result = call_claude(prompt)

        combined = {
            "id": ex["id"],
            "input": ex,
            "evaluation": eval_result,
        }
        results.append(combined)
        
        with open(OUTPUT_DIR+"/"+str(ex['id'])+".txt", "w", encoding="utf-8") as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)


    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            for item in results:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return results


if __name__ == "__main__":
    output_file = "evaluations.jsonl"
    all_results = evaluate_file(INPUT_FILE, output_path=output_file)
    print(f"Done. Wrote {len(all_results)} evaluations to {output_file}")
