from fastapi import APIRouter
from app.api.v2 import books

router = APIRouter(prefix="/api/v2")
router.include_router(books.router)
