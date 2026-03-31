from typing import List
from openai import AsyncOpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating text embeddings using an OpenAI-compatible API (Ollama).
    """
    def __init__(self):
        """
        Initialize the embedding service with Ollama connectivity.
        """
        # We use the OpenAI-compatible client which points to Ollama
        self.client = AsyncOpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",
        )
        self.model = settings.EMBEDDING_MODEL

    async def get_embeddings(self, text: str, prefix: str = "") -> List[float]:
        """
        Generate a vector embedding for a given text string.

        Args:
            text (str): The input text to embed.
            prefix (str, optional): Prefix for the text (e.g., 'passage: ' or 'query: '). Defaults to "".

        Returns:
            List[float]: The generated vector embedding.
        """
        try:
            # Add prefix if provided (required by models like E5)
            full_text = f"{prefix}{text}"
            response = await self.client.embeddings.create(
                input=[full_text],
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

embedding_service = EmbeddingService()
