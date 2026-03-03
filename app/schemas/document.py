from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentBase(BaseModel):
    filename: str
    metadata: Optional[dict] = {}


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    status: str
    page_count: int
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
