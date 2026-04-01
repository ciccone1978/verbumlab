import httpx
from typing import List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating text embeddings using Ollama's native API.
    """
    def __init__(self):
        """
        Initialize the embedding service with Ollama connectivity.
        """
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.EMBEDDING_MODEL

    async def get_embeddings(self, text: str, prefix: str = "") -> List[float]:
        """
        Generate a vector embedding for a given text string using Ollama.

        Args:
            text (str): The input text to embed.
            prefix (str, optional): Prefix for the text (e.g., 'passage: ' or 'query: '). Defaults to "".

        Returns:
            List[float]: The generated vector embedding.
        """
        if not text.strip():
            logger.warning("Empty text passed to embedding service.")
            return []

        try:
            # Add prefix if provided (required by models like E5)
            full_text = f"{prefix}{text}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": full_text
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Ollama error {response.status_code}: {response.text}")
                    raise Exception(f"Ollama returned {response.status_code}: {response.text}")
                
                data = response.json()
                embedding = data.get("embedding")
                
                if not embedding:
                    logger.error(f"Ollama returned no embedding. Full response: {data}")
                    raise Exception("No embedding in Ollama response")
                
                # Check for NaNs in the embedding list (rare but possible given the error)
                if any(val != val for val in embedding): # NaN check
                    logger.error("Ollama returned NaN values in the embedding vector!")
                    raise Exception("Model returned NaN values")
                    
                return embedding

        except Exception as e:
            logger.error(f"Error generating embeddings for text '{text[:50]}...': {e}")
            raise

embedding_service = EmbeddingService()
