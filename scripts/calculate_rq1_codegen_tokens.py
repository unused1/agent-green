import json
import tiktoken
from pathlib import Path
from collections import defaultdict

# Initialize tokenizer (cl100k_base for Qwen models)
encoder = tiktoken.get_encoding("cl100k_base")

# Directory with code generation results
results_dir = Path('/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results/runpod_codegen')

# Files to process (RQ1 Single-Agent only)
files = [
    ('Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_20251107-123658_detailed_results.jsonl', '30B', 'Instruct', 'Zero-shot'),
    ('Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_20251107-130505_detailed_results.jsonl', '30B', 'Instruct', 'Few-shot'),
    ('Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20251107-123611_detailed_results.jsonl', '30B', 'Thinking', 'Zero-shot'),
    ('Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20251107-132927_detailed_results.jsonl', '30B', 'Thinking', 'Few-shot'),
    ('Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251107-131154_detailed_results.jsonl', '4B', 'Instruct', 'Zero-shot'),
    ('Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251107-133348_detailed_results.jsonl', '4B', 'Instruct', 'Few-shot'),
    ('Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251107-133841_detailed_results.jsonl', '4B', 'Thinking', 'Zero-shot'),
    ('Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-144419_detailed_results.jsonl', '4B', 'Thinking', 'Few-shot'),
]

results = []

for filename, model_size, model_type, prompting in files:
    file_path = results_dir / filename

    if not file_path.exists():
        print(f"⚠️  File not found: {filename}")
        continue

    token_counts = []

    with open(file_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            generated_solution = data.get('generated_solution', '')

            if generated_solution:
                # Count tokens using tiktoken
                tokens = len(encoder.encode(generated_solution))
                token_counts.append(tokens)

    if token_counts:
        avg_tokens = sum(token_counts) / len(token_counts)
        min_tokens = min(token_counts)
        max_tokens = max(token_counts)

        results.append({
            'Model Size': model_size,
            'Model Type': model_type,
            'Prompting': prompting,
            'Avg Tokens': int(avg_tokens),
            'Min Tokens': min_tokens,
            'Max Tokens': max_tokens,
            'Samples': len(token_counts)
        })

        print(f"✅ {model_size}-{model_type}-{prompting}: {int(avg_tokens)} avg tokens ({len(token_counts)} samples)")
    else:
        print(f"❌ {model_size}-{model_type}-{prompting}: No data found")

# Print summary table
print("\n" + "="*100)
print("RQ1 CODE GENERATION - AVERAGE OUTPUT TOKENS")
print("="*100)
print(f"{'Model':<20} {'Prompting':<15} {'Avg Tokens':<12} {'Min':<8} {'Max':<8} {'Samples':<8}")
print("-"*100)

for r in results:
    model = f"{r['Model Size']}-{r['Model Type']}"
    print(f"{model:<20} {r['Prompting']:<15} {r['Avg Tokens']:<12} {r['Min Tokens']:<8} {r['Max Tokens']:<8} {r['Samples']:<8}")

print("="*100)
