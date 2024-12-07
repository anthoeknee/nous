from abc import ABC
from ..interfaces import StorageInterface, StorageKey, StorageScope


class BaseStorageService(StorageInterface, ABC):
    """Base class for all storage services with common utilities"""

    def __init__(self, prefix: str = "bot"):
        self.prefix = prefix

    def _make_key(self, key: StorageKey) -> str:
        """Create a standardized storage key string"""
        return (
            f"{self.prefix}:{key.namespace}:{key.scope.value}:{key.scope_id}:{key.name}"
        )

    def _parse_key(self, key_str: str) -> StorageKey:
        """Parse a storage key string back into a StorageKey object"""
        parts = key_str.split(":")
        if len(parts) < 5:
            raise ValueError(f"Invalid key format: {key_str}")

        _, namespace, scope, scope_id, *name_parts = parts
        return StorageKey(
            namespace=namespace,
            scope=StorageScope(scope),
            scope_id=int(scope_id) if scope_id != "None" else None,
            name=":".join(name_parts),
        )
