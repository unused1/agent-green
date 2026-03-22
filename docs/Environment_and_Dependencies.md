# Environment and Dependencies

**Purpose**: Document the software and hardware environment used for all experiments to ensure reproducibility.
**Last Updated**: March 21, 2026

---

## 1. Experiment Execution Environment (RunPod)

All LLM experiments are executed on RunPod cloud GPU instances.

### 1.1 Operating System

| Component | Version |
|-----------|---------|
| OS | Ubuntu 24.04.3 LTS (Noble Numbat) |
| Kernel | Linux (RunPod managed) |

### 1.2 Python Environment

| Component | Version |
|-----------|---------|
| Python | 3.12.3 |
| pip | Latest (managed by RunPod) |

### 1.3 CUDA / GPU Stack

| Component | Version (Phase 5-8, Dec 2025) | Version (Phase 9, Mar 2026) |
|-----------|-------------------------------|------------------------------|
| NVIDIA Driver | 570.195.03 | 580.126.09 |
| CUDA | 12.8 | 12.8 |

### 1.4 Hardware Configurations

#### Nemotron-Nano-8B (Single GPU)
| Component | Specification |
|-----------|---------------|
| GPU | 1x NVIDIA H100 80GB HBM3 |
| GPU Memory | 81,559 MiB |
| Tensor Parallelism | N/A (single GPU) |

#### Nemotron-Super-49B (Multi-GPU)
| Component | Specification |
|-----------|---------------|
| GPU | 2x NVIDIA H100 80GB HBM3 SXM |
| GPU Memory | 81,559 MiB per GPU |
| Tensor Parallelism | 2 |
| Inter-GPU Connection | NVLink |

### 1.5 Key Python Packages (RunPod)

| Package | Version (Phase 5-8, Dec 2025) | Version (Phase 9 B1-B6, Mar 17-20) | Version (Phase 9 B7-B8 NA, Mar 21+) | Purpose |
|---------|-------------------------------|--------------------------------------|---------------------------------------|---------|
| vllm | 0.13.0 | 0.17.1 | 0.18.0 | LLM inference server |
| ag2 (autogen) | 0.10.3 | 0.11.4 | 0.11.4 | Multi-agent framework |
| openai | 2.14.0 | 2.24.0 | 2.24.0+ | OpenAI-compatible API client |
| codecarbon | 2.7.1 | 3.2.3 | 3.2.3 | Energy/emissions tracking |
| torch | — | 2.10.0 | 2.10.0+ | PyTorch (vLLM dependency) |

**Note**: NA experiments (Batch 7-8) on newly created pods may use vllm 0.18.0 (latest pip release as of Mar 21, 2026). Pods created earlier (B1-B6) use vllm 0.17.1. Both versions use the same OpenAI-compatible API and model parameters. NA experiments do not use the AutoGen agent framework, so the autogen version is irrelevant for NA runs.

---

## 2. Local Development Environment

Local machine is used for analysis, visualization, and experiment orchestration.

### 2.1 System Information

| Component | Specification |
|-----------|---------------|
| OS | macOS Darwin 25.1.0 |
| Python | 3.9.6 |

### 2.2 Key Python Packages (Local)

| Package | Version | Purpose |
|---------|---------|---------|
| ag2 (autogen) | 0.7.5 | Multi-agent framework |
| openai | 1.97.0 | API client |
| codecarbon | 3.0.4 | Emissions analysis |
| pandas | 2.2.3 | Data analysis |
| scikit-learn | 1.6.1 | ML metrics |
| matplotlib | 3.10.3 | Visualization |
| seaborn | 0.13.2 | Statistical visualization |

---

## 3. Mars Server Environment (Historical - Qwen3 Experiments)

The Mars server was used for initial Qwen3 experiments (RQ1, RQ2).

### 3.1 System Information

| Component | Specification |
|-----------|---------------|
| OS | Ubuntu 24.04.1 LTS |
| CUDA | 12.4 |
| Driver | 550.90.07 |

### 3.2 Hardware

| Component | Specification |
|-----------|---------------|
| GPU | 4x NVIDIA RTX A5000 (24GB VRAM each) |
| Total VRAM | 96GB |

---

## 4. Models Used

### 4.1 Primary Models (Qwen3 - RQ1/RQ2)

| Model | Parameters | Architecture | Thinking Toggle |
|-------|------------|--------------|-----------------|
| Qwen/Qwen3-4B-Instruct-2507 | 4B | Dense | N/A (Instruct only) |
| Qwen/Qwen3-4B-Thinking-2507 | 4B | Dense | Built-in (Thinking model) |
| Qwen/Qwen3-30B-A3B-Instruct-2507 | 30B (3B active) | MoE | N/A (Instruct only) |
| Qwen/Qwen3-30B-A3B-Thinking-2507 | 30B (3B active) | MoE | Built-in (Thinking model) |

### 4.2 Cross-Architecture Validation Models (Nemotron)

| Model | Parameters | Architecture | Thinking Toggle | Hardware Required |
|-------|------------|--------------|-----------------|-------------------|
| nvidia/Llama-3.1-Nemotron-Nano-8B-v1 | 8B | Dense (Llama-based) | System prompt: `detailed thinking on/off` | 1x H100 80GB |
| nvidia/Llama-3_3-Nemotron-Super-49B-v1_5 | 49B | Dense (Llama-based) | System prompt: `detailed thinking on/off` | 2x H100 80GB |

---

## 5. vLLM Server Configuration

### 5.1 Nemotron-Nano-8B

```bash
python3 -m vllm.entrypoints.openai.api_server \
    --model "nvidia/Llama-3.1-Nemotron-Nano-8B-v1" \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.90 \
    --enforce-eager
```

### 5.2 Nemotron-Super-49B (FP16)

```bash
python3 -m vllm.entrypoints.openai.api_server \
    --model "nvidia/Llama-3_3-Nemotron-Super-49B-v1_5" \
    --trust-remote-code \
    --tensor-parallel-size=2 \
    --max-model-len=65536 \
    --gpu-memory-utilization 0.90 \
    --dtype float16
```

---

## 6. Complete Python Dependencies

The full list of Python dependencies is maintained in `requirements.txt` at the project root.

### 6.1 Core Dependencies

```
ag2==0.7.2                    # Multi-agent framework (alias: autogen, pyautogen)
openai==1.60.1                # OpenAI API client
codecarbon==3.0.1             # Carbon emissions tracking
pandas==2.2.3                 # Data manipulation
numpy==2.2.0                  # Numerical computing
scikit-learn==1.6.1           # ML metrics and evaluation
matplotlib==3.10.3            # Visualization
seaborn==0.13.2               # Statistical visualization
python-dotenv==1.0.1          # Environment variable management
```

### 6.2 vLLM (RunPod Only)

```
vllm==0.13.0                  # LLM inference server
```

Note: vLLM is installed on RunPod instances only, not in local development environment.

---

## 7. Datasets

| Dataset | Samples | Task | Source |
|---------|---------|------|--------|
| HumanEval | 164 | Code Generation | OpenAI |
| VulTrial-386 | 386 (384 unique) | Vulnerability Detection | Custom balanced dataset |
| VulTrial-486 | 486 (386 + 100 incremental) | Vulnerability Detection (Phase 8) | Expanded from VulTrial-870 pool |
| VulTrial-870 | 870 (486 + 384 incremental) | Vulnerability Detection (Phase 9) | Full PrimeVul balanced dataset |
| VulTrial-384-incremental | 384 (192 vuln + 192 safe) | Phase 9 incremental runs | Set difference: 870 - 486 |
| HDFS Log Sessions | 385 | Log Analysis | Sampled from HDFS_2k |

---

## 8. Energy Tracking Configuration

CodeCarbon is configured with the following settings:

```python
tracker = OfflineEmissionsTracker(
    project_name="agent-green",
    country_iso_code="CAN",      # Canada grid carbon intensity
    save_to_file=True,
)
```

---

## 9. Version Control

| Tool | Version |
|------|---------|
| Git | 2.x |
| Repository | https://github.com/unused1/agent-green |
| Branch (Cross-Architecture) | rq3-explainability |

---

## 10. Notes on Reproducibility

1. **Package Version Pinning**: All Python packages are pinned to specific versions in `requirements.txt` to ensure reproducibility.

2. **RunPod Environment**: RunPod images may be updated. The versions documented here are as of December 2025.

3. **vLLM Context Length**: All experiments use 64K context (`--max-model-len 65536`) for fair comparison across models and configurations.

4. **Thinking Toggle**: Nemotron models use system prompt prefixes (`detailed thinking on` / `detailed thinking off`) rather than API parameters.

5. **Random Seeds**: Experiments use `temperature=0` for deterministic outputs where possible. AutoGen's `cache_seed=None` disables response caching.
