from typing import Optional, Type, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .services.cache import RedisCacheService
from .services.database import PostgresDatabaseService
from .services.hybrid import HybridStorageService
from .models.base import BaseModel
from .events import EventEmitter
from src.utils.logging import logger
from src.config import settings


class StorageManager:
    """
    Central manager for all storage services.
    Handles initialization and provides access to different storage layers.
    """

    def __init__(self):
        self.event_emitter = EventEmitter()
        self.engine = None
        self.session_factory = None
        self._cache = None
        self._database = None
        self._hybrid = None
        logger.info("Initialized StorageManager")

    async def initialize(self) -> None:
        """Initialize all storage services."""
        try:
            # For Supabase, use minimal pooling settings to work with PgBouncer
            pool_settings = {
                "pool_size": settings.database_pool_size,
                "max_overflow": 0,  # Disable overflow for PgBouncer
                "pool_pre_ping": True,
                "pool_timeout": settings.database_pool_timeout,
                "pool_use_lifo": True,
            }

            # Use transaction pooler URL for normal operations
            self.engine = create_async_engine(
                settings.active_database_url, **pool_settings
            )

            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            # Initialize Redis cache service
            self._cache = RedisCacheService(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                prefix="bot:",
                events=self.event_emitter,
            )

            logger.info("Storage services initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize storage services: {str(e)}")
            raise

    def get_database(self, model: Type[BaseModel]) -> PostgresDatabaseService:
        """
        Get or create a database service for a specific model.

        Args:
            model: SQLAlchemy model class

        Returns:
            PostgresDatabaseService instance
        """
        return PostgresDatabaseService(
            url=settings.active_database_url,
            model=model,
            events=self.event_emitter,
            **settings.pooling_kwargs,
        )

    def get_hybrid(
        self, model: Type[BaseModel], ttl: Optional[int] = None
    ) -> HybridStorageService:
        """
        Get or create a hybrid service for a specific model.

        Args:
            model: SQLAlchemy model class
            ttl: Optional TTL for cache entries

        Returns:
            HybridStorageService instance
        """
        db_service = self.get_database(model)
        return HybridStorageService(
            cache_service=self._cache,
            db_service=db_service,
            default_ttl=ttl or settings.redis_conversation_ttl,
            events=self.event_emitter,
        )

    @property
    def cache(self) -> RedisCacheService:
        """Get the Redis cache service."""
        if not self._cache:
            raise RuntimeError(
                "Storage services not initialized. Call initialize() first."
            )
        return self._cache

    async def close(self) -> None:
        """Close all storage connections."""
        try:
            if self._cache:
                await self._cache.close()

            if self.engine:
                await self.engine.dispose()

            logger.info("Closed all storage connections")

        except Exception as e:
            logger.error(f"Error closing storage connections: {str(e)}")
            raise

    async def health_check(self) -> Dict[str, bool]:
        """
        Check the health of all storage services.

        Returns:
            Dict with service status
        """
        status = {"cache": False, "database": False}

        try:
            # Check Redis
            if self._cache:
                await self._cache.exists("health_check")
                status["cache"] = True

            # Check Database
            if self.engine:
                async with self.session_factory() as session:
                    await session.execute("SELECT 1")
                status["database"] = True

            logger.info(f"Health check results: {status}")

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")

        return status


# Create a global instance
storage = StorageManager()

# Usage example:
# from src.storage.manager import storage
# await storage.initialize()
# hybrid_service = storage.get_hybrid(UserModel)
# await hybrid_service.get("user_123")
