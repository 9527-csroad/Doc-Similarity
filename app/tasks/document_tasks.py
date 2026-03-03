from app.tasks.celery_app import celery_app
from app.tasks.pipeline import process_document_pipeline


@celery_app.task(bind=True, max_retries=3)
def process_document(self, doc_id: str, file_content: bytes):
    try:
        return process_document_pipeline(doc_id, file_content)
    except Exception as e:
        self.retry(exc=e, countdown=60)
