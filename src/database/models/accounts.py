from enum import StrEnum

from sqlalchemy import Enum
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
