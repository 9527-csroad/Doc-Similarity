from typing import List
from app.processors.embedding_processor import EmbeddingProvider
from app.config import get_settings
import httpx


class ZhipuEmbedding(EmbeddingProvider):
    """智谱 API 向量化"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ZHIPU_API_KEY
        self._dimension = 1024

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            response = httpx.post(
                "https://open.bigmodel.cn/api/paas/v4/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": "embedding-2", "input": text}
            )
            data = response.json()
            embeddings.append(data["data"][0]["embedding"])
        return embeddings

    @property
    def dimension(self) -> int:
        return self._dimension
