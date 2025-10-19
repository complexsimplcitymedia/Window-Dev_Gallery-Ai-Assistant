import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass

@dataclass
class OllamaResponse:
    """Response from Ollama API"""
    content: str
    model: str
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None

class OllamaClient:
    """Client for communicating with local Ollama server"""
    
    def __init__(self, host: str = "localhost", port: int = 11434):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_connection(self) -> bool:
        """Check if Ollama server is running and accessible"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    self.logger.info("Successfully connected to Ollama server")
                    return True
                else:
                    self.logger.error(f"Ollama server returned status {response.status}")
                    return False
        except aiohttp.ClientError as e:
            self.logger.error(f"Failed to connect to Ollama server: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to Ollama: {e}")
            return False
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models on the Ollama server"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Failed to list models: HTTP {response.status}")
                    return {"models": []}
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return {"models": []}
    
    async def generate_response(self, 
                              prompt: str, 
                              model: str = "llama3.2:3b",
                              system_prompt: Optional[str] = None,
                              temperature: float = 0.7,
                              stream: bool = False) -> OllamaResponse:
        """Generate a response from the AI model"""
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": 1000,  # Max tokens to generate
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    self.logger.error(f"Ollama API error: HTTP {response.status}")
                    return OllamaResponse(
                        content=f"Error: HTTP {response.status}",
                        model=model,
                        done=True
                    )
                
                if stream:
                    # Handle streaming response
                    full_content = ""
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                if 'response' in chunk:
                                    full_content += chunk['response']
                                if chunk.get('done', False):
                                    return OllamaResponse(
                                        content=full_content,
                                        model=chunk.get('model', model),
                                        done=True,
                                        total_duration=chunk.get('total_duration'),
                                        load_duration=chunk.get('load_duration'),
                                        prompt_eval_count=chunk.get('prompt_eval_count'),
                                        eval_count=chunk.get('eval_count')
                                    )
                            except json.JSONDecodeError:
                                continue
                else:
                    # Handle non-streaming response
                    result = await response.json()
                    return OllamaResponse(
                        content=result.get('response', ''),
                        model=result.get('model', model),
                        done=result.get('done', True),
                        total_duration=result.get('total_duration'),
                        load_duration=result.get('load_duration'),
                        prompt_eval_count=result.get('prompt_eval_count'),
                        eval_count=result.get('eval_count')
                    )
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error communicating with Ollama: {e}")
            return OllamaResponse(
                content=f"Network error: {str(e)}",
                model=model,
                done=True
            )
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return OllamaResponse(
                content=f"Unexpected error: {str(e)}",
                model=model,
                done=True
            )
    
    async def chat(self, messages: list, model: str = "llama3.2:3b") -> OllamaResponse:
        """Chat with the model using conversation history"""
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    self.logger.error(f"Ollama chat API error: HTTP {response.status}")
                    return OllamaResponse(
                        content=f"Error: HTTP {response.status}",
                        model=model,
                        done=True
                    )
                
                result = await response.json()
                message_content = result.get('message', {}).get('content', '')
                
                return OllamaResponse(
                    content=message_content,
                    model=result.get('model', model),
                    done=result.get('done', True),
                    total_duration=result.get('total_duration'),
                    load_duration=result.get('load_duration'),
                    prompt_eval_count=result.get('prompt_eval_count'),
                    eval_count=result.get('eval_count')
                )
                
        except Exception as e:
            self.logger.error(f"Error in chat: {e}")
            return OllamaResponse(
                content=f"Error: {str(e)}",
                model=model,
                done=True
            )