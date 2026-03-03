from fastapi import APIRouter
from app.schemas import ThresholdConfig, ThresholdResponse
from app.services import RedisService

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/threshold", response_model=ThresholdResponse)
async def get_threshold():
    """获取当前阈值配置"""
    redis_svc = RedisService()
    return ThresholdResponse(
        global_threshold=redis_svc.get_threshold(),
        source="global"
    )


@router.put("/threshold", response_model=ThresholdResponse)
async def set_threshold(config: ThresholdConfig):
    """设置全局阈值"""
    redis_svc = RedisService()
    redis_svc.set_threshold(config.threshold)
    return ThresholdResponse(
        global_threshold=config.threshold,
        source="global"
    )
