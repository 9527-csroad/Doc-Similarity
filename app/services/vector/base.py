from abc import ABC, abstractmethod
from typing import List, Tuple


class VectorStore(ABC):
    @abstractmethod
    def insert(self, doc_id: str, vector: List[float]) -> None:
        pass

    @abstractmethod
    def search(self, vector: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        pass

    @abstractmethod
    def delete(self, doc_id: str) -> None:
        pass
