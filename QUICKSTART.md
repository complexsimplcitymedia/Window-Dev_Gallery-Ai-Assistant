# Windows AI Assistant - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Ollama (2 minutes)
1. Download from https://ollama.ai
2. Run the installer
3. Open PowerShell and verify:
   ```powershell
   ollama --version
   ```

### Step 2: Clone & Install (2 minutes)
```powershell
# Clone the repository
git clone https://github.com/yourusername/AI-Windows_Assistant.git
cd AI-Windows_Assistant

# Copy example config
copy .env.example .env

# IMPORTANT: Customize your keywords in .env
# Edit the file and change:
# - WAKE_WORD: What you say to activate (default: "wolf-logic")
# - CONFIRMATION_KEYWORD: What you say to execute high-risk commands (default: "wolf-logic")
notepad .env

# Install Python dependencies
pip install -r requirements.txt
```

**Keyword Customization:**
- Make up your own wake word and confirmation keyword
- Don't use the defaults if sharing your workstation
- See [SECURITY_CONFIGURATION.md](SECURITY_CONFIGURATION.md) for best practices

### Step 3: Start Ollama (1 minute)
```powershell
# In a new PowerShell terminal, start Ollama
ollama serve

# In another terminal, pull a model (first time only)
ollama pull llama3.2:3b
```

### Step 4: Run the Assistant (1 minute)
```powershell
# In your project directory
python main.py
```

**That's it!** Your Windows AI Assistant is running.

---

## First Use

**Your Keywords:**
- **Wake Word:** Whatever you set in `.env` (default: "wolf-logic")
- **Confirmation Keyword:** Whatever you set in `.env` (default: "wolf-logic")

1. **Say the wake word:** "wolf-logic" (or your custom word)
   - Assistant responds: "Yes? How can I help you?"
2. **Give a command:** "open calculator"
3. **Wait for response:** AI confirms the action
4. **If confirmation needed:** Say your confirmation keyword to execute

---

## First Use Example

**Customized Setup:**
```
WAKE_WORD=falcon-eyes
CONFIRMATION_KEYWORD=authorize-delta
```

**Usage:**
- You: "Falcon-eyes"
- Assistant: "Yes? How can I help you?"
- You: "Shutdown the computer"
- Assistant: "This will shutdown Windows. Say 'authorize-delta' to confirm."
- You: "authorize-delta"
- Assistant: "Shutting down..."

---

## Common First Commands to Try

### Safe Commands (No Confirmation Needed)
- "Assistant, what time is it?"
- "Assistant, tell me a joke"
- "Assistant, open calculator"
- "Assistant, open notepad"

### Commands Needing Confirmation
- "Assistant, delete the file on my desktop" → Say "wolf-logic" to confirm
- "Assistant, shutdown my computer" → Say "wolf-logic" to confirm

---

## Troubleshooting First Run

### "Failed to connect to Ollama server"
```powershell
# Make sure Ollama is running in another terminal
ollama serve

# Verify it's accessible
curl http://127.0.0.1:11434/api/tags
```

### "No audio input detected"
1. Check Windows sound settings
2. Select your microphone as default input device
3. Restart the assistant

### "Command takes forever to respond"
- First time loading the model takes longer
- Subsequent commands are faster
- Smaller models (llama3.2:3b) are faster than larger ones

---

## Next Steps

1. **Customize Configuration**
   - Edit `.env` to change wake word, model, etc.
   - See `.env.example` for all options

2. **Explore Commands**
   - Try different AI models: `ollama pull phi3`
   - Experiment with voice commands
   - Check `logs/assistant.log` for what's happening

3. **Advanced Setup**
   - Use Whisper for higher accuracy (set `USE_WHISPER=true` in `.env`)
   - Enable Tailscale for remote access
   - Configure DirectML for your GPU

4. **Contribute**
   - Report issues on GitHub
   - Share your custom commands
   - Help improve the project

---

## Getting Help

- **Check logs:** `type logs/assistant.log`
- **GitHub Issues:** https://github.com/yourusername/AI-Windows_Assistant/issues
- **Documentation:** See README.md for full details

---

## Security Reminders

✅ **Always review commands before confirming with "wolf-logic"**
✅ **Audit log is saved for your review**
✅ **No data leaves your computer**
✅ **Everything runs locally on your workstation**

---

**Enjoy your personal AI assistant! 🤖**