from typing import Optional, List
from src.database.models.settings import Setting, SettingScope, SettingCategory
from .base import BaseRepository
from src.database.manager import db


class SettingRepository(BaseRepository[Setting]):
    def __init__(self):
        super().__init__(Setting)

    async def set_setting(
        self,
        key: str,
        value: any,
        scope: str = "global",
        scope_id: Optional[int] = None,
        category: str = "general",
    ) -> Setting:
        """Set or update a setting"""
        with db.get_session() as session:
            setting = (
                session.query(Setting)
                .filter_by(
                    key=key,
                    scope=SettingScope(scope),
                    scope_id=scope_id,
                    category=SettingCategory(category),
                )
                .first()
            )

            if setting:
                setting.value = value
            else:
                setting = Setting(
                    key=key,
                    value=value,
                    scope=SettingScope(scope),
                    scope_id=scope_id,
                    category=SettingCategory(category),
                )
                session.add(setting)

            session.commit()
            return setting

    async def get_setting(
        self,
        key: str,
        scope: str = "global",
        scope_id: Optional[int] = None,
        category: str = "general",
    ) -> Optional[Setting]:
        """Get a setting value"""
        with db.get_session() as session:
            return (
                session.query(Setting)
                .filter_by(
                    key=key,
                    scope=SettingScope(scope),
                    scope_id=scope_id,
                    category=SettingCategory(category),
                )
                .first()
            )

    async def get_settings(
        self, scope: str = "global", scope_id: Optional[int] = None
    ) -> List[Setting]:
        """Get all settings for a scope"""
        with db.get_session() as session:
            return (
                session.query(Setting)
                .filter_by(scope=SettingScope(scope), scope_id=scope_id)
                .all()
            )
