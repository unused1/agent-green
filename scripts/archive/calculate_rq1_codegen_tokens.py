import json
import tiktoken
from pathlib import Path
from collections import defaultdict

# Initialize tokenizer (cl100k_base for Qwen models)
encoder = tiktoken.get_encoding("cl100k_base")

# Base directory
base_dir = Path('/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results')

# Files to process (RQ1 Single-Agent only) - organized by platform
files = [
    # H100 experiments (runpod_codegen)
    ('runpod_codegen', 'Sa-zero_Qwen-Qwen3-30B-A3B-Instruct-2507_20251107-123658_detailed_results.jsonl', '30B', 'Instruct', 'Zero-shot', 'H100'),
    ('runpod_codegen', 'Sa-few_Qwen-Qwen3-30B-A3B-Instruct-2507_20251107-130505_detailed_results.jsonl', '30B', 'Instruct', 'Few-shot', 'H100'),
    ('runpod_codegen', 'Sa-zero_Qwen-Qwen3-30B-A3B-Thinking-2507_20251107-123611_detailed_results.jsonl', '30B', 'Thinking', 'Zero-shot', 'H100'),
    ('runpod_codegen', 'Sa-few_Qwen-Qwen3-30B-A3B-Thinking-2507_20251107-132927_detailed_results.jsonl', '30B', 'Thinking', 'Few-shot', 'H100'),
    ('runpod_codegen', 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251107-131154_detailed_results.jsonl', '4B', 'Instruct', 'Zero-shot', 'H100'),
    ('runpod_codegen', 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251107-133348_detailed_results.jsonl', '4B', 'Instruct', 'Few-shot', 'H100'),
    ('runpod_codegen', 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251107-133841_detailed_results.jsonl', '4B', 'Thinking', 'Zero-shot', 'H100'),
    ('runpod_codegen', 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-144419_detailed_results.jsonl', '4B', 'Thinking', 'Few-shot', 'H100'),
    # Mars RTX A5000 experiments (mars_codegen)
    ('mars_codegen', 'Sa-zero_Qwen-Qwen3-4B-Instruct-2507_20251106-210549_detailed_results.jsonl', '4B', 'Instruct', 'Zero-shot', 'RTX A5000'),
    ('mars_codegen', 'Sa-few_Qwen-Qwen3-4B-Instruct-2507_20251106-221304_detailed_results.jsonl', '4B', 'Instruct', 'Few-shot', 'RTX A5000'),
    ('mars_codegen', 'Sa-zero_Qwen-Qwen3-4B-Thinking-2507_20251106-210015_detailed_results.jsonl', '4B', 'Thinking', 'Zero-shot', 'RTX A5000'),
    ('mars_codegen', 'Sa-few_Qwen-Qwen3-4B-Thinking-2507_20251107-220000_detailed_results.jsonl', '4B', 'Thinking', 'Few-shot', 'RTX A5000'),
]

results = []

for results_dir_name, filename, model_size, model_type, prompting, platform in files:
    results_dir = base_dir / results_dir_name
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
            'Platform': platform,
            'Model Size': model_size,
            'Model Type': model_type,
            'Prompting': prompting,
            'Avg Tokens': int(avg_tokens),
            'Min Tokens': min_tokens,
            'Max Tokens': max_tokens,
            'Samples': len(token_counts)
        })

        print(f"✅ {platform} {model_size}-{model_type}-{prompting}: {int(avg_tokens)} avg tokens ({len(token_counts)} samples)")
    else:
        print(f"❌ {platform} {model_size}-{model_type}-{prompting}: No data found")

# Print summary table
print("\n" + "="*110)
print("RQ1 CODE GENERATION - AVERAGE OUTPUT TOKENS (BY PLATFORM)")
print("="*110)
print(f"{'Platform':<12} {'Model':<20} {'Prompting':<15} {'Avg Tokens':<12} {'Min':<8} {'Max':<8} {'Samples':<8}")
print("-"*110)

for r in results:
    model = f"{r['Model Size']}-{r['Model Type']}"
    print(f"{r['Platform']:<12} {model:<20} {r['Prompting']:<15} {r['Avg Tokens']:<12} {r['Min Tokens']:<8} {r['Max Tokens']:<8} {r['Samples']:<8}")

print("="*100)
