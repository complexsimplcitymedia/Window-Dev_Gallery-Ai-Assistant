# Windows AI Assistant - Complete Project Files

## 📋 Index of All Project Files

### 📁 Root Directory Files

#### Documentation
- **README.md** - Full project documentation, features, architecture, installation guide
- **QUICKSTART.md** - 5-minute setup guide for first-time users
- **CONTRIBUTING.md** - How to contribute code and improvements
- **PROJECT_SUMMARY.md** - Complete project overview and status
- **LICENSE** - MIT License with AI safety disclaimer
- **Build Phases** - Original implementation planning document

#### Configuration
- **.env.example** - Configuration template (copy to .env and customize)
- **.env** - Your personalized configuration (create from .env.example)

#### Python Application
- **main.py** - Entry point, initializes and runs the assistant
- **requirements.txt** - All Python dependencies (pip install -r requirements.txt)

#### Setup & Deployment
- **setup_ollama.ps1** - PowerShell script to install and configure Ollama
- **docker-compose.yml** - Docker Compose configuration (optional WSL/container setup)
- **WindowsAIAssistant.csproj** - Legacy C# project file (can be removed)

#### Additional Files
- **Modelfile** - Ollama model configuration
- **README.pdf** - Original PDF documentation
- **.README.md.kate-swp** - Text editor temporary file (can be removed)

---

### 📁 src/ - Application Source Code

#### src/core/
- **assistant.py** - Main WindowsAIAssistant class
  - Orchestrates all components
  - Manages speech recognition
  - Processes AI responses
  - Handles device control
  - Manages conversation history

#### src/config/
- **settings.py** - Configuration management
  - AssistantSettings (Pydantic model)
  - load_config() function
  - All configuration options defined here

#### src/ai/
- **ollama_client.py** - Ollama API client
  - OllamaClient class
  - OllamaResponse dataclass
  - HTTP communication with Ollama server
  - Streaming and non-streaming support
  - Model management

#### src/speech/
- **recognition.py** - Speech recognition engine
  - SpeechRecognitionManager class
  - SpeechEngine enum (WINDOWS_NATIVE, WHISPER_LOCAL, WHISPER_SERVER)
  - Wake word detection
  - Voice activity detection
  - Command processing callbacks
  - Audio capture and processing

#### src/control/
- **device_controller.py** - Windows device control
  - WindowsDeviceController class
  - CommandRiskLevel enum (SAFE, MODERATE, HIGH, CRITICAL)
  - PendingCommand dataclass
  - Command confirmation system ("wolf-logic" keyword)
  - Device control implementations:
    - Application launching
    - File operations
    - System commands
    - PowerShell execution
    - Window management
    - Input automation

---

### 📁 docker/ - Container Deployment (Optional)

#### docker/whisper/
- **Dockerfile** - Container image for Whisper speech recognition server
- **requirements.txt** - Python dependencies for Whisper container
- **whisper_server.py** - FastAPI server for Whisper transcription

**Note:** Docker setup is optional. Native Windows installation is recommended for better GPU support.

---

## 🗂️ Directory Structure

```
AI-Windows_Assistant/
│
├── 📄 Root Files (Documentation & Config)
│   ├── README.md                      ← Start here!
│   ├── QUICKSTART.md                 ← 5-min setup
│   ├── CONTRIBUTING.md               ← Want to help?
│   ├── PROJECT_SUMMARY.md            ← Full project overview
│   ├── LICENSE                       ← MIT License
│   ├── Build Phases                  ← Original planning
│   │
│   ├── .env.example                  ← Copy to .env
│   ├── .env                          ← Your config (create this)
│   │
│   ├── main.py                       ← Start here (run this)
│   ├── requirements.txt              ← Dependencies
│   │
│   ├── setup_ollama.ps1             ← Ollama setup script
│   ├── docker-compose.yml            ← Docker (optional)
│   └── WindowsAIAssistant.csproj    ← Legacy C# (can remove)
│
├── 📁 src/                           ← Application source code
│   ├── core/
│   │   └── assistant.py             ← Main assistant class
│   │
│   ├── config/
│   │   └── settings.py              ← Configuration
│   │
│   ├── ai/
│   │   └── ollama_client.py         ← Ollama API client
│   │
│   ├── speech/
│   │   └── recognition.py           ← Speech recognition
│   │
│   └── control/
│       └── device_controller.py     ← Device control
│
├── 📁 docker/                        ← Container files (optional)
│   └── whisper/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── whisper_server.py
│
├── 📁 logs/                          ← Application logs (created at runtime)
│   └── assistant.log                ← All operations logged here
│
└── 📁 models/                        ← Local model storage (optional)
    └── (Ollama models go here)
```

---

## 🚀 Quick Reference

### To Get Started
1. Read: **README.md**
2. Follow: **QUICKSTART.md**
3. Run: `python main.py`

### For Development
1. Read: **CONTRIBUTING.md**
2. Explore: **src/** directory
3. Check: **PROJECT_SUMMARY.md** for architecture

### For Configuration
1. Copy: `.env.example` → `.env`
2. Edit: `.env` with your settings
3. Reference: `.env.example` for all options

### For Troubleshooting
1. Check: `logs/assistant.log`
2. Review: **README.md** troubleshooting section
3. Search: **CONTRIBUTING.md** for issues

### For Docker (Optional)
1. Review: `docker-compose.yml`
2. Run: `docker-compose up`
3. Note: Native Windows is recommended

---

## 📊 File Statistics

### Documentation (6 files)
- README.md - Complete guide
- QUICKSTART.md - Getting started
- CONTRIBUTING.md - Developer guide
- PROJECT_SUMMARY.md - Project overview
- LICENSE - Legal
- Build Phases - Planning

### Configuration (2 files)
- .env.example - Configuration template
- .env - User configuration

### Application Code (5 files)
- main.py - Entry point
- src/core/assistant.py - Main class
- src/config/settings.py - Configuration
- src/ai/ollama_client.py - Ollama integration
- src/speech/recognition.py - Speech I/O
- src/control/device_controller.py - Device control

### Setup & Deployment (3 files)
- requirements.txt - Dependencies
- setup_ollama.ps1 - Ollama setup
- docker-compose.yml - Docker compose

### Optional/Legacy (4 files)
- WindowsAIAssistant.csproj - Legacy C#
- docker/whisper/* - Container setup
- Modelfile - Ollama config
- README.pdf - Original PDF

**Total:** ~24 files covering all aspects of the project

---

## 🔄 Data Flow

```
User Voice Input
     ↓
src/speech/recognition.py (Wake word detection)
     ↓
src/core/assistant.py (Command processing)
     ↓
src/ai/ollama_client.py (AI inference via Ollama)
     ↓
src/control/device_controller.py (Risk assessment)
     ↓
User Confirmation (if needed - say "wolf-logic")
     ↓
Execute Command
     ↓
Response via TTS
     ↓
logs/assistant.log (Audit trail)
```

---

## 📝 Configuration Reference

All settings are in `.env` (copy from `.env.example`):

```
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b
WAKE_WORD=assistant
USE_WHISPER=false
WHISPER_MODEL=base
TTS_RATE=200
USE_DIRECTML=true
ALLOW_SYSTEM_CONTROL=true
CONFIRMATION_KEYWORD=wolf-logic
LOG_LEVEL=INFO
LOG_FILE=logs/assistant.log
```

See `.env.example` for complete documentation on each option.

---

## 🛠️ Development Workflow

1. **Setup**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Configure**
   ```powershell
   copy .env.example .env
   # Edit .env with your settings
   ```

3. **Run**
   ```powershell
   python main.py
   ```

4. **Modify Code**
   - Edit files in `src/`
   - Follow PEP 8 style
   - Add type hints
   - Test thoroughly

5. **Test**
   ```powershell
   pytest tests/
   ```

6. **Commit**
   ```powershell
   git add .
   git commit -m "descriptive message"
   git push origin feature/branch-name
   ```

7. **Submit PR**
   - Create pull request on GitHub
   - Reference related issues
   - Wait for review

---

## 🎯 Next Steps

- **For Users:** Start with QUICKSTART.md
- **For Developers:** Read CONTRIBUTING.md and explore src/
- **For Operators:** Review .env.example and setup_ollama.ps1
- **For Everyone:** Check out PROJECT_SUMMARY.md for full details

---

## 📞 Support

- **Issues:** GitHub Issues
- **Questions:** GitHub Discussions
- **Documentation:** README.md
- **Contributing:** CONTRIBUTING.md

---

**Welcome to the Windows AI Assistant project! 🤖**

*This is an open-source project built by and for the community.*