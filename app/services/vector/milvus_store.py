from typing import List, Tuple
from app.services.vector.base import VectorStore
from app.services.milvus_service import MilvusService


class MilvusStore(VectorStore):
    def __init__(self):
        self.client = MilvusService()

    def insert(self, doc_id: str, vector: List[float]) -> None:
        self.client.insert(doc_id, vector)

    def search(self, vector: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        return self.client.search(vector, top_k)

    def delete(self, doc_id: str) -> None:
        self.client.delete(doc_id)
