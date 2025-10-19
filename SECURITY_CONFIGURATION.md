# Security Configuration Guide

## The wolf-logic System

The Windows AI Assistant uses a two-tier security model built around customizable keywords:

### Wake Word
**Default:** "wolf-logic"

- Activates the assistant
- Starts listening for your command
- Should be memorable to YOU
- Can be anything: "jarvis", "cortana", "activate", etc.

### Confirmation Keyword  
**Default:** "wolf-logic"

- Required to execute system-changing commands
- Prevents accidental/unauthorized system modifications
- Should be something ONLY YOU would know
- Can differ from wake word for extra security

## Why Customize?

### Security Through Obscurity
If someone hears you use the assistant, they won't know the confirmation keyword needed to execute high-risk commands.

```
Scenario 1: Not Customized
─────────────────────────
Attacker hears: "Wolf-logic, shutdown"
Attacker knows: Say "wolf-logic" to confirm
Risk: ⚠️ High - Confirmation keyword is public knowledge

Scenario 2: Customized
─────────────────────────
Attacker hears: "Falcon-eyes, shutdown"
Attacker does NOT know: Confirmation keyword is "authorize-delta"
Risk: ✅ Low - Can't execute high-risk commands without keyword
```

### Personal Identity
Your keywords become YOUR security signature. Nobody else has the same phrase.

## Customization Guide

### Step 1: Choose Your Wake Word

This is what you say to START listening. Make it:
- **Easy to pronounce** - You'll say it many times per day
- **Distinctive** - Shouldn't accidentally trigger from normal conversation
- **Personal** - Something meaningful to you

**Examples:**
- "Falcon-eyes"
- "Nexus"
- "Activate"
- "Cerebrum"
- "Illuminate"
- "Beacon"

### Step 2: Choose Your Confirmation Keyword

This is what you say to EXECUTE high-risk commands. Make it:
- **Hard to guess** - Don't use common words
- **Personal** - Something only YOU would use
- **Memorable** - You need to say it fast in stressful situations
- **Distinct from wake word** - Different phrase reduces confusion

**Examples:**
- "authorize-delta"
- "execute-omega"
- "confirm-bravo"
- "proceed-alpha"
- "approve-charlie"

**Safety Tip:** Use a phrase nobody would naturally say:
```
❌ Bad: "yes" (too common)
❌ Bad: "confirm" (too obvious)
❌ Bad: "admin" (too predictable)

✅ Good: "authorize-delta-seven"
✅ Good: "execute-my-command"
✅ Good: "proceed-falcon-alpha"
```

### Step 3: Configure in `.env`

Edit your `.env` file:

```bash
# Wake word - what you say to activate the assistant
WAKE_WORD=falcon-eyes

# Confirmation keyword - what you say to execute high-risk commands
CONFIRMATION_KEYWORD=authorize-delta-seven
```

### Step 4: Test Your Keywords

1. Start the assistant:
   ```powershell
   python main.py
   ```

2. Test wake word:
   - Say: "Falcon-eyes"
   - Assistant should respond: "Yes? How can I help you?"

3. Test safe command:
   - Say: "Open calculator"
   - Assistant should open calculator without asking for confirmation

4. Test confirmation system:
   - Say: "Shutdown"
   - Assistant should ask: "This will shutdown Windows. Say 'authorize-delta-seven' to confirm."
   - Say: "authorize-delta-seven"
   - Assistant should shutdown (or log the action if testing)

## Risk Levels & Confirmation

### Safe Commands (No Confirmation)
Execute immediately:
- "What time is it?"
- "Open calculator"
- "Launch Chrome"
- "What's the weather?"
- "Tell me a joke"

### Moderate Commands (Confirmation Required)
Require your confirmation keyword:
- "Create a text file"
- "Move this file to Documents"
- "Change desktop wallpaper"
- "Type this text"

### High-Risk Commands (Confirmation + Warning)
Require your confirmation keyword + explicit warning:
- "Delete this file"
- "Kill this process"
- "Disconnect from network"
- "Run this PowerShell command"

### Critical Commands (Detailed Confirmation)
Require your confirmation keyword + detailed explanation of consequences:
- "Shutdown the computer"
- "Restart Windows"
- "Edit the registry"
- "Modify system files"
- "Change admin settings"

## Multi-User Security

If multiple people use the same workstation:

### Option 1: Different Keywords Per User
Each user has their own configuration:

```bash
# User 1 (.env)
WAKE_WORD=user-one-activate
CONFIRMATION_KEYWORD=user-one-execute

# User 2 (.env)
WAKE_WORD=user-two-activate
CONFIRMATION_KEYWORD=user-two-execute
```

### Option 2: Shared Keywords with Awareness
If sharing the same .env:
- Use a neutral wake word: "assistant"
- Use a shared confirmation: "proceed"
- Add logging to track who said what (optional future feature)

### Option 3: Separate Instances
Each user runs their own Python process:
```powershell
# User 1
python main.py --config user1.env

# User 2
python main.py --config user2.env
```

## Advanced Security Tips

### 1. Pair with Screen Lock
Don't rely solely on keywords - also:
- Enable Windows Hello (face/fingerprint)
- Set automatic lock on idle
- Use full-disk encryption
- Keep Windows updated

### 2. Log Monitoring
Check logs regularly:
```powershell
Get-Content logs/assistant.log -Tail 50
```

### 3. Firewall Rules
If exposing via network:
- Only allow Tailscale IPs
- Block direct access
- Use Caddy reverse proxy (documented in AMD_GPU_SETUP.md)

### 4. Command Auditing
Review confirmed commands:
```bash
grep "COMMAND_CONFIRMED" logs/assistant.log
```

### 5. Voice Authentication (Future)
Consider adding:
- Voice biometrics (speaker verification)
- Multi-factor: keyword + voice pattern
- Time-based OTP for critical commands

## Resetting Your Keywords

If you forget or want to change:

1. **Edit `.env` file directly:**
   ```bash
   nano .env  # or use your text editor
   ```

2. **Set new values:**
   ```bash
   WAKE_WORD=new-wake-word
   CONFIRMATION_KEYWORD=new-confirmation
   ```

3. **Restart assistant:**
   ```powershell
   python main.py
   ```

New keywords take effect immediately.

## Emergency Override

If the assistant malfunctions:
1. Press `Ctrl+C` to stop it
2. Edit `.env` with new keywords
3. Restart the process

There's no backdoor - you always control your keywords.

## Recommendations

### For Home Use
```bash
WAKE_WORD=falcon        # Simple, distinctive
CONFIRMATION_KEYWORD=delta-seven  # Personal, memorable
```

### For Work/Enterprise
```bash
WAKE_WORD=business-mode           # Professional
CONFIRMATION_KEYWORD=authorize-executive-access  # Formal, clear
```

### For High Security
```bash
WAKE_WORD=alpha-activate-neural-link
CONFIRMATION_KEYWORD=authorize-critical-delta-niner
```

## Testing Checklist

Before using in production:
- [ ] Wake word is distinct (doesn't accidentally trigger)
- [ ] Confirmation keyword is memorable
- [ ] Keywords work in noisy environments
- [ ] You can say them quickly under stress
- [ ] Safe commands execute immediately
- [ ] High-risk commands require confirmation
- [ ] Confirmation actually prevents execution if not said
- [ ] Logs show correct commands being executed

---

## Security Philosophy

This assistant follows **security by design** principles:

1. **Default Deny** - Commands must be approved before execution
2. **Explicit Confirmation** - You must actively say the keyword
3. **User Control** - YOU decide the keywords, not us
4. **No Backdoors** - No master override, no cloud access
5. **Transparent Logging** - All actions logged locally for audit

**Your keywords = Your control.**

---

## Questions?

See also:
- [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) - Why these security choices
- [AMD_GPU_SETUP.md](AMD_GPU_SETUP.md) - Full deployment with Tailscale + Caddy
- [README.md](README.md) - General usage guide
