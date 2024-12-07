from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Awaitable, Optional
import asyncio


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


class EventSystem:
    def __init__(self):
        self._handlers: Dict[type, List[Callable]] = {}

    def on(self, event_type: type):
        def decorator(func: Callable[[Any], Awaitable[None]]):
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(func)
            return func

        return decorator

    async def emit(self, event: Any):
        if type(event) in self._handlers:
            handlers = self._handlers[type(event)]
            await asyncio.gather(*(handler(event) for handler in handlers))


# Global events instance
events = EventSystem()
