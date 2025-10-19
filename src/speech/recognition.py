import asyncio
import logging
import json
from typing import Optional, Callable, Dict, Any
from enum import Enum
import threading
import queue
import time

# Windows Speech Recognition
try:
    import win32com.client
    import pythoncom
    WINDOWS_SPEECH_AVAILABLE = True
except ImportError:
    WINDOWS_SPEECH_AVAILABLE = False

# Whisper for local speech recognition
try:
    import whisper
    import torch
    import numpy as np
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Audio capture
try:
    import pyaudio
    import wave
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

class SpeechEngine(Enum):
    WINDOWS_NATIVE = "windows_native"
    WHISPER_LOCAL = "whisper_local"
    WHISPER_SERVER = "whisper_server"

class SpeechRecognitionManager:
    """
    Unified speech recognition manager supporting:
    - Windows Native Speech Recognition (System.Speech.Recognition equivalent)
    - Local Whisper model with DirectML acceleration
    - Remote Whisper server (optional)
    """
    
    def __init__(self, 
                 engine: SpeechEngine = SpeechEngine.WINDOWS_NATIVE,
                 wake_word: str = "assistant",
                 whisper_model: str = "base",
                 use_directml: bool = True):
        self.engine = engine
        self.wake_word = wake_word.lower()
        self.whisper_model = whisper_model
        self.use_directml = use_directml
        self.logger = logging.getLogger(__name__)
        
        # State management
        self.is_listening = False
        self.is_wake_word_detected = False
        self.audio_queue = queue.Queue()
        self.callback_queue = queue.Queue()
        
        # Audio configuration
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.audio_format = pyaudio.paInt16
        
        # Initialize components
        self.audio = None
        self.stream = None
        self.whisper_model_obj = None
        self.windows_speech = None
        
        # Callbacks
        self.wake_word_callback: Optional[Callable] = None
        self.command_callback: Optional[Callable[[str], None]] = None
        self.error_callback: Optional[Callable[[Exception], None]] = None
    
    async def initialize(self) -> bool:
        """Initialize the speech recognition system"""
        try:
            if self.engine == SpeechEngine.WINDOWS_NATIVE:
                return await self._initialize_windows_speech()
            elif self.engine == SpeechEngine.WHISPER_LOCAL:
                return await self._initialize_whisper_local()
            elif self.engine == SpeechEngine.WHISPER_SERVER:
                return await self._initialize_whisper_server()
            else:
                self.logger.error(f"Unknown speech engine: {self.engine}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize speech recognition: {e}")
            if self.error_callback:
                self.error_callback(e)
            return False
    
    async def _initialize_windows_speech(self) -> bool:
        """Initialize Windows native speech recognition"""
        if not WINDOWS_SPEECH_AVAILABLE:
            self.logger.error("Windows speech recognition not available")
            return False
        
        try:
            # Initialize COM for Windows Speech API
            pythoncom.CoInitialize()
            
            # Create speech recognition engine
            self.windows_speech = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Initialize audio capture for wake word detection
            if AUDIO_AVAILABLE:
                self.audio = pyaudio.PyAudio()
                self.stream = self.audio.open(
                    format=self.audio_format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.chunk_size,
                    stream_callback=self._audio_callback
                )
            
            self.logger.info("Windows speech recognition initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Windows speech: {e}")
            return False
    
    async def _initialize_whisper_local(self) -> bool:
        """Initialize local Whisper model with DirectML acceleration"""
        if not WHISPER_AVAILABLE:
            self.logger.error("Whisper not available")
            return False
        
        try:
            # Configure DirectML for AMD GPU acceleration
            if self.use_directml and torch.cuda.is_available():
                device = "cuda"
                self.logger.info("Using CUDA/DirectML acceleration")
            else:
                device = "cpu"
                self.logger.info("Using CPU inference")
            
            # Load Whisper model
            self.logger.info(f"Loading Whisper model: {self.whisper_model}")
            self.whisper_model_obj = whisper.load_model(
                self.whisper_model, 
                device=device
            )
            
            # Initialize audio capture
            if AUDIO_AVAILABLE:
                self.audio = pyaudio.PyAudio()
                self.stream = self.audio.open(
                    format=self.audio_format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.chunk_size,
                    stream_callback=self._audio_callback
                )
            
            self.logger.info("Local Whisper model initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Whisper: {e}")
            return False
    
    async def _initialize_whisper_server(self) -> bool:
        """Initialize connection to remote Whisper server"""
        # TODO: Implement Whisper server client
        self.logger.info("Whisper server client not yet implemented")
        return False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback for continuous listening"""
        if self.is_listening:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    async def start_listening(self):
        """Start continuous speech recognition"""
        if not self.audio or not self.stream:
            self.logger.error("Audio system not initialized")
            return
        
        self.is_listening = True
        self.stream.start_stream()
        
        # Start processing thread
        processing_thread = threading.Thread(target=self._process_audio_loop)
        processing_thread.daemon = True
        processing_thread.start()
        
        self.logger.info("Started listening for speech")
    
    async def stop_listening(self):
        """Stop speech recognition"""
        self.is_listening = False
        
        if self.stream:
            self.stream.stop_stream()
        
        self.logger.info("Stopped listening for speech")
    
    def _process_audio_loop(self):
        """Main audio processing loop running in separate thread"""
        audio_buffer = []
        last_speech_time = time.time()
        
        while self.is_listening:
            try:
                # Get audio data with timeout
                try:
                    audio_data = self.audio_queue.get(timeout=0.1)
                    audio_buffer.append(audio_data)
                except queue.Empty:
                    continue
                
                # Process accumulated audio every 2 seconds or when buffer gets large
                current_time = time.time()
                if (current_time - last_speech_time > 2.0) or (len(audio_buffer) > 32):
                    if audio_buffer:
                        self._process_audio_chunk(audio_buffer)
                        audio_buffer = []
                        last_speech_time = current_time
                
            except Exception as e:
                self.logger.error(f"Error in audio processing loop: {e}")
    
    def _process_audio_chunk(self, audio_buffer: list):
        """Process a chunk of audio data for speech recognition"""
        try:
            # Convert audio buffer to numpy array
            audio_data = b''.join(audio_buffer)
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            if self.engine == SpeechEngine.WHISPER_LOCAL and self.whisper_model_obj:
                # Use Whisper for transcription
                result = self.whisper_model_obj.transcribe(
                    audio_np,
                    language="en",
                    task="transcribe"
                )
                
                text = result.get("text", "").strip().lower()
                if text:
                    self._handle_transcription(text)
            
            elif self.engine == SpeechEngine.WINDOWS_NATIVE:
                # For Windows native, we'd use the COM API here
                # This is a simplified version - full implementation would use
                # the Windows Speech Recognition API directly
                pass
                
        except Exception as e:
            self.logger.error(f"Error processing audio chunk: {e}")
    
    def _handle_transcription(self, text: str):
        """Handle transcribed text"""
        self.logger.debug(f"Transcribed: {text}")
        
        # Check for wake word
        if not self.is_wake_word_detected:
            if self.wake_word in text:
                self.is_wake_word_detected = True
                self.logger.info(f"Wake word '{self.wake_word}' detected!")
                if self.wake_word_callback:
                    asyncio.create_task(self._call_wake_word_callback())
                return
        else:
            # We're in command mode - process the command
            if text and len(text.strip()) > 2:  # Ignore very short utterances
                self.logger.info(f"Command received: {text}")
                if self.command_callback:
                    asyncio.create_task(self._call_command_callback(text))
                # Reset wake word state after processing command
                self.is_wake_word_detected = False
    
    async def _call_wake_word_callback(self):
        """Safely call wake word callback"""
        try:
            if self.wake_word_callback:
                if asyncio.iscoroutinefunction(self.wake_word_callback):
                    await self.wake_word_callback()
                else:
                    self.wake_word_callback()
        except Exception as e:
            self.logger.error(f"Error in wake word callback: {e}")
    
    async def _call_command_callback(self, text: str):
        """Safely call command callback"""
        try:
            if self.command_callback:
                if asyncio.iscoroutinefunction(self.command_callback):
                    await self.command_callback(text)
                else:
                    self.command_callback(text)
        except Exception as e:
            self.logger.error(f"Error in command callback: {e}")
    
    def set_wake_word_callback(self, callback: Callable):
        """Set callback for wake word detection"""
        self.wake_word_callback = callback
    
    def set_command_callback(self, callback: Callable[[str], None]):
        """Set callback for command processing"""
        self.command_callback = callback
    
    def set_error_callback(self, callback: Callable[[Exception], None]):
        """Set callback for error handling"""
        self.error_callback = callback
    
    async def cleanup(self):
        """Clean up resources"""
        await self.stop_listening()
        
        if self.stream:
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
        
        if self.engine == SpeechEngine.WINDOWS_NATIVE and WINDOWS_SPEECH_AVAILABLE:
            try:
                pythoncom.CoUninitialize()
            except:
                pass
        
        self.logger.info("Speech recognition cleaned up")