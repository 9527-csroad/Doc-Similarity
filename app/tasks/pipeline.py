import os
import tempfile
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import Document
from app.processors import OCRProcessor, PDFProcessor, get_embedding_provider
from app.services.storage import get_storage
from app.services.vector import get_vector_store

settings = get_settings()
sync_db_url = (
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)
sync_engine = create_engine(sync_db_url)
Session = sessionmaker(bind=sync_engine)


def process_document_pipeline(doc_id: str, file_content: bytes) -> dict:
    session = Session()
    doc = None
    temp_path = None
    try:
        doc = session.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return {"status": "error", "message": "Document not found"}

        doc.status = "processing"
        session.commit()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(file_content)
            temp_path = f.name

        pdf_proc = PDFProcessor()
        text, page_count = pdf_proc.extract_text(temp_path)
        images = pdf_proc.extract_images(temp_path)

        if images:
            ocr_proc = OCRProcessor()
            ocr_text = ocr_proc.batch_extract(images)
            if ocr_text:
                text = text + "\n" + ocr_text

        embedding = get_embedding_provider()
        vectors = embedding.embed([text])

        vector_store = get_vector_store()
        vector_store.insert(doc_id, vectors[0])

        storage = get_storage()
        storage.upload(f"{doc_id}.pdf", file_content)

        doc.status = "completed"
        doc.text_content = text
        doc.page_count = page_count
        doc.processed_at = datetime.utcnow()
        session.commit()

        return {"status": "completed", "page_count": page_count}
    except Exception as e:
        if doc:
            doc.status = "failed"
            doc.error_message = str(e)
            session.commit()
        raise
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        session.close()
