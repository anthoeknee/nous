from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from src.storage.models.base import BaseModel
from src.storage.interfaces import StorageKey, StorageScope, StorageValue
from src.storage.manager import storage

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], namespace: str = "models"):
        self.model = model
        self.namespace = namespace

    def _make_storage_key(self, id: Optional[int] = None, **kwargs) -> StorageKey:
        return StorageKey(
            name=f"{self.model.__name__.lower()}{f'_{id}' if id else ''}",
            scope=StorageScope.GLOBAL,
            namespace=self.namespace,
            **kwargs,
        )

    def _model_to_dict(self, instance: T) -> Dict[str, Any]:
        return {
            column.name: getattr(instance, column.name)
            for column in instance.__table__.columns
        }

    def _dict_to_model(self, data: Dict[str, Any]) -> T:
        return self.model(**data)

    async def create(self, **kwargs) -> T:
        try:
            instance = self.model(**kwargs)
            storage_key = self._make_storage_key()
            storage_value = StorageValue(value=self._model_to_dict(instance))
            await storage.get_storage().set(storage_key, storage_value)
            return instance
        except Exception as e:
            raise ValueError(f"Failed to create {self.model.__name__}: {str(e)}")

    async def get(self, id: int) -> Optional[T]:
        try:
            storage_key = self._make_storage_key(id)
            storage_value = await storage.get_storage().get(storage_key)
            return self._dict_to_model(storage_value.value)
        except KeyError:
            return None
        except Exception as e:
            raise ValueError(f"Failed to get {self.model.__name__}: {str(e)}")

    async def get_all(self) -> List[T]:
        keys = await storage.list(StorageScope.GLOBAL)
        instances = []
        for key in keys:
            if (
                key.namespace == self.namespace
                and self.model.__name__.lower() in key.name
            ):
                try:
                    value = await storage.get(key)
                    instances.append(self._dict_to_model(value.value))
                except KeyError:
                    continue
        return instances

    async def update(self, id: int, **kwargs) -> Optional[T]:
        instance = await self.get(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            storage_key = self._make_storage_key(id)
            storage_value = StorageValue(value=self._model_to_dict(instance))
            await storage.set(storage_key, storage_value)
        return instance

    async def delete(self, id: int) -> bool:
        storage_key = self._make_storage_key(id)
        try:
            await storage.delete(storage_key)
            return True
        except KeyError:
            return False

    async def exists(self, id: int) -> bool:
        try:
            storage_key = self._make_storage_key(id)
            await storage.get(storage_key)
            return True
        except KeyError:
            return False

    async def count(self) -> int:
        return len(await self.get_all())

    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        instances = []
        for item in items:
            instance = await self.create(**item)
            instances.append(instance)
        return instances

    async def bulk_delete(self, ids: List[int]) -> int:
        deleted_count = 0
        for id in ids:
            if await self.delete(id):
                deleted_count += 1
        return deleted_count
