import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.book import Book, BookUpload
from app.schemas.book import (
    BookSearchRequest, BookSearchResponse, BookSearchItem,
    BookUploadRequest, BookUploadResponse,
    HotlistRequest, HotlistResponse, HotlistBookItem,
)
from app.services.vector import get_fingerprint_store
from app.tasks.book_pipeline import process_book_pipeline

router = APIRouter(prefix="/books", tags=["books-v2"])


@router.post("/upload", response_model=BookUploadResponse)
async def upload_book(request: BookUploadRequest):
    t0 = time.perf_counter()
    try:
        result = process_book_pipeline(
            pdf_id=request.pdf_id,
            pdf_url=request.pdf_url,
            txt_url=request.txt_url,
            fingerprint_mode=request.fingerprint_mode,
        )
        book_id = result.get("book_id")
        msg = (
            "success"
            if book_id
            else (result.get("message") or "error")
        )
        elapsed = round(time.perf_counter() - t0, 6)
        return BookUploadResponse(
            message=msg,
            time=elapsed,
            book_id=book_id,
            pdf_id=request.pdf_id,
            is_duplicate=result.get("is_duplicate", False),
            match_reason=result.get("match_reason"),
            upload_count=result.get("upload_count", 1),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=BookSearchResponse)
async def search_similar_books(
    request: BookSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    t0 = time.perf_counter()
    upload_result = await db.execute(
        select(BookUpload).where(BookUpload.pdf_id == request.pdf_id)
    )
    upload = upload_result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="pdf_id not found")

    query_book_id = upload.book_id
    mode = request.fingerprint_mode
    vector_store = get_fingerprint_store(mode)
    vector = vector_store.get_vector(query_book_id)
    if vector is None:
        raise HTTPException(status_code=400, detail="Book vector not found, not processed yet")
    matches = vector_store.search(vector, top_k=500)

    matched_book_ids = [
        book_id for book_id, score in matches
        if score >= request.threshold
    ]
    score_map = {book_id: score for book_id, score in matches}

    if query_book_id not in matched_book_ids:
        matched_book_ids.append(query_book_id)
        score_map[query_book_id] = 1.0

    results: List[BookSearchItem] = []
    for book_id in matched_book_ids:
        uploads_result = await db.execute(
            select(BookUpload).where(BookUpload.book_id == book_id)
        )
        uploads = uploads_result.scalars().all()

        book_result = await db.execute(select(Book).where(Book.id == book_id))
        book = book_result.scalar_one_or_none()

        for up in uploads:
            results.append(BookSearchItem(
                pdf_id=up.pdf_id,
                pdf_url=up.pdf_url,
                book_id=book_id,
                upload_date=up.upload_date,
                similarity=round(score_map.get(book_id, 1.0), 6),
                title=book.title if book else None,
                author=book.author if book else None,
                isbn=book.isbn if book else None,
                is_self=(book_id == query_book_id),
            ))

    results.sort(key=lambda x: (-x.similarity, x.upload_date))
    elapsed = round(time.perf_counter() - t0, 6)
    return BookSearchResponse(
        message="success",
        time=elapsed,
        query_pdf_id=request.pdf_id,
        threshold=request.threshold,
        total=len(results),
        results=results,
    )


@router.post("/hotlist", response_model=HotlistResponse)
async def hot_books(
    request: HotlistRequest,
    db: AsyncSession = Depends(get_db),
):
    t0 = time.perf_counter()
    uploads_result = await db.execute(
        select(BookUpload).where(
            and_(
                BookUpload.upload_date >= request.start_date,
                BookUpload.upload_date <= request.end_date,
            )
        )
    )
    uploads = uploads_result.scalars().all()
    if not uploads:
        elapsed = round(time.perf_counter() - t0, 6)
        return HotlistResponse(
            message="success",
            time=elapsed,
            start_date=request.start_date,
            end_date=request.end_date,
            threshold=request.threshold,
            total_groups=0,
            results=[],
        )

    from collections import defaultdict
    book_uploads_map: dict = defaultdict(list)
    for up in uploads:
        book_uploads_map[up.book_id].append((up.pdf_id, up.pdf_url))

    unique_book_ids = list(book_uploads_map.keys())

    if request.threshold >= 1.0:
        groups = [
            {"book_ids": [bid], "pdfs": book_uploads_map[bid]}
            for bid in unique_book_ids
        ]
    else:
        vector_store = get_fingerprint_store(request.fingerprint_mode)
        book_vectors = {}
        for bid in unique_book_ids:
            vec = vector_store.get_vector(bid)
            if vec is not None:
                book_vectors[bid] = vec

        visited = set()
        groups = []
        for bid in unique_book_ids:
            if bid in visited:
                continue
            visited.add(bid)
            group_book_ids = [bid]
            group_pdfs = list(book_uploads_map[bid])
            if bid in book_vectors:
                matches = vector_store.search(book_vectors[bid], top_k=500)
                for other_id, score in matches:
                    if other_id != bid and other_id not in visited and score >= request.threshold:
                        if other_id in book_uploads_map:
                            visited.add(other_id)
                            group_book_ids.append(other_id)
                            group_pdfs.extend(book_uploads_map[other_id])
            groups.append({"book_ids": group_book_ids, "pdfs": group_pdfs})

    results: List[HotlistBookItem] = []
    for group in groups:
        rep_id = group["book_ids"][0]
        book_result = await db.execute(select(Book).where(Book.id == rep_id))
        book = book_result.scalar_one_or_none()
        pdf_ids = [pid for pid, _ in group["pdfs"]]
        pdf_urls = [purl for _, purl in group["pdfs"]]
        results.append(HotlistBookItem(
            book_ids=group["book_ids"],
            pdf_ids=pdf_ids,
            pdf_urls=pdf_urls,
            upload_count=len(pdf_ids),
            title=book.title if book else None,
            author=book.author if book else None,
            isbn=book.isbn if book else None,
            representative_book_id=rep_id,
        ))

    results.sort(key=lambda x: -x.upload_count)
    results = results[: request.top_n]

    elapsed = round(time.perf_counter() - t0, 6)
    return HotlistResponse(
        message="success",
        time=elapsed,
        start_date=request.start_date,
        end_date=request.end_date,
        threshold=request.threshold,
        total_groups=len(results),
        results=results,
    )
