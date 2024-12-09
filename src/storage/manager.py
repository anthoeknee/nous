from typing import Optional, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from .interfaces import StorageInterface, StorageBackend
from .services.memory import MemoryStorageService
from .services.redis import RedisStorageService
from .services.database import DatabaseStorageService
from .services.hybrid import HybridStorageService
from src.config import Settings
import asyncio
import pymysql

# Create Base model instance
Base = declarative_base()


class StorageManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.storages: Dict[StorageBackend, StorageInterface] = {}

        # Initialize configured backends
        if settings.use_memory_storage:
            memory_storage = MemoryStorageService()
            self.storages[StorageBackend.MEMORY] = memory_storage

        if settings.redis_url:
            redis_storage = RedisStorageService(settings.redis_url)
            self.storages[StorageBackend.REDIS] = redis_storage

        if settings.database_url:
            db_storage = DatabaseStorageService(settings.database_url)
            self.storages[StorageBackend.DATABASE] = db_storage

        # Initialize hybrid storage if multiple backends are available
        if len(self.storages) > 1:
            hybrid_storage = HybridStorageService(
                memory_storage=self.storages.get(StorageBackend.MEMORY),
                redis_storage=self.storages.get(StorageBackend.REDIS),
                database_storage=self.storages.get(StorageBackend.DATABASE),
            )
            self.storages[StorageBackend.HYBRID] = hybrid_storage

        # Set default backend - ensure it exists in storages
        self.default_backend = StorageBackend(settings.default_storage_backend)
        if self.default_backend not in self.storages:
            # Fallback to MEMORY if default isn't available
            self.default_backend = StorageBackend.MEMORY
            if StorageBackend.MEMORY not in self.storages:
                self.storages[StorageBackend.MEMORY] = MemoryStorageService()

    def get_storage(self, backend: Optional[StorageBackend] = None) -> StorageInterface:
        """Get storage implementation for specified backend"""
        backend = backend or self.default_backend
        if backend not in self.storages:
            raise KeyError(f"Storage backend {backend} not configured")
        return self.storages[backend]

    async def initialize(self):
        """Initialize async components of storage services"""
        init_tasks = []

        if StorageBackend.DATABASE in self.storages:
            init_tasks.append(self.storages[StorageBackend.DATABASE].initialize())

        if StorageBackend.HYBRID in self.storages:
            init_tasks.append(self.storages[StorageBackend.HYBRID].initialize())

        if init_tasks:
            await asyncio.gather(*init_tasks)


# Global storage instance
storage = StorageManager(Settings())
