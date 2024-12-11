from typing import Optional, TypeVar, Generic, Dict, Any, List
from ..interfaces import StorageInterface
from .cache import RedisCacheService
from .database import PostgresDatabaseService
from ..events import EventEmitter, EventType, StorageEvent
from src.utils.logging import logger

T = TypeVar("T")


class HybridStorageService(StorageInterface[T]):
    """Hybrid storage service combining Redis and PostgreSQL."""

    def __init__(
        self,
        cache_service: RedisCacheService,
        db_service: PostgresDatabaseService,
        default_ttl: Optional[int] = None,
        events: Optional[EventEmitter] = None,
    ):
        self.cache = cache_service
        self.db = db_service
        self.default_ttl = default_ttl
        self.events = events or EventEmitter()
        logger.info("Initialized hybrid storage service")

    async def get(self, key: str) -> Optional[T]:
        """Get value from cache, falling back to database."""
        try:
            # Try cache first
            value = await self.cache.get(key)
            if value is not None:
                return value

            # Fall back to database
            value = await self.db.get(key)
            if value is not None:
                # Update cache
                await self.cache.set(key, value, self.default_ttl)
            return value

        except Exception as e:
            logger.error(f"Hybrid get error for key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Set value in both cache and database."""
        try:
            # Set in database first
            db_success = await self.db.set(key, value)
            if not db_success:
                return False

            # Then set in cache
            cache_success = await self.cache.set(key, value, ttl or self.default_ttl)

            if cache_success:
                await self.events.emit(
                    StorageEvent(type=EventType.CREATE, key=key, value=value)
                )

            return cache_success

        except Exception as e:
            logger.error(f"Hybrid set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from both cache and database."""
        try:
            # Delete from database first
            db_success = await self.db.delete(key)

            # Then delete from cache
            cache_success = await self.cache.delete(key)

            if db_success or cache_success:
                await self.events.emit(StorageEvent(type=EventType.DELETE, key=key))

            return db_success and cache_success

        except Exception as e:
            logger.error(f"Hybrid delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in either cache or database."""
        try:
            # Check cache first
            if await self.cache.exists(key):
                return True

            # Fall back to database
            return await self.db.exists(key)

        except Exception as e:
            logger.error(f"Hybrid exists error for key {key}: {str(e)}")
            return False

    async def sync_cache(self, pattern: str = "*") -> int:
        """Sync database values to cache."""
        try:
            count = 0
            async for key, value in self.db.iterate_pattern(pattern):
                await self.cache.set(key, value, self.default_ttl)
                count += 1
            return count

        except Exception as e:
            logger.error(f"Hybrid sync_cache error: {str(e)}")
            return 0

    async def close(self) -> None:
        """Close both cache and database connections."""
        try:
            await self.cache.close()
            await self.db.close()
            logger.info("Closed hybrid storage connections")
        except Exception as e:
            logger.error(f"Error closing hybrid storage connections: {str(e)}")
