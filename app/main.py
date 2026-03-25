from fastapi import FastAPI
from app.api.v2 import router as api_v2_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="文档相似度检索系统",
    version="2.0.0"
)

app.include_router(api_v2_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
