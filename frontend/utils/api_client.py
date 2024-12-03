import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import backoff  # for retry logic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    name: str
    size: int
    modified_at: datetime
    sha256: str
    details: Dict[str, Any]

@dataclass
class GenerateResponse:
    response: str
    context: List[int]
    total_duration: int
    load_duration: int
    prompt_eval_duration: int
    eval_duration: int
    tokens: int
    raw_response: Dict[str, Any]

class OllamaAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(self.message)

class OllamaAPI:
    def __init__(self, base_url: str = "http://localhost:11434/api", timeout: int = 30):
        """
        Initialize the Ollama API client.
        
        Args:
            base_url: Base URL for the Ollama API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        self._initialize_headers()

    def _initialize_headers(self) -> None:
        """Initialize default headers for API requests"""
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=self.timeout, headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    @backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=3)
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Make an HTTP request to the Ollama API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
        
        Returns:
            Tuple of (response_data, status_code)
        """
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout, headers=self.headers)

        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with self.session.request(method, url, json=data, params=params) as response:
                response_text = await response.text()
                try:
                    response_data = json.loads(response_text) if response_text else {}
                except json.JSONDecodeError:
                    response_data = {"raw_response": response_text}
                
                if not response.ok:
                    raise OllamaAPIError(
                        f"API request failed: {response_data.get('error', 'Unknown error')}",
                        response.status,
                        response_text
                    )
                
                return response_data, response.status
                
        except aiohttp.ClientError as e:
            raise OllamaAPIError(f"Request failed: {str(e)}")

    async def generate(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[List[int]] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> GenerateResponse:
        """
        Generate a response from the model.
        
        Args:
            prompt: The prompt to generate from
            model: Model name to use
            system: System prompt
            template: Template to use for generation
            context: Context from previous generation
            options: Additional model options
            stream: Whether to stream the response
        
        Returns:
            GenerateResponse object
        """
        data = {
            "model": model,
            "prompt": prompt,
            **({"system": system} if system else {}),
            **({"template": template} if template else {}),
            **({"context": context} if context else {}),
            **({"options": options} if options else {}),
            "stream": stream
        }

        response_data, _ = await self._make_request("POST", "generate", data)
        
        return GenerateResponse(
            response=response_data.get("response", ""),
            context=response_data.get("context", []),
            total_duration=response_data.get("total_duration", 0),
            load_duration=response_data.get("load_duration", 0),
            prompt_eval_duration=response_data.get("prompt_eval_duration", 0),
            eval_duration=response_data.get("eval_duration", 0),
            tokens=response_data.get("tokens", 0),
            raw_response=response_data
        )

    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[List[int]] = None,
        options: Optional[Dict[str, Any]] = None
    ):
        """
        Stream responses from the model.
        
        Args:
            Same as generate()
        
        Yields:
            Stream of responses
        """
        data = {
            "model": model,
            "prompt": prompt,
            **({"system": system} if system else {}),
            **({"template": template} if template else {}),
            **({"context": context} if context else {}),
            **({"options": options} if options else {}),
            "stream": True
        }

        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout, headers=self.headers)

        async with self.session.post(f"{self.base_url}/generate", json=data) as response:
            async for line in response.content:
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode streaming response: {line}")

    async def list_models(self) -> List[ModelInfo]:
        """Get list of available models"""
        response_data, _ = await self._make_request("GET", "tags")
        
        models = []
        for model_data in response_data.get("models", []):
            models.append(ModelInfo(
                name=model_data.get("name", ""),
                size=model_data.get("size", 0),
                modified_at=datetime.fromisoformat(model_data.get("modified_at", "")),
                sha256=model_data.get("digest", ""),
                details=model_data
            ))
        
        return models

    async def show_model(self, name: str) -> ModelInfo:
        """Get details about a specific model"""
        response_data, _ = await self._make_request("POST", "show", {"name": name})
        
        return ModelInfo(
            name=response_data.get("name", ""),
            size=response_data.get("size", 0),
            modified_at=datetime.fromisoformat(response_data.get("modified_at", "")),
            sha256=response_data.get("digest", ""),
            details=response_data
        )

    async def copy_model(self, source: str, destination: str) -> bool:
        """Copy a model to a new name"""
        try:
            await self._make_request("POST", "copy", {
                "source": source,
                "destination": destination
            })
            return True
        except OllamaAPIError:
            return False

    async def delete_model(self, name: str) -> bool:
        """Delete a model"""
        try:
            await self._make_request("DELETE", "delete", {"name": name})
            return True
        except OllamaAPIError:
            return False

    async def pull_model(self, name: str) -> bool:
        """Pull a model from the registry"""
        try:
            await self._make_request("POST", "pull", {"name": name})
            return True
        except OllamaAPIError:
            return False

    async def push_model(self, name: str) -> bool:
        """Push a model to the registry"""
        try:
            await self._make_request("POST", "push", {"name": name})
            return True
        except OllamaAPIError:
            return False

    async def create_model(
        self,
        name: str,
        modelfile: str,
        path: Optional[str] = None
    ) -> bool:
        """Create a model from a Modelfile"""
        try:
            data = {
                "name": name,
                "modelfile": modelfile,
                **({"path": path} if path else {})
            }
            await self._make_request("POST", "create", data)
            return True
        except OllamaAPIError:
            return False

# Example usage:
async def example_usage():
    async with OllamaAPI() as client:
        # Generate a response
        response = await client.generate(
            prompt="What is the meaning of life?",
            model="llama2",
            options={"temperature": 0.7}
        )
        print(f"Response: {response.response}")
        print(f"Tokens used: {response.tokens}")
        
        # List available models
        models = await client.list_models()
        for model in models:
            print(f"Model: {model.name}, Size: {model.size} bytes")
        
        # Stream responses
        async for chunk in client.generate_stream(
            prompt="Tell me a story",
            model="llama2"
        ):
            print(chunk.get("response", ""), end="", flush=True)

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())