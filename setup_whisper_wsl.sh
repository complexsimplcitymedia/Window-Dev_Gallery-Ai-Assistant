#!/bin/bash
# Setup Whisper Server in WSL with Conda isolation
# Run this in WSL2 Ubuntu terminal

set -e  # Exit on error

echo "=========================================="
echo "Setting up Whisper Server in WSL"
echo "=========================================="

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Conda not found. Installing Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
    bash ~/miniconda.sh -b -p ~/miniconda
    rm ~/miniconda.sh
    
    # Initialize conda
    ~/miniconda/bin/conda init bash
    source ~/.bashrc
    echo "✅ Miniconda installed"
else
    echo "✅ Conda found"
fi

# Create isolated conda environment
echo ""
echo "Creating Conda environment: whisper-server"
conda create -n whisper-server python=3.11 -y

# Activate environment
echo "Activating environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate whisper-server

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel

# Core dependencies
pip install openai-whisper==20240314
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install aiofiles==23.2.1
pip install python-multipart==0.0.6

# PyTorch (CPU by default, add GPU support below if needed)
echo ""
echo "Installing PyTorch (CPU)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Optional: GPU support (uncomment if using AMD GPU in WSL with ROCm)
# echo "Installing PyTorch with ROCm GPU support..."
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7

# Download Whisper model (base model ~140MB)
echo ""
echo "Downloading Whisper 'base' model..."
python -c "import whisper; whisper.load_model('base')"

# Verify installation
echo ""
echo "Verifying installation..."
python -c "import whisper, fastapi, uvicorn, aiofiles; print('✅ All packages installed successfully')"

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To run Whisper server:"
echo "  1. Activate environment:"
echo "     conda activate whisper-server"
echo ""
echo "  2. Run server:"
echo "     python docker/whisper/whisper_server.py"
echo ""
echo "  3. Server will be available at:"
echo "     http://localhost:8000"
echo "     http://127.0.0.1:8000"
echo ""
echo "  4. Test it:"
echo "     curl http://localhost:8000/health"
echo ""
echo "Environment details:"
conda info --envs
