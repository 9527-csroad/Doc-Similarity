from abc import ABC, abstractmethod


class TaskExecutor(ABC):
    @abstractmethod
    def submit_document(self, doc_id: str, file_content: bytes) -> None:
        pass
