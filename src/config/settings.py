# Configuration settings for Windows AI Assistant
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class AssistantSettings(BaseSettings):
    """Configuration settings for the AI Assistant"""
    
    # Ollama Configuration (Tailscale networking)
    ollama_host: str = Field(default="127.0.0.1", description="Ollama server host - use Tailscale IP if remote")
    ollama_port: int = Field(default=11434, description="Ollama server port")
    ollama_model: str = Field(default="llama3.2:3b", description="Default Ollama model to use")
    use_tailscale: bool = Field(default=True, description="Use Tailscale networking for distributed setup")
    
    # Speech Recognition Settings
    wake_word: str = Field(default="wolf-logic", description="Wake word to activate the assistant")
    use_whisper: bool = Field(default=False, description="Use local Whisper instead of Windows Speech Recognition")
    whisper_model: str = Field(default="base", description="Whisper model size (tiny, base, small, medium, large)")
    
    # Text-to-Speech Settings
    tts_rate: int = Field(default=200, description="Speech rate for TTS")
    tts_voice: Optional[str] = Field(default=None, description="Voice to use for TTS")
    
    # DirectML Settings
    use_directml: bool = Field(default=True, description="Enable DirectML acceleration")
    directml_device_id: int = Field(default=0, description="DirectML device ID to use")
    
    # Security - Confirmation Keyword
    confirmation_keyword: str = Field(default="wolf-logic", description="Keyword required to confirm system-changing commands")
    
    # System Control Settings
    allow_system_control: bool = Field(default=True, description="Allow the assistant to control system functions")
    max_command_length: int = Field(default=1000, description="Maximum length of voice commands")
    
    # mem0 Persistent Memory Settings
    enable_persistent_memory: bool = Field(default=True, description="Enable mem0 persistent memory system")
    mem0_api_url: str = Field(default="https://mem0-api.complexsimplicity.com", description="mem0 REST API endpoint")
    mem0_api_key: str = Field(default="", description="mem0 API authentication key")
    mem0_retrieval_agent_host: str = Field(default="100.110.82.181", description="Retrieval agent host (SSE stream)")
    mem0_retrieval_agent_port: int = Field(default=8765, description="Retrieval agent SSE port (5-second loop)")
    enable_sse_streaming: bool = Field(default=True, description="Enable SSE streaming from retrieval agent")
    memory_context_limit: int = Field(default=5, description="Number of memories to retrieve per query")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/assistant.log", description="Log file path")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def load_config() -> AssistantSettings:
    """Load configuration from environment variables and .env file"""
    return AssistantSettings()