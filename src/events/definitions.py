from dataclasses import dataclass
from typing import Any, Dict
from .types import EventType


@dataclass
class Event:
    """Base class for all events"""

    type: EventType


@dataclass
class MessageEvent(Event):
    """Event fired when a message is processed"""

    content: str
    author_id: int
    channel_id: int
    metadata: Dict[str, Any]

    def __init__(
        self, content: str, author_id: int, channel_id: int, metadata: Dict[str, Any]
    ):
        super().__init__(type=EventType.MESSAGE_RECEIVED)
        self.content = content
        self.author_id = author_id
        self.channel_id = channel_id
        self.metadata = metadata


@dataclass
class CommandEvent(Event):
    """Event fired when a command is executed"""

    command_name: str
    args: tuple
    kwargs: Dict[str, Any]
    success: bool

    def __init__(
        self, command_name: str, args: tuple, kwargs: Dict[str, Any], success: bool
    ):
        super().__init__(type=EventType.COMMAND_EXECUTED)
        self.command_name = command_name
        self.args = args
        self.kwargs = kwargs
        self.success = success


@dataclass
class ErrorEvent(Event):
    """Event fired when an error occurs"""

    error: Exception
    context: Dict[str, Any]

    def __init__(self, error: Exception, context: Dict[str, Any]):
        super().__init__(type=EventType.ERROR)
        self.error = error
        self.context = context
