from app.services.minio_service import MinioService
from app.services.storage.base import ObjectStorage


class MinioStorage(ObjectStorage):
    def __init__(self):
        self.client = MinioService()

    def upload(self, object_name: str, data: bytes, content_type: str = "application/pdf") -> None:
        self.client.upload(object_name, data, content_type)

    def download(self, object_name: str) -> bytes:
        return self.client.download(object_name)

    def delete(self, object_name: str) -> None:
        self.client.delete(object_name)
