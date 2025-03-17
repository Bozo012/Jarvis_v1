import json
import requests
from typing import Dict, List, Optional, Union, Any
from loguru import logger

from config.settings import settings


class LLMService:
    """
    LLM service using Ollama for local language model inference.
    """
    
    def __init__(self):
        self.model = settings.llm.model
        self.ollama_host = settings.llm.ollama_host
        
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {e}")
            return False
            
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models in Ollama."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                logger.error(f"Failed to list models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
            
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """
        Generate text using the configured LLM.
        
        Args:
            prompt: The user prompt to process
            system_prompt: Optional system prompt for context
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text
        """
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
                
            # Make request to Ollama API
            logger.info(f"Generating text with model: {self.model}")
            response = requests.post(
                f"{self.ollama_host}/api/generate", 
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Failed to generate text: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Error during text generation: {e}")
            return ""
            
    def generate_streaming(self, prompt: str, system_prompt: Optional[str] = None,
                          temperature: float = 0.7, max_tokens: Optional[int] = None):
        """
        Generate text using the configured LLM with streaming response.
        
        Args:
            prompt: The user prompt to process
            system_prompt: Optional system prompt for context
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Yields:
            Generated text chunks
        """
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": temperature
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
                
            # Make request to Ollama API with streaming
            logger.info(f"Generating text with streaming from model: {self.model}")
            response = requests.post(
                f"{self.ollama_host}/api/generate", 
                json=payload,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                yield chunk["response"]
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode JSON from chunk: {line}")
            else:
                logger.error(f"Failed to generate streaming text: {response.status_code}")
                yield ""
                
        except Exception as e:
            logger.error(f"Error during streaming text generation: {e}")
            yield ""
            
    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None,
            temperature: float = 0.7, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a chat completion using the configured LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            system_prompt: Optional system prompt for context
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Response containing the assistant's message
        """
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
                
            # Make request to Ollama API
            logger.info(f"Generating chat completion with model: {self.model}")
            response = requests.post(
                f"{self.ollama_host}/api/chat", 
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to generate chat completion: {response.status_code}")
                return {"message": {"content": ""}}
                
        except Exception as e:
            logger.error(f"Error during chat completion: {e}")
            return {"message": {"content": ""}}
