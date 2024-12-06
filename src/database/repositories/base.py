from typing import Generic, TypeVar, Type, Optional, List
from src.database.models.base import BaseModel
from src.database.manager import db

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    async def create(self, **kwargs) -> T:
        with db.get_session() as session:
            try:
                instance = self.model(**kwargs)
                session.add(instance)
                session.commit()
                session.refresh(instance)
                await db.emit_db_event("create", self.model.__name__, kwargs, True)
                return instance
            except Exception as e:
                await db.emit_db_event("create", self.model.__name__, kwargs, False, e)
                raise

    async def get(self, id: int) -> Optional[T]:
        with db.get_session() as session:
            return session.query(self.model).filter_by(id=id).first()

    async def get_all(self) -> List[T]:
        with db.get_session() as session:
            return session.query(self.model).all()

    async def update(self, id: int, **kwargs) -> Optional[T]:
        with db.get_session() as session:
            try:
                instance = session.query(self.model).filter_by(id=id).first()
                if instance:
                    for key, value in kwargs.items():
                        setattr(instance, key, value)
                    session.commit()
                    session.refresh(instance)
                    await db.emit_db_event(
                        "update", self.model.__name__, {"id": id, **kwargs}, True
                    )
                return instance
            except Exception as e:
                await db.emit_db_event(
                    "update", self.model.__name__, {"id": id, **kwargs}, False, e
                )
                raise

    async def delete(self, id: int) -> bool:
        with db.get_session() as session:
            try:
                instance = session.query(self.model).filter_by(id=id).first()
                if instance:
                    session.delete(instance)
                    session.commit()
                    await db.emit_db_event(
                        "delete", self.model.__name__, {"id": id}, True
                    )
                    return True
                return False
            except Exception as e:
                await db.emit_db_event(
                    "delete", self.model.__name__, {"id": id}, False, e
                )
                raise
