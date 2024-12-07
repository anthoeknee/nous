from typing import Optional
from src.storage.models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User, namespace="users")

    async def get_by_discord_id(self, discord_id: int) -> Optional[User]:
        all_users = await self.get_all()
        return next((user for user in all_users if user.discord_id == discord_id), None)
