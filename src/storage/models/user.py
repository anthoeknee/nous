from sqlalchemy import Column, String, BigInteger, Boolean
from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    discord_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    is_admin = Column(Boolean, default=False)
