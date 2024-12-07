from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Deque, Tuple


class ShortTermMemory:
    def __init__(self, capacity: int = 25, expiry_minutes: int = 45):
        self.capacity = capacity
        self.expiry_minutes = expiry_minutes
        # Dict of channel_id -> deque of (timestamp, message) tuples
        self.memories: Dict[str, Deque[Tuple[datetime, dict]]] = {}

    def add_message(self, channel_id: str, message: dict) -> None:
        """Enhanced to handle multimodal messages"""
        if channel_id not in self.memories:
            self.memories[channel_id] = deque(maxlen=self.capacity)

        # Special handling for multimodal messages
        if isinstance(message.get("content"), list):
            # Simplify multimodal content for memory storage
            simplified_content = " ".join(
                [
                    item["text"] if item["type"] == "text" else "[Image]"
                    for item in message["content"]
                ]
            )
            message = {**message, "content": simplified_content}

        self.memories[channel_id].append((datetime.now(), message))
        self._cleanup_expired(channel_id)

    def get_context(self, channel_id: str) -> list[dict]:
        """Get all valid messages for a channel."""
        if channel_id not in self.memories:
            return []

        self._cleanup_expired(channel_id)
        return [msg for _, msg in self.memories[channel_id]]

    def _cleanup_expired(self, channel_id: str) -> None:
        """Remove expired messages from memory."""
        if channel_id not in self.memories:
            return

        expiry_time = datetime.now() - timedelta(minutes=self.expiry_minutes)
        while self.memories[channel_id]:
            timestamp, _ = self.memories[channel_id][0]
            if timestamp < expiry_time:
                self.memories[channel_id].popleft()
            else:
                break
