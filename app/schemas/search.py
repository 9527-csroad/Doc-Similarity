from pydantic import BaseModel, Field
from typing import Optional, List


class SearchRequest(BaseModel):
    document_id: Optional[str] = None
    text: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=100)
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class SimilarDocument(BaseModel):
    id: str
    filename: str
    score: float
    match_level: str
    snippet: Optional[str] = None


class SearchResponse(BaseModel):
    query_id: str
    results: List[SimilarDocument]
    total: int
    same_count: int
    likely_same_count: int
    similar_count: int
    threshold_used: float
