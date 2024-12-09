from typing import Dict, List, Any, Optional, Set, AsyncIterator, Tuple
from datetime import datetime
import asyncio
import re
import time
from ..interfaces import (
    StorageInterface,
    StorageKey,
    StorageValue,
    StorageEvent,
    StorageEventType,
)
from collections import defaultdict


class MemoryStorageService(StorageInterface):
    def __init__(self):
        self._data = {}
        self._subscribers = {}
        self._expiry_times = {}

    async def get(self, key: StorageKey) -> StorageValue:
        """Get a value from memory storage"""
        key_str = str(key)
        if key_str not in self._data:
            raise KeyError(f"Key not found: {key_str}")

        # Check expiration
        if key_str in self._expiry_times:
            if datetime.now().timestamp() > self._expiry_times[key_str]:
                del self._data[key_str]
                del self._expiry_times[key_str]
                raise KeyError(f"Key expired: {key_str}")

        return self._data[key_str]

    async def set(self, key: StorageKey, value: StorageValue) -> None:
        """Set a value in memory storage"""
        self._data[key] = value.value
        if value.expires_at:
            self._expiry_times[key] = value.expires_at

        # Create storage event
        event = StorageEvent(type=StorageEventType.SET, key=key, value=value)

        # Notify subscribers
        await self._notify_subscribers(event)

    async def delete(self, key: StorageKey) -> None:
        """Delete a value from memory storage"""
        key_str = str(key)
        if key_str in self._data:
            del self._data[key_str]
            if key_str in self._expiry_times:
                del self._expiry_times[key_str]

            # Notify subscribers
            event = StorageEvent(type=StorageEventType.DELETE, key=key, value=None)
            await self._notify_subscribers(event)

    async def list(
        self, scope: str, scope_id: Optional[int] = None
    ) -> List[StorageKey]:
        """List all keys in a scope"""
        keys = []
        prefix = f"{scope}:{scope_id if scope_id else ''}"
        for key_str in self._data.keys():
            if key_str.startswith(prefix):
                parts = key_str.split(":")
                keys.append(
                    StorageKey(
                        name=parts[-1],
                        scope=scope,
                        scope_id=scope_id,
                        namespace=parts[2] if len(parts) > 3 else None,
                    )
                )
        return keys

    async def watch(
        self, pattern: str
    ) -> AsyncIterator[Tuple[StorageKey, StorageValue]]:
        """Watch for changes to keys matching pattern"""
        queue = await self.subscribe(pattern)
        try:
            while True:
                event = await queue.get()
                if event.type in [StorageEventType.SET, StorageEventType.DELETE]:
                    yield (event.key, event.value)
        finally:
            await self.unsubscribe(pattern, queue)

    async def subscribe(self, pattern: str) -> asyncio.Queue:
        """Subscribe to storage events matching pattern"""
        queue = asyncio.Queue()
        self._subscribers[pattern].add(queue)
        return queue

    async def unsubscribe(self, pattern: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from storage events"""
        if pattern in self._subscribers:
            self._subscribers[pattern].discard(queue)
            if not self._subscribers[pattern]:
                del self._subscribers[pattern]

    async def _notify_subscribers(self, event: StorageEvent) -> None:
        """Notify subscribers of storage events"""
        for pattern, queues in self._subscribers.items():
            if self._matches_pattern(event.key, pattern):
                for queue in queues:
                    await queue.put(event)

    async def initialize(self) -> None:
        """Initialize the storage service"""
        pass  # No initialization needed for memory storage

    async def cleanup(self) -> None:
        """Clean up expired values"""
        current_time = datetime.now().timestamp()
        expired_keys = [
            key
            for key, expiry_time in self._expiry_times.items()
            if current_time > expiry_time
        ]
        for key in expired_keys:
            if key in self._data:
                del self._data[key]
                del self._expiry_times[key]
