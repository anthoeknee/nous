from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime, timezone


class EventType(Enum):
    """Storage event types."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPIRE = "expire"


@dataclass
class StorageEvent:
    """Event data structure."""

    type: EventType
    key: str
    value: Optional[Any] = None
    timestamp: datetime = datetime.now(timezone.utc)
    metadata: Optional[dict] = None


class EventEmitter:
    """Simple event emitter for storage events."""

    def __init__(self):
        self._handlers = {}

    async def emit(self, event: StorageEvent) -> None:
        """Emit an event to all registered handlers."""
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                await handler(event)

    def on(self, event_type: EventType, handler: callable) -> None:
        """Register an event handler."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def off(self, event_type: EventType, handler: callable) -> None:
        """Remove an event handler."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
