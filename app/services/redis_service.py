import redis
from app.config import get_settings
from app.services.config_service import get_threshold as file_get_threshold, set_threshold as file_set_threshold

THRESHOLD_KEY = "config:threshold"


class RedisService:
    def __init__(self):
        self.settings = get_settings()
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis | None:
        if self._client is None and self.settings.DEPLOY_MODE != "standalone":
            try:
                self._client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    decode_responses=True
                )
            except Exception:
                pass
        return self._client

    def get_threshold(self) -> float:
        if self.settings.DEPLOY_MODE == "standalone" or self.client is None:
            return file_get_threshold()
        val = self.client.get(THRESHOLD_KEY)
        return float(val) if val else self.settings.DEFAULT_THRESHOLD

    def set_threshold(self, value: float) -> None:
        if self.settings.DEPLOY_MODE == "standalone" or self.client is None:
            file_set_threshold(value)
        else:
            self.client.set(THRESHOLD_KEY, str(value))
