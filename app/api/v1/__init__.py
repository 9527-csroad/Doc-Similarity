from fastapi import APIRouter
from app.api.v1 import documents, search, stats, config

router = APIRouter(prefix="/api/v1")

router.include_router(documents.router)
router.include_router(search.router)
router.include_router(stats.router)
router.include_router(config.router)
