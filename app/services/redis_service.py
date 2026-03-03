import redis
from typing import Optional
from app.config import get_settings

THRESHOLD_KEY = "config:threshold"


class RedisService:
    """Redis 缓存服务"""

    def __init__(self):
        settings = get_settings()
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.default_threshold = settings.DEFAULT_THRESHOLD

    def get_threshold(self) -> float:
        """获取全局阈值"""
        val = self.client.get(THRESHOLD_KEY)
        return float(val) if val else self.default_threshold

    def set_threshold(self, value: float):
        """设置全局阈值"""
        self.client.set(THRESHOLD_KEY, str(value))
