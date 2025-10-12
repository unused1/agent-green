# Gemma-7B-IT Setup on Mars Server (SMU SCIS)

## Server Specifications
- **Server**: Mars (10.193.104.137)
- **GPUs**: 4 x NVIDIA RTX A5000 (24GB VRAM each, 96GB total)
- **OS**: Ubuntu 24.04.1 LTS
- **CUDA**: 12.4 (driver 550.90.07)
- **Python**: 3.12.3
- **Docker**: Available (v27.3.1)
- **Workspace**: `/mnt/hdd2/huabengtan` (6.8TB available)

## Setup Instructions (Simplified Docker Approach)

**Note**: Since Mars server doesn't have pip installed, we'll use Docker for everything.

### Prerequisites
Before starting, you need:
- Hugging Face account with access token
- Accept Gemma license at: https://huggingface.co/google/gemma-1.1-7b-it
- Get your token from: https://huggingface.co/settings/tokens

### 1. Connect to Mars Server
```bash
# From your local machine (with VPN connected)
ssh huabengtan@10.193.104.137
```

### 2. Set Up Working Directory
```bash
# Create project directory in your allocated space
mkdir -p /mnt/hdd2/huabengtan/llm-inference/{models,logs,scripts}
cd /mnt/hdd2/huabengtan/llm-inference
```

### 3. Pull vLLM Docker Image
```bash
# Pull the latest vLLM image
docker pull vllm/vllm-openai:latest
```

### 4. Check GPU Availability and Run Gemma Server

#### IMPORTANT: Check Available GPUs First
Before running the Docker container, check which GPUs are free:

```bash
# Check GPU availability and memory usage
nvidia-smi

# Look for GPUs with low memory usage (ideally < 100MiB)
# Note the GPU IDs that are available (0, 1, 2, or 3)
# Avoid GPUs being used by other processes (e.g., sglang::scheduler)

```

#### Multi-GPU Configuration (Recommended for full 8192 context)
Using 2 GPUs provides 48GB total VRAM, enabling full context length support.

Replace `YOUR_HF_TOKEN` with your actual Hugging Face token and **UPDATE device IDs based on nvidia-smi output**:

```bash
# IMPORTANT: Update --gpus '"device=X,Y"' based on available GPUs from nvidia-smi
# Example configurations:
# --gpus '"device=0,1"'  # If GPUs 0 and 1 are free
# --gpus '"device=1,3"'  # If GPUs 1 and 3 are free
# --gpus '"device=0,3"'  # If GPUs 0 and 3 are free

docker run -d \
    --name gemma-server \
    --gpus '"device=0,1"' \
    --shm-size=32g \
    -v /mnt/hdd2/huabengtan/llm-inference/models:/models \
    -p 8000:8000 \
    -e HUGGING_FACE_HUB_TOKEN=YOUR_HF_TOKEN \
    --restart unless-stopped \
    vllm/vllm-openai:latest \
    --model google/gemma-1.1-7b-it \
    --download-dir /models \
    --gpu-memory-utilization 0.90 \
    --max-model-len 8192 \
    --dtype auto \
    --tensor-parallel-size 2

# Monitor download progress and server startup
docker logs gemma-server -f
```

**⚠️ IMPORTANT - Initial Setup Time:**
- **Model Download**: ~16GB, takes 2-5 minutes on Mars network
- **Model Loading**: Takes 3-5 minutes to load into GPU memory after download
- **Total First Run**: Expect 5-10 minutes before server is ready
- **Subsequent Runs**: Only 3-5 minutes (model already downloaded)
- **Multi-GPU Setup**: May take slightly longer due to model sharding across GPUs

**Progress Indicators to Watch For:**
1. `Downloading weights...` - Download starting
2. `Time spent downloading weights... seconds` - Download complete
3. `Loading model weights...` - Loading into GPU
4. `Application startup complete` - Server ready!
5. API responds at `http://localhost:8000/v1/models`

### 5. Verify Server is Running
Wait for "Application startup complete" in logs (5-10 minutes on first run), then test:

```bash
# Test locally on Mars
curl http://localhost:8000/v1/models

# Test with a sample prompt
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-1.1-7b-it",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "max_tokens": 50,
    "temperature": 0
  }'
```


### 6. Set Up SSH Tunnel (from your local machine)
```bash
# Create SSH tunnel to access the API
ssh -L 8000:localhost:8000 huabengtan@10.193.104.137 -N

# Keep this terminal open while using the API
```

### 7. Test the Setup (from local machine)
```bash
# With SSH tunnel active, test the API
curl http://localhost:8000/v1/models

# Test a completion
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-1.1-7b-it",
    "messages": [{"role": "user", "content": "Is this code vulnerable? int main() { char buf[10]; gets(buf); }"}],
    "max_tokens": 100,
    "temperature": 0
  }'
```

### 8. Update Local Environment Variables
Add to your local `.env` file:

```bash
# Private inference endpoint for Gemma on Mars server
PRIVATE_INFERENCE_ENDPOINT=http://localhost:8000/v1
PRIVATE_INFERENCE_API_KEY=dummy_key  # vLLM doesn't require auth by default
```

## Docker Container Management

### Starting and Stopping the Server

```bash
# Check if container is running
docker ps | grep gemma-server

# Stop the server
docker stop gemma-server

# Start the server again
docker start gemma-server

# Restart the server
docker restart gemma-server

# Remove container (if needed to recreate)
docker rm gemma-server
```

### Viewing Logs

```bash
# View all logs
docker logs gemma-server

# Follow logs in real-time
docker logs -f gemma-server

# View last 100 lines
docker logs --tail 100 gemma-server
```

## Resource Management on Shared Server

Since Mars is a shared server, please follow these guidelines:

1. **GPU Selection**: Use `CUDA_VISIBLE_DEVICES` to select specific GPUs
   - GPU 0 has some usage (1490MB), avoid if possible
   - GPUs 1-3 are mostly free

2. **Memory Management**: 
   - Use `--gpu-memory-utilization 0.8` to leave headroom
   - Monitor with `nvidia-smi`

3. **Process Management**:
   ```bash
   # Check your GPU processes
   nvidia-smi | grep huabengtan
   
   # Kill Docker container if needed
   docker stop gemma-server
   ```

4. **Storage**: Keep all files in `/mnt/hdd2/huabengtan/`

## Monitoring and Logs

### Monitor GPU Usage
```bash
# Watch GPU usage in real-time
watch -n 1 nvidia-smi

# Check specific GPU
nvidia-smi -i 1  # For GPU 1
```

### Check Server Logs
```bash
# View Docker logs
docker logs -f gemma-server

# Check last 50 lines with timestamps
docker logs --tail 50 -t gemma-server
```

### Test from Mars Server Directly
```bash
# Test locally on Mars (without tunnel)
curl http://localhost:8000/v1/models
```

## Monitoring and Troubleshooting

### Essential Monitoring Commands

```bash
# 1. Check container status
docker ps -a | grep gemma-server

# 2. View recent logs with timestamps
docker logs -t --tail 20 gemma-server

# 3. Check GPU memory usage (should be ~19GB when loaded)
nvidia-smi -i 1

# 4. Verify model download completed
ls -lah /mnt/hdd2/huabengtan/llm-inference/models/
du -sh /mnt/hdd2/huabengtan/llm-inference/models/models--google--gemma-1.1-7b-it/

# 5. Test if API is responding
curl -s http://localhost:8000/v1/models | jq . || echo "API not ready yet"

# 6. Follow logs in real-time during startup
docker logs -f gemma-server

# 7. Check for errors in logs
docker logs gemma-server 2>&1 | grep -E "ERROR|Failed|Exception"
```

### Startup Timeline
- **0-2 min**: Container initialization, detecting CUDA
- **2-5 min**: Downloading model weights (first run only)
- **5-8 min**: Loading model into GPU memory
- **8-10 min**: Server initialization and API startup
- **Ready**: Look for "Application startup complete" in logs

### Common Issues and Solutions

1. **No Logs Output / Container Silent**
   - Container may still be downloading/loading (check with `docker ps -a`)
   - Use `docker logs --tail 100 gemma-server` for more history
   - Check GPU memory: `nvidia-smi -i 1` (should show ~19GB used when loaded)

2. **CUDA Out of Memory**
   - Reduce `--gpu-memory-utilization` to 0.6 or 0.5
   - Reduce `--max-model-len` to 1024
   - Check other processes: `nvidia-smi` for all GPUs

3. **Port Already in Use**
   - Check who's using port: `lsof -i :8000`
   - Use a different port (e.g., 8001, 8002)

4. **Model Download Issues**
   - Verify HF token is correct: `echo $HUGGING_FACE_HUB_TOKEN`
   - Check disk space: `df -h /mnt/hdd2` (need ~20GB free)
   - Verify internet: `curl -I https://huggingface.co`
   - Check if model partially downloaded: `ls /mnt/hdd2/huabengtan/llm-inference/models/`

5. **Container Exits Immediately**
   - Check exit code: `docker inspect gemma-server --format='{{.State.ExitCode}}'`
   - View full error: `docker logs gemma-server 2>&1 | head -50`
   - Common cause: Invalid HF token or no access to Gemma model

6. **SSH Tunnel Drops**
   - Use `autossh` for persistent tunnels:
   ```bash
   autossh -M 0 -L 8000:localhost:8000 huabengtan@10.0.104.137 -N
   ```

## Testing the Setup

### Quick Functionality Test
```bash
# Test vulnerability detection capability
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-1.1-7b-it",
    "messages": [{"role": "user", "content": "Is this code vulnerable? int main() { char buf[10]; gets(buf); return 0; }"}],
    "max_tokens": 100,
    "temperature": 0
  }' | jq .
```

## Clean Up
When done with experiments:

```bash
# Stop Docker container
docker stop gemma-server

# Remove container (keeps downloaded model)
docker rm gemma-server

# Deactivate virtual environment
deactivate

# Optional: Remove model to free space
# rm -rf /mnt/hdd2/huabengtan/llm-inference/models/gemma-7b-it
```

## Integration with Replication Scripts

Your scripts at `src/replication/` will automatically use this private endpoint when:
1. Gemma-7b-it is selected from the model menu
2. `PRIVATE_INFERENCE_ENDPOINT` is set in `.env`
3. SSH tunnel is active on port 8000

The scripts already have the logic to route Gemma-7b-it to the private endpoint!