from app.config import get_settings
from app.tasks.base import TaskExecutor
from app.tasks.sync_executor import SyncTaskExecutor


def get_task_executor() -> TaskExecutor:
    settings = get_settings()
    if settings.task_mode == "celery":
        from app.tasks.celery_executor import CeleryTaskExecutor

        return CeleryTaskExecutor()
    return SyncTaskExecutor()

__all__ = ["get_task_executor", "TaskExecutor"]
