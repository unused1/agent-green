#!/usr/bin/env python3
"""
Test script to verify Agent Green setup
"""

import os
import sys
import subprocess

def check_python():
    """Check Python version"""
    print(f"✓ Python {sys.version}")
    return True

def check_ollama():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Ollama installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("✗ Ollama not found. Install from: https://ollama.com")
        return False

def check_model():
    """Check if required model is available"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if 'qwen2.5-coder:7b-instruct' in result.stdout:
            print("✓ Model qwen2.5-coder:7b-instruct is available")
            return True
        else:
            print("✗ Model qwen2.5-coder:7b-instruct not found")
            print("  Run: ollama pull qwen2.5-coder:7b-instruct")
            return False
    except:
        return False

def check_imports():
    """Check if required packages can be imported"""
    packages = ['ag2', 'codecarbon', 'ollama', 'pandas', 'numpy', 'logparser3']
    success = True
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✓ {pkg} imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import {pkg}: {e}")
            success = False
    return success

def check_directories():
    """Check if required directories exist"""
    from src import config
    dirs = {
        'LOG_DIR': config.LOG_DIR,
        'RESULT_DIR': config.RESULT_DIR,
        'DATA_DIR': config.DATA_DIR,
    }

    for name, path in dirs.items():
        if os.path.exists(path):
            print(f"✓ {name}: {path}")
        else:
            print(f"✗ {name} not found: {path}")
            os.makedirs(path, exist_ok=True)
            print(f"  Created: {path}")
    return True

def check_log_files():
    """Check if sample log files exist"""
    from src import config
    log_files = [
        'HDFS_200_sampled.log',
        'HDFS_200_sampled_log_structured.csv',
        'ground_truth_corrected_by_Khan2022.txt'
    ]

    for file in log_files:
        path = os.path.join(config.LOG_DIR, file)
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024  # KB
            print(f"✓ {file} ({size:.1f} KB)")
        else:
            print(f"✗ {file} not found")
    return True

def main():
    print("=" * 50)
    print("Agent Green Setup Verification")
    print("=" * 50)

    print("\n1. Python Environment:")
    check_python()

    print("\n2. Ollama Setup:")
    ollama_ok = check_ollama()
    if ollama_ok:
        check_model()

    print("\n3. Python Packages:")
    check_imports()

    print("\n4. Directory Structure:")
    check_directories()

    print("\n5. Log Files:")
    check_log_files()

    print("\n" + "=" * 50)
    print("Setup verification complete!")
    print("\nNext steps:")
    print("1. If Ollama is not installed: brew install ollama")
    print("2. Start Ollama: ollama serve")
    print("3. Pull model: ollama pull qwen2.5-coder:7b-instruct")
    print("4. Run experiments: jupyter notebook src/no_agents.ipynb")
    print("=" * 50)

if __name__ == "__main__":
    main()