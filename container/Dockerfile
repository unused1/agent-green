# Agent-Green Vulnerability Detection — Replication Container
# Tag: v1.0-replication
# Base: RunPod PyTorch 2.8.0 (Ubuntu 24.04, CUDA 12.8.1, PyTorch 2.8.0)
# Matches RunPod template: runpod-torch-v280
FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

LABEL replication_tag="v1.0-replication"
LABEL maintainer="Shane Tan"
LABEL description="Agent-Green vulnerability detection replication — RQ1/RQ2/RQ3 on VulTrial-870"

WORKDIR /workspace

# Install experiment dependencies
# hf_transfer first for fast model downloads (per RunPod_Setup_Guide.md)
COPY requirements_runpod.txt .
RUN pip install --no-cache-dir hf_transfer && \
    pip install --no-cache-dir -r requirements_runpod.txt

# Install ollama binary (used when INFERENCE_BACKEND=ollama; serves models on port 11434)
# Models are downloaded on first run; cache with -v /host/path:/root/.ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy selected source files (4 runners + direct/transitive imports + config modules)
COPY src/single_agent_vuln_detection.py \
     src/no_agent_vuln_detection.py \
     src/dual_agent_vuln.py \
     src/multi_agent_vuln_detection_four_agents.py \
     src/agent_utils_vuln.py \
     src/vuln_evaluation.py \
     src/ollama_utils.py \
     src/resume_utils.py \
     src/config.py \
     src/config_nemotron.py \
     ./src/

# Copy datasets (870 primary + 10 smoke-test)
COPY vuln_database/VulTrial_870_samples_balanced.jsonl \
     vuln_database/VulTrial_10_samples_test.jsonl \
     ./vuln_database/

# Copy entrypoint and replication README
COPY container/entrypoint.sh container/REPLICATION_README.md ./
RUN chmod +x entrypoint.sh

# Runtime env
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/src

# Expose vLLM server port (for external inspection if needed)
EXPOSE 8000

ENTRYPOINT ["/workspace/entrypoint.sh"]
