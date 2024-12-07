from sqlalchemy import (
    Column,
    String,
    Boolean,
    BigInteger,
    Integer,
    Enum as SQLEnum,
)
from enum import Enum
from .base import BaseModel


class PermissionScope(Enum):
    GLOBAL = "global"
    GUILD = "guild"
    CHANNEL = "channel"
    ROLE = "role"
    USER = "user"


class Permission(BaseModel):
    __tablename__ = "permissions"

    name = Column(String(100), nullable=False)
    scope = Column(SQLEnum(PermissionScope), nullable=False)
    scope_id = Column(BigInteger, nullable=True)
    allowed = Column(Boolean, default=False)
    priority = Column(Integer, default=0)  # Higher priority overrides lower
