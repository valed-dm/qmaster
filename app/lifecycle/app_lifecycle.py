"""
Application lifecycle management.

Handles startup and shutdown sequences including initialization
of monitoring, HTTP sessions, database connections, and Redis/RateLimiting.
"""

from typing import Optional

import aiohttp
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis
import sentry_sdk

from app.core.config import settings
from app.core.logging import log
from app.lifecycle.db_lifecycle import DatabaseLifecycle


class AppLifecycle:
    """Manages the startup and shutdown of the FastAPI application."""

    app: FastAPI
    aiohttp_session: Optional[aiohttp.ClientSession]
    redis: Optional[Redis]

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self.aiohttp_session = None
        self.redis = None

    async def on_startup(self) -> None:
        """Orchestrates the application's startup sequence."""
        log.info("Starting {} app...", settings.APP_NAME)

        if settings.GLITCHTIP_DSN:
            sentry_sdk.init(str(settings.GLITCHTIP_DSN), traces_sample_rate=1.0)

        await self._initialize_aiohttp()
        await self._initialize_redis_limiter()
        await DatabaseLifecycle.initialize()

        log.info("{} startup complete. Ready to serve requests.", settings.APP_NAME)

    async def on_shutdown(self) -> None:
        """Orchestrates the application's shutdown sequence."""
        log.info("Shutting down {} app...", settings.APP_NAME)

        await self._close_aiohttp()
        await self._close_redis()
        await DatabaseLifecycle.shutdown()

        log.info("{} shutdown complete.", settings.APP_NAME)

    async def _initialize_aiohttp(self) -> None:
        """Initializes the shared aiohttp client session."""
        self.aiohttp_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.AIOHTTP_TIMEOUT_SECONDS)
        )
        self.app.state.aiohttp_session = self.aiohttp_session
        log.info("Aiohttp session initialized.")

    async def _close_aiohttp(self) -> None:
        """Gracefully closes the shared aiohttp client session."""
        try:
            if self.aiohttp_session and not self.aiohttp_session.closed:
                await self.aiohttp_session.close()
                log.info("Aiohttp session closed.")
        except Exception as e:
            log.error("Error closing aiohttp session: {}", e, exc_info=True)

    async def _initialize_redis_limiter(self) -> None:
        """Initializes Redis connection and FastAPILimiter."""
        try:
            self.redis = Redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )

            await FastAPILimiter.init(self.redis)

            log.info("Redis and Rate Limiter initialized.")
        except Exception as e:
            log.error("Failed to initialize Redis/Limiter: {}", e, exc_info=True)
            raise

    async def _close_redis(self) -> None:
        """Gracefully closes the Redis connection."""
        try:
            if self.redis:
                await self.redis.close()
                log.info("Redis connection closed.")
        except Exception as e:
            log.error("Error closing Redis connection: {}", e, exc_info=True)
