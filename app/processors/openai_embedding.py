from typing import List
from app.processors.embedding_processor import EmbeddingProvider
from app.config import get_settings


class OpenAIEmbedding(EmbeddingProvider):
    """OpenAI API 向量化"""

    def __init__(self):
        from openai import OpenAI
        settings = get_settings()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._dimension = 1536

    def embed(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]

    @property
    def dimension(self) -> int:
        return self._dimension
