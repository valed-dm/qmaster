from typing import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.db_manager import db_manager


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """
    Dependency for getting an async Redis client.
    decode_responses=True ensures we get Strings, not Bytes.
    """
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True, encoding="utf-8")
    try:
        yield client
    finally:
        await client.aclose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session and handles the
    transaction lifecycle (commit/rollback) for each request.
    """
    async with db_manager.get_session() as session:
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()

            raise
