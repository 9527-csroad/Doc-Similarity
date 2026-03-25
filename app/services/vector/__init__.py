from typing import Literal

from app.config import get_settings
from app.services.vector.base import VectorStore


def get_vector_store() -> VectorStore:
    settings = get_settings()
    if settings.vector_store == "milvus":
        from app.services.vector.milvus_store import MilvusStore

        return MilvusStore()
    from app.services.vector.faiss_store import FaissStore

    return FaissStore()


def get_fingerprint_store(mode: Literal["merged", "pooled"]) -> VectorStore:
    settings = get_settings()
    if settings.vector_store == "milvus":
        raise NotImplementedError("Fingerprint dual index only supports FAISS")
    from app.services.vector.faiss_store import FaissStore

    if mode == "merged":
        return FaissStore(
            index_path=settings.FAISS_FINGERPRINT_MERGED_PATH,
            meta_path=settings.FAISS_FINGERPRINT_MERGED_META,
        )
    return FaissStore(
        index_path=settings.FAISS_FINGERPRINT_POOLED_PATH,
        meta_path=settings.FAISS_FINGERPRINT_POOLED_META,
    )


__all__ = ["VectorStore", "get_vector_store", "get_fingerprint_store"]
