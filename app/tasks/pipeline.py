import os
import tempfile
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import Document
from app.processors import OCRProcessor, PDFProcessor, TextCleaner, get_embedding_provider
from app.services.storage import get_storage
from app.services.vector import get_vector_store

settings = get_settings()
sync_engine = create_engine(settings.sync_database_url)
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
        text, page_count, scan_page_images = pdf_proc.extract_text(temp_path)
        metadata = pdf_proc.extract_metadata(temp_path)
        images = list(scan_page_images)
        if settings.ocr_provider != "glm":
            images.extend(pdf_proc.extract_images(temp_path))
        else:
            images = images[:30]

        ocr_text = ""
        if images:
            ocr_proc = OCRProcessor()
            ocr_text = ocr_proc.batch_extract(images)
            if ocr_text:
                text = text + "\n" + ocr_text

        cleaner = TextCleaner()
        cleaned_text, clean_stats = cleaner.clean(text)
        doc.text_content = cleaned_text
        doc.page_count = page_count
        doc.doc_metadata = {
            **(doc.doc_metadata or {}),
            **metadata,
            "clean_stats": clean_stats,
        }
        doc.processed_at = datetime.utcnow()

        if cleaner.is_low_quality(cleaned_text):
            fallback_text = _build_fallback_text(cleaned_text, ocr_text)
            if fallback_text:
                embedding = get_embedding_provider()
                embedding_text = _prepare_embedding_text(embedding, fallback_text)
                vectors = embedding.embed([embedding_text])
                vector_store = get_vector_store()
                vector_store.insert(doc_id, vectors[0])
                doc.status = "completed"
                doc.doc_metadata = {
                    **(doc.doc_metadata or {}),
                    "low_quality_fallback": True,
                    "fallback_chars": len(fallback_text),
                }
                session.commit()
                storage = get_storage()
                storage.upload(f"{doc_id}.pdf", file_content)
                return {"status": "completed", "page_count": page_count}
            doc.status = "low_quality"
            session.commit()
            storage = get_storage()
            storage.upload(f"{doc_id}.pdf", file_content)
            return {"status": "low_quality", "page_count": page_count}

        embedding = get_embedding_provider()
        embedding_text = _prepare_embedding_text(embedding, cleaned_text)
        vectors = embedding.embed([embedding_text])

        vector_store = get_vector_store()
        vector_store.insert(doc_id, vectors[0])

        storage = get_storage()
        storage.upload(f"{doc_id}.pdf", file_content)

        doc.status = "completed"
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


def _prepare_embedding_text(embedding_provider, cleaned_text: str) -> str:
    prepare_fn = getattr(embedding_provider, "prepare_document_text", None)
    if callable(prepare_fn):
        return prepare_fn(cleaned_text)
    return cleaned_text[:24000]


def _build_fallback_text(cleaned_text: str, ocr_text: str) -> str:
    ocr_text = (ocr_text or "").strip()
    cleaned_text = (cleaned_text or "").strip()
    if len(ocr_text) >= 60:
        return ocr_text[:12000]
    if len(cleaned_text) >= 60:
        return cleaned_text[:12000]
    return ""
