from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # App
    APP_NAME: str = "Document Similarity System"
    DEBUG: bool = False
    DEPLOY_MODE: Literal["demo", "production", "standalone"] = "demo"

    # Database
    DB_BACKEND: Literal["postgres", "sqlite"] = "postgres"
    SQLITE_PATH: str = "./data/docsim.db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "docsim"
    POSTGRES_PASSWORD: str = "docsim123"
    POSTGRES_DB: str = "docsim"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "documents"
    LOCAL_STORAGE_PATH: str = "./data/files"
    FAISS_INDEX_PATH: str = "./data/faiss/index.bin"
    FAISS_META_PATH: str = "./data/faiss/meta.json"
    CONFIG_FILE_PATH: str = "./data/config.json"

    # Embedding
    EMBEDDING_PROVIDER: Literal["bge", "openai", "zhipu"] = "bge"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIM: int = 1024
    OPENAI_API_KEY: str = ""
    ZHIPU_API_KEY: str = ""
    GLM_API_KEY: str = "1a09fa8a73c14d0989e7bf0d5fc37d18.biFY8H2nhMiWkgwn"
    GLM_OCR_ENDPOINT: str = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"
    GLM_OCR_MODEL: str = "glm-ocr"

    # Search
    DEFAULT_THRESHOLD: float = 0.8
    DEFAULT_TOP_K: int = 10
    FILE_HASH_DEDUP: bool = True
    OCR_PROVIDER: Optional[Literal["rapid", "paddle", "glm", "none"]] = None
    VECTOR_STORE: Optional[Literal["faiss", "milvus"]] = None
    STORAGE_BACKEND: Optional[Literal["local", "minio"]] = None
    TASK_MODE: Optional[Literal["sync", "celery"]] = None

    @property
    def ocr_provider(self) -> Literal["rapid", "paddle", "glm", "none"]:
        if self.OCR_PROVIDER:
            return self.OCR_PROVIDER
        return "rapid"

    @property
    def vector_store(self) -> Literal["faiss", "milvus"]:
        if self.VECTOR_STORE:
            return self.VECTOR_STORE
        return "milvus" if self.DEPLOY_MODE == "production" else "faiss"

    @property
    def storage_backend(self) -> Literal["local", "minio"]:
        if self.STORAGE_BACKEND:
            return self.STORAGE_BACKEND
        return "minio" if self.DEPLOY_MODE == "production" else "local"

    @property
    def task_mode(self) -> Literal["sync", "celery"]:
        if self.TASK_MODE:
            return self.TASK_MODE
        return "celery" if self.DEPLOY_MODE == "production" else "sync"

    @property
    def db_backend(self) -> Literal["postgres", "sqlite"]:
        if self.DEPLOY_MODE == "standalone" or self.DB_BACKEND == "sqlite":
            return "sqlite"
        return "postgres"

    @property
    def database_url(self) -> str:
        if self.db_backend == "sqlite":
            return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def sync_database_url(self) -> str:
        if self.db_backend == "sqlite":
            return f"sqlite:///{self.SQLITE_PATH}"
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
