# Windows AI Assistant - WSL2 + Docker Engine Setup Guide

## Overview

This guide covers running the Windows AI Assistant using Docker Engine inside WSL2 with Ubuntu 24.04 LTS.

## Prerequisites

### Windows 11
- Windows 11 Pro or higher
- WSL2 enabled
- Virtualization enabled in BIOS

### WSL2 Ubuntu 24.04 LTS
```powershell
# In PowerShell (Admin)
wsl --install -d Ubuntu-24.04
wsl --set-default-version 2
```

### Docker Engine (not Docker Desktop)
```bash
# In WSL2 Ubuntu 24.04 terminal

# Install Docker dependencies
sudo apt-get update
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (so you don't need sudo)
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Verify installation
docker --version
docker run hello-world
```

### GPU Support (AMD 7900 XT)

```bash
# Install ROCm on WSL2 Ubuntu 24.04
sudo apt-get install -y rocm-core rocm-libs hip-runtime-amd hip-dev

# Add user to video group
sudo usermod -a -G video $USER
sudo usermod -a -G render $USER

# Verify GPU access
rocm-smi

# For Docker GPU access, ensure /dev/kfd and /dev/dri are accessible
ls -la /dev/kfd
ls -la /dev/dri
```

## Project Setup

### 1. Clone the Repository
```bash
# In WSL2 Ubuntu
cd ~
git clone https://github.com/yourusername/AI-Windows_Assistant.git
cd AI-Windows_Assistant
```

### 2. Configure for Docker

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env`:
```env
# Docker-specific configuration
OLLAMA_HOST=ollama:11434  # Docker service name
WHISPER_HOST=whisper:8080  # Docker service name

# Rest of config
WAKE_WORD=assistant
USE_WHISPER=true
WHISPER_MODEL=base
ALLOW_SYSTEM_CONTROL=true
CONFIRMATION_KEYWORD=wolf-logic
LOG_LEVEL=INFO
```

### 3. Build and Start Services
```bash
# Build and start all services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Verify Services

```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test Whisper
curl http://localhost:8080/health

# Pull a model (first time only)
docker exec ai-assistant-ollama ollama pull llama3.2:3b
```

### 5. Run the Python Assistant

#### Option A: Inside Container (Recommended for Docker setup)
```bash
# Create a Docker container for the Python app
docker-compose exec ollama bash

# Inside container, run the assistant
python main.py
```

#### Option B: On Windows (Connect to Docker services)
```powershell
# In PowerShell
cd AI-Windows_Assistant
pip install -r requirements.txt
python main.py
```

## Architecture

```
Windows 11 Pro for Workstations (Host)
    ├─ Ollama Running Natively on Windows
    │   ├─ Direct GPU Access (AMD 7900 XT, NVIDIA, Intel)
    │   ├─ Full DirectML/CUDA Acceleration
    │   └─ Port: 11434
    │
    ├─ Python App (Windows or WSL2)
    │   ├─ Voice input/output
    │   ├─ Device control
    │   └─ Connects to Ollama on Windows
    │
    └─ WSL2 (Ubuntu 24.04 LTS) - Optional Docker
        ├─ Whisper Server Container (Optional)
        │   └─ Speech recognition server
        │   └─ Port: 8080
        │
        └─ Python App Container (Optional)
            └─ Connects to Windows Ollama via host.docker.internal:11434
            └─ Connects to Whisper on localhost:8080
```

### Why This Architecture?

1. **Ollama on Windows (Not Docker)**
   - Direct GPU access to AMD/NVIDIA
   - Full DirectML acceleration
   - No performance loss from containerization
   - Sees host GPU natively

2. **Optional Docker for Whisper**
   - Can containerize non-GPU services
   - Keeps Windows cleaner
   - Easy to deploy/remove
   - Still connects to Windows Ollama

3. **Python App Flexibility**
   - Run on Windows directly (recommended for voice)
   - Or run in WSL2 Docker container
   - Both can connect to Windows Ollama
   - Both get full GPU performance

## Common Tasks

### Start All Services
```bash
docker-compose up -d
```

### Stop All Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ollama
docker-compose logs -f whisper-server
```

### Pull a New Model
```bash
docker exec ai-assistant-ollama ollama pull phi3
```

### Remove All Data and Rebuild
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Access Container Shell
```bash
docker exec -it ai-assistant-ollama bash
docker exec -it ai-assistant-whisper bash
```

## Performance Optimization

### GPU Pass-through (AMD 7900 XT)

The docker-compose.yml already includes GPU device mapping:
```yaml
devices:
  - /dev/kfd:/dev/kfd      # AMD GPU compute
  - /dev/dri:/dev/dri      # GPU rendering
group_add:
  - video
  - render
```

Verify GPU is accessible:
```bash
docker exec ai-assistant-ollama rocm-smi
```

### Memory Management

Check current memory usage:
```bash
docker stats
```

Limit container memory (in docker-compose.yml):
```yaml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 32G  # Adjust as needed
```

### Storage

Clean up unused Docker data:
```bash
docker system prune -a --volumes
```

Check storage usage:
```bash
docker system df
```

## Troubleshooting

### Docker Daemon Not Running
```bash
# Start Docker daemon
sudo systemctl start docker

# Enable auto-start
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

### GPU Not Available in Container
```bash
# Check WSL2 can see GPU
rocm-smi

# Check device permissions
ls -la /dev/kfd /dev/dri

# Verify group membership
groups $USER
```

### Ollama Model Download Stuck
```bash
# Check Ollama logs
docker-compose logs ollama

# Try again with verbose output
docker exec ai-assistant-ollama ollama pull llama3.2:3b --verbose
```

### High Memory Usage
```bash
# Check what's consuming memory
docker stats

# Reduce model size
docker exec ai-assistant-ollama ollama pull phi3  # Smaller model
```

### Whisper Server Not Responding
```bash
# Check Whisper logs
docker-compose logs whisper-server

# Verify endpoint is accessible
curl -v http://localhost:8080/health
```

## Integration with Windows

### From PowerShell (Connect to Docker)

```powershell
# Install Python (if not already)
# Then configure to use Docker services

$env:OLLAMA_HOST = "http://localhost:11434"
$env:WHISPER_HOST = "http://localhost:8080"

python main.py
```

### Accessing Services from Windows Host

All services are exposed to Windows via port forwarding:
- **Ollama:** http://localhost:11434
- **Whisper:** http://localhost:8080

Use these URLs in your `.env` configuration on Windows.

## Next Steps

1. Follow QUICKSTART.md for usage
2. Check PROJECT_SUMMARY.md for architecture details
3. Review docker-compose.yml for configuration options
4. Explore the Python application in src/

## Support

- Check `docker-compose logs` for errors
- Review troubleshooting section above
- Consult GitHub Issues
- See main README.md for general help

---

**Happy building with WSL2 + Docker! 🚀**