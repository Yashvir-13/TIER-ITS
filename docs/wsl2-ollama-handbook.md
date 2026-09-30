# WSL2 + Ollama Operational Handbook

Quick reference for operating Ollama on this specific WSL2 setup.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Windows Host                               │
│  - NVIDIA Driver 592.82 (CUDA 13.1)        │
│  - Port namespace shared via mirrored mode  │
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │  WSL2 (Ubuntu, systemd=true)          │ │
│  │  - Ollama v0.35.0 (systemd service)   │ │
│  │  - Binds: 127.0.0.1:11434            │ │
│  │  - GPU: RTX 4050 6GB, CUDA 8.9       │ │
│  │  - Models: ~/.ollama/models/          │ │
│  │  - Service data: /usr/share/ollama/   │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

## Daily Operations

### Check if Ollama is running

```bash
curl -s --max-time 5 http://127.0.0.1:11434/
# Expected: "Ollama is running"
```

### Service management

```bash
sudo systemctl status ollama --no-pager   # Check status
sudo systemctl restart ollama              # Restart
sudo systemctl stop ollama                 # Stop
sudo journalctl -u ollama -f               # Follow logs
sudo journalctl -u ollama --no-pager -n 30 # Last 30 log lines
```

### Model management

```bash
ollama list                    # List installed models
ollama pull qwen3:4b           # Pull a model
ollama rm <model>              # Remove a model
ollama show qwen3:4b           # Show model details
ollama ps                      # Show loaded models + GPU usage
```

### GPU monitoring

```bash
nvidia-smi                     # Full GPU status
watch -n 1 nvidia-smi --query-gpu=temperature.gpu,power.draw,memory.used --format=csv,noheader
```

## Configuration

### Systemd override

Location: `/etc/systemd/system/ollama.service.d/environment.conf`

```ini
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_KEEP_ALIVE=5m"
Environment="OLLAMA_NUM_PARALLEL=1"
```

After editing: `sudo systemctl daemon-reload && sudo systemctl restart ollama`.

### Shell environment

Same variables are set in `~/.bashrc` for CLI usage.

## Troubleshooting

### "address already in use"

A Windows process is holding the port. With mirrored networking, WSL2 tools (`ss`, `lsof`) cannot see it.

```bash
# 1. Find the culprit on Windows
netstat.exe -ano | findstr.exe "11434"

# 2. Identify it
tasklist.exe /FI "PID eq <PID>"

# 3. Kill it
taskkill.exe /F /PID <PID>

# 4. Restart Ollama
sudo systemctl restart ollama
```

Common culprit: `svchost.exe` hosting a leftover Windows Ollama service. Prevent recurrence by removing `C:\Users\<user>\AppData\Local\Programs\Ollama` on Windows.

### "permission denied" on startup

The `ollama` service user can't write to its data directory.

```bash
sudo mkdir -p /usr/share/ollama/.ollama
sudo chown -R ollama:ollama /usr/share/ollama
sudo systemctl restart ollama
```

### curl hangs on localhost

IPv6 resolution issue. `localhost` may resolve to `::1` before `127.0.0.1`.

```bash
# Always use 127.0.0.1 explicitly
curl -s --max-time 5 http://127.0.0.1:11434/
```

### Service won't start after WSL restart

```bash
# Check if systemd is actually running
ps -p 1 -o comm=
# Should print "systemd". If it prints "init", systemd isn't enabled.

# Verify /etc/wsl.conf has:
# [boot]
# systemd=true

# Then from Windows PowerShell: wsl --shutdown
# Re-open WSL terminal.
```

### GPU not detected

```bash
# Check if nvidia-smi works
nvidia-smi

# If not, the Windows NVIDIA driver may need updating.
# WSL2 uses the Windows host driver — no CUDA toolkit needed inside WSL.

# Check Ollama logs for GPU detection
sudo journalctl -u ollama --no-pager | grep -i "gpu\|cuda\|vram"
```

## Models for This Project

| Model | Purpose | Pull command |
|:------|:--------|:------------|
| `qwen3:4b` | Primary extractor + report generator | `ollama pull qwen3:4b` |
| `phi4-mini` | Alternative extractor (better reasoning) | `ollama pull phi4-mini` |
| `llama3.2:3b` | Fast baseline runs | `ollama pull llama3.2:3b` |

## Python Integration

```python
from ollama import chat

response = chat(
    model="qwen3:4b",
    messages=[{"role": "user", "content": "Hello"}],
    options={"temperature": 0, "num_ctx": 4096}
)
print(response.message.content)
```

For structured output with Pydantic:

```python
from ollama import chat
from pydantic import BaseModel

class MySchema(BaseModel):
    name: str
    value: int

response = chat(
    model="qwen3:4b",
    messages=[{"role": "user", "content": "Extract: John scored 95"}],
    format=MySchema.model_json_schema()
)
result = MySchema.model_validate_json(response.message.content)
```
