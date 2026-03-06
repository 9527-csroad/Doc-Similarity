from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re
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
    same_threshold = 0.92

    # 获取查询向量
    query_metadata = {}
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
        query_metadata = doc.doc_metadata or {}
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
    same_count = 0
    likely_same_count = 0
    similar_count = 0
    for doc_id, score in matches:
        if score < threshold:
            continue
        if request.document_id and doc_id == request.document_id:
            continue

        doc_result = await db.execute(
            select(Document).where(Document.id == doc_id)
        )
        doc = doc_result.scalar_one_or_none()
        if not doc:
            continue
        if score >= same_threshold:
            if _metadata_match(query_metadata, doc.doc_metadata or {}):
                match_level = "same"
                same_count += 1
            else:
                match_level = "likely_same"
                likely_same_count += 1
        else:
            match_level = "similar"
            similar_count += 1

        results.append(SimilarDocument(
            id=doc.id,
            filename=doc.original_filename,
            score=score,
            match_level=match_level,
            snippet=doc.text_content[:200] if doc.text_content else None
        ))

    return SearchResponse(
        query_id=request.document_id or "text_query",
        results=results,
        total=len(results),
        same_count=same_count,
        likely_same_count=likely_same_count,
        similar_count=similar_count,
        threshold_used=threshold
    )


def _metadata_match(source: dict, target: dict) -> bool:
    if not source or not target:
        return False
    title_a = _normalize_text(source.get("title", ""))
    title_b = _normalize_text(target.get("title", ""))
    author_a = _normalize_text(source.get("author", ""))
    author_b = _normalize_text(target.get("author", ""))

    title_match = _fuzzy_equal(title_a, title_b)
    author_match = _fuzzy_equal(author_a, author_b)
    if title_a and title_b and author_a and author_b:
        return title_match and author_match
    return title_match or author_match


def _normalize_text(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "", (value or "").lower())


def _fuzzy_equal(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    return short in long
