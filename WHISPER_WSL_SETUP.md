# Whisper Server Setup for WSL (Native GPU Support)

This guide sets up OpenAI Whisper as a FastAPI server running natively in WSL2 with GPU acceleration (ROCm for AMD).

## Why WSL Native Whisper?

- **Better GPU Support**: Direct ROCm access for AMD GPUs
- **No Docker Overhead**: Lighter weight than Docker container
- **Easier Reverse Proxy**: Native WSL networking, easier to reverse proxy via Caddy
- **Direct Integration**: Python subprocess in same WSL environment
- **Better Logging**: Direct access to stdout/stderr

## Prerequisites

- Windows 11 with WSL2 enabled
- Ubuntu 22.04 or later in WSL
- GPU (optional, CPU works but slower)

## Quick Setup (5 minutes)

### Step 1: Copy Setup Script to WSL

From PowerShell:
```powershell
# Copy setup script to WSL
wsl -- cp /mnt/c/Users/<YourUsername>/Window-Dev_Gallery-Ai-Assistant/setup_whisper_wsl.sh ~/
```

### Step 2: Run Setup in WSL

```bash
# Open WSL
wsl

# Make script executable
chmod +x ~/setup_whisper_wsl.sh

# Run setup
~/setup_whisper_wsl.sh
```

This will:
- Install Miniconda (if needed)
- Create `whisper-server` Conda environment
- Install all dependencies
- Download Whisper `base` model (~140MB)

### Step 3: Test the Server

```bash
# Activate environment
conda activate whisper-server

# Run server
python ~/Window-Dev_Gallery-Ai-Assistant/docker/whisper/whisper_server.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:5000
```

### Step 4: Test from Windows PowerShell

```powershell
# Get WSL IP address
$wslIP = wsl -- hostname -I | %{$_.split()[0]}
echo $wslIP

# Test health endpoint
curl.exe "http://$wslIP:5000/health"
```

Should return:
```json
{
  "status": "healthy",
  "model": "base",
  "device": "cpu",
  "model_loaded": true
}
```

## Configuration

### Environment Variables

Create `.env` file in WSL project root:

```bash
export WHISPER_MODEL=base        # tiny, base, small, medium, large
export WHISPER_DEVICE=cpu        # cpu, cuda, rocm (AMD GPU)
export WHISPER_LANGUAGE=en       # Language code
export WHISPER_PORT=5000         # Listen port
```

### Enable GPU Acceleration (AMD)

#### For ROCm GPU in WSL:

1. **Install ROCm in WSL:**
   ```bash
   wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -
   echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/debian focal main' | sudo tee /etc/apt/sources.list.d/rocm.list
   sudo apt update
   sudo apt install rocm-dkms
   ```

2. **Activate Conda environment and reinstall PyTorch with ROCm:**
   ```bash
   conda activate whisper-server
   pip uninstall torch torchaudio torchvision -y
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7
   ```

3. **Set device in environment:**
   ```bash
   export WHISPER_DEVICE=rocm
   ```

## Auto-Start on WSL Boot

### Option 1: Systemd Service (Recommended)

1. **Edit systemd service file:**
   ```bash
   sudo nano whisper-server.service
   ```

2. **Replace placeholders:**
   - `<YOUR_WSL_USERNAME>` → Your WSL username (e.g., `ubuntu`)
   - Path to project directory

3. **Install service:**
   ```bash
   sudo cp whisper-server.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable whisper-server
   sudo systemctl start whisper-server
   ```

4. **Check status:**
   ```bash
   sudo systemctl status whisper-server
   ```

### Option 2: Bash Alias (Simple)

Add to `~/.bashrc`:

```bash
alias whisper-start='conda activate whisper-server && python ~/Window-Dev_Gallery-Ai-Assistant/docker/whisper/whisper_server.py &'
```

Then run:
```bash
whisper-start
```

## Reverse Proxy Setup (Caddy)

To expose Whisper via reverse proxy (e.g., `whisper.yourdomain.com`):

### In Caddy config:

```
whisper.yourdomain.com {
    reverse_proxy localhost:5000 {
        header_up X-Real-IP {http.request.remote.host}
        header_up X-Forwarded-For {http.request.remote.host}
        header_up X-Forwarded-Proto https
    }
}
```

### In Windows AI Assistant `.env`:

```env
# Use Caddy reverse proxy URL instead of direct WSL IP
WHISPER_SERVER_URL=https://whisper.yourdomain.com
```

## API Usage

### Health Check

```bash
curl http://localhost:5000/health
```

### Transcribe Audio

```bash
# Transcribe audio file
curl -X POST -F "file=@audio.wav" http://localhost:5000/transcribe
```

Response:
```json
{
  "text": "Hello, how are you?",
  "language": "en",
  "segments": [
    {
      "id": 0,
      "seek": 0,
      "start": 0.0,
      "end": 1.2,
      "text": "Hello, how are you?",
      "tokens": [50258, 2425, 11, 577, 366, 291, 30],
      "temperature": 0.0,
      "avg_logprob": -0.273,
      "compression_ratio": 1.12,
      "no_speech_prob": 0.001
    }
  ],
  "model": "base"
}
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'whisper'"

```bash
conda activate whisper-server
pip install openai-whisper
```

### "CUDA/ROCm not found"

Check device setting:
```bash
python -c "import torch; print(torch.cuda.is_available())"  # NVIDIA
python -c "import torch; print(torch.version.hip)"           # AMD ROCm
```

### Port 5000 Already in Use

```bash
# Find process using port
lsof -i :5000

# Kill it or use different port
export WHISPER_PORT=8001
```

### WSL IP Unreachable from Windows

Enable WSL networking:
```powershell
# In PowerShell as admin
wsl -l -v  # List WSL instances
wsl -e ip addr  # Get WSL IP
```

Try `127.0.0.1:5000` first (localhost forwarding works in recent WSL versions).

## Performance Tips

1. **Use `base` or `small` model** for real-time (faster)
   - `base`: ~1 second for 30-second audio
   - `small`: ~2 seconds for 30-second audio

2. **Pre-warm model** on startup to avoid first-request delay

3. **Enable GPU** for 2-3x speed improvement

4. **Batch requests** if transcribing multiple files

## Next Steps

- Configure Windows AI Assistant to use Whisper server:
  ```env
  USE_WHISPER=true
  WHISPER_SERVER_URL=http://localhost:5000  # or your reverse proxy URL
  ```

- Set up Caddy reverse proxy for secure external access

- Monitor with: `journalctl -u whisper-server -f`
