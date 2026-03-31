from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class BookUploadRequest(BaseModel):
    pdf_id: str
    pdf_url: str
    txt_url: str
    fingerprint_mode: Literal["merged", "pooled"] = "merged"


class BookUploadResponse(BaseModel):
    message: str
    time: float
    book_id: Optional[str] = None
    pdf_id: str
    is_duplicate: bool = False
    match_reason: Optional[str] = None
    upload_count: int = 1


class BookSearchRequest(BaseModel):
    pdf_id: str
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    fingerprint_mode: Literal["merged", "pooled"] = "merged"


class BookSearchItem(BaseModel):
    pdf_id: str
    pdf_url: Optional[str] = None
    book_id: str
    upload_date: datetime
    similarity: float
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    is_self: bool = False


class BookSearchResponse(BaseModel):
    message: str
    time: float
    query_pdf_id: str
    threshold: float
    total: int
    results: List[BookSearchItem]


class HotlistRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    threshold: float = Field(default=1.0, ge=0.0, le=1.0)
    top_n: int = Field(default=20, ge=1, le=100)
    fingerprint_mode: Literal["merged", "pooled"] = "merged"


class HotlistBookItem(BaseModel):
    book_ids: List[str]
    pdf_ids: List[str]
    pdf_urls: List[Optional[str]]
    upload_count: int
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    representative_book_id: str


class HotlistResponse(BaseModel):
    message: str
    time: float
    start_date: datetime
    end_date: datetime
    threshold: float
    total_groups: int
    results: List[HotlistBookItem]
