# Setup - Copy & Paste Ready

Follow these exact steps in order. Replace `<PLACEHOLDER>` with your values.

## Step 1: Install Prerequisites

```powershell
# Install Ollama from website
# Download from: https://ollama.ai
# Run installer, restart PowerShell when done

# Verify Ollama installed
ollama --version
```

## Step 2: Pull Ollama Model

```powershell
# Download the AI model (3-5 minutes, ~2GB)
ollama pull llama3.2:3b
```

## Step 3: Clone Repository

```powershell
cd <YOUR_PROJECTS_FOLDER>
git clone https://github.com/complexsimplcitymedia/Window-Dev_Gallery-Ai-Assistant.git
cd Window-Dev_Gallery-Ai-Assistant
```

## Step 4: Create .env File

```powershell
# Copy template
Copy-Item .env.example .env

# Edit .env with your values
notepad .env
```

**In .env, change these:**
```env
WAKE_WORD=<your-custom-word>                    # Example: "activate", "hey-there", "roger"
CONFIRMATION_KEYWORD=<your-custom-keyword>     # Example: "confirm", "approved", "do-it"
OLLAMA_MODEL=llama3.2:3b                        # Use this model
```

## Step 5: Install Python Dependencies

```powershell
# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
```

## Step 6: Start Ollama Service

```powershell
# Open NEW PowerShell window, run:
ollama serve
# Leave this running in the background
```

## Step 7: Run the Assistant

```powershell
# In the ORIGINAL PowerShell window (with venv activated):
python main.py
```

**You should see:**
```
[INFO] Starting Windows AI Assistant...
[INFO] Connecting to Ollama at 127.0.0.1:11434...
[INFO] Speech recognition initialized
[INFO] Assistant ready. Say: "<your-wake-word>"
```

## Step 8: Test It

Say: `"<your-wake-word>, open calculator"`

Assistant responds: "Opening calculator..."

✅ **Done!**

---

## Optional: Persistent Memory (mem0)

To enable learning from past commands:

1. Ensure mem0 containers are running (see DEPLOYMENT.md)
2. Set in .env:
   ```env
   ENABLE_PERSISTENT_MEMORY=true
   MEM0_API_URL=https://mem0-api.complexsimplicity.com
   MEM0_API_KEY=<your-mem0-key>
   ```
3. Restart: `python main.py`

---

## Troubleshooting

**"Ollama not found"**
- Install from https://ollama.ai and restart PowerShell

**"ModuleNotFoundError"**
- Run: `pip install -r requirements.txt` again

**Assistant doesn't respond to wake word**
- Verify: `WAKE_WORD=<your-word>` in .env (case-sensitive)
- Check microphone is working: Settings → Sound → Input devices

**"Connection refused" to Ollama**
- Make sure `ollama serve` is running in separate window
- Verify at: http://127.0.0.1:11434/api/tags

---

## Next Steps

- Read [QUICKSTART.md](QUICKSTART.md) for voice command examples
- Read [SECURITY_CONFIGURATION.md](SECURITY_CONFIGURATION.md) to customize security
- Read [AMD_GPU_SETUP.md](AMD_GPU_SETUP.md) for GPU optimization
