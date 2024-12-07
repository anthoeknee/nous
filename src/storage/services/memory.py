from typing import Dict, List, Optional, AsyncIterator, Tuple
from collections import defaultdict
import time
import asyncio
from ..interfaces import StorageValue, StorageKey, StorageScope
from .base import BaseStorageService


class MemoryStorageService(BaseStorageService):
    def __init__(self, prefix: str = "bot"):
        super().__init__(prefix)
        self._storage: Dict[str, Dict[str, StorageValue]] = defaultdict(dict)
        self._indices: Dict[str, Dict[str, List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)

    def _make_index_key(self, scope: StorageScope, scope_id: Optional[int]) -> str:
        return f"{scope.value}:{scope_id if scope_id is not None else '*'}"

    async def get(self, key: StorageKey) -> StorageValue:
        storage_key = self._make_key(key)
        value = self._storage.get(key.namespace, {}).get(storage_key)

        if not value:
            raise KeyError(f"Key {storage_key} not found")

        if value.expires_at and value.expires_at < time.time():
            await self.delete(key)
            raise KeyError(f"Key {storage_key} has expired")

        return value

    async def set(self, key: StorageKey, value: StorageValue) -> None:
        storage_key = self._make_key(key)
        index_key = self._make_index_key(key.scope, key.scope_id)

        if key.namespace not in self._storage:
            self._storage[key.namespace] = {}

        self._storage[key.namespace][storage_key] = value
        self._indices[key.namespace][index_key].append(storage_key)

        # Notify subscribers
        for pattern, queues in self._subscribers.items():
            if self._key_matches_pattern(storage_key, pattern):
                for queue in queues:
                    await queue.put((key, value))

    async def delete(self, key: StorageKey) -> None:
        storage_key = self._make_key(key)
        index_key = self._make_index_key(key.scope, key.scope_id)

        if storage_key in self._storage.get(key.namespace, {}):
            del self._storage[key.namespace][storage_key]
            self._indices[key.namespace][index_key].remove(storage_key)

    async def list(
        self, scope: StorageScope, scope_id: Optional[int] = None
    ) -> List[StorageKey]:
        index_key = self._make_index_key(scope, scope_id)
        keys = []

        for namespace, indices in self._indices.items():
            for storage_key in indices.get(index_key, []):
                keys.append(self._parse_key(storage_key))

        return keys

    def _key_matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if a key matches a glob-style pattern"""
        import fnmatch

        return fnmatch.fnmatch(key, pattern)

    async def watch(
        self, pattern: str
    ) -> AsyncIterator[Tuple[StorageKey, StorageValue]]:
        queue = asyncio.Queue()
        watch_pattern = f"{self.prefix}:{pattern}"
        self._subscribers[watch_pattern].append(queue)

        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers[watch_pattern].remove(queue)
