from typing import Optional, List
from src.database.models.permissions import Permission, PermissionScope
from .base import BaseRepository
from src.database.manager import db


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self):
        super().__init__(Permission)

    async def set_permission(
        self,
        name: str,
        allowed: bool,
        scope: str = "global",
        scope_id: Optional[int] = None,
        priority: int = 0,
    ) -> Permission:
        """Set or update a permission"""
        with db.get_session() as session:
            permission = (
                session.query(Permission)
                .filter_by(name=name, scope=PermissionScope(scope), scope_id=scope_id)
                .first()
            )

            if permission:
                permission.allowed = allowed
                permission.priority = priority
            else:
                permission = Permission(
                    name=name,
                    allowed=allowed,
                    scope=PermissionScope(scope),
                    scope_id=scope_id,
                    priority=priority,
                )
                session.add(permission)

            session.commit()
            return permission

    async def get_permission(
        self, name: str, scope: str = "global", scope_id: Optional[int] = None
    ) -> Optional[Permission]:
        """Get a permission"""
        with db.get_session() as session:
            return (
                session.query(Permission)
                .filter_by(name=name, scope=PermissionScope(scope), scope_id=scope_id)
                .first()
            )

    async def get_permissions(
        self, scope: str = "global", scope_id: Optional[int] = None
    ) -> List[Permission]:
        """Get all permissions for a scope"""
        with db.get_session() as session:
            return (
                session.query(Permission)
                .filter_by(scope=PermissionScope(scope), scope_id=scope_id)
                .all()
            )

    async def delete_permission(
        self, name: str, scope: str = "global", scope_id: Optional[int] = None
    ) -> bool:
        """Delete a permission"""
        with db.get_session() as session:
            permission = (
                session.query(Permission)
                .filter_by(name=name, scope=PermissionScope(scope), scope_id=scope_id)
                .first()
            )

            if permission:
                session.delete(permission)
                session.commit()
                return True
            return False

    async def get_all_permissions_for_scope_id(
        self, scope_id: int, scope: str
    ) -> List[Permission]:
        """Get all permissions for a specific scope ID"""
        with db.get_session() as session:
            return (
                session.query(Permission)
                .filter_by(scope=PermissionScope(scope), scope_id=scope_id)
                .order_by(Permission.priority.desc())
                .all()
            )

    async def get_effective_permissions(
        self,
        user_id: int,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        role_ids: Optional[List[int]] = None,
    ) -> dict:
        """
        Get effective permissions for a user considering all scopes
        Returns a dictionary of permission names and their effective allowed status
        """
        with db.get_session() as session:
            # Start with global permissions
            query = session.query(Permission).filter(
                Permission.scope == PermissionScope.GLOBAL
            )

            permissions = {}
            for perm in query.all():
                permissions[perm.name] = {
                    "allowed": perm.allowed,
                    "priority": perm.priority,
                }

            # Add guild permissions if applicable
            if guild_id:
                guild_perms = (
                    session.query(Permission)
                    .filter(
                        Permission.scope == PermissionScope.GUILD,
                        Permission.scope_id == guild_id,
                    )
                    .all()
                )
                for perm in guild_perms:
                    if (
                        perm.name not in permissions
                        or perm.priority > permissions[perm.name]["priority"]
                    ):
                        permissions[perm.name] = {
                            "allowed": perm.allowed,
                            "priority": perm.priority,
                        }

            # Add channel permissions
            if channel_id:
                channel_perms = (
                    session.query(Permission)
                    .filter(
                        Permission.scope == PermissionScope.CHANNEL,
                        Permission.scope_id == channel_id,
                    )
                    .all()
                )
                for perm in channel_perms:
                    if (
                        perm.name not in permissions
                        or perm.priority > permissions[perm.name]["priority"]
                    ):
                        permissions[perm.name] = {
                            "allowed": perm.allowed,
                            "priority": perm.priority,
                        }

            # Add role permissions
            if role_ids:
                role_perms = (
                    session.query(Permission)
                    .filter(
                        Permission.scope == PermissionScope.ROLE,
                        Permission.scope_id.in_(role_ids),
                    )
                    .all()
                )
                for perm in role_perms:
                    if (
                        perm.name not in permissions
                        or perm.priority > permissions[perm.name]["priority"]
                    ):
                        permissions[perm.name] = {
                            "allowed": perm.allowed,
                            "priority": perm.priority,
                        }

            # Add user-specific permissions (highest priority)
            user_perms = (
                session.query(Permission)
                .filter(
                    Permission.scope == PermissionScope.USER,
                    Permission.scope_id == user_id,
                )
                .all()
            )
            for perm in user_perms:
                if (
                    perm.name not in permissions
                    or perm.priority > permissions[perm.name]["priority"]
                ):
                    permissions[perm.name] = {
                        "allowed": perm.allowed,
                        "priority": perm.priority,
                    }

            # Convert to simple dictionary of name: allowed
            return {name: data["allowed"] for name, data in permissions.items()}
