from minio import Minio
from minio.error import S3Error
from app.config import get_settings
import io


class MinioService:
    """MinIO 文件存储服务"""

    def __init__(self):
        settings = get_settings()
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保 Bucket 存在"""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload(self, object_name: str, data: bytes, content_type: str = "application/pdf"):
        """上传文件"""
        self.client.put_object(
            self.bucket,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type
        )

    def download(self, object_name: str) -> bytes:
        """下载文件"""
        response = self.client.get_object(self.bucket, object_name)
        return response.read()

    def delete(self, object_name: str):
        """删除文件"""
        self.client.remove_object(self.bucket, object_name)
