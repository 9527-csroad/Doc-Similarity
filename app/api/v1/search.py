from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import Document
from app.schemas import SearchRequest, SearchResponse, SimilarDocument
from app.services import RedisService
from app.services.vector import get_vector_store
from app.processors import get_embedding_provider

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/similar", response_model=SearchResponse)
async def search_similar(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """相似度检索"""
    redis_svc = RedisService()
    threshold = request.threshold if request.threshold is not None else redis_svc.get_threshold()

    # 获取查询向量
    if request.document_id:
        # 基于文档 ID 查询
        result = await db.execute(
            select(Document).where(Document.id == request.document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(404, "Document not found")
        if not doc.text_content:
            raise HTTPException(400, "Document not processed yet")
        query_text = doc.text_content
    elif request.text:
        query_text = request.text
    else:
        raise HTTPException(400, "Either document_id or text is required")

    # 向量化
    embedding = get_embedding_provider()
    query_vector = embedding.embed([query_text])[0]

    vector_store = get_vector_store()
    matches = vector_store.search(query_vector, request.top_k)

    # 过滤阈值并获取文档信息
    results = []
    for doc_id, score in matches:
        if score >= threshold:
            doc_result = await db.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = doc_result.scalar_one_or_none()
            if doc:
                results.append(SimilarDocument(
                    id=doc.id,
                    filename=doc.original_filename,
                    score=score,
                    snippet=doc.text_content[:200] if doc.text_content else None
                ))

    return SearchResponse(
        query_id=request.document_id or "text_query",
        results=results,
        total=len(results),
        threshold_used=threshold
    )
