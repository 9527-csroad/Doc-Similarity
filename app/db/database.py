from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()
connect_args = {}
if settings.db_backend == "sqlite":
    connect_args = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, echo=settings.DEBUG, connect_args=connect_args)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
