from collections import defaultdict
from typing import Dict, List, Optional, AsyncIterator, Tuple
from ..interfaces import StorageValue, StorageKey, StorageScope, StorageInterface
from .base import BaseStorageService
import asyncio


class HybridStorageService(BaseStorageService):
    def __init__(
        self,
        memory_storage: Optional[StorageInterface] = None,
        redis_storage: Optional[StorageInterface] = None,
        database_storage: Optional[StorageInterface] = None,
        prefix: str = "bot",
    ):
        super().__init__(prefix)
        self.memory = memory_storage
        self.redis = redis_storage
        self.database = database_storage
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)

    async def get(self, key: StorageKey) -> StorageValue:
        """Try to get value from fastest to slowest storage"""
        errors = []

        # Try memory first
        if self.memory:
            try:
                return await self.memory.get(key)
            except Exception as e:
                errors.append(f"Memory error: {str(e)}")

        # Try Redis next
        if self.redis:
            try:
                value = await self.redis.get(key)
                if self.memory:  # Cache in memory if available
                    await self.memory.set(key, value)
                return value
            except Exception as e:
                errors.append(f"Redis error: {str(e)}")

        # Finally, try database
        if self.database:
            try:
                value = await self.database.get(key)
                # Cache in faster storages
                if self.memory:
                    await self.memory.set(key, value)
                if self.redis:
                    await self.redis.set(key, value)
                return value
            except Exception as e:
                errors.append(f"Database error: {str(e)}")

        raise KeyError(
            f"Key {key} not found in any storage. Errors: {', '.join(errors)}"
        )

    async def set(self, key: StorageKey, value: StorageValue) -> None:
        """Set value in all available storages"""
        tasks = []

        if self.memory:
            tasks.append(self.memory.set(key, value))
        if self.redis:
            tasks.append(self.redis.set(key, value))
        if self.database:
            tasks.append(self.database.set(key, value))

        # Execute all storage operations concurrently
        await asyncio.gather(*tasks)

        # Notify subscribers
        await self._notify_change(key, value)

    async def delete(self, key: StorageKey) -> None:
        """Delete from all storages"""
        tasks = []

        if self.memory:
            tasks.append(self.memory.delete(key))
        if self.redis:
            tasks.append(self.redis.delete(key))
        if self.database:
            tasks.append(self.database.delete(key))

        await asyncio.gather(*tasks)

    async def list(
        self, scope: StorageScope, scope_id: Optional[int] = None
    ) -> List[StorageKey]:
        """Get list from most complete storage"""
        if self.database:
            return await self.database.list(scope, scope_id)
        if self.redis:
            return await self.redis.list(scope, scope_id)
        if self.memory:
            return await self.memory.list(scope, scope_id)
        return []

    async def watch(
        self, pattern: str
    ) -> AsyncIterator[Tuple[StorageKey, StorageValue]]:
        """Combine watch streams from all available storages"""
        queue = asyncio.Queue()
        self._subscribers[pattern].append(queue)

        async def forward_changes(storage: StorageInterface):
            try:
                async for key, value in storage.watch(pattern):
                    await queue.put((key, value))
            except Exception as e:
                print(f"Watch error from {storage.__class__.__name__}: {e}")

        # Start watching all available storages
        tasks = []
        if self.redis:
            tasks.append(asyncio.create_task(forward_changes(self.redis)))
        if self.memory:
            tasks.append(asyncio.create_task(forward_changes(self.memory)))
        if self.database:
            tasks.append(asyncio.create_task(forward_changes(self.database)))

        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers[pattern].remove(queue)
            for task in tasks:
                task.cancel()

    async def _notify_change(self, key: StorageKey, value: StorageValue) -> None:
        """Notify subscribers of changes"""
        storage_key = self._make_key(key)
        for pattern, queues in self._subscribers.items():
            if self._key_matches_pattern(storage_key, pattern):
                for queue in queues:
                    await queue.put((key, value))

    def _key_matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if a key matches a glob-style pattern"""
        import fnmatch

        return fnmatch.fnmatch(key, pattern)
