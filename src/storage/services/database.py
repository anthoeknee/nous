from typing import Any, Dict, List, Optional, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete
from ..interfaces import DatabaseInterface
from ..events import EventEmitter, EventType, StorageEvent
from src.utils.logging import logger

T = TypeVar("T")


class PostgresDatabaseService(DatabaseInterface[T]):
    """PostgreSQL database implementation using SQLAlchemy."""

    def __init__(
        self, url: str, model: Any, events: Optional[EventEmitter] = None, **kwargs
    ):
        self.engine = create_async_engine(url, **kwargs)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.model = model
        self.events = events or EventEmitter()
        logger.info(
            f"Initialized PostgreSQL database service for model: {model.__name__}"
        )

    async def get(self, key: str) -> Optional[T]:
        """Retrieve a record by key."""
        try:
            async with self.async_session() as session:
                result = await session.execute(select(self.model).filter_by(key=key))
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database get error for key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Create or update a record."""
        try:
            async with self.async_session() as session:
                async with session.begin():
                    instance = await self.get(key)
                    if instance:
                        for k, v in value.__dict__.items():
                            if not k.startswith("_"):
                                setattr(instance, k, v)
                        event_type = EventType.UPDATE
                    else:
                        instance = self.model(key=key, **value.__dict__)
                        session.add(instance)
                        event_type = EventType.CREATE

                    await session.commit()

                    await self.events.emit(
                        StorageEvent(type=event_type, key=key, value=value)
                    )
                    return True
        except Exception as e:
            logger.error(f"Database set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a record by key."""
        try:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(
                        delete(self.model).filter_by(key=key)
                    )
                    if result.rowcount:
                        await self.events.emit(
                            StorageEvent(type=EventType.DELETE, key=key)
                        )
                    return bool(result.rowcount)
        except Exception as e:
            logger.error(f"Database delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a record exists."""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(self.model.key).filter_by(key=key)
                )
                return result.scalar() is not None
        except Exception as e:
            logger.error(f"Database exists error for key {key}: {str(e)}")
            return False

    async def query(self, query: str, params: Optional[Dict] = None) -> List[T]:
        """Execute a raw query."""
        try:
            async with self.async_session() as session:
                result = await session.execute(query, params or {})
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            return []

    async def batch_insert(self, items: List[T]) -> bool:
        """Insert multiple records."""
        try:
            async with self.async_session() as session:
                async with session.begin():
                    session.add_all(items)
                    await session.commit()
                    return True
        except Exception as e:
            logger.error(f"Database batch insert error: {str(e)}")
            return False

    async def update_where(self, criteria: Dict, values: Dict) -> int:
        """Update records matching criteria."""
        try:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(
                        update(self.model).filter_by(**criteria).values(**values)
                    )
                    await session.commit()
                    return result.rowcount
        except Exception as e:
            logger.error(f"Database update_where error: {str(e)}")
            return 0

    async def close(self) -> None:
        """Close database connection."""
        await self.engine.dispose()
        logger.info("Closed database connection")
