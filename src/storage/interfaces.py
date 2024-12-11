from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar("T")


class StorageInterface(Generic[T], ABC):
    """Base interface for all storage implementations."""

    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Retrieve a value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Store a value with optional TTL in seconds."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value by key."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        pass


class CacheInterface(StorageInterface[T], ABC):
    """Extended interface for cache operations."""

    @abstractmethod
    async def get_pattern(self, pattern: str) -> Dict[str, T]:
        """Get all keys matching pattern."""
        pass

    @abstractmethod
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel."""
        pass

    @abstractmethod
    async def subscribe(self, channel: str, callback: callable) -> None:
        """Subscribe to channel with callback."""
        pass


class DatabaseInterface(StorageInterface[T], ABC):
    """Extended interface for database operations."""

    @abstractmethod
    async def query(self, query: str, params: Optional[Dict] = None) -> List[T]:
        """Execute raw query."""
        pass

    @abstractmethod
    async def batch_insert(self, items: List[T]) -> bool:
        """Insert multiple items."""
        pass

    @abstractmethod
    async def update_where(self, criteria: Dict, values: Dict) -> int:
        """Update items matching criteria."""
        pass
