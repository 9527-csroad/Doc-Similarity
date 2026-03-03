from pathlib import Path

from app.config import get_settings
from app.services.storage.base import ObjectStorage


class LocalStorage(ObjectStorage):
    def __init__(self):
        settings = get_settings()
        self.base_path = Path(settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload(self, object_name: str, data: bytes, content_type: str = "application/pdf") -> None:
        path = self.base_path / object_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def download(self, object_name: str) -> bytes:
        path = self.base_path / object_name
        return path.read_bytes()

    def delete(self, object_name: str) -> None:
        path = self.base_path / object_name
        if path.exists():
            path.unlink()
