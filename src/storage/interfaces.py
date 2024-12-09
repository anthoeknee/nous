from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import time

T = TypeVar("T")


class StorageScope(str, Enum):
    """Scope of storage keys"""

    GLOBAL = "global"
    GUILD = "guild"
    CHANNEL = "channel"
    USER = "user"
    FEATURE = "feature"


class StorageBackend(str, Enum):
    """Available storage backends"""

    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"
    HYBRID = "hybrid"


class StorageEventType(str, Enum):
    """Types of storage events"""

    SET = "set"
    DELETE = "delete"
    EXPIRE = "expire"


@dataclass(frozen=True)
class StorageKey:
    """Key for storage operations"""

    name: str
    scope: StorageScope
    scope_id: Optional[int] = None
    namespace: Optional[str] = None

    def __hash__(self):
        # Create a hash based on all attributes
        return hash((self.name, self.scope, self.scope_id, self.namespace))

    def __eq__(self, other):
        if not isinstance(other, StorageKey):
            return False
        return (
            self.name == other.name
            and self.scope == other.scope
            and self.scope_id == other.scope_id
            and self.namespace == other.namespace
        )

    def __str__(self) -> str:
        parts = [self.scope.value]
        if self.scope_id is not None:
            parts.append(str(self.scope_id))
        if self.namespace:
            parts.append(self.namespace)
        parts.append(self.name)
        return ":".join(parts)


@dataclass
class StorageValue(Generic[T]):
    """Value for storage operations"""

    value: T
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = None
    version: Optional[int] = None  # For optimistic locking


@dataclass
class StorageEvent:
    """Event for storage operations"""

    type: StorageEventType
    key: StorageKey
    value: Optional[StorageValue] = None
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class StorageInterface(ABC, Generic[T]):
    @abstractmethod
    async def get(self, key: StorageKey) -> StorageValue[T]:
        pass

    @abstractmethod
    async def set(self, key: StorageKey, value: StorageValue[T]) -> None:
        pass

    @abstractmethod
    async def delete(self, key: StorageKey) -> None:
        pass

    @abstractmethod
    async def list(
        self, scope: StorageScope, scope_id: Optional[int] = None
    ) -> List[StorageKey]:
        pass

    @abstractmethod
    async def watch(
        self, pattern: str
    ) -> AsyncIterator[Tuple[StorageKey, StorageValue]]:
        """Watch for changes to keys matching pattern"""
        pass

    @abstractmethod
    async def subscribe(self, pattern: str) -> Any:
        """Subscribe to storage events matching pattern"""
        pass

    @abstractmethod
    async def unsubscribe(self, pattern: str, subscription: Any) -> None:
        """Unsubscribe from storage events"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage service"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up expired values"""
        pass
