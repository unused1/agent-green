import pandas as pd
import json
import tiktoken
from pathlib import Path

# Initialize tokenizer for RQ1 code generation token calculation
encoder = tiktoken.get_encoding("cl100k_base")

# File paths
rq1_vuln = '/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results/analysis/vuln_detection_comprehensive_analysis.xlsx'
rq1_code = '/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results/analysis/code_generation_comprehensive_analysis.xlsx'
rq2_vuln = '/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results/analysis/rq2/rq2_vulnerability_detection_analysis.xlsx'
rq2_code = '/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results/analysis/rq2/rq2_code_generation_analysis.xlsx'

# Token counts calculated from JSONL files (RQ1 code generation)
# Key: (platform, model_size, model_type, prompting) -> avg_tokens
RQ1_CODE_TOKENS = {
    # H100 experiments
    ('H100', '30B', 'Instruct', 'Zero-shot'): 230,
    ('H100', '30B', 'Instruct', 'Few-shot'): 231,
    ('H100', '30B', 'Thinking', 'Zero-shot'): 347,
    ('H100', '30B', 'Thinking', 'Few-shot'): 198,
    ('H100', '4B', 'Instruct', 'Zero-shot'): 202,
    ('H100', '4B', 'Instruct', 'Few-shot'): 182,
    ('H100', '4B', 'Thinking', 'Zero-shot'): 196,
    ('H100', '4B', 'Thinking', 'Few-shot'): 193,
    # RTX A5000 experiments (Mars)
    ('RTX A5000', '4B', 'Instruct', 'Zero-shot'): 198,
    ('RTX A5000', '4B', 'Instruct', 'Few-shot'): 178,
    ('RTX A5000', '4B', 'Thinking', 'Zero-shot'): 68,
    ('RTX A5000', '4B', 'Thinking', 'Few-shot'): 67,
}

# Read all data
df_rq1_vuln = pd.read_excel(rq1_vuln, sheet_name='All Experiments')
df_rq1_code = pd.read_excel(rq1_code, sheet_name='All Experiments')
df_rq2_vuln = pd.read_excel(rq2_vuln, sheet_name='All Results')
df_rq2_code = pd.read_excel(rq2_code, sheet_name='All Results')

table_data = []

# ============ RQ1 VULNERABILITY DETECTION ============
for _, row in df_rq1_vuln.iterrows():
    platform = 'RTX A5000' if 'Mars' in row['hardware'] else 'H100'
    table_data.append({
        'Experiment': 'RQ1',
        'Task': 'Vulnerability Detection',
        'Agent Type': 'Single-Agent',
        'Model': f"{row['model_size']} {row['model_type']}",
        'Prompting': row['prompting'],
        'Platform': platform,
        'F1 Score (%)': f"{row['F1_Score_pct']:.2f}",
        'Pass@1 Score (%)': 'N/A',
        'Energy (kWh)': f"{row['energy_consumed_kwh']:.3f}",
        'Avg Tokens': '~5557' if row['model_type'] == 'Thinking' else '~1512'
    })

# ============ RQ1 CODE GENERATION ============
for _, row in df_rq1_code.iterrows():
    platform = 'RTX A5000' if 'Mars' in row['hardware'] else 'H100'
    token_key = (platform, row['model_size'], row['model_type'], row['prompting'])
    avg_tokens = RQ1_CODE_TOKENS.get(token_key, 'Unknown')

    table_data.append({
        'Experiment': 'RQ1',
        'Task': 'Code Generation',
        'Agent Type': 'Single-Agent',
        'Model': f"{row['model_size']} {row['model_type']}",
        'Prompting': row['prompting'],
        'Platform': platform,
        'F1 Score (%)': 'N/A',
        'Pass@1 Score (%)': f"{row['pass_rate_pct']:.2f}",
        'Energy (kWh)': f"{row['energy_consumed_kwh']:.3f}",
        'Avg Tokens': str(avg_tokens)
    })

# ============ RQ2 VULNERABILITY DETECTION ============
for _, row in df_rq2_vuln.iterrows():
    table_data.append({
        'Experiment': 'RQ2',
        'Task': 'Vulnerability Detection',
        'Agent Type': row['agent_type'],
        'Model': f"{row['model_size']} {row['model_type']}",
        'Prompting': row['prompting'],
        'Platform': 'H100',
        'F1 Score (%)': f"{row['f1_score_pct']:.2f}",
        'Pass@1 Score (%)': 'N/A',
        'Energy (kWh)': f"{row['energy_kwh']:.3f}",
        'Avg Tokens': str(int(row['avg_output_tokens']))
    })

# ============ RQ2 CODE GENERATION ============
for _, row in df_rq2_code.iterrows():
    table_data.append({
        'Experiment': 'RQ2',
        'Task': 'Code Generation',
        'Agent Type': row['agent_type'],
        'Model': f"{row['model_size']} {row['model_type']}",
        'Prompting': row['prompting'],
        'Platform': 'H100',
        'F1 Score (%)': 'N/A',
        'Pass@1 Score (%)': f"{row['pass_at_1_pct']:.2f}",
        'Energy (kWh)': f"{row['energy_kwh']:.3f}",
        'Avg Tokens': str(int(row['avg_output_tokens']))
    })

# Create DataFrame
df = pd.DataFrame(table_data)

# Sort by: Experiment (RQ1 first), Task (Vuln first), Agent Type, Model, Prompting
df['Task_Sort'] = df['Task'].map({'Vulnerability Detection': 1, 'Code Generation': 2})
df['Agent_Sort'] = df['Agent Type'].map({'Single-Agent': 1, 'Dual-Agent': 2, 'Multi-Agent': 3})
df = df.sort_values(['Experiment', 'Task_Sort', 'Agent_Sort', 'Model', 'Prompting'])
df = df.drop(columns=['Task_Sort', 'Agent_Sort'])

# Generate markdown table
print("\n## 📊 Complete Cross-Experiment Comparison (RQ1 vs RQ2)\n")
print(f"**Total Experiments**: {len(df)} ({len(df_rq1_vuln) + len(df_rq1_code)} RQ1 + {len(df_rq2_vuln) + len(df_rq2_code)} RQ2)\n")

# Markdown table
print("\n| Exp | Task | Agent Type | Model | Prompting | Platform | F1 (%) | Pass@1 (%) | Energy (kWh) | Avg Tokens |")
print("|-----|------|------------|-------|-----------|----------|--------|------------|--------------|------------|")

for _, row in df.iterrows():
    print(f"| {row['Experiment']} | {row['Task']} | {row['Agent Type']} | {row['Model']} | {row['Prompting']} | {row['Platform']} | {row['F1 Score (%)']} | {row['Pass@1 Score (%)']} | {row['Energy (kWh)']} | {row['Avg Tokens']} |")

print(f"\n**Total Rows**: {len(df)} experiments")
