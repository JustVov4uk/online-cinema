from datetime import datetime
from enum import StrEnum

from sqlalchemy import Enum, Integer, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models import Base


class UserGroupEnum(StrEnum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class UserGroup(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    name: Mapped[UserGroupEnum] = mapped_column(
        Enum(UserGroupEnum, name="user_group_name"),
        unique=True,
        nullable=False,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column("hashed_password", String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    group_id: Mapped[int] = mapped_column(ForeignKey("user_groups.id"), nullable=False)