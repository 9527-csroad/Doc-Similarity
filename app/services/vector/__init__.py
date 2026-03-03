from app.config import get_settings
from app.services.vector.base import VectorStore


def get_vector_store() -> VectorStore:
    settings = get_settings()
    if settings.vector_store == "milvus":
        from app.services.vector.milvus_store import MilvusStore

        return MilvusStore()
    from app.services.vector.faiss_store import FaissStore

    return FaissStore()


__all__ = ["VectorStore", "get_vector_store"]
