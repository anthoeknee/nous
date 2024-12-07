from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass

T = TypeVar("T")


class StorageScope(Enum):
    USER = "user"
    CHANNEL = "channel"
    ROLE = "role"
    GUILD = "guild"
    GLOBAL = "global"


class StorageBackend(Enum):
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"
    HYBRID = "hybrid"


@dataclass
class StorageKey:
    name: str
    scope: StorageScope
    scope_id: Optional[int] = None
    namespace: Optional[str] = None
    category: Optional[str] = None


@dataclass
class StorageValue(Generic[T]):
    value: T
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = None
    version: Optional[int] = None  # For optimistic locking


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
