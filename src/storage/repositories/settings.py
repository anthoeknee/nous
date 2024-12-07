from typing import Optional, List
from src.storage.models.settings import Setting, SettingScope, SettingCategory
from .base import BaseRepository
from src.storage.interfaces import StorageKey, StorageScope
from src.storage.manager import storage


class SettingRepository(BaseRepository[Setting]):
    def __init__(self):
        super().__init__(Setting, namespace="settings")

    async def set_setting(
        self,
        key: str,
        value: any,
        scope: str = "global",
        scope_id: Optional[int] = None,
        category: str = "general",
    ) -> Setting:
        setting = Setting(
            key=key,
            value=value,
            scope=SettingScope(scope),
            scope_id=scope_id,
            category=SettingCategory(category),
        )
        await self.create(**self._model_to_dict(setting))
        return setting

    async def get_setting(
        self,
        key: str,
        scope: str = "global",
        scope_id: Optional[int] = None,
        category: str = "general",
    ) -> Optional[Setting]:
        storage_key = StorageKey(
            name=key,
            scope=StorageScope(scope),
            scope_id=scope_id,
            namespace=self.namespace,
            category=category,
        )
        try:
            value = await storage.get_storage().get(storage_key)
            return self._dict_to_model(value.value)
        except KeyError:
            return None

    async def get_settings(
        self, scope: str = "global", scope_id: Optional[int] = None
    ) -> List[Setting]:
        """Get all settings for a scope"""
        storage = storage.get_storage()
        keys = await storage.list(StorageScope(scope), scope_id)
        settings = []

        for key in keys:
            if key.namespace == self.namespace:
                try:
                    value = await storage.get(key)
                    settings.append(self._dict_to_model(value.value))
                except KeyError:
                    continue

        return settings
