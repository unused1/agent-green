import subprocess
import signal
import os
import threading
import urllib.request
from typing import Optional

def _check_vllm_running() -> bool:
    """Check if vLLM server is already running on port 8000."""
    try:
        urllib.request.urlopen("http://localhost:8000/v1/models", timeout=2)
        return True
    except:
        return False

def _start_ollama_server_base(
    stream_stdout: bool = False,
    log_file: Optional[str] = None
) -> subprocess.Popen:
    """
    Helper to start the Ollama server with optional stdout streaming or logging.
    If vLLM is already running, returns a dummy process.
    """
    # Check if vLLM is already running
    if _check_vllm_running():
        print("vLLM server already running on port 8000, skipping Ollama startup...")
        # Return a dummy process object that won't be used
        class DummyProcess:
            def __init__(self):
                self.pid = None
        return DummyProcess()

    print("Starting Ollama server...")
    if log_file:
        logfile = open(log_file, "w")
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=logfile,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
        return process
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid
    )
    if stream_stdout:
        def stream_output(stream, prefix):
            for line in iter(stream.readline, ''):
                print(f"[{prefix}] {line}", end='')
        threading.Thread(target=stream_output, args=(process.stdout, 'STDOUT'), daemon=True).start()
        threading.Thread(target=stream_output, args=(process.stderr, 'STDERR'), daemon=True).start()
    return process

def start_ollama_server() -> subprocess.Popen:
    """Start Ollama server (no output streaming). Skips if vLLM is running."""
    return _start_ollama_server_base()

def start_ollama_server_stream_stdout() -> subprocess.Popen:
    """Start Ollama server and stream stdout/stderr to console. Skips if vLLM is running."""
    return _start_ollama_server_base(stream_stdout=True)

def start_ollama_server_log(log_file: str = "ollama.log") -> subprocess.Popen:
    """Start Ollama server and log output to a file. Skips if vLLM is running."""
    return _start_ollama_server_base(log_file=log_file)

def stop_ollama_server(process: subprocess.Popen) -> None:
    """Stop the Ollama server process. Skips if it's a dummy process (vLLM was used)."""
    # Check if it's a dummy process
    if not hasattr(process, 'pid') or process.pid is None:
        print("vLLM server is running, no Ollama server to stop...")
        return

    print("Stopping Ollama server...")
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except Exception as e:
        print(f"Error stopping Ollama server: {e}")
