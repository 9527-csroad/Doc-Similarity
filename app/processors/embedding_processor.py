from abc import ABC, abstractmethod
from typing import List
from app.config import get_settings


class EmbeddingProvider(ABC):
    """向量化提供者抽象基类"""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """将文本转换为向量"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass
