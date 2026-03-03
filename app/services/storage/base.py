from abc import ABC, abstractmethod


class ObjectStorage(ABC):
    @abstractmethod
    def upload(self, object_name: str, data: bytes, content_type: str = "application/pdf") -> None:
        pass

    @abstractmethod
    def download(self, object_name: str) -> bytes:
        pass

    @abstractmethod
    def delete(self, object_name: str) -> None:
        pass
