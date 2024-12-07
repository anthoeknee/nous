from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Awaitable, Optional
import asyncio
from .interfaces import StorageBackend
from .manager import storage


@dataclass
class FileChangeEvent:
    file_path: str
    module_path: str
    change_type: str


@dataclass
class FeatureReloadEvent:
    feature_name: str
    success: bool
    error: Optional[Exception] = None


class StorageEventBus:
    def __init__(self):
        self._handlers: Dict[type, List[Callable]] = {}
        self._redis = None

    async def initialize(self):
        """Initialize Redis connection if available"""
        if StorageBackend.REDIS in storage.storages:
            self._redis = storage.get_storage(StorageBackend.REDIS)

    def on(self, event_type: type):
        def decorator(func: Callable[[Any], Awaitable[None]]):
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(func)
            return func

        return decorator

    async def emit(self, event: Any):
        """Emit event to local handlers and Redis pub/sub if available"""
        # Local event handling
        if type(event) in self._handlers:
            handlers = self._handlers[type(event)]
            await asyncio.gather(*(handler(event) for handler in handlers))

        # Redis pub/sub if available
        if self._redis:
            event_data = {"type": event.__class__.__name__, "data": event.__dict__}
            await self._redis.publish("events", event_data)


# Global event bus instance
events = StorageEventBus()
