from sqlalchemy import Column, String, JSON, Enum as SQLEnum, BigInteger
from enum import Enum
from .base import BaseModel


class SettingScope(Enum):
    GLOBAL = "global"
    GUILD = "guild"
    CHANNEL = "channel"
    USER = "user"
    ROLE = "role"


class SettingCategory(Enum):
    OWNER = "owner"
    GENERAL = "general"


class Setting(BaseModel):
    __tablename__ = "settings"

    key = Column(String(100), nullable=False)
    value = Column(JSON, nullable=False)
    scope = Column(SQLEnum(SettingScope), nullable=False)
    category = Column(SQLEnum(SettingCategory), nullable=False)
    scope_id = Column(
        BigInteger, nullable=True
    )  # ID of guild/channel/user/role if not global
    description = Column(String(500), nullable=True)
