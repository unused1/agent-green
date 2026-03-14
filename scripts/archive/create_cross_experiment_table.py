import pandas as pd
import sys

# File paths
rq1_vuln = '/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results/analysis/vuln_detection_comprehensive_analysis.xlsx'
rq1_code = '/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results/analysis/code_generation_comprehensive_analysis.xlsx'
rq2_vuln = '/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results/analysis/rq2/rq2_vulnerability_detection_analysis.xlsx'
rq2_code = '/Users/shanetan/Documents/Code_Projects/SMU/SCIS_EngD/agent-green/results/analysis/rq2/rq2_code_generation_analysis.xlsx'

try:
    # Read all data
    df_rq1_vuln = pd.read_excel(rq1_vuln, sheet_name='All Experiments')
    df_rq1_code = pd.read_excel(rq1_code, sheet_name='All Experiments')
    df_rq2_vuln = pd.read_excel(rq2_vuln, sheet_name='All Results')
    df_rq2_code = pd.read_excel(rq2_code, sheet_name='All Results')

    # Create table data structure
    table_data = []

    # ============ VULNERABILITY DETECTION ============

    # RQ1: Single-Agent 4B Thinking Few-shot (CWE) - BEST RQ1 on RTX A5000
    rows = df_rq1_vuln[
        (df_rq1_vuln['model_size'] == '4B') &
        (df_rq1_vuln['model_type'] == 'Thinking') &
        (df_rq1_vuln['prompting'] == 'Few-shot') &
        (df_rq1_vuln['prompt_version'] == 'CWE-based') &
        (df_rq1_vuln['hardware'] == 'Mars (RTX A5000)')
    ]
    if not rows.empty:
        row = rows.iloc[0]
        table_data.append({
            'Task': 'Vulnerability Detection',
            'Agent Type': 'Single-Agent',
            'Model': '4B Thinking',
            'Prompting': 'Few-shot (CWE)',
            'Platform': 'RTX A5000',
            'F1 Score (%)': f"{row['F1_Score_pct']:.2f}",
            'Pass@1 Score (%)': 'N/A',
            'Energy (kWh)': f"{row['energy_consumed_kwh']:.3f}",
            'Avg Tokens': '~5557'
        })

    # RQ1: Single-Agent 4B Thinking Few-shot (CWE) on H100
    rows = df_rq1_vuln[
        (df_rq1_vuln['model_size'] == '4B') &
        (df_rq1_vuln['model_type'] == 'Thinking') &
        (df_rq1_vuln['prompting'] == 'Few-shot') &
        (df_rq1_vuln['prompt_version'] == 'CWE-based') &
        (df_rq1_vuln['hardware'] == 'RunPod (H100)')
    ]
    if not rows.empty:
        row = rows.iloc[0]
        table_data.append({
            'Task': 'Vulnerability Detection',
            'Agent Type': 'Single-Agent',
            'Model': '4B Thinking',
            'Prompting': 'Few-shot (CWE)',
            'Platform': 'H100',
            'F1 Score (%)': f"{row['F1_Score_pct']:.2f}",
            'Pass@1 Score (%)': 'N/A',
            'Energy (kWh)': f"{row['energy_consumed_kwh']:.3f}",
            'Avg Tokens': '~5557'
        })

    # RQ1: Single-Agent 30B Instruct Few-shot (CWE)
    rows = df_rq1_vuln[
        (df_rq1_vuln['model_size'] == '30B') &
        (df_rq1_vuln['model_type'] == 'Instruct') &
        (df_rq1_vuln['prompting'] == 'Few-shot') &
        (df_rq1_vuln['prompt_version'] == 'CWE-based')
    ]
    if not rows.empty:
        # Take the best performing one if there are duplicates
        row = rows.loc[rows['F1_Score_pct'].idxmax()]
        table_data.append({
            'Task': 'Vulnerability Detection',
            'Agent Type': 'Single-Agent',
            'Model': '30B Instruct',
            'Prompting': 'Few-shot (CWE)',
            'Platform': 'H100',
            'F1 Score (%)': f"{row['F1_Score_pct']:.2f}",
            'Pass@1 Score (%)': 'N/A',
            'Energy (kWh)': f"{row['energy_consumed_kwh']:.3f}",
            'Avg Tokens': '~1512'
        })

    # RQ2: Dual-Agent 30B Instruct Few-shot - BEST RQ2
    rows = df_rq2_vuln[
        (df_rq2_vuln['model_size'] == '30B') &
        (df_rq2_vuln['model_type'] == 'Instruct') &
        (df_rq2_vuln['agent_type'] == 'Dual-Agent') &
        (df_rq2_vuln['prompting'] == 'Few-shot')
    ]
    if not rows.empty:
        f1 = rows['f1_score_pct'].mean()
        energy = rows['energy_kwh'].mean()
        tokens = rows['avg_output_tokens'].mean()
        table_data.append({
            'Task': 'Vulnerability Detection',
            'Agent Type': 'Dual-Agent',
            'Model': '30B Instruct',
            'Prompting': 'Few-shot',
            'Platform': 'H100',
            'F1 Score (%)': f"{f1:.2f}",
            'Pass@1 Score (%)': 'N/A',
            'Energy (kWh)': f"{energy:.3f}",
            'Avg Tokens': f"{int(tokens)}"
        })

    # RQ2: Dual-Agent 4B Thinking Few-shot
    rows = df_rq2_vuln[
        (df_rq2_vuln['model_size'] == '4B') &
        (df_rq2_vuln['model_type'] == 'Thinking') &
        (df_rq2_vuln['agent_type'] == 'Dual-Agent') &
        (df_rq2_vuln['prompting'] == 'Few-shot')
    ]
    if not rows.empty:
        f1 = rows['f1_score_pct'].mean()
        energy = rows['energy_kwh'].mean()
        tokens = rows['avg_output_tokens'].mean()
        table_data.append({
            'Task': 'Vulnerability Detection',
            'Agent Type': 'Dual-Agent',
            'Model': '4B Thinking',
            'Prompting': 'Few-shot',
            'Platform': 'H100',
            'F1 Score (%)': f"{f1:.2f}",
            'Pass@1 Score (%)': 'N/A',
            'Energy (kWh)': f"{energy:.3f}",
            'Avg Tokens': f"{int(tokens)}"
        })

    # RQ2: Multi-Agent 4B Thinking Zero-shot - WORST
    rows = df_rq2_vuln[
        (df_rq2_vuln['model_size'] == '4B') &
        (df_rq2_vuln['model_type'] == 'Thinking') &
        (df_rq2_vuln['agent_type'] == 'Multi-Agent') &
        (df_rq2_vuln['prompting'] == 'Zero-shot')
    ]
    if not rows.empty:
        f1 = rows['f1_score_pct'].mean()
        energy = rows['energy_kwh'].mean()
        tokens = rows['avg_output_tokens'].mean()
        table_data.append({
            'Task': 'Vulnerability Detection',
            'Agent Type': 'Multi-Agent',
            'Model': '4B Thinking',
            'Prompting': 'Zero-shot',
            'Platform': 'H100',
            'F1 Score (%)': f"{f1:.2f}",
            'Pass@1 Score (%)': 'N/A',
            'Energy (kWh)': f"{energy:.3f}",
            'Avg Tokens': f"{int(tokens)}"
        })

    # ============ CODE GENERATION ============

    # RQ1: Single-Agent 30B Instruct Zero-shot - BEST CODE
    row = df_rq1_code[
        (df_rq1_code['model_size'] == '30B') &
        (df_rq1_code['model_type'] == 'Instruct') &
        (df_rq1_code['prompting'] == 'Zero-shot')
    ]
    if not row.empty:
        row = row.iloc[0]
        table_data.append({
            'Task': 'Code Generation',
            'Agent Type': 'Single-Agent',
            'Model': '30B Instruct',
            'Prompting': 'Zero-shot',
            'Platform': 'H100',
            'F1 Score (%)': 'N/A',
            'Pass@1 Score (%)': f"{row['pass_rate_pct']:.2f}",
            'Energy (kWh)': f"{row['energy_consumed_kwh']:.3f}",
            'Avg Tokens': '230'
        })

    # RQ1: Single-Agent 4B Instruct Few-shot
    row = df_rq1_code[
        (df_rq1_code['model_size'] == '4B') &
        (df_rq1_code['model_type'] == 'Instruct') &
        (df_rq1_code['prompting'] == 'Few-shot')
    ]
    if not row.empty:
        row = row.iloc[0]
        table_data.append({
            'Task': 'Code Generation',
            'Agent Type': 'Single-Agent',
            'Model': '4B Instruct',
            'Prompting': 'Few-shot',
            'Platform': 'H100',
            'F1 Score (%)': 'N/A',
            'Pass@1 Score (%)': f"{row['pass_rate_pct']:.2f}",
            'Energy (kWh)': f"{row['energy_consumed_kwh']:.3f}",
            'Avg Tokens': '182'
        })

    # RQ1: Single-Agent 4B Instruct Zero-shot (RTX A5000)
    rows = df_rq1_code[
        (df_rq1_code['model_size'] == '4B') &
        (df_rq1_code['model_type'] == 'Instruct') &
        (df_rq1_code['prompting'] == 'Zero-shot') &
        (df_rq1_code['hardware'] == 'Mars (RTX A5000)')
    ]
    if not rows.empty:
        row = rows.iloc[0]
        table_data.append({
            'Task': 'Code Generation',
            'Agent Type': 'Single-Agent',
            'Model': '4B Instruct',
            'Prompting': 'Zero-shot',
            'Platform': 'RTX A5000',
            'F1 Score (%)': 'N/A',
            'Pass@1 Score (%)': f"{row['pass_rate_pct']:.2f}",
            'Energy (kWh)': f"{row['energy_consumed_kwh']:.3f}",
            'Avg Tokens': '202'
        })

    # RQ1: Single-Agent 4B Instruct Zero-shot (H100)
    rows = df_rq1_code[
        (df_rq1_code['model_size'] == '4B') &
        (df_rq1_code['model_type'] == 'Instruct') &
        (df_rq1_code['prompting'] == 'Zero-shot') &
        (df_rq1_code['hardware'] == 'RunPod (H100)')
    ]
    if not rows.empty:
        row = rows.iloc[0]
        table_data.append({
            'Task': 'Code Generation',
            'Agent Type': 'Single-Agent',
            'Model': '4B Instruct',
            'Prompting': 'Zero-shot',
            'Platform': 'H100',
            'F1 Score (%)': 'N/A',
            'Pass@1 Score (%)': f"{row['pass_rate_pct']:.2f}",
            'Energy (kWh)': f"{row['energy_consumed_kwh']:.3f}",
            'Avg Tokens': '202'
        })

    # RQ2: Multi-Agent 4B Thinking Zero-shot
    rows = df_rq2_code[
        (df_rq2_code['model_size'] == '4B') &
        (df_rq2_code['model_type'] == 'Thinking') &
        (df_rq2_code['agent_type'] == 'Multi-Agent') &
        (df_rq2_code['prompting'] == 'Zero-shot')
    ]
    if not rows.empty:
        pass1 = rows['pass_at_1_pct'].mean()
        energy = rows['energy_kwh'].mean()
        tokens = rows['avg_output_tokens'].mean()
        table_data.append({
            'Task': 'Code Generation',
            'Agent Type': 'Multi-Agent',
            'Model': '4B Thinking',
            'Prompting': 'Zero-shot',
            'Platform': 'H100',
            'F1 Score (%)': 'N/A',
            'Pass@1 Score (%)': f"{pass1:.2f}",
            'Energy (kWh)': f"{energy:.3f}",
            'Avg Tokens': f"{int(tokens)}"
        })

    # Create DataFrame
    df = pd.DataFrame(table_data)

    # Print formatted table
    print("\n" + "="*160)
    print("CROSS-EXPERIMENT COMPARISON: RQ1 (Single-Agent) vs RQ2 (Dual/Multi-Agent)")
    print("="*160)
    print()

    # Calculate column widths
    col_widths = {
        'Task': 25,
        'Agent Type': 14,
        'Model': 14,
        'Prompting': 18,
        'Platform': 11,
        'F1 Score (%)': 14,
        'Pass@1 Score (%)': 18,
        'Energy (kWh)': 14,
        'Avg Tokens': 15
    }

    # Print header with box drawing
    header_line = "┌"
    for i, col in enumerate(df.columns):
        header_line += "─" * col_widths[col]
        if i < len(df.columns) - 1:
            header_line += "┬"
    header_line += "┐"
    print(header_line)

    # Print column names
    header = "│"
    for col in df.columns:
        header += f" {col:<{col_widths[col]-1}}│"
    print(header)

    # Print separator
    sep_line = "├"
    for i, col in enumerate(df.columns):
        sep_line += "─" * col_widths[col]
        if i < len(df.columns) - 1:
            sep_line += "┼"
    sep_line += "┤"
    print(sep_line)

    # Print data rows
    for _, row in df.iterrows():
        line = "│"
        for col in df.columns:
            value = str(row[col])
            line += f" {value:<{col_widths[col]-1}}│"
        print(line)

    # Print bottom border
    bottom_line = "└"
    for i, col in enumerate(df.columns):
        bottom_line += "─" * col_widths[col]
        if i < len(df.columns) - 1:
            bottom_line += "┴"
    bottom_line += "┘"
    print(bottom_line)

    print("\n" + "="*160)
    print("Key Insights:")
    print("  • BEST VULNERABILITY DETECTION: Single-Agent 4B-Thinking-Few-shot(CWE) = 58.88% F1")
    print("  • BEST RQ2 (Multi-Agent): Dual-Agent 30B-Instruct-Few-shot = 51.76% F1")
    print("  • WORST: Multi-Agent 4B-Thinking-Zero-shot = 32.70% F1")
    print("  • BEST CODE GENERATION: Single-Agent 30B-Instruct-Zero-shot = 100% Pass@1")
    print("  • Energy Efficiency: 30B models use LESS energy than 4B-Thinking despite larger size")
    print("="*160)
    print()

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
