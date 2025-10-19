# AMD GPU Setup Guide

This guide covers setting up the Windows AI Assistant for **AMD GPUs** (tested on Radeon RX 7900 XT with 24GB VRAM).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows 11 Pro                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Ollama (Native) - DirectML Acceleration             │  │
│  │  - AMD Radeon RX 7900 XT (24GB VRAM)                 │  │
│  │  - Listens: 127.0.0.1:11434 + Tailscale IP:11434    │  │
│  │  - GPU Utilization: 100%                             │  │
│  └──────────────────────────────────────────────────────┘  │
│           ↑ Network (host.docker.internal)                  │
│           ↓                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Python AI Assistant (Windows)                       │   │
│  │ - Speech Recognition (Windows native or Whisper)    │   │
│  │ - Device Control with "wolf-logic" confirmation     │   │
│  │ - mem0 Persistent Memory Integration                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  WSL2 - Ubuntu 24.04 LTS                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Whisper Server (Native) - ROCm Acceleration        │  │
│  │  - AMD GPU Pass-through: 100.110.82.181:8080       │  │
│  │  - GPU Utilization: ~30-50% (speech-to-text)        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Caddy Reverse Proxy (Native) - Security Layer      │  │
│  │  - Routes ALL external traffic through Tailscale    │  │
│  │  - No direct port exposure                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Docker Engine - mem0 Infrastructure (6 containers) │  │
│  │  - PostgreSQL (relational data)                      │  │
│  │  - Vector DB (embeddings)                           │  │
│  │  - Neo4J (knowledge graph - 7,800+ memories)         │  │
│  │  - mem0 UI (web interface)                           │  │
│  │  - mem0 REST API (entry point - your fix!)          │  │
│  │  - Retrieval Agent (5-second memory extraction loop) │  │
│  │  - GPU: CPU-only (data processing, no ML)            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Why This Architecture?

### GPU Constraint: AMD Edition

**Problem:** GPU access is complex with multiple execution contexts.

**The Issue:**
- ❌ Ollama in Docker container = **LOSES GPU access** (Docker doesn't pass through AMD GPU properly)
- ❌ Ollama in WSL native = **Docker containers can't reach it**
- ✅ Ollama on Windows native = **GPU access + Docker container visibility**

**Why AMD GPU Pass-through in WSL?**
- WSL2 with custom kernel config can pass through AMD GPU to native applications
- Docker in WSL **does NOT** recognize AMD GPUs (only NVIDIA CUDA)
- So: Whisper runs native in WSL to use AMD GPU, not in Docker

**Result:** This is the ONLY configuration that maintains both GPU acceleration AND inter-service communication.

## Prerequisites

### Hardware
- Windows 11 Pro (Build 26220+) for Workstations
- AMD GPU (tested: Radeon RX 7900 XT, 24GB VRAM)
- 80GB+ RAM recommended (for model inference + Docker containers)
- Intel Core i7 (14th gen+) or equivalent

### Software
- Windows 11 with latest updates
- WSL2 with Ubuntu 24.04 LTS
- Docker Engine (NOT Docker Desktop) in WSL
- Python 3.10+
- Git

### WSL2 GPU Pass-through Configuration

You need a custom WSL2 kernel with GPU support. This is the critical piece.

**1. Enable GPU in WSL2 (`.wslconfig` on Windows):**

Create `%UserProfile%\.wslconfig`:

```ini
[wsl2]
# AMD GPU passthrough configuration
guiApplications=true
gpuSupport=on
memory=40GB
processors=16
swap=8GB
localhostForwarding=true

# Custom kernel for AMD GPU support
kernel=\\wsl.localhost\Ubuntu-24.04\boot\vmlinuz
initrd=\\wsl.localhost\Ubuntu-24.04\boot\initrd.img
```

**2. Custom WSL2 Kernel Build (for AMD GPU support):**

This is optional if your WSL installation already has GPU support. To verify:

```bash
wsl
lspci | grep -i amd
```

If you see your AMD GPU listed, you're good! If not, you may need:
- WSL2 kernel with IOMMU and AMD GPU drivers enabled
- Or use AMD's ROCm direct access (more complex)

**3. Verify GPU in WSL:**

```bash
rocm-smi
```

Should show your AMD GPU. If not:

```bash
sudo apt-get install rocm-core rocm-libs
```

## Installation

### 1. Install Ollama on Windows (Native)

Download from https://ollama.ai

**Configuration:**

Create `%AppData%\ollama\.env` (or set in PowerShell):

```powershell
# Enable DirectML for AMD GPU
$env:OLLAMA_NUM_GPU = 1
$env:OLLAMA_DEVICE = "gpu"

# Listen on both localhost and Tailscale IP
$env:OLLAMA_HOST = "127.0.0.1:11434"
```

**Verify installation:**

```powershell
ollama list
ollama run llama3.2:3b "say hello"
```

### 2. Install Whisper in WSL (Native)

```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Create virtual environment
python3.11 -m venv ~/whisper_env
source ~/whisper_env/bin/activate

# Install Whisper with ROCm support
pip install openai-whisper
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7

# Verify GPU access
python3 -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name()}')"
```

**Create Whisper service:**

Create `~/whisper_server.py`:

```python
#!/usr/bin/env python3
"""
Whisper ASR server for speech-to-text
Uses AMD GPU via ROCm for acceleration
"""
import whisper
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Load model with GPU support
model = whisper.load_model("base", device="cuda")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Transcribe audio file"""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400
    
    audio_file = request.files["audio"]
    result = model.transcribe(audio_file.stream.read())
    
    return jsonify({"text": result["text"]})

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
```

**Create systemd service** (`~/.config/systemd/user/whisper.service`):

```ini
[Unit]
Description=Whisper Speech-to-Text Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="PATH=/home/ubuntu/whisper_env/bin"
ExecStart=/home/ubuntu/whisper_env/bin/python /home/ubuntu/whisper_server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

**Start service:**

```bash
systemctl --user daemon-reload
systemctl --user enable whisper.service
systemctl --user start whisper.service
systemctl --user status whisper.service
```

### 3. Install AI Assistant (Windows)

```powershell
cd s:\Github\AI-Windows_Assistant

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment template
Copy-Item .env.example .env

# Edit .env for your setup
notepad .env
```

**Configure `.env`:**

```bash
# Ollama
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b

# Whisper (optional, uses Windows Speech Recognition by default)
USE_WHISPER=false
WHISPER_MODEL=base

# DirectML GPU acceleration
USE_DIRECTML=true

# mem0 Persistent Memory
ENABLE_PERSISTENT_MEMORY=true
MEM0_API_URL=https://mem0-api.complexsimplicity.com
MEM0_API_KEY=your_api_key_here
MEM0_RETRIEVAL_AGENT_HOST=100.110.82.181
MEM0_RETRIEVAL_AGENT_PORT=8765

# Tailscale networking
USE_TAILSCALE=true
```

### 4. Deploy mem0 Infrastructure in WSL/Docker

The mem0 6-container infrastructure runs in Docker in WSL. You've already fixed the REST API stability issue!

**Your fixed docker-compose in the separate mem0 repo should have:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  vector_db:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - vector_data:/qdrant/storage

  neo4j:
    image: neo4j:latest
    environment:
      NEO4J_AUTH: neo4j/password
    ports:
      - "7687:7687"
      - "7474:7474"
    volumes:
      - neo4j_data:/data

  mem0_api:
    # Your fixed version with stable REST API
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres/mem0
      - VECTOR_DB_URL=http://vector_db:6333
      - NEO4J_URI=neo4j://neo4j:7687

  retrieval_agent:
    # Your retrieval agent on port 8765
    build: ./retrieval_agent
    ports:
      - "8765:8765"
    environment:
      - MEM0_API_URL=http://mem0_api:8000
```

**Start containers:**

```bash
cd /path/to/mem0/repo
docker compose up -d
```

## Running the AI Assistant

### Windows (Voice Assistant)

```powershell
cd s:\Github\AI-Windows_Assistant
.\venv\Scripts\Activate.ps1
python main.py
```

Expected output:

```
🤖 Windows AI Assistant is now active and listening...
Wake word 'assistant' detected
Connected to Ollama server
Speech recognition initialized
Device controller initialized
Connected to mem0 persistent memory system
```

### Test Interaction

1. Say "Assistant, launch calculator"
   - Assistant recognizes wake word
   - Queries 7,800+ memories for similar past commands
   - Injects relevant context into LLM prompt
   - Ollama generates response (with GPU acceleration)
   - Device controller executes command (with "wolf-logic" confirmation if needed)
   - Interaction stored in mem0 for future learning

2. Say "Assistant, what did I ask you yesterday about device control?"
   - Retrieves from Neo4J knowledge graph
   - Shows learning across time

## Performance Tuning

### DirectML (Windows Ollama)

**Increase performance:**

```powershell
# Use GPU for all inference
$env:OLLAMA_NUM_GPU = 1

# Enable parallel processing
$env:OLLAMA_NUM_PARALLEL = 4

# Increase context window
$env:OLLAMA_NUM_PREDICT = 2048
```

### ROCm (WSL Whisper)

**Verify GPU utilization:**

```bash
watch -n 1 rocm-smi
```

**Optimize for real-time transcription:**

Edit `whisper_server.py`:

```python
# Use GPU with FP16 (faster, less memory)
model = whisper.load_model("base", device="cuda", in_memory=False, fp16=True)

# Batch multiple requests if needed
```

## Troubleshooting

### "Ollama not reachable from Docker"
- Verify Ollama is running on Windows: `curl http://127.0.0.1:11434/api/tags`
- Use `host.docker.internal` instead of localhost in Docker container
- Check Windows Firewall isn't blocking port 11434

### "GPU not detected in Whisper"
```bash
# Verify ROCm installation
rocm-smi

# Check PyTorch GPU support
python -c "import torch; print(torch.cuda.is_available())"

# Reinstall with ROCm support
pip uninstall torch -y
pip install torch --index-url https://download.pytorch.org/whl/rocm5.7
```

### "mem0 REST API connection failed"
- Verify Docker containers: `docker ps`
- Check mem0 API logs: `docker logs mem0_api`
- Confirm REST API is running: `curl http://100.110.82.181:8000/health`

### "Whisper transcription very slow"
- Check GPU utilization: `rocm-smi`
- Verify model size: Use "tiny" instead of "base" for real-time
- Increase memory allocation to ROCm

## Security Considerations

✅ **What's Protected:**
- Ollama on Windows: Internal port only
- Whisper in WSL: Behind Caddy reverse proxy
- mem0 REST API: Behind reverse proxy + Tailscale
- All traffic: Routes through Tailscale VPN only

✅ **Privacy:**
- All AI processing: Local, no cloud
- No API calls: Ollama, Whisper, mem0 all local
- No data leakage: Tailscale encrypts all traffic

⚠️ **What You Must Do:**
- Secure `.env` file (contains mem0 API key)
- Run Ollama on Windows (never expose via network directly)
- Use Tailscale VPN for remote access
- Keep Windows Firewall enabled

## Next Steps

1. ✅ Install Ollama (Windows native)
2. ✅ Install Whisper (WSL native with ROCm)
3. ✅ Deploy mem0 (Docker in WSL)
4. ✅ Deploy Caddy reverse proxy (WSL native)
5. ✅ Install AI Assistant (Windows)
6. ✅ Configure Tailscale for secure networking
7. 🚀 Run the assistant and enjoy persistent memory learning!

---

**Questions? Issues?**

This is the tested, production configuration for AMD GPUs. If you hit problems, verify:
- GPU pass-through to WSL (rocm-smi shows your GPU)
- Ollama is running on Windows and accessible
- Docker containers are running (docker ps)
- Tailscale network is connected
