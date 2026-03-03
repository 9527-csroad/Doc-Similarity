from fastapi import FastAPI
from app.api.v1 import router as api_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="文档相似度检索系统",
    version="1.0.0"
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
