from dataclasses import dataclass
from typing import Any, Dict, Optional
from .types import EventType
from pathlib import Path


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


@dataclass
class DatabaseEvent(Event):
    """Event fired for database operations"""

    operation: str
    model: str
    data: Dict[str, Any]
    success: bool
    error: Optional[Exception] = None

    def __init__(
        self,
        operation: str,
        model: str,
        data: Dict[str, Any],
        success: bool,
        error: Optional[Exception] = None,
    ):
        super().__init__(type=EventType.DATABASE_OPERATION)
        self.operation = operation
        self.model = model
        self.data = data
        self.success = success
        self.error = error


@dataclass
class FileChangeEvent(Event):
    """Event fired when a file in the src directory changes"""

    file_path: Path
    module_path: str
    change_type: str  # 'modified', 'created', 'deleted'

    def __init__(self, file_path: Path, module_path: str, change_type: str):
        super().__init__(type=EventType.FILE_CHANGED)
        self.file_path = file_path
        self.module_path = module_path
        self.change_type = change_type


@dataclass
class FeatureReloadEvent(Event):
    """Event fired when a feature is reloaded"""

    feature_name: str
    success: bool
    error: Optional[Exception] = None

    def __init__(
        self, feature_name: str, success: bool, error: Optional[Exception] = None
    ):
        super().__init__(type=EventType.FEATURE_RELOADED)
        self.feature_name = feature_name
        self.success = success
        self.error = error
