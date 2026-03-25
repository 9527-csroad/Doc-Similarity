import hashlib
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.book import Book, BookUpload
from app.processors import PDFProcessor, get_embedding_provider
from app.processors.fingerprint import compute_merged_vector, compute_pooled_vector
from app.services.vector import get_fingerprint_store

settings = get_settings()
sync_engine = create_engine(settings.sync_database_url)
Session = sessionmaker(bind=sync_engine)

_VECTOR_SIMILARITY_THRESHOLD = 0.9999


def process_book_pipeline(
    pdf_id: str,
    pdf_url: str,
    txt_url: str,
    fingerprint_mode: str = "merged",
) -> dict:
    if fingerprint_mode not in ("merged", "pooled"):
        fingerprint_mode = "merged"
    session = Session()
    try:
        if session.query(BookUpload).filter(BookUpload.pdf_id == pdf_id).first():
            return {"status": "error", "message": f"pdf_id {pdf_id} already exists"}

        pdf_bytes = _download(pdf_url)
        content_hash = hashlib.sha256(pdf_bytes).hexdigest()
        metadata = _extract_metadata_from_pdf_then_delete(pdf_bytes)

        txt_content = _download_text(txt_url)
        existing_book, match_reason = _find_existing_book(
            session, content_hash, txt_content, metadata, fingerprint_mode
        )

        if existing_book:
            existing_book.upload_count += 1
            existing_book.updated_at = datetime.utcnow()
            upload = BookUpload(
                pdf_id=pdf_id,
                book_id=existing_book.id,
                pdf_url=pdf_url,
                txt_url=txt_url,
                upload_date=datetime.utcnow(),
            )
            session.add(upload)
            session.commit()
            return {
                "status": "success",
                "book_id": existing_book.id,
                "is_duplicate": True,
                "match_reason": match_reason,
                "upload_count": existing_book.upload_count,
            }

        embedding = get_embedding_provider()
        prepare_fn = getattr(embedding, "prepare_document_text", None)
        embed_fn = lambda texts: embedding.embed(texts)
        chars_per_page = settings.CHARS_PER_PSEUDO_PAGE
        title = metadata.get("title") or None

        vec_merged = compute_merged_vector(
            txt_content, embed_fn, chars_per_page, title, prepare_fn
        )
        vec_pooled = compute_pooled_vector(
            txt_content, embed_fn, chars_per_page, title
        )

        from app.processors.pseudo_pages import build_fingerprint_segments
        _, _, pseudo_page_count = build_fingerprint_segments(
            txt_content, chars_per_page, title
        )

        book = Book(
            content_hash=content_hash,
            isbn=metadata.get("isbn") or None,
            title=metadata.get("title") or None,
            author=metadata.get("author") or None,
            publisher=metadata.get("publisher") or None,
            edition=metadata.get("edition") or None,
            text_content=txt_content[:65535] if txt_content else None,
            page_count=pseudo_page_count,
            pseudo_page_count=pseudo_page_count,
            status="completed",
            upload_count=1,
        )
        session.add(book)
        session.flush()

        text_path = _save_text_to_local(book.id, txt_content)
        book.text_path = text_path
        session.flush()

        store_merged = get_fingerprint_store("merged")
        store_pooled = get_fingerprint_store("pooled")
        store_merged.insert(book.id, vec_merged)
        store_pooled.insert(book.id, vec_pooled)

        upload = BookUpload(
            pdf_id=pdf_id,
            book_id=book.id,
            pdf_url=pdf_url,
            txt_url=txt_url,
            upload_date=datetime.utcnow(),
        )
        session.add(upload)
        session.commit()
        return {
            "status": "success",
            "book_id": book.id,
            "is_duplicate": False,
            "match_reason": None,
            "upload_count": 1,
        }

    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


def _extract_metadata_from_pdf_then_delete(pdf_bytes: bytes) -> dict:
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            temp_path = f.name
        metadata = PDFProcessor().extract_metadata(temp_path)
        return metadata or {}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def _save_text_to_local(book_id: str, content: str) -> str:
    base = Path(settings.TEXTS_BASE_PATH)
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{book_id}.txt"
    path.write_text(content or "", encoding="utf-8")
    return str(path)


def _find_existing_book(
    session,
    content_hash: str,
    txt_content: str,
    metadata: dict,
    fingerprint_mode: str,
) -> Tuple[Optional[Book], Optional[str]]:
    book = session.query(Book).filter(Book.content_hash == content_hash).first()
    if book:
        return book, "content_hash"

    isbn = metadata.get("isbn")
    if isbn:
        book = session.query(Book).filter(Book.isbn == isbn).first()
        if book:
            return book, "isbn"

    embedding = get_embedding_provider()
    prepare_fn = getattr(embedding, "prepare_document_text", None)
    embed_fn = lambda texts: embedding.embed(texts)
    chars = get_settings().CHARS_PER_PSEUDO_PAGE
    title = metadata.get("title") or None

    if fingerprint_mode == "merged":
        vec = compute_merged_vector(
            txt_content, embed_fn, chars, title, prepare_fn
        )
    else:
        vec = compute_pooled_vector(txt_content, embed_fn, chars, title)

    store = get_fingerprint_store(fingerprint_mode)
    matches = store.search(vec, top_k=1)
    if matches:
        best_id, best_score = matches[0]
        if best_score >= _VECTOR_SIMILARITY_THRESHOLD:
            book = session.query(Book).filter(Book.id == best_id).first()
            if book:
                return book, "vector"

    return None, None


def _download(url: str) -> bytes:
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content


def _download_text(url: str) -> str:
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text
