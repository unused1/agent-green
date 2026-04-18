# Agent-Green Replication Container (v1.0-replication)

This container packages the Agent-Green vulnerability detection pipeline for consistent replication of RQ1/RQ2/RQ3 experiments on the VulTrial-870 dataset, across all 64 configurations in the ASE 2026 paper.

## Contents

- Base image: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` (Ubuntu 24.04, CUDA 12.8.1, PyTorch 2.8.0)
- 4 vulnerability-detection runners (NA, SA, DA, MA) — patched to support deterministic `EXP_NAME` for auto-resume
- vLLM server (OpenAI-compatible API) embedded and started per invocation
- CodeCarbon offline emissions tracker
- VulTrial-870 dataset + 10-sample smoke-test dataset
- Deterministic seed-based results layout for 3-run replication

## Quick Start

### 1. Load the image

```bash
# On a RunPod H100 pod (or any host with NVIDIA GPUs + nvidia-container-toolkit):
gunzip -c agent-green-v1.0-replication.tar.gz | docker load
docker images agent-green
```

### 2. Run a smoke test (optional but recommended)

Verifies the full pipeline with 10 samples (~5 minutes):

```bash
docker run --rm --gpus all \
  --user $(id -u):$(id -g) \
  -v $(pwd)/results:/workspace/results \
  -e DESIGN=SA -e MODE=instruct -e MODEL=qwen3-4b \
  -e PROMPTING=zero -e SEED=1 -e SMOKE_TEST=1 \
  -e HF_TOKEN="$HF_TOKEN" \
  --name huabengtan_smoke \
  agent-green:v1.0-replication
```

### 3. Run a single replication config

```bash
docker run --rm --gpus all \
  --user $(id -u):$(id -g) \
  -v $(pwd)/results:/workspace/results \
  -e DESIGN=SA -e MODE=thinking -e MODEL=qwen3-4b \
  -e PROMPTING=zero -e SEED=1 \
  -e HF_TOKEN="$HF_TOKEN" \
  --name huabengtan_SA_thinking_qwen3-4b_zero_seed1 \
  agent-green:v1.0-replication
```

Results are written to `./results/run1/SA_thinking_qwen3-4b_zero/`.

### 4. Run all 3 replication seeds for a config

```bash
for SEED in 1 2 3; do
  docker run --rm --gpus all \
    --user $(id -u):$(id -g) \
    -v $(pwd)/results:/workspace/results \
    -e DESIGN=SA -e MODE=thinking -e MODEL=qwen3-4b \
    -e PROMPTING=zero -e SEED=$SEED \
    -e HF_TOKEN="$HF_TOKEN" \
    --name huabengtan_SA_thinking_qwen3-4b_zero_seed${SEED} \
    agent-green:v1.0-replication
done
```

## Environment Variables

### Required

| Var | Values | Description |
|-----|--------|-------------|
| `DESIGN` | `NA`, `SA`, `DA`, `MA` | Experimental design |
| `MODE` | `instruct`, `thinking` | Reasoning mode |
| `MODEL` | `qwen3-4b`, `qwen3-30b`, `nemotron-nano-8b`, `nemotron-super-49b` | Model variant |
| `PROMPTING` | `zero`, `few` | Prompt strategy |

### Optional

| Var | Default | Description |
|-----|---------|-------------|
| `SEED` | `1` | Replication seed (1, 2, 3 for 3 runs) |
| `SMOKE_TEST` | `0` | Set to `1` to use 10-sample dataset |
| `HF_TOKEN` | *(none)* | HuggingFace token; required for Nemotron (gated) |
| `MAX_MODEL_LEN` | `65536` | vLLM max context length |
| `GPU_MEM_UTIL` | `0.9` | vLLM GPU memory utilization fraction |
| `VLLM_READY_TIMEOUT` | `900` | Seconds to wait for vLLM startup (15 min default) |
| `RESULTS_DIR` | `/workspace/results` | Base directory inside container for outputs |

## GPU Requirements

| Model | GPUs | Notes |
|-------|------|-------|
| `qwen3-4b` | 1× H100 80GB | Any single H100 |
| `qwen3-30b` | 1× H100 80GB | Fits in a single H100 |
| `nemotron-nano-8b` | 1× H100 80GB | Gated — requires `HF_TOKEN` |
| `nemotron-super-49b` | 2× H100 80GB | Tensor parallel (TP=2); gated model |

For multi-GPU runs (Nemotron-Super-49B), ensure `--gpus all` on a 2× H100 pod.

## Decoding: Deterministic (temp=0)

All runs use greedy decoding (temperature=0). With fixed `MODEL` + `MODE` + `PROMPTING`, outputs are deterministic across replication seeds. Variance across 3 runs measures **infrastructure stability** (wall-clock time, CodeCarbon emissions sampling, memory footprint) — not model output variance.

## Auto-Resume on Crash / Interruption

The runners use a deterministic `EXP_NAME` derived from `DESIGN / MODE / MODEL / PROMPTING / SEED`. If a container run crashes or is interrupted:

1. The partial results file on the host volume is preserved.
2. Re-run **the exact same `docker run` command**.
3. The runner detects existing results and resumes from the next unprocessed sample.

No special `--resume` flag needed — the deterministic exp_name makes it automatic.

## Results Layout

```
results/
├── run1/
│   ├── SA_thinking_qwen3-4b_zero/
│   │   ├── SA-vuln-zero_shot_Qwen__Qwen3-4B-Thinking-2507_seed1_detailed_results.jsonl
│   │   ├── SA-vuln-zero_shot_Qwen__Qwen3-4B-Thinking-2507_seed1_energy_tracking.json
│   │   ├── emissions.csv
│   │   └── *_metrics.csv
│   └── ...
├── run2/
│   └── ...
└── run3/
    └── ...
```

Each config × seed produces its own directory; analysis scripts can compare across seeds.

## File Ownership: `--user $(id -u):$(id -g)`

All `docker run` examples above use `--user $(id -u):$(id -g)`. Without this flag, the container runs as root (UID 0) and writes output files to the bind-mounted `results/` directory with root ownership on the host — making them undeletable by your normal user account without `sudo`.

The flag maps the container's user/group to your host UID/GID so output files belong to you.

**If you already have root-owned files from an earlier run** and cannot delete them:

```bash
docker run --rm -v $(pwd)/results:/r --entrypoint /bin/sh alpine -c 'rm -rf /r/*'
```

## Container Resource Limits (Optional)

Resource limits are NOT enforced by default. For shared-server deployments (e.g., DGX H100 per admin guidelines), pass limits explicitly:

```bash
# Small models (Qwen3-4B, Qwen3-30B, Nemotron-Nano-8B):
docker run --cpus=16 --memory=64g --shm-size=8g ...

# Nemotron-Super-49B (TP=2):
docker run --cpus=32 --memory=128g --shm-size=16g ...
```

On Mars (A5000 server) and RunPod, defaults are fine — no limits needed.

## Debugging / Interactive Shell

### Override the entrypoint for exploration:

```bash
docker run -it --rm --gpus all \
  --user $(id -u):$(id -g) \
  -v $(pwd)/results:/workspace/results \
  --entrypoint /bin/bash \
  agent-green:v1.0-replication
# Inside container:
# - Inspect /workspace/src/ to review runners
# - Cat /workspace/entrypoint.sh to see dispatch logic
# - Run python -c "import vllm; print(vllm.__version__)" etc.
```

### Attach to a running container:

```bash
docker run -d --gpus all \
  --user $(id -u):$(id -g) \
  -v $(pwd)/results:/workspace/results \
  -e DESIGN=SA -e MODE=instruct -e MODEL=qwen3-4b -e PROMPTING=zero \
  --name huabengtan_longrun \
  agent-green:v1.0-replication

docker exec -it huabengtan_longrun /bin/bash   # in another terminal
docker logs -f huabengtan_longrun              # follow runner output
```

## Known Limitations

- vLLM restarts for each `docker run` invocation (~2-5 min overhead for model load). Plan per-config overhead accordingly when budgeting runs.
- Only VulTrial-870 is included. RQ3 LLM-as-judge evaluation is API-based (Claude Opus) and runs separately on the host — not part of this container.
- Nemotron models are gated on HuggingFace — team members must have their own `HF_TOKEN` with access.
- Driver requirement: NVIDIA driver ≥ 550.54.14 for CUDA 12.8 support. RunPod H100 pods meet this; older on-prem servers (e.g., driver 535) will fail at inference time.

## Troubleshooting

### "vLLM process died during startup"

- Check `docker logs <container>` for the vLLM log tail.
- Most common cause: insufficient GPU memory. Try reducing `GPU_MEM_UTIL` (e.g., `0.85`) or `MAX_MODEL_LEN` (e.g., `32768`).
- For Nemotron-Super-49B: ensure 2× H100 are visible (`nvidia-smi` inside container).

### "HuggingFace model access denied"

- Nemotron models require Meta's and NVIDIA's license acceptance on the HuggingFace model page.
- Pass `HF_TOKEN` to the container (`-e HF_TOKEN="hf_..."`).

### Container exits immediately

- Verify required env vars are set: `DESIGN`, `MODE`, `MODEL`, `PROMPTING`.
- Check `docker logs <container>` for the `[ERROR]` message.

## Image Provenance

- Built from repository `agent-green` at git tag `v1.0-replication`
- See `/workspace/src/` inside the container for the exact Python source shipped
- Dataset: `/workspace/vuln_database/VulTrial_870_samples_balanced.jsonl` (870 samples, 435 PrimeVul pairs)
