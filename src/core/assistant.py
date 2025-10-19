import asyncio
import logging
from typing import Optional, List, Dict, Any
import time

from ..config.settings import AssistantSettings
from ..ai.ollama_client import OllamaClient, OllamaResponse
from ..speech.recognition import SpeechRecognitionManager, SpeechEngine
from ..control.device_controller import WindowsDeviceController, CommandRiskLevel
from ..memory.mem0_client import Mem0Client, format_memories_for_context

class WindowsAIAssistant:
    """
    Main AI Assistant class that coordinates all components:
    - Speech recognition (wake word + commands)
    - AI processing via Ollama
    - Device control with confirmation system
    - Text-to-speech responses
    """
    
    def __init__(self, config: AssistantSettings):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.ollama_client: Optional[OllamaClient] = None
        self.speech_manager: Optional[SpeechRecognitionManager] = None
        self.device_controller: Optional[WindowsDeviceController] = None
        self.mem0_client: Optional[Mem0Client] = None
        
        # State management
        self.is_running = False
        self.conversation_history: List[Dict[str, str]] = []
        self.last_interaction_time = time.time()
        
        # System prompt for the AI model
        self.system_prompt = """You are a Windows AI Assistant with full control over the user's workstation. 
        
Your capabilities include:
- Launching applications and managing processes
- File operations (create, open, delete, move, copy)
- System control (shutdown, restart, lock, sleep) 
- Window management
- Keyboard and mouse automation
- PowerShell command execution
- System settings changes
- Network management

CRITICAL SECURITY PROTOCOL:
- ALL operations that could modify the system require user confirmation with the keyword 'wolf-logic'
- You MUST explain what you're about to do before requesting confirmation
- For high-risk operations, provide clear warnings about potential consequences
- Never execute destructive commands without explicit confirmation

Response Format:
1. Acknowledge the user's request
2. If the action requires confirmation, explain what you'll do and ask for 'wolf-logic' confirmation
3. If safe, execute immediately and report results
4. Be conversational but professional

Available commands include: launch_app, open_file, delete_file, run_powershell, type_text, press_key, 
click_mouse, shutdown, restart, lock_workstation, kill_process, and many others.

Remember: You have great power - use it responsibly and always prioritize user safety.

PERSISTENT MEMORY CONTEXT:
You have access to persistent memory across 7,800+ interactions stored in Neo4J knowledge graph.
Before responding, relevant past memories are included below. Use them to:
- Reference past decisions and their outcomes
- Learn from mistakes
- Provide consistent, informed responses
- Build on previous knowledge about the user's preferences and patterns"""
    
    async def start(self):
        """Start the AI Assistant"""
        self.logger.info("Starting Windows AI Assistant...")
        
        try:
            # Initialize Ollama client
            self.ollama_client = OllamaClient(
                host=self.config.ollama_host,
                port=self.config.ollama_port
            )
            
            async with self.ollama_client:
                # Test Ollama connection
                if not await self.ollama_client.check_connection():
                    raise Exception("Failed to connect to Ollama server")
                
                self.logger.info("Connected to Ollama server")
                
                # Initialize speech recognition
                speech_engine = SpeechEngine.WHISPER_LOCAL if self.config.use_whisper else SpeechEngine.WINDOWS_NATIVE
                self.speech_manager = SpeechRecognitionManager(
                    engine=speech_engine,
                    wake_word=self.config.wake_word,
                    whisper_model=self.config.whisper_model,
                    use_directml=self.config.use_directml
                )
                
                if not await self.speech_manager.initialize():
                    raise Exception("Failed to initialize speech recognition")
                
                self.logger.info("Speech recognition initialized")
                
                # Initialize device controller with confirmation keyword
                self.device_controller = WindowsDeviceController(
                    confirmation_keyword=self.config.confirmation_keyword
                )
                self.device_controller.set_confirmation_callback(self._speak_response)
                
                self.logger.info("Device controller initialized")
                
                # Initialize mem0 client for persistent memory if enabled
                if self.config.enable_persistent_memory:
                    try:
                        self.mem0_client = Mem0Client(
                            mem0_api_url=self.config.mem0_api_url,
                            mem0_api_key=self.config.mem0_api_key,
                            retrieval_agent_host=self.config.mem0_retrieval_agent_host,
                            retrieval_agent_sse_port=self.config.mem0_retrieval_agent_port,
                            enable_sse_streaming=self.config.enable_sse_streaming
                        )
                        
                        if await self.mem0_client.connect():
                            self.logger.info("Connected to mem0 persistent memory system")
                        else:
                            self.logger.warning("Failed to connect to mem0, continuing without persistent memory")
                            self.mem0_client = None
                    except Exception as e:
                        self.logger.warning(f"mem0 initialization failed: {e}, continuing without persistent memory")
                        self.mem0_client = None
                
                # Set up speech callbacks
                self.speech_manager.set_wake_word_callback(self._on_wake_word)
                self.speech_manager.set_command_callback(self._on_voice_command)
                self.speech_manager.set_error_callback(self._on_speech_error)
                
                # Start speech recognition
                await self.speech_manager.start_listening()
                
                self.is_running = True
                self.logger.info("🤖 Windows AI Assistant is now active and listening...")
                await self._speak_response("Windows AI Assistant activated. I'm listening for commands.")
                
                # Main loop
                while self.is_running:
                    await asyncio.sleep(1)
                    
                    # Clean up old conversation history (keep last 10 exchanges)
                    if len(self.conversation_history) > 20:
                        self.conversation_history = self.conversation_history[-20:]
                        
        except Exception as e:
            self.logger.error(f"Failed to start assistant: {e}")
            raise
    
    async def stop(self):
        """Stop the AI Assistant"""
        self.logger.info("Stopping Windows AI Assistant...")
        self.is_running = False
        
        if self.mem0_client:
            await self.mem0_client.disconnect()
        
        if self.speech_manager:
            await self.speech_manager.cleanup()
        
        await self._speak_response("Windows AI Assistant shutting down.")
    
    async def _on_wake_word(self):
        """Handle wake word detection"""
        self.logger.info(f"Wake word '{self.config.wake_word}' detected")
        await self._speak_response("Yes? How can I help you?")
    
    async def _on_voice_command(self, command_text: str):
        """Handle voice command processing with memory storage"""
        self.logger.info(f"Processing command: {command_text}")
        
        try:
            # Check if this is a confirmation
            if self.config.confirmation_keyword.lower() in command_text.lower():
                result = await self.device_controller.confirm_command(command_text)
                await self._speak_response(result["message"])
                return
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": command_text
            })
            
            # Get AI response with memory context
            response = await self._get_ai_response(command_text)
            
            # Add AI response to history
            self.conversation_history.append({
                "role": "assistant", 
                "content": response.content
            })
            
            # Store interaction in mem0 if enabled
            if self.mem0_client and self.mem0_client.is_connected:
                try:
                    await self.mem0_client.store_interaction(
                        user_input=command_text,
                        assistant_response=response.content,
                        topic="voice_command",
                        metadata={
                            "model": self.config.ollama_model,
                            "timestamp": str(time.time()),
                            "device": "voice_assistant"
                        }
                    )
                    self.logger.info("Stored interaction in mem0")
                except Exception as e:
                    self.logger.warning(f"Failed to store interaction in mem0: {e}")
            
            # Parse and execute any commands from AI response
            await self._process_ai_response(response.content)
            
            # Speak the response
            await self._speak_response(response.content)
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            await self._speak_response("I'm sorry, I encountered an error processing that command.")
    
    async def _get_ai_response(self, user_input: str) -> OllamaResponse:
        """Get response from AI model with persistent memory context"""
        try:
            # Retrieve relevant memories if mem0 is enabled
            memory_context = ""
            if self.mem0_client and self.mem0_client.is_connected:
                try:
                    # Search memories by semantic similarity to user input
                    memories = await self.mem0_client.retrieve_memories_by_query(
                        query=user_input,
                        limit=self.config.memory_context_limit
                    )
                    
                    if memories:
                        memory_context = format_memories_for_context(memories)
                        self.logger.info(f"Retrieved {len(memories)} relevant memories for context injection")
                except Exception as e:
                    self.logger.warning(f"Error retrieving memories: {e}")
            
            # Prepare conversation for chat API
            system_message = self.system_prompt
            if memory_context:
                system_message += f"\n{memory_context}"
            
            messages = [
                {"role": "system", "content": system_message}
            ] + self.conversation_history[-10:]  # Last 10 exchanges for context
            
            response = await self.ollama_client.chat(
                messages=messages,
                model=self.config.ollama_model
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting AI response: {e}")
            return OllamaResponse(
                content="I'm sorry, I'm having trouble processing your request right now.",
                model=self.config.ollama_model,
                done=True
            )
    
    async def _process_ai_response(self, ai_response: str):
        """Parse AI response and execute any system commands"""
        # This is where we'd parse the AI response for action commands
        # For now, we'll implement a simple keyword-based system
        
        response_lower = ai_response.lower()
        
        # Simple command extraction (this could be made more sophisticated)
        if "launch" in response_lower or "open" in response_lower:
            # Extract application name
            if "calculator" in response_lower:
                await self.device_controller.execute_command("launch_app", app_name="calculator")
            elif "notepad" in response_lower:
                await self.device_controller.execute_command("launch_app", app_name="notepad")
            elif "chrome" in response_lower:
                await self.device_controller.execute_command("launch_app", app_name="chrome")
            elif "explorer" in response_lower:
                await self.device_controller.execute_command("launch_app", app_name="explorer")
        
        elif "shutdown" in response_lower:
            await self.device_controller.execute_command("shutdown")
        
        elif "restart" in response_lower:
            await self.device_controller.execute_command("restart")
        
        elif "lock" in response_lower:
            await self.device_controller.execute_command("lock_workstation")
        
        # Add more command parsing as needed
    
    async def _speak_response(self, text: str):
        """Convert text to speech (placeholder - implement with pyttsx3 or Windows SAPI)"""
        # For now, just log the response
        # In full implementation, this would use text-to-speech
        self.logger.info(f"🗣️ Assistant: {text}")
        print(f"🗣️ Assistant: {text}")
        
        # TODO: Implement actual TTS
        # import pyttsx3
        # engine = pyttsx3.init()
        # engine.say(text)
        # engine.runAndWait()
    
    async def _on_speech_error(self, error: Exception):
        """Handle speech recognition errors"""
        self.logger.error(f"Speech recognition error: {error}")
        await self._speak_response("I'm having trouble with speech recognition.")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the assistant"""
        pending_commands = []
        if self.device_controller:
            pending_commands = self.device_controller.get_pending_commands()
        
        cached_memories = 0
        if self.mem0_client:
            cached_memories = len(self.mem0_client.get_cached_memories())
        
        return {
            "running": self.is_running,
            "ollama_connected": self.ollama_client is not None,
            "speech_active": self.speech_manager is not None and self.speech_manager.is_listening,
            "mem0_connected": self.mem0_client is not None and self.mem0_client.is_connected,
            "cached_memories": cached_memories,
            "pending_commands": len(pending_commands),
            "conversation_length": len(self.conversation_history),
            "last_interaction": self.last_interaction_time
        }