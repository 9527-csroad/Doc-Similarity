import sys
from pathlib import Path

from fastapi import FastAPI
from app.api.v2 import router as api_v2_router
from app.config import get_settings

_dm_root = Path(__file__).resolve().parent / "dm"
if str(_dm_root) not in sys.path:
    sys.path.insert(0, str(_dm_root))

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="文档相似度检索系统",
    version="2.0.0"
)

import dm.nacos.NacosHelper as nacosHelper


@app.on_event("startup")
def startup_event():
    nacosHelper.registerService()
    nacosHelper.sendHeartbeatJob()


@app.on_event("shutdown")
def shutdown_event():
    nacosHelper.shutdown_heartbeat()


app.include_router(api_v2_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
