from typing import Optional, List, Dict
from src.storage.models.permissions import Permission, PermissionScope
from .base import BaseRepository
from src.storage.interfaces import StorageScope
from src.storage.manager import storage


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self):
        super().__init__(Permission, namespace="permissions")

    async def set_permission(
        self,
        name: str,
        allowed: bool,
        scope: str = "global",
        scope_id: Optional[int] = None,
        priority: int = 0,
    ) -> Permission:
        permission = Permission(
            name=name,
            allowed=allowed,
            scope=PermissionScope(scope),
            scope_id=scope_id,
            priority=priority,
        )
        await self.create(**self._model_to_dict(permission))
        return permission

    async def get_effective_permissions(
        self,
        user_id: int,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        role_ids: Optional[List[int]] = None,
    ) -> Dict[str, bool]:
        permissions = {}

        # Get permissions in order of priority
        scopes = [
            (StorageScope.GLOBAL, None),
            (StorageScope.GUILD, guild_id),
            (StorageScope.CHANNEL, channel_id),
            *[(StorageScope.ROLE, role_id) for role_id in (role_ids or [])],
            (StorageScope.USER, user_id),
        ]

        for scope, scope_id in scopes:
            if scope_id is None and scope != StorageScope.GLOBAL:
                continue

            perms = await storage.list(scope, scope_id)
            for perm_key in perms:
                if perm_key.namespace != self.namespace:
                    continue

                value = await storage.get(perm_key)
                perm_data = value.value
                permissions[perm_data["name"]] = perm_data["allowed"]

        return permissions
