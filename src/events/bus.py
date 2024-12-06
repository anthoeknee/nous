from typing import Dict, List, Type, Set, TypeVar, Callable, Optional
from collections import defaultdict
import asyncio
from functools import wraps
from src.utils.logging import logger
from src.events.types import EventHandler, EventPriority
from src.events.definitions import Event

T = TypeVar("T", bound=Event)


class EventBus:
    def __init__(self):
        # Simplified handler storage
        self._handlers: Dict[Type[Event], List[tuple[EventPriority, EventHandler]]] = (
            defaultdict(list)
        )
        self._event_history: List[Event] = []
        self._max_history = 100

    async def emit(self, event: Event) -> None:
        """Publish an event (alias for publish)"""
        event_type = type(event)

        # Store event in history
        self._event_history = self._event_history[-self._max_history :] + [event]

        # Sort handlers by priority and execute
        handlers = sorted(
            self._handlers[event_type], key=lambda x: x[0].value, reverse=True
        )
        for _, handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"Handler error: {handler.__name__} - {str(e)}", exc_info=True
                )

    # Alias for emit
    publish = emit

    def on(
        self,
        event_type: Type[T],
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False,
    ) -> Callable:
        """
        Decorator to subscribe to events

        Usage:
            @event_bus.on(MessageEvent)
            async def handle_message(event):
                print(f"Got message: {event.content}")

            @event_bus.on(CommandEvent, priority=EventPriority.HIGH)
            async def handle_command(event):
                print(f"Command executed: {event.command_name}")
        """

        def decorator(handler: EventHandler) -> EventHandler:
            @wraps(handler)
            async def wrapper(event: T) -> None:
                await handler(event)
                if once:
                    self.remove(event_type, wrapper)

            self._handlers[event_type].append((priority, wrapper))
            return wrapper

        return decorator

    def remove(self, event_type: Type[Event], handler: EventHandler) -> None:
        """Remove a handler for an event type"""
        self._handlers[event_type] = [
            (p, h) for p, h in self._handlers[event_type] if h != handler
        ]

    async def wait_for(
        self,
        event_type: Type[T],
        timeout: Optional[float] = None,
        check: Callable[[T], bool] = None,
    ) -> T:
        """
        Wait for a specific event to occur

        Usage:
            # Wait for a message from user 123
            event = await event_bus.wait_for(
                MessageEvent,
                timeout=5.0,
                check=lambda e: e.author_id == 123
            )
        """
        future = asyncio.Future()

        @self.on(event_type, once=True)
        async def waiter(event: T):
            if check is None or check(event):
                future.set_result(event)

        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Timeout waiting for {event_type.__name__}")

    def clear(self, event_type: Optional[Type[Event]] = None) -> None:
        """Clear handlers for a specific event type or all handlers"""
        if event_type is None:
            self._handlers.clear()
        else:
            self._handlers[event_type].clear()


# Global event bus instance
events = EventBus()
