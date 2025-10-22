#!/usr/bin/env python3
"""
Local Whisper Server for Windows AI Assistant
Provides speech-to-text API using OpenAI Whisper models
"""

import os
import tempfile
import logging
import asyncio
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
import whisper
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import aiofiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperServer:
    def __init__(self):
        self.model = None
        self.model_name = os.getenv("WHISPER_MODEL", "base")
        # Use CUDA (ROCm) if available, fallback to CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.language = os.getenv("WHISPER_LANGUAGE", "en")
        
        logger.info(f"Initializing Whisper Server with device: {self.device}")
        if self.device == "cuda":
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        
        # Initialize FastAPI app with lifespan
        self.app = FastAPI(
            title="Windows AI Whisper Server",
            description="Speech-to-text API using OpenAI Whisper with GPU acceleration",
            version="1.0.0",
            lifespan=self.lifespan
        )
        
        # Setup routes
        self.setup_routes()
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        # Startup
        await self.load_model()
        yield
        # Shutdown (cleanup if needed)
        pass
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return JSONResponse({
                "status": "healthy",
                "model": self.model_name,
                "device": self.device,
                "model_loaded": self.model is not None
            })
        
        @self.app.get("/")
        async def root():
            """Root endpoint with server info"""
            return JSONResponse({
                "message": "Local Whisper Server",
                "model": self.model_name,
                "device": self.device,
                "endpoints": {
                    "transcribe": "/transcribe",
                    "health": "/health"
                }
            })
        
        @self.app.post("/transcribe")
        async def transcribe_audio(
            file: UploadFile = File(...),
            language: Optional[str] = None,
            task: str = "transcribe"
        ):
            """Transcribe audio file to text"""
            
            if not self.model:
                raise HTTPException(status_code=503, detail="Model not loaded")
            
            if not file.content_type or not file.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="File must be an audio file")
            
            try:
                # Save uploaded file temporarily
                temp_dir = Path("/app/audio_temp")
                temp_dir.mkdir(exist_ok=True)
                
                temp_file = temp_dir / f"temp_{file.filename}"
                
                async with aiofiles.open(temp_file, 'wb') as f:
                    content = await file.read()
                    await f.write(content)
                
                # Transcribe audio
                result = await self.transcribe_file(
                    str(temp_file), 
                    language or self.language,
                    task
                )
                
                # Clean up temp file
                temp_file.unlink(missing_ok=True)
                
                return JSONResponse({
                    "text": result["text"],
                    "language": result.get("language", "unknown"),
                    "segments": result.get("segments", []),
                    "model": self.model_name
                })
                
            except Exception as e:
                logger.error(f"Transcription error: {e}")
                raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    async def load_model(self):
        """Load Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.model_name} on device: {self.device}")
            
            # Run model loading in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                whisper.load_model, 
                self.model_name, 
                self.device
            )
            
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    async def transcribe_file(self, audio_path: str, language: str, task: str):
        """Transcribe audio file"""
        try:
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_path,
                    language=language if language != "auto" else None,
                    task=task,
                    verbose=False
                )
            )
            return result
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    def run(self, host: str = "100.110.82.181", port: int = 8001):
        """Run the Whisper server"""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )

if __name__ == "__main__":
    server = WhisperServer()
    server.run()