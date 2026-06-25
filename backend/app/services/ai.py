from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator
import google.generativeai as genai
from app.core.config import settings

class AIService(ABC):
    """Abstract Base Class defining the contract for AI model interactions."""

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Generates text from a prompt."""
        pass

    @abstractmethod
    async def stream_text(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        """Streams text response from a prompt."""
        pass

    @abstractmethod
    async def get_embeddings(self, text: str | list[str], **kwargs: Any) -> list[list[float]]:
        """Generates embedding vectors for the provided text."""
        pass


class GeminiAIService(AIService):
    """Concrete implementation of AIService integrating Google Gemini API."""

    def __init__(self) -> None:
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None

    async def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Generates text from Gemini model."""
        if not self.model:
            return "Gemini API key is not configured. This is a scaffold response."
        
        # Placeholder implementation calling Gemini API in a threadsafe/async pool
        # actual API call logic:
        # response = await genai.generate_content_async(prompt=prompt, **kwargs)
        # return response.text
        return f"Mocked Gemini response for prompt: {prompt}"

    async def stream_text(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        """Streams text from Gemini model."""
        if not self.model:
            yield "Gemini API key is not configured. This is a scaffold response."
            return
        
        # Mock generator. Real code:
        # response = await genai.generate_content_async(prompt=prompt, stream=True, **kwargs)
        # async for chunk in response:
        #     yield chunk.text
        yield f"Mocked Gemini stream start: {prompt}\n"
        yield "Mocked Gemini stream middle\n"
        yield "Mocked Gemini stream end\n"

    async def get_embeddings(self, text: str | list[str], **kwargs: Any) -> list[list[float]]:
        """Generates text embedding vectors using Gemini embeddings API."""
        if not self.api_key:
            # Return dummy 1536 or 768 dimension mock vector
            return [[0.0] * 768]
        
        # Real code:
        # result = genai.embed_content(model="models/embedding-001", contents=text, **kwargs)
        # return result['embedding']
        return [[0.1, 0.2, 0.3] * 256]
