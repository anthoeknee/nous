from typing import Optional
from src.database.models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_discord_id(self, discord_id: int) -> Optional[User]:
        with self.db.get_session() as session:
            return session.query(User).filter_by(discord_id=discord_id).first()
