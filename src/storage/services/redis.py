from redis.asyncio import Redis
from typing import Optional, List, AsyncIterator, Tuple
from ..interfaces import StorageValue, StorageKey, StorageScope
from .base import BaseStorageService
import json
import time


class RedisStorageService(BaseStorageService):
    def __init__(self, redis_url: str, prefix: str = "bot"):
        super().__init__(prefix)
        self.redis = Redis.from_url(redis_url)

    async def get(self, key: StorageKey) -> StorageValue:
        redis_key = self._make_key(key)
        data = await self.redis.get(redis_key)

        if not data:
            raise KeyError(f"Key {redis_key} not found")

        value_data = json.loads(data)
        return StorageValue(
            value=value_data["value"],
            expires_at=value_data.get("expires_at"),
            metadata=value_data.get("metadata", {}),
            version=value_data.get("version"),
        )

    async def set(self, key: StorageKey, value: StorageValue) -> None:
        redis_key = self._make_key(key)
        data = {
            "value": value.value,
            "expires_at": value.expires_at,
            "metadata": value.metadata,
            "version": (value.version or 0) + 1,
        }

        if value.expires_at:
            await self.redis.setex(
                redis_key, int(value.expires_at - time.time()), json.dumps(data)
            )
        else:
            await self.redis.set(redis_key, json.dumps(data))

        # Publish change event
        await self.redis.publish(redis_key, json.dumps(data))

    async def delete(self, key: StorageKey) -> None:
        redis_key = self._make_key(key)
        await self.redis.delete(redis_key)
        # Publish deletion event
        await self.redis.publish(redis_key, json.dumps({"deleted": True}))

    async def list(
        self, scope: StorageScope, scope_id: Optional[int] = None
    ) -> List[StorageKey]:
        pattern = self._make_key(
            StorageKey(name="*", scope=scope, scope_id=scope_id, namespace="*")
        )
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(self._parse_key(key.decode()))
        return keys

    async def watch(
        self, pattern: str
    ) -> AsyncIterator[Tuple[StorageKey, StorageValue]]:
        pubsub = self.redis.pubsub()
        watch_pattern = f"{self.prefix}:{pattern}"
        await pubsub.psubscribe(watch_pattern)

        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    key_str = message["channel"].decode()
                    data = json.loads(message["data"])
                    if "deleted" in data:
                        continue
                    yield self._parse_key(key_str), StorageValue(**data)
        finally:
            await pubsub.punsubscribe(watch_pattern)
