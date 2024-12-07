from enum import Enum, auto
from typing import Any, Callable, Coroutine

# Type alias for event handlers
EventHandler = Callable[..., Coroutine[Any, Any, None]]


class EventPriority(Enum):
    """Priority levels for event handlers"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    MONITOR = 3


class EventType(Enum):
    """Predefined event types for the bot"""

    # Core events
    BOT_READY = auto()
    BOT_SHUTDOWN = auto()

    # Message events
    MESSAGE_RECEIVED = auto()
    MESSAGE_EDITED = auto()
    MESSAGE_DELETED = auto()

    # Command events
    COMMAND_EXECUTED = auto()
    COMMAND_ERROR = auto()
    COMMAND_COOLDOWN = auto()

    # User events
    USER_JOIN = auto()
    USER_LEAVE = auto()
    USER_UPDATE = auto()

    # Voice events
    VOICE_JOIN = auto()
    VOICE_LEAVE = auto()
    VOICE_STATE_UPDATE = auto()

    # Error events
    ERROR = auto()
    API_ERROR = auto()
    DATABASE_ERROR = auto()

    # Custom events
    CUSTOM_EVENT = auto()  # For user-defined events

    # Database events
    DATABASE_OPERATION = auto()

    # Hot reload events
    FILE_CHANGED = auto()
    FEATURE_RELOADED = auto()

    def __str__(self) -> str:
        return self.name.lower()
