# Windows AI Assistant - Open Source Project

A fully local, privacy-first AI voice assistant for Windows that gives you complete voice control over your workstation - just like Google Assistant controls your phone, but for your desktop.

## Features

✅ **100% Local - No Cloud Dependencies**
- All AI processing happens on your machine via Ollama
- Speech recognition runs locally (Windows native or Whisper)
- Everything stays private - no data leaves your computer

✅ **Full Workstation Control**
- Launch applications and manage processes
- File operations (create, open, delete, move, copy)
- System control (shutdown, restart, lock, sleep)
- Window management and keyboard/mouse automation
- PowerShell command execution
- And much more...

✅ **Safe by Design**
- **Mandatory confirmation for all system changes** using "wolf-logic" keyword
- Risk-level classification (Safe/Moderate/High/Critical)
- Detailed audit logging of all commands
- Timeout protection for pending commands

✅ **Perfect Voice UX**
- Windows native speech recognition with perfect voice activity detection
- Stops listening after 1-2 seconds of silence (no endless listening like MacBook)
- Local Whisper support for higher accuracy if needed
- Works with any Bluetooth headphones (Sony WH-XB910N, etc.)

✅ **DirectML GPU Acceleration**
- Optimized for AMD, NVIDIA, and Intel GPUs
- Tested on AMD 7900 XT with ROCm/DirectML
- Leverages your hardware for blazing fast inference

✅ **Tailscale Network Ready**
- Works seamlessly over Tailscale VPN
- Access your assistant from anywhere
- No firewall configuration needed

✅ **Persistent Contextual Memory (Optional)**
- Integrates with mem0 local deployment
- 7,800+ stored memories across interactions
- Learns from every command (what works, what doesn't)
- References past decisions and user preferences
- Neo4J knowledge graph for intelligent reasoning
- Assistant gets smarter over time

## Hardware Requirements

### Minimum (Basic Usage)
- Windows 10 (build 17763 or later) or Windows 11
- 8GB RAM
- 20GB free disk space
- Intel/AMD CPU with 4+ cores
- CPU-only inference (slower, but functional)
- No GPU required

### Recommended (Good Experience)
- Windows 11 Pro or Pro for Workstations
- 16GB+ RAM
- 50GB free disk space
- GPU with 8GB+ VRAM (AMD, NVIDIA, Intel)
- Bluetooth headphones for voice I/O
- Ollama running natively on Windows

### Optimal (Best Performance - Enterprise)
- **Windows 11 Pro for Workstations** (recommended)
- **32GB+ RAM** (64GB+ for concurrent operations)
- **100GB+ SSD space** (for models and logs)
- **High-end GPU** (AMD 7900 XT, NVIDIA RTX 4090, etc.)
- **8-core+ CPU** (Intel i7/i9 or AMD Ryzen 7/9)
- Wired Gigabit+ networking or high-speed WiFi 6
- Professional audio interface with low-latency drivers
- Windows Feature Experience Pack installed

**Tested Configuration:**
- Intel Core i7-14700K @ 3.40 GHz
- 80GB DDR5 RAM
- AMD Radeon RX 7900 XT (24GB VRAM)
- Windows 11 Pro for Workstations Build 26220
- Tailscale VPN for networking
- Sony WH-XB910N Bluetooth headphones

## Installation

### 1. Prerequisites

```powershell
# Install Ollama from https://ollama.ai
# Download and install from the website

# Install Python 3.10+
# Download from https://www.python.org/

# Clone this repository
git clone https://github.com/yourusername/AI-Windows_Assistant.git
cd AI-Windows_Assistant
```

### 2. Create Conda Environment (Optional but Recommended)

```powershell
# For DirectML/Windows native GPU support:
conda create -n windows-ai python=3.10
conda activate windows-ai

# Or use DirectML-optimized environment:
conda create -n windows-ai-directml python=3.10
conda activate windows-ai-directml
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Ollama

```powershell
# Run the setup script
.\setup_ollama.ps1

# Or manually:
# 1. Download and install Ollama from https://ollama.ai
# 2. Pull a model: ollama pull llama3.2:3b
# 3. Start Ollama service (it runs in the background)
```

### 5. Configure the Assistant

Create a `.env` file in the project root from `.env.example`:

```env
# Ollama Configuration
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b

# Speech Recognition
WAKE_WORD=wolf-logic                    # Change this to your own wake word
USE_WHISPER=false
WHISPER_MODEL=base

# Text-to-Speech
TTS_RATE=200

# Security - Confirmation Keyword
CONFIRMATION_KEYWORD=wolf-logic         # Change this to your own keyword

# System Control
ALLOW_SYSTEM_CONTROL=true

# Logging
LOG_LEVEL=INFO
```

**Important**: The `.env.example` file has `WAKE_WORD` and `CONFIRMATION_KEYWORD` defaulted to `"wolf-logic"`. **Please customize these to your own values** when setting up your instance.
ALLOW_SYSTEM_CONTROL=true

# Logging
LOG_LEVEL=INFO

# Security - Confirmation keyword for all system changes
CONFIRMATION_KEYWORD=wolf-logic
```

## Usage

### Start the Assistant

```powershell
# Activate environment (if using conda)
conda activate windows-ai

# Run the assistant
python main.py
```

### Voice Commands

**Default Wake Word:** "wolf-logic" (customize in `.env`)

**Default Confirmation Keyword:** "wolf-logic" (customize in `.env`)

1. **Activate:** Say your wake word (default: "wolf-logic")
   - Assistant responds: "Yes? How can I help you?"
   - Now listening for your command

2. **Give Command:** Say what you want
   - "Open calculator"
   - "Launch chrome"  
   - "Shutdown the computer"
   - etc.

3. **Confirm if Needed:** For system-changing commands, assistant asks for confirmation
   - Assistant: "This will [action]. Say '[confirmation keyword]' to proceed."
   - You must explicitly say your confirmation keyword
   - Only then does the command execute

4. **Results:** Command is executed and logged

### Examples

**Safe Command (No Confirmation Needed):**
- You: "Wolf-logic, open calculator"
- Assistant: "Opening calculator..." ✓ (Executes immediately)

**High-Risk Command (Requires Confirmation):**
- You: "Wolf-logic, shutdown the computer"
- Assistant: "This will shutdown Windows. Say 'wolf-logic' to confirm."
- You: "Wolf-logic"
- Assistant: "Shutting down Windows..." ✓ (Executes after confirmation)

**Learning Over Time:**
- You: "Wolf-logic, what's my favorite browser?"
- Assistant: "Based on your history, I know you prefer Chrome. I've opened it 47 times."
- (After 100+ commands, the assistant remembers your patterns)

## Architecture

### Core Components

```
┌─────────────────────────────────────────┐
│  Windows AI Assistant                   │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────┐                   │
│  │  Speech Input   │ (Windows native   │
│  │                 │  or Whisper)      │
│  └────────┬────────┘                   │
│           │                            │
│  ┌────────▼─────────┐                 │
│  │  Wake Word       │                 │
│  │  Detection       │                 │
│  └────────┬─────────┘                 │
│           │                            │
│  ┌────────▼──────────────┐            │
│  │  Memory Retrieval     │ (optional) │
│  │  (mem0 integration)   │            │
│  └────────┬──────────────┘            │
│           │                            │
│  ┌────────▼──────────────┐            │
│  │  Command Processing   │            │
│  │  (Ollama AI Model)    │            │
│  └────────┬──────────────┘            │
│           │                            │
│  ┌────────▼──────────────┐            │
│  │  Risk Assessment &    │            │
│  │  Confirmation System  │            │
│  │  (wolf-logic keyword) │            │
│  └────────┬──────────────┘            │
│           │                            │
│  ┌────────▼──────────────┐            │
│  │  Memory Storage       │ (optional) │
│  │  (Save to mem0)       │            │
│  └────────┬──────────────┘            │
│           │                            │
│  ┌────────▼──────────────┐            │
│  │  Device Control       │            │
│  │  Execution           │            │
│  └────────┬──────────────┘            │
│           │                            │
│  ┌────────▼──────────────┐            │
│  │  Text-to-Speech      │            │
│  │  Response Output     │            │
│  └──────────────────────┘            │
│                                       │
└─────────────────────────────────────────┘
        ↕ (Ollama on localhost:11434)
```

### GPU Architecture by Hardware

Choose the setup that matches your GPU:

#### **AMD GPU** (Recommended for this project)
- **Ollama**: Windows native (DirectML acceleration)
- **Whisper**: WSL native (ROCm acceleration)  
- **Setup Guide**: See [AMD_GPU_SETUP.md](AMD_GPU_SETUP.md)
- **Tested**: AMD Radeon RX 7900 XT (24GB VRAM)

#### **NVIDIA GPU**
- **Ollama**: Docker container with CUDA support
- **Whisper**: Docker container with CUDA support
- **Setup Guide**: See [NVIDIA_DOCKER_SETUP.md](NVIDIA_DOCKER_SETUP.md) (coming soon)

#### **No GPU / CPU Only**
- **Ollama**: CPU inference
- **Whisper**: CPU inference
- **Setup Guide**: See [CPU_ONLY_SETUP.md](CPU_ONLY_SETUP.md) (slower but works)

### Persistent Memory Architecture (Optional)

```
Voice Input
    ↓
┌─────────────────────────────────────────────────┐
│  Retrieval Agent (SSE Stream, Port 8765)        │
│  - Extracts relevant memories from user input   │
│  - Continuous 5-second processing loop         │
└──────────┬──────────────────────────────────────┘
           ↓ SSE Streaming
┌──────────────────────────────────────────────────┐
│  Memory Injection into LLM Prompt               │
│  - Retrieve past context (7,800+ memories)      │
│  - Inject into system prompt for context        │
│  - Assistant becomes contextually aware         │
└──────────┬──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────┐
│  Ollama Generates Response                       │
│  - Uses historical context for better reasoning │
│  - References past decisions                    │
│  - Learns user preferences                      │
└──────────┬──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────┐
│  Store Interaction in mem0                      │
│  - PostgreSQL: Raw interaction data             │
│  - Vector DB: Semantic embeddings               │
│  - Neo4J: Knowledge graph relationships         │
│  - Builds institutional knowledge over time     │
└──────────────────────────────────────────────────┘
```

**Result:** Assistant learns from every interaction. Same question asked tomorrow gets a smarter answer because it remembers today's context.

See [MEMORY_INTEGRATION.md](MEMORY_INTEGRATION.md) for detailed explanation of how persistent memory works.

## Project Structure

```
AI-Windows_Assistant/
├── main.py                          # Entry point
├── requirements.txt                 # Python dependencies
├── setup_ollama.ps1                # Ollama setup script
├── .env                            # Configuration (create this)
│
├── src/
│   ├── core/
│   │   └── assistant.py           # Main assistant class
│   ├── config/
│   │   └── settings.py            # Configuration management
│   ├── ai/
│   │   └── ollama_client.py       # Ollama API client
│   ├── speech/
│   │   └── recognition.py         # Speech recognition engine
│   └── control/
│       └── device_controller.py    # Windows device control
│
├── logs/                           # Application logs
├── docker/                         # Docker files (optional)
│   └── whisper/
│       └── Dockerfile             # Whisper server container
│
├── README.md                       # This file
├── Build Phases                    # Implementation guide
└── LICENSE                         # MIT License
```

## Security Model

### Risk Levels

- **SAFE:** Executed immediately (query questions, info, etc.)
- **MODERATE:** Requires "wolf-logic" confirmation (file operations, app launch)
- **HIGH:** Requires "wolf-logic" + warning (process termination, system changes)
- **CRITICAL:** Requires "wolf-logic" + detailed warning (shutdown, registry edits, PowerShell)

### Confirmation Timeout

Commands require confirmation within 30 seconds. After that, the pending command expires for safety.

### Audit Logging

All commands and confirmations are logged to `logs/assistant.log` for transparency and debugging.

## Advanced Configuration

### Using Local Whisper (Higher Accuracy)

Edit `.env`:
```env
USE_WHISPER=true
WHISPER_MODEL=base  # or small, medium, large
```

### Using Tailscale

```env
USE_TAILSCALE=true
OLLAMA_HOST=<your-tailscale-ip>
```

### DirectML GPU Optimization

The system automatically detects and uses your GPU. For manual configuration:

```env
USE_DIRECTML=true
DIRECTML_DEVICE_ID=0
```

## Troubleshooting

### Ollama Connection Failed
- Ensure Ollama is installed and running
- Check `localhost:11434` is accessible
- Run: `ollama serve` in a separate terminal

### Speech Recognition Not Working
- Ensure microphone is properly connected and configured
- Check Windows sound settings
- Try: `Settings → Privacy & security → Microphone`

### Commands Not Executing
- Check `logs/assistant.log` for errors
- Verify the command risk level
- Make sure to say "wolf-logic" to confirm

### GPU Not Being Used
- Verify DirectML drivers are installed
- Check NVIDIA/AMD GPU drivers are up to date
- View Ollama logs for acceleration status

## Development

### Running Tests
```powershell
pytest tests/
```

### Adding New Commands
See `src/control/device_controller.py` for the command system architecture.

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Future Enhancements

- [ ] WinUI 3 desktop application UI
- [ ] Sony WH-XB910N headphone button integration
- [ ] Advanced intent parsing with entity extraction
- [ ] Custom voice profiles and training
- [ ] Multi-user support with voice identification
- [ ] Integration with Windows Task Scheduler
- [ ] Webhook support for external integrations
- [ ] Mobile companion app

## License

MIT License - See LICENSE file for details

## Support

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Documentation:** See `Build Phases` file for implementation details

## Disclaimer

This is an advanced system that gives AI voice control over your computer. Always review commands before confirming execution. The developers are not responsible for accidental system changes. Use responsibly.

## Acknowledgments

- Built with [Ollama](https://ollama.ai) for local LLM inference
- Speech recognition via [Whisper](https://github.com/openai/whisper) and Windows native APIs
- Inspired by Google Assistant, Alexa, and Cortana
- Designed for privacy-conscious developers

---

**Made with ❤️ for the open source community**
