from app.tasks.base import TaskExecutor
from app.tasks.pipeline import process_document_pipeline


class SyncTaskExecutor(TaskExecutor):
    def submit_document(self, doc_id: str, file_content: bytes) -> None:
        process_document_pipeline(doc_id, file_content)
