from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.storage.interfaces import StorageKey, StorageScope, StorageValue
from src.storage.manager import storage


class ShortTermMemory:
    def __init__(self, capacity: int = 25, expiry_minutes: int = 45):
        self.capacity = capacity
        self.expiry_minutes = expiry_minutes
        self.namespace = "llm_memory"

    def _make_key(self, channel_id: str) -> StorageKey:
        return StorageKey(
            name=f"chat_history_{channel_id}",
            scope=StorageScope.CHANNEL,
            scope_id=int(channel_id),
            namespace=self.namespace,
        )

    async def add_message(self, channel_id: str, message: dict) -> None:
        """Add a message to the conversation history"""
        key = self._make_key(channel_id)

        try:
            # Get existing history
            history = await self._get_history(channel_id)
        except KeyError:
            history = []

        # Add new message with timestamp
        history.append({"timestamp": datetime.now().isoformat(), "message": message})

        # Keep only the most recent messages
        history = history[-self.capacity :]

        # Store updated history
        await storage.get_storage().set(
            key,
            StorageValue(
                value=history,
                expires_at=(
                    datetime.now() + timedelta(minutes=self.expiry_minutes)
                ).timestamp(),
            ),
        )

    async def get_context(self, channel_id: str) -> List[dict]:
        """Get conversation history for context"""
        try:
            history = await self._get_history(channel_id)

            # Filter out expired messages
            cutoff = datetime.now() - timedelta(minutes=self.expiry_minutes)
            valid_history = [
                item["message"]
                for item in history
                if datetime.fromisoformat(item["timestamp"]) > cutoff
            ]

            return valid_history
        except KeyError:
            return []

    async def _get_history(self, channel_id: str) -> List[dict]:
        """Get raw history with timestamps"""
        key = self._make_key(channel_id)
        value = await storage.get_storage().get(key)
        return value.value
