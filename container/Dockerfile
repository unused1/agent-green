# Agent-Green Vulnerability Detection — Replication Container
# Tag: v1.1-replication
# Base: RunPod PyTorch 2.8.0 (Ubuntu 24.04, CUDA 12.8.1, PyTorch 2.8.0)
FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

LABEL replication_tag="v1.1-replication"
LABEL maintainer="Shane Tan"
LABEL description="Agent-Green vulnerability detection replication — RQ1/RQ2/RQ3 on VulTrial-870"

WORKDIR /workspace

# Step 1: Uninstall base image's torch 2.8.0. vllm 0.17.x requires torch==2.10.0;
# leaving both installed creates 2.8/2.10 module confusion that triggers
# "duplicate template name" AssertionError in torch._inductor during model inspection.
RUN pip uninstall -y torch torchvision torchaudio 2>/dev/null || true

# Step 2: Upgrade cryptography (base image's dpkg version lacks pip RECORD file).
# Narrow --ignore-installed scope avoids other accidental reinstalls.
RUN pip install --no-cache-dir --ignore-installed cryptography

# Step 3: Install everything else. pip will resolve torch==2.10.0 from vllm's deps.
COPY requirements_runpod.txt .
RUN pip install --no-cache-dir hf_transfer && \
    pip install --no-cache-dir -r requirements_runpod.txt

# Install ollama binary (used when INFERENCE_BACKEND=ollama)
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy selected source files
COPY src/single_agent_vuln_detection.py \
     src/no_agent_vuln_detection.py \
     src/dual_agent_vuln.py \
     src/multi_agent_vuln_detection_four_agents.py \
     src/agent_utils_vuln.py \
     src/vuln_parser.py \
     src/vuln_evaluation.py \
     src/ollama_utils.py \
     src/resume_utils.py \
     src/config.py \
     src/config_nemotron.py \
     ./src/

COPY vuln_database/VulTrial_870_samples_balanced.jsonl \
     vuln_database/VulTrial_10_samples_test.jsonl \
     ./vuln_database/

COPY container/entrypoint.sh container/REPLICATION_README.md ./
RUN chmod +x entrypoint.sh

ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/src
ENV HF_HOME=/tmp/hf_cache
ENV XDG_CACHE_HOME=/tmp/xdg_cache
ENV OLLAMA_MODELS=/tmp/ollama_models
ENV PIP_CACHE_DIR=/tmp/pip_cache
ENV UV_CACHE_DIR=/tmp/uv_cache
ENV VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv
# flashinfer (vllm dep) spawns subprocesses that may not inherit HOME; point its
# workspace explicitly so os.makedirs doesn't fall back to "/.cache".
ENV FLASHINFER_WORKSPACE_BASE=/tmp
ENV HOME=/tmp
ENV TORCHINDUCTOR_CACHE_DIR=/tmp/torchinductor

EXPOSE 8000
ENTRYPOINT ["/workspace/entrypoint.sh"]
