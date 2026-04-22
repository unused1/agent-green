# Agent-Green Replication Container (v1.1-replication)

This container packages the Agent-Green vulnerability detection pipeline for consistent replication of RQ1/RQ2/RQ3 experiments on the VulTrial-870 dataset, across all 64 configurations in the ASE 2026 paper.

## Contents

- Base image: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` (Ubuntu 24.04, CUDA 12.8.1, PyTorch 2.8.0)
- 4 vulnerability-detection runners (NA, SA, DA, MA) — patched to support deterministic `EXP_NAME` for auto-resume
- Two inference backends, selectable per-run:
  - **vLLM** (default) — OpenAI-compatible server at localhost:8000, full-precision weights
  - **Ollama** — Ollama server at localhost:11434, serves GGUF-format (typically quantized) models
- AG2 (autogen) ≥ 0.10.0
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

### Optional (shared)

| Var | Default | Description |
|-----|---------|-------------|
| `SEED` | `1` | Replication seed (1, 2, 3 for 3 runs) |
| `SMOKE_TEST` | `0` | Set to `1` to use 10-sample dataset |
| `HF_TOKEN` | *(none)* | HuggingFace token; required for Nemotron (gated) |
| `RESULTS_DIR` | `/workspace/results` | Base directory inside container for outputs |
| `INFERENCE_BACKEND` | `vllm` | `vllm` (default) or `ollama`. See *Inference Backend* section below. |

### Backend-specific (vLLM)

| Var | Default | Description |
|-----|---------|-------------|
| `VLLM_DTYPE` | `auto` | Precision: `auto` (from model config — bf16 for Qwen3/Nemotron), `float16`, `bfloat16`, `float32` |
| `MAX_MODEL_LEN` | `65536` | vLLM max context length |
| `GPU_MEM_UTIL` | `0.9` | vLLM GPU memory utilization fraction |
| `VLLM_READY_TIMEOUT` | `900` | Seconds to wait for vLLM startup (15 min default) |

### Backend-specific (Ollama)

| Var | Default | Description |
|-----|---------|-------------|
| `OLLAMA_MODEL` | *(required)* | Full ollama model tag, e.g., `qwen3:4b`, `qwen3:4b-instruct-q8_0`. Precision is implied by the tag. |
| `OLLAMA_NUM_CTX` | `65536` | Ollama context window (passed via config.py) |
| `OLLAMA_READY_TIMEOUT` | `1800` | Seconds to wait for ollama startup + first model pull (30 min default) |

## GPU Requirements

| Model | GPUs | Notes |
|-------|------|-------|
| `qwen3-4b` | 1× H100 80GB | Any single H100 |
| `qwen3-30b` | 1× H100 80GB | Fits in a single H100 |
| `nemotron-nano-8b` | 1× H100 80GB | Gated — requires `HF_TOKEN` |
| `nemotron-super-49b` | 2× H100 80GB | Tensor parallel (TP=2); gated model |

For multi-GPU runs (Nemotron-Super-49B), ensure `--gpus all` on a 2× H100 pod.

## Inference Backend: vLLM vs Ollama

Set `INFERENCE_BACKEND=vllm` (default) or `INFERENCE_BACKEND=ollama`.

### vLLM (default)

Loads HuggingFace safetensors weights and serves an OpenAI-compatible API. `VLLM_DTYPE=auto` picks up the checkpoint's native precision — **bf16 for Qwen3 and Nemotron**, matching the ASE 2026 paper experiments.

```bash
docker run --rm --gpus all \
  --user $(id -u):$(id -g) \
  -v $(pwd)/results:/workspace/results \
  -e INFERENCE_BACKEND=vllm \
  -e DESIGN=SA -e MODE=instruct -e MODEL=qwen3-4b \
  -e PROMPTING=zero -e SEED=1 \
  -e HF_TOKEN="$HF_TOKEN" \
  --name huabengtan_vllm_run \
  agent-green:v1.1-replication
```

### Ollama

Loads GGUF-format (typically quantized) weights and serves the Ollama API. The team member specifies the exact ollama model tag — including precision — via `OLLAMA_MODEL`.

**The ollama model cache is required to persist across container invocations** — without it, every run re-downloads the model. Mount a host directory to `/root/.ollama`:

```bash
mkdir -p ollama_cache results

docker run --rm --gpus all \
  --user $(id -u):$(id -g) \
  -v $(pwd)/results:/workspace/results \
  -v $(pwd)/ollama_cache:/root/.ollama \
  -e INFERENCE_BACKEND=ollama \
  -e DESIGN=SA -e MODE=instruct -e MODEL=qwen3-4b \
  -e PROMPTING=zero -e SEED=1 \
  -e OLLAMA_MODEL=qwen3:4b \
  --name huabengtan_ollama_run \
  agent-green:v1.1-replication
```

Note: because the ollama model cache directory is also written by the root user inside the container, use the `--user` flag consistently; the first run creates the cache with your UID.

### Precision / Quantization

- **vLLM default** (`VLLM_DTYPE=auto`) loads model weights at the checkpoint's native precision — **bf16** for Qwen3 and Nemotron. This matches the ASE 2026 paper experiments.
- **Ollama precision** is determined entirely by the **model tag** specified via `OLLAMA_MODEL`. The default tags on the ollama library (e.g., `qwen3:4b`) are typically **4-bit quantized (Q4_K_M)**. Team members should pick explicit precision tags (e.g., `...-q8_0`, `...-fp16`, `...-bf16`) if matched precision is required for a fair vLLM-vs-ollama comparison.
- An out-of-the-box `vllm` vs `ollama` run with default settings measures **both backend and precision effects simultaneously**. Interpret results accordingly.
- Nemotron-Super-49B is **not** in the official ollama library at the time of writing; running it on the ollama backend would require a custom `ollama create` with a local GGUF file (not provided by this container).

### Results Layout (backend-differentiated)

Results directories include the backend name so vLLM and ollama runs don't overwrite each other:

```
results/
├── run1/
│   ├── vllm_SA_instruct_qwen3-4b_zero/
│   └── ollama_SA_instruct_qwen3-4b_zero/
├── run2/
│   └── ...
└── run3/
    └── ...
```

## Decoding: Deterministic (temp=0)

All runs use greedy decoding (temperature=0). With fixed `MODEL` + `MODE` + `PROMPTING`, outputs are deterministic across replication seeds. Variance across 3 runs measures **infrastructure stability** (wall-clock time, CodeCarbon emissions sampling, memory footprint) — not model output variance.

## Auto-Resume on Crash / Interruption

The runners use a deterministic `EXP_NAME` derived from `DESIGN / MODE / MODEL / PROMPTING / SEED`. If a container run crashes or is interrupted:

1. The partial results file on the host volume is preserved.
2. Re-run **the exact same `docker run` command**.
3. The runner detects existing results and resumes from the next unprocessed sample.

No special `--resume` flag needed — the deterministic exp_name makes it automatic.

## Results Layout (per-config files)

Each `<backend>_<design>_<mode>_<model>_<prompting>/` directory contains:

```
├── <EXP_NAME>_detailed_results.jsonl      # per-sample predictions + reasoning
├── <EXP_NAME>_detailed_results.csv        # CSV mirror of above
├── <EXP_NAME>_energy_tracking.json        # cumulative energy/emissions
├── emissions.csv                          # CodeCarbon per-session data
└── *_metrics.csv                          # DA/MA only — classification metrics
```

Each config × seed × backend produces its own directory; analysis scripts can compare across seeds and backends.

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

- Inference backend restarts for each `docker run` invocation (~2-5 min overhead for model load on vLLM; first-run ollama pull adds extra time per model). Plan per-config overhead accordingly when budgeting runs.
- Only VulTrial-870 is included. RQ3 LLM-as-judge evaluation is API-based (Claude Opus) and runs separately on the host — not part of this container.
- Nemotron models are gated on HuggingFace — team members must have their own `HF_TOKEN` with access for the vLLM backend. Nemotron-Super-49B is not in the official ollama library.
- Driver requirement: NVIDIA driver ≥ 550.54.14 for CUDA 12.8 support. RunPod H100 pods meet this; older on-prem servers (e.g., driver 535) will fail at inference time.
- vLLM-vs-ollama comparison is not precision-matched by default (see *Precision / Quantization* above).

## Troubleshooting

### "vLLM process died during startup"

- Check `docker logs <container>` for the vLLM log tail (also saved to `results/.../vllm.log`).
- Most common cause: insufficient GPU memory. Try reducing `GPU_MEM_UTIL` (e.g., `0.85`) or `MAX_MODEL_LEN` (e.g., `32768`).
- For Nemotron-Super-49B: ensure 2× H100 are visible (`nvidia-smi` inside container).

### "HuggingFace model access denied"

- Nemotron models require Meta's and NVIDIA's license acceptance on the HuggingFace model page.
- Pass `HF_TOKEN` to the container (`-e HF_TOKEN="hf_..."`).

### Container exits immediately

- Verify required env vars are set: `DESIGN`, `MODE`, `MODEL`, `PROMPTING`.
- If `INFERENCE_BACKEND=ollama`, also need `OLLAMA_MODEL`.
- Check `docker logs <container>` for the `[ERROR]` message.

## Version Dependencies & Rebuild Notes

The image pins several versions due to known compatibility traps discovered during v1.1 builds. Anyone rebuilding the image (e.g., pulling a fresh base or updating AG2) should be aware of these:

### `vllm>=0.17.0,<0.18.0` (upper bound)

`vllm>=0.18.0` pulls deep transitive changes (newer torch inductor paths) that trigger startup assertion errors regardless of torch version. Until vllm and the RunPod base image are jointly upgraded, keep this cap. Confirmed working: vllm 0.17.1 + torch 2.10.0.

### Uninstall base-image torch before installing requirements

The Dockerfile runs `pip uninstall -y torch torchvision torchaudio` **before** installing `requirements_runpod.txt`. Reason:

- The base image `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` ships **torch 2.8.0**
- `vllm 0.17.x` transitively requires **torch==2.10.0**
- Without the explicit uninstall, pip installs torch 2.10 *alongside* the base's torch 2.8 (because `--ignore-installed` skips cleanup), producing two torch trees in `dist-packages`
- Result: `AssertionError: duplicate template name` in `torch._inductor.select_algorithm` when vLLM's subprocess inspects the model architecture

Do **not** pin `torch==2.8.0` in `requirements_runpod.txt` — it conflicts with vllm's explicit `torch==2.10.0` requirement and `pip install` will fail with `ResolutionImpossible`.

### `--ignore-installed cryptography` only (not all packages)

The base image's `cryptography` was installed via `apt-get` (dpkg), so it lacks a pip `RECORD` file. When a transitive dep wants to upgrade it, pip fails with *"Cannot uninstall cryptography — no RECORD file was found"*.

Fix: `pip install --no-cache-dir --ignore-installed cryptography` **before** the main install.

Do **not** apply `--ignore-installed` globally — it skips the uninstall step for every package, which is why earlier attempts left duplicate `torch` installs behind.

### `--user <host-UID>` runtime workarounds

When the container runs with `--user $(id -u):$(id -g)` (which all `docker run` examples above use), the non-root UID may not exist in the container's `/etc/passwd`. Several libraries fall over:

| Issue | Fix |
|-------|-----|
| `getpass.getuser() → KeyError: getpwuid(): uid not found` | Dockerfile `ENV HOME=/tmp`; entrypoint `export USER` |
| HF downloads to root-owned `/workspace/.cache/huggingface/` | Dockerfile `ENV HF_HOME=/tmp/hf_cache` (overrides base image default) |
| flashinfer creates `/.cache` (root-only) | Dockerfile `ENV FLASHINFER_WORKSPACE_BASE=/tmp` |
| torch inductor writes to cwd | Dockerfile `ENV TORCHINDUCTOR_CACHE_DIR=/tmp/torchinductor` |
| Server logs can't write to `/workspace/` | Entrypoint redirects vllm/ollama logs to the bind-mounted results dir |

All above are baked in — team members just need to remember to pass `--user $(id -u):$(id -g)`. Without the flag, the container runs as root and outputs become root-owned on the host (undeletable without sudo).

### If rebuilding fails

1. **Check `docker system df`** — the build needs ~30 GB transient space. Clear cache if needed with `docker builder prune`.
2. **Check pip resolution order** — if a new dep introduces a torch version conflict, `pip install` fails with `ResolutionImpossible`. Inspect the build log tail; pip names the conflicting packages explicitly.
3. **Uninstall + reinstall everything** as a last resort: `docker rmi agent-green:v1.1-replication && docker build --no-cache -t agent-green:v1.1-replication -f container/Dockerfile .`

## Image Provenance

- Built from repository `agent-green` at git tag `v1.1-replication`
- See `/workspace/src/` inside the container for the exact Python source shipped
- Dataset: `/workspace/vuln_database/VulTrial_870_samples_balanced.jsonl` (870 samples, 435 PrimeVul pairs)
- Changes from v1.0: adds ollama backend option, bumps AG2 to ≥0.10.0, adds `VLLM_DTYPE`
