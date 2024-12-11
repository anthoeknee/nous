import json
from typing import Any, Dict, Optional, TypeVar, List
import redis.asyncio as redis
from ..interfaces import CacheInterface
from ..events import EventEmitter, EventType, StorageEvent
from src.utils.logging import logger

T = TypeVar("T")


class RedisCacheService(CacheInterface[T]):
    """Redis-based cache implementation."""

    def __init__(
        self,
        host: str,
        port: int,
        password: str,
        db: int = 0,
        prefix: str = "bot:",
        events: Optional[EventEmitter] = None,
    ):
        self.prefix = prefix
        self.events = events or EventEmitter()
        self.redis = redis.Redis(
            host=host, port=port, password=password, db=db, decode_responses=True
        )
        logger.info(f"Initialized Redis cache service with prefix: {prefix}")

    def _key(self, key: str) -> str:
        """Prefix key with namespace."""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[T]:
        """Get value from Redis."""
        try:
            value = await self.redis.get(self._key(key))
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL."""
        try:
            key = self._key(key)
            await self.redis.set(key, json.dumps(value), ex=ttl)
            await self.events.emit(
                StorageEvent(type=EventType.CREATE, key=key, value=value)
            )
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from Redis."""
        try:
            key = self._key(key)
            result = await self.redis.delete(key)
            if result:
                await self.events.emit(StorageEvent(type=EventType.DELETE, key=key))
            return bool(result)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return bool(await self.redis.exists(self._key(key)))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {str(e)}")
            return False

    async def get_pattern(self, pattern: str) -> Dict[str, T]:
        """Get all keys matching pattern."""
        try:
            keys = await self.redis.keys(self._key(pattern))
            if not keys:
                return {}

            pipeline = self.redis.pipeline()
            for key in keys:
                pipeline.get(key)

            values = await pipeline.execute()
            return {
                k.removeprefix(self.prefix): json.loads(v)
                for k, v in zip(keys, values)
                if v is not None
            }
        except Exception as e:
            logger.error(f"Redis pattern match error for pattern {pattern}: {str(e)}")
            return {}

    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to Redis channel."""
        try:
            return await self.redis.publish(self._key(channel), json.dumps(message))
        except Exception as e:
            logger.error(f"Redis publish error for channel {channel}: {str(e)}")
            return 0

    async def subscribe(self, channel: str, callback: callable) -> None:
        """Subscribe to Redis channel."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self._key(channel))

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await callback(json.loads(message["data"]))
        except Exception as e:
            logger.error(f"Redis subscribe error for channel {channel}: {str(e)}")
            await pubsub.unsubscribe(self._key(channel))

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.close()
        logger.info("Closed Redis connection")
