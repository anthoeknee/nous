from typing import TypeVar, Generic, Optional, List, Type, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from ..models.base import BaseModel
from src.utils.logging import logger

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        try:
            result = await self.session.execute(select(self.model).filter_by(id=id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Repository get error for id {id}: {str(e)}")
            return None

    async def get_by_key(self, key: str) -> Optional[T]:
        """Get entity by key."""
        try:
            result = await self.session.execute(select(self.model).filter_by(key=key))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Repository get_by_key error for key {key}: {str(e)}")
            return None

    async def list(self, **filters) -> List[T]:
        """Get all entities matching filters."""
        try:
            result = await self.session.execute(select(self.model).filter_by(**filters))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Repository list error: {str(e)}")
            return []

    async def create(self, **data) -> Optional[T]:
        """Create new entity."""
        try:
            instance = self.model(**data)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"Repository create error: {str(e)}")
            await self.session.rollback()
            return None

    async def update(self, id: int, **data) -> Optional[T]:
        """Update entity by ID."""
        try:
            await self.session.execute(
                update(self.model).filter_by(id=id).values(**data)
            )
            await self.session.commit()
            return await self.get(id)
        except Exception as e:
            logger.error(f"Repository update error for id {id}: {str(e)}")
            await self.session.rollback()
            return None

    async def delete(self, id: int) -> bool:
        """Delete entity by ID."""
        try:
            result = await self.session.execute(delete(self.model).filter_by(id=id))
            await self.session.commit()
            return bool(result.rowcount)
        except Exception as e:
            logger.error(f"Repository delete error for id {id}: {str(e)}")
            await self.session.rollback()
            return False

    async def upsert(self, key: str, **data) -> Optional[T]:
        """Create or update entity by key."""
        try:
            instance = await self.get_by_key(key)
            if instance:
                for k, v in data.items():
                    setattr(instance, k, v)
            else:
                instance = self.model(key=key, **data)
                self.session.add(instance)

            await self.session.commit()
            await self.session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"Repository upsert error for key {key}: {str(e)}")
            await self.session.rollback()
            return None
