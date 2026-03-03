from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db import get_db
from app.models import Document

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    """系统统计概览"""
    total = await db.execute(select(func.count(Document.id)))
    completed = await db.execute(
        select(func.count(Document.id)).where(Document.status == "completed")
    )
    pending = await db.execute(
        select(func.count(Document.id)).where(Document.status == "pending")
    )

    return {
        "total_documents": total.scalar(),
        "completed": completed.scalar(),
        "pending": pending.scalar()
    }
