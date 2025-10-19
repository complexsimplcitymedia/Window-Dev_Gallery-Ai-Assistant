import asyncio
import logging
import io
import wave
import pyaudio
import threading
from abc import ABC, abstractmethod
from typing import Optional, Callable
import aiohttp

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

class SpeechRecognizer(ABC):
    """Abstract base class for speech recognition"""
    
    @abstractmethod
    async def listen_for_wake_word(self, wake_word: str, callback: Callable) -> None:
        """Listen continuously for wake word"""
        pass
    
    @abstractmethod
    async def recognize_speech(self, timeout: float = 5.0) -> Optional[str]:
        """Recognize speech and return transcribed text"""
        pass
    
    @abstractmethod
    async def start_listening(self) -> None:
        """Start the speech recognition service"""
        pass
    
    @abstractmethod
    async def stop_listening(self) -> None:
        """Stop the speech recognition service"""
        pass

class WindowsSpeechRecognizer(SpeechRecognizer):
    """Windows native speech recognition using speech_recognition library"""
    
    def __init__(self):
        if not SPEECH_RECOGNITION_AVAILABLE:
            raise ImportError("speech_recognition library not available")
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = False
        self.logger = logging.getLogger(__name__)
        
        # Adjust for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
    
    async def start_listening(self) -> None:
        """Start listening service"""
        self.listening = True
        self.logger.info("Windows Speech Recognition started")
    
    async def stop_listening(self) -> None:
        """Stop listening service"""
        self.listening = False
        self.logger.info("Windows Speech Recognition stopped")
    
    async def listen_for_wake_word(self, wake_word: str, callback: Callable) -> None:
        """Listen continuously for wake word"""
        self.logger.info(f"Listening for wake word: '{wake_word}'")
        
        while self.listening:
            try:
                # Listen for audio
                with self.microphone as source:
                    # Listen for audio with timeout
                    audio = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    )
                
                # Recognize speech
                text = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.recognizer.recognize_windows(audio)
                )
                
                if wake_word.lower() in text.lower():
                    self.logger.info(f"Wake word detected: '{text}'")
                    await callback()
                
            except sr.WaitTimeoutError:
                # Normal timeout, continue listening
                continue
            except sr.UnknownValueError:
                # Speech not understood
                continue
            except sr.RequestError as e:
                self.logger.error(f"Windows Speech Recognition error: {e}")
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Unexpected error in wake word detection: {e}")
                await asyncio.sleep(1)
    
    async def recognize_speech(self, timeout: float = 5.0) -> Optional[str]:
        """Recognize speech and return transcribed text"""
        try:
            self.logger.info("Listening for command...")
            
            with self.microphone as source:
                # Listen for command
                audio = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                )
            
            # Recognize speech
            text = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.recognizer.recognize_windows(audio)
            )
            
            self.logger.info(f"Recognized: '{text}'")
            return text
            
        except sr.WaitTimeoutError:
            self.logger.warning("Speech recognition timeout")
            return None
        except sr.UnknownValueError:
            self.logger.warning("Could not understand speech")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition error: {e}")
            return None

class WhisperSpeechRecognizer(SpeechRecognizer):
    """Whisper-based speech recognition using local server"""
    
    def __init__(self, whisper_url: str = "http://localhost:8000"):
        self.whisper_url = whisper_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.listening = False
        self.logger = logging.getLogger(__name__)
        
        # Audio recording parameters
        self.chunk = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.p = pyaudio.PyAudio()
    
    async def start_listening(self) -> None:
        """Start listening service"""
        self.session = aiohttp.ClientSession()
        self.listening = True
        
        # Test connection to Whisper server
        try:
            async with self.session.get(f"{self.whisper_url}/health") as response:
                if response.status == 200:
                    self.logger.info("Connected to Whisper server")
                else:
                    self.logger.error(f"Whisper server health check failed: {response.status}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Whisper server: {e}")
    
    async def stop_listening(self) -> None:
        """Stop listening service"""
        self.listening = False
        if self.session:
            await self.session.close()
        self.p.terminate()
        self.logger.info("Whisper Speech Recognition stopped")
    
    async def record_audio(self, duration: float) -> bytes:
        """Record audio for specified duration"""
        stream = self.p.open(
            format=self.sample_format,
            channels=self.channels,
            rate=self.rate,
            frames_per_buffer=self.chunk,
            input=True
        )
        
        frames = []
        frames_to_record = int(self.rate / self.chunk * duration)
        
        for _ in range(frames_to_record):
            data = stream.read(self.chunk)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Convert to WAV format
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.sample_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
        
        return wav_buffer.getvalue()
    
    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Send audio to Whisper server for transcription"""
        if not self.session:
            return None
        
        try:
            data = aiohttp.FormData()
            data.add_field('file', audio_data, filename='audio.wav', content_type='audio/wav')
            
            async with self.session.post(f"{self.whisper_url}/transcribe", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('text', '').strip()
                else:
                    self.logger.error(f"Whisper transcription failed: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            return None
    
    async def listen_for_wake_word(self, wake_word: str, callback: Callable) -> None:
        """Listen continuously for wake word"""
        self.logger.info(f"Listening for wake word: '{wake_word}' using Whisper")
        
        while self.listening:
            try:
                # Record 3 seconds of audio
                audio_data = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: asyncio.run(self.record_audio(3.0))
                )
                
                # Transcribe audio
                text = await self.transcribe_audio(audio_data)
                
                if text and wake_word.lower() in text.lower():
                    self.logger.info(f"Wake word detected: '{text}'")
                    await callback()
                
                # Small delay to prevent overwhelming the server
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error in wake word detection: {e}")
                await asyncio.sleep(1)
    
    async def recognize_speech(self, timeout: float = 5.0) -> Optional[str]:
        """Recognize speech and return transcribed text"""
        try:
            self.logger.info("Recording command...")
            
            # Record audio for the specified duration
            audio_data = await asyncio.get_event_loop().run_in_executor(
                None, lambda: asyncio.run(self.record_audio(timeout))
            )
            
            # Transcribe audio
            text = await self.transcribe_audio(audio_data)
            
            if text:
                self.logger.info(f"Recognized: '{text}'")
                return text
            else:
                self.logger.warning("No speech recognized")
                return None
                
        except Exception as e:
            self.logger.error(f"Error recognizing speech: {e}")
            return None

def create_speech_recognizer(use_whisper: bool = False, whisper_url: str = "http://localhost:8000") -> SpeechRecognizer:
    """Factory function to create appropriate speech recognizer"""
    if use_whisper:
        return WhisperSpeechRecognizer(whisper_url)
    else:
        if not SPEECH_RECOGNITION_AVAILABLE:
            raise ImportError("speech_recognition library not available for Windows Speech Recognition")
        return WindowsSpeechRecognizer()