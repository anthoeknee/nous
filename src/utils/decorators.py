from functools import wraps
from typing import Callable, Any, List, Union
from discord.ext import commands


def with_typing():
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(ctx: commands.Context, *args: Any, **kwargs: Any):
            async with ctx.typing():
                return await func(ctx, *args, **kwargs)

        return wrapper

    return decorator


def require_roles(roles: List[Union[int, str]]):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(ctx: commands.Context, *args: Any, **kwargs: Any):
            if not any(
                role.name in roles or role.id in roles for role in ctx.author.roles
            ):
                await ctx.send("You don't have permission to use this command!")
                return
            return await func(ctx, *args, **kwargs)

        return wrapper

    return decorator


def cooldown(seconds: int):
    def decorator(func: Callable) -> Callable:
        last_used = {}

        @wraps(func)
        async def wrapper(ctx: commands.Context, *args: Any, **kwargs: Any):
            user_id = ctx.author.id
            current_time = ctx.message.created_at.timestamp()

            if user_id in last_used and current_time - last_used[user_id] < seconds:
                remaining = int(seconds - (current_time - last_used[user_id]))
                await ctx.send(
                    f"Please wait {remaining} seconds before using this command again."
                )
                return

            last_used[user_id] = current_time
            return await func(ctx, *args, **kwargs)

        return wrapper

    return decorator


def dm_only():
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(ctx: commands.Context, *args: Any, **kwargs: Any):
            if ctx.guild is not None:
                await ctx.send("This command can only be used in DMs!")
                return
            return await func(ctx, *args, **kwargs)

        return wrapper

    return decorator
