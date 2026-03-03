from app.config import get_settings
from app.services.storage.base import ObjectStorage


def get_storage() -> ObjectStorage:
    settings = get_settings()
    if settings.storage_backend == "minio":
        from app.services.storage.minio_storage import MinioStorage

        return MinioStorage()
    from app.services.storage.local_storage import LocalStorage

    return LocalStorage()


__all__ = ["ObjectStorage", "get_storage"]
