from app.tasks.base import TaskExecutor
from app.tasks.document_tasks import process_document


class CeleryTaskExecutor(TaskExecutor):
    def submit_document(self, doc_id: str, file_content: bytes) -> None:
        process_document.delay(doc_id, file_content)
