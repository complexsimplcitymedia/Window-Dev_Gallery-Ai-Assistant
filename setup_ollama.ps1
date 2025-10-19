# Windows AI Assistant Setup Scripts
# Native Windows execution with DirectML for AMD 7900 XT

# PowerShell script to install and configure Ollama with DirectML
Write-Host "Setting up Windows AI Assistant with native Ollama + DirectML..." -ForegroundColor Green

# Check if Ollama is installed
if (-not (Get-Command "ollama" -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Ollama for Windows..." -ForegroundColor Yellow
    # Download and install Ollama
    Invoke-WebRequest -Uri "https://ollama.ai/download/windows" -OutFile "$env:TEMP\ollama-windows-amd64.exe"
    Start-Process "$env:TEMP\ollama-windows-amd64.exe" -Wait
}

# Set environment variables for DirectML with AMD ROCm
$env:OLLAMA_HOST = "127.0.0.1:11434"
$env:HSA_OVERRIDE_GFX_VERSION = "11.0.0"
$env:ROC_ENABLE_PRE_VEGA = "1"
$env:GPU_MAX_ALLOC_PERCENT = "95"
$env:GPU_SINGLE_ALLOC_PERCENT = "95"

# Start Ollama service
Write-Host "Starting Ollama service with DirectML support..." -ForegroundColor Yellow
Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden

# Wait for service to start
Start-Sleep -Seconds 5

# Pull the default model
Write-Host "Pulling llama3.2:3b model..." -ForegroundColor Yellow
ollama pull llama3.2:3b

Write-Host "Ollama setup complete! Service running on localhost:11434" -ForegroundColor Green