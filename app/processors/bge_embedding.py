from typing import List
from app.processors.embedding_processor import EmbeddingProvider


class BGEEmbedding(EmbeddingProvider):
    """BGE-M3 本地向量化"""

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        from FlagEmbedding import BGEM3FlagModel
        self.model = BGEM3FlagModel(model_name, use_fp16=True)
        self._dimension = 1024

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            max_length=8192
        )['dense_vecs']
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self._dimension
