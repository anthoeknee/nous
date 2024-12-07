from typing import Optional
from discord.ext import commands
from src.storage.repositories.permissions import PermissionRepository


async def has_permission(
    ctx: commands.Context, permission: str, scope_id: Optional[int] = None
) -> bool:
    """
    Check if a user has a specific permission
    Checks in order: User -> Role -> Channel -> Guild -> Global
    Higher priority overrides lower priority
    """
    repo = PermissionRepository()

    # Check user-specific permission
    user_perm = await repo.get_permission(
        name=permission, scope="user", scope_id=ctx.author.id
    )
    if user_perm:
        return user_perm.allowed

    # Check role permissions
    if ctx.guild:
        for role in ctx.author.roles:
            role_perm = await repo.get_permission(
                name=permission, scope="role", scope_id=role.id
            )
            if role_perm:
                return role_perm.allowed

    # Check channel permission
    channel_perm = await repo.get_permission(
        name=permission, scope="channel", scope_id=ctx.channel.id
    )
    if channel_perm:
        return channel_perm.allowed

    # Check guild permission
    if ctx.guild:
        guild_perm = await repo.get_permission(
            name=permission, scope="guild", scope_id=ctx.guild.id
        )
        if guild_perm:
            return guild_perm.allowed

    # Check global permission
    global_perm = await repo.get_permission(name=permission, scope="global")
    if global_perm:
        return global_perm.allowed

    return False  # Default to denied if no permission found
