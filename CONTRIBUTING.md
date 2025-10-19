# Contributing to Windows AI Assistant

Thank you for your interest in contributing! This is an open-source project and we welcome contributions from the community.

## Code of Conduct

Be respectful, inclusive, and professional. We're building this together.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/AI-Windows_Assistant.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Submit a pull request

## Areas We Need Help With

### High Priority
- [ ] **WinUI 3 Desktop Application** - Modern Windows UI for the assistant
- [ ] **Sony WH-XB910N Button Integration** - Capture headphone assistant button
- [ ] **Advanced Intent Parsing** - Better command understanding
- [ ] **Custom Voice Profiles** - User-specific voice training
- [ ] **Unit Tests** - Improve test coverage

### Medium Priority
- [ ] **Multi-user Support** - Voice identification for different users
- [ ] **Webhook Integration** - Trigger external services
- [ ] **Task Scheduler Integration** - Schedule commands
- [ ] **Documentation Improvements** - More examples and guides
- [ ] **Performance Optimization** - Faster response times

### Lower Priority
- [ ] **Mobile Companion App** - Control from phone
- [ ] **Browser Extension** - Web integration
- [ ] **Third-party LLM Support** - Beyond Ollama
- [ ] **Visual Feedback System** - Better UI/UX indicators

## Development Setup

### Windows Setup
```powershell
# Clone the repository
git clone https://github.com/yourusername/AI-Windows_Assistant.git
cd AI-Windows_Assistant

# Create conda environment
conda create -n windows-ai-dev python=3.10
conda activate windows-ai-dev

# Install dependencies including dev tools
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8

# Run tests
pytest tests/
```

### Code Style
- Follow PEP 8
- Use type hints where possible
- Format with `black`: `black src/`
- Lint with `flake8`: `flake8 src/`

## Making Changes

### 1. Identify an Issue or Feature
- Check existing issues on GitHub
- Create a new issue if your idea isn't listed
- Discuss your approach before starting large changes

### 2. Create a Feature Branch
```bash
git checkout -b feature/descriptive-name
```

### 3. Make Your Changes
- Keep commits focused and atomic
- Write clear commit messages
- Include tests for new functionality
- Update documentation as needed

### 4. Test Your Changes
```bash
# Run tests
pytest tests/

# Test manually with your changes
python main.py

# Check logs
type logs/assistant.log
```

### 5. Submit a Pull Request
- Push to your fork
- Create a PR against the main repository
- Describe what your changes do
- Reference any related issues
- Wait for review and feedback

## Pull Request Guidelines

### Description Should Include
- What problem does this solve?
- How does it solve it?
- Any breaking changes?
- Testing you've done

### Before Submitting
- [ ] Code passes all tests
- [ ] Code is properly formatted (`black`)
- [ ] Code passes linting (`flake8`)
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No secrets or sensitive data in code

## Adding New Commands

### 1. Define the Command
Edit `src/control/device_controller.py`:

```python
self.command_risks = {
    "your_new_command": CommandRiskLevel.SAFE,  # or MODERATE/HIGH/CRITICAL
}
```

### 2. Implement the Handler
```python
async def _your_new_command(self, param1: str, param2: int) -> Dict[str, Any]:
    """Implementation of your_new_command"""
    try:
        # Your code here
        return {
            "success": True,
            "message": "Success message",
            "data": {"result": "data"}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }
```

### 3. Add to Executor
In `_execute_internal()`:
```python
elif command == "your_new_command":
    return await self._your_new_command(...)
```

### 4. Test It
```python
# In a test file
@pytest.mark.asyncio
async def test_your_new_command():
    controller = WindowsDeviceController()
    result = await controller.execute_command("your_new_command", param1="test")
    assert result["success"] == True
```

## Improving Speech Recognition

Currently supporting:
- Windows Native Speech Recognition (default)
- Local Whisper

To add new recognition engines:

1. Create new class in `src/speech/recognition.py`
2. Implement `SpeechEngine` interface
3. Add to `SpeechRecognitionManager`
4. Document in README

## Performance Optimization

If you're working on performance:
1. Profile the code: `python -m cProfile -s cumulative main.py`
2. Identify bottlenecks
3. Test improvements with benchmarks
4. Document performance impact

## Documentation

### Code Comments
- Explain the "why", not the "what"
- Use docstrings for all functions/classes
- Include type hints

### User Documentation
- Update README.md for major features
- Add examples to QUICKSTART.md
- Update Build Phases for implementation details

## Reporting Issues

### When Reporting a Bug
- Describe steps to reproduce
- Include error messages and logs
- Share your configuration (OS, GPU, etc.)
- What did you expect vs. what happened?

### Example Issue Report
```
**Description:** Assistant crashes when launching apps with spaces in name

**Steps to Reproduce:**
1. Say "Assistant, open Visual Studio"
2. Observe error

**Environment:**
- Windows 11 Pro
- Python 3.10
- AMD 7900 XT
- Ollama llama3.2:3b

**Error Log:**
[paste relevant error]

**Expected Behavior:**
Visual Studio should launch successfully
```

## Questions?

- Open a GitHub Discussion
- Create an Issue with [QUESTION] tag
- Check existing documentation

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in releases
- Featured in project documentation

Thank you for contributing to make AI accessible to everyone! 🎉