from collections import defaultdict
from typing import Optional, List, Dict, AsyncIterator, Tuple
from sqlalchemy import (
    Index,
    create_engine,
    Column,
    String,
    JSON,
    DateTime,
    Integer,
    and_,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import asyncio
from ..interfaces import StorageValue, StorageKey, StorageScope
from .base import BaseStorageService

Base = declarative_base()


class StorageEntry(Base):
    __tablename__ = "storage_entries"

    id = Column(Integer, primary_key=True)
    key = Column(String(255), nullable=False, index=True)
    namespace = Column(String(100), nullable=False)
    scope = Column(String(50), nullable=False)
    scope_id = Column(String(50), nullable=True)
    value = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Composite index for faster lookups
        Index("idx_scope_lookup", "scope", "scope_id", "namespace"),
    )


class DatabaseStorageService(BaseStorageService):
    def __init__(self, database_url: str, prefix: str = "bot"):
        super().__init__(prefix)
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

        # Change notification system
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._notification_task = None

    async def initialize(self):
        """Initialize async components"""
        self._notification_task = asyncio.create_task(self._process_notifications())
        return self

    async def get(self, key: StorageKey) -> StorageValue:
        with self.SessionLocal() as session:
            entry = (
                session.query(StorageEntry).filter_by(key=self._make_key(key)).first()
            )

            if not entry:
                raise KeyError(f"Key {key} not found")

            if entry.expires_at and entry.expires_at < datetime.utcnow():
                session.delete(entry)
                session.commit()
                raise KeyError(f"Key {key} has expired")

            return StorageValue(
                value=entry.value,
                expires_at=entry.expires_at.timestamp() if entry.expires_at else None,
                metadata={"version": entry.version},
                version=entry.version,
            )

    async def set(self, key: StorageKey, value: StorageValue) -> None:
        storage_key = self._make_key(key)

        with self.SessionLocal() as session:
            entry = session.query(StorageEntry).filter_by(key=storage_key).first()

            if entry:
                entry.value = value.value
                entry.version += 1
                if value.expires_at:
                    entry.expires_at = datetime.fromtimestamp(value.expires_at)
            else:
                entry = StorageEntry(
                    key=storage_key,
                    namespace=key.namespace or "default",
                    scope=key.scope.value,
                    scope_id=str(key.scope_id),
                    value=value.value,
                    expires_at=datetime.fromtimestamp(value.expires_at)
                    if value.expires_at
                    else None,
                )
                session.add(entry)

            session.commit()

            # Notify subscribers
            await self._notify_change(key, value)

    async def delete(self, key: StorageKey) -> None:
        with self.SessionLocal() as session:
            session.query(StorageEntry).filter_by(key=self._make_key(key)).delete()
            session.commit()

    async def list(
        self, scope: StorageScope, scope_id: Optional[int] = None
    ) -> List[StorageKey]:
        with self.SessionLocal() as session:
            query = session.query(StorageEntry).filter(
                and_(
                    StorageEntry.scope == scope.value,
                    StorageEntry.scope_id == str(scope_id) if scope_id else None,
                )
            )

            return [self._parse_key(entry.key) for entry in query.all()]

    async def watch(
        self, pattern: str
    ) -> AsyncIterator[Tuple[StorageKey, StorageValue]]:
        queue = asyncio.Queue()
        watch_pattern = f"{self.prefix}:{pattern}"
        self._subscribers[watch_pattern].append(queue)

        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers[watch_pattern].remove(queue)

    async def _notify_change(self, key: StorageKey, value: StorageValue) -> None:
        """Notify subscribers of changes"""
        storage_key = self._make_key(key)
        for pattern, queues in self._subscribers.items():
            if self._key_matches_pattern(storage_key, pattern):
                for queue in queues:
                    await queue.put((key, value))

    def _key_matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if a key matches a glob-style pattern"""
        import fnmatch

        return fnmatch.fnmatch(key, pattern)

    async def _process_notifications(self):
        """Process database notifications in the background"""
        while True:
            try:
                # Check for notifications every second
                await asyncio.sleep(1)
                # Process any pending notifications from the database
                for pattern, queues in self._subscribers.items():
                    for queue in queues:
                        if not queue.full():
                            # Check for changes and notify subscribers
                            pass
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing notifications: {e}")
                await asyncio.sleep(5)  # Back off on error
