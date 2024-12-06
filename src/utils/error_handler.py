from typing import Type, Callable, Any, Optional
from functools import wraps
from discord.ext import commands
from src.events import events, ErrorEvent
from src.utils.logging import logger


class BotError(Exception):
    """Base exception for bot-related errors"""

    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context or {}
        self.user_message: Optional[str] = None  # Message to show to users


class DatabaseError(BotError):
    """Database-related errors"""

    def __init__(self, message: str, context: dict = None):
        super().__init__(message, context)
        self.user_message = "A database error occurred. Please try again later."


class CommandError(BotError):
    """Command execution errors"""

    def __init__(self, message: str, context: dict = None):
        super().__init__(message, context)
        self.user_message = message  # For command errors, show the actual message


async def handle_command_error(ctx: commands.Context, error: Exception) -> None:
    """Global error handler for command errors"""
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"Please wait {error.retry_after:.1f}s before using this command again."
        )
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command!")
        return

    if isinstance(error, BotError):
        # Log the technical error
        logger.error(f"Bot error in {ctx.command}: {str(error)}", exc_info=True)
        # Send user-friendly message
        await ctx.send(
            error.user_message or "An error occurred. Please try again later."
        )
        return

    # For unexpected errors
    logger.error(f"Unexpected error in {ctx.command}: {str(error)}", exc_info=True)
    await ctx.send("An unexpected error occurred. Please try again later.")


def handle_errors(*error_types: Type[Exception], send_message: bool = True):
    """Decorator for handling errors in any async function"""
    if not error_types:
        error_types = (Exception,)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            try:
                return await func(*args, **kwargs)
            except error_types as e:
                # Get context if available (for commands)
                ctx = next(
                    (arg for arg in args if isinstance(arg, commands.Context)), None
                )

                # Create error context
                context = {
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                }

                # Emit error event
                await events.emit(ErrorEvent(error=e, context=context))

                # Handle the error
                if ctx and send_message:
                    await handle_command_error(ctx, e)
                else:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                raise

        return wrapper

    return decorator
