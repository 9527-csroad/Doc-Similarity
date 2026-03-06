from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import Document
from app.schemas import DocumentResponse
from app.tasks import get_task_executor
from app.services.storage import get_storage
from app.services.vector import get_vector_store
from app.config import get_settings
import hashlib
import uuid

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """上传文档"""
    settings = get_settings()
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")

    content = await file.read()
    raw_file_hash = hashlib.sha256(content).hexdigest()
    file_hash = raw_file_hash

    if settings.FILE_HASH_DEDUP:
        existing = await db.execute(
            select(Document).where(Document.file_hash == file_hash)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(409, "Document already exists")
    else:
        file_hash = hashlib.sha256(
            f"{raw_file_hash}:{uuid.uuid4().hex}".encode("utf-8")
        ).hexdigest()

    doc = Document(
        filename=file_hash + ".pdf",
        original_filename=file.filename,
        file_size=len(content),
        file_hash=file_hash,
        status="pending",
        doc_metadata={"source_file_hash": raw_file_hash}
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    executor = get_task_executor()
    executor.submit_document(doc.id, content)
    return doc


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """获取文档信息"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """删除文档"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    # 删除 Milvus 向量
    try:
        vector_store = get_vector_store()
        vector_store.delete(doc_id)
    except Exception:
        pass

    # 删除 MinIO 文件
    try:
        storage = get_storage()
        storage.delete(f"{doc_id}.pdf")
    except Exception:
        pass

    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}
