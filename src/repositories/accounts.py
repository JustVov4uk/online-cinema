from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.accounts import ActivationToken, User, UserGroup, UserGroupEnum


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()

async def get_user_group_by_name(
        session: AsyncSession,
        name: UserGroupEnum,
) -> UserGroup | None:
    statement = select(UserGroup).where(UserGroup.name == name)
    result = await session.execute(statement)
    return result.scalar_one_or_none()

async def create_user(
        session: AsyncSession,
        email: str,
        hashed_password: str,
        group_id: int,
) -> User:
    user = User(
        email=email,
        hashed_password=hashed_password,
        group_id=group_id,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user

async def create_activation_token(
        session: AsyncSession,
        user_id: int,
        token: str,
        expires_at: datetime,
) -> ActivationToken:
    activation_token = ActivationToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    session.add(activation_token)
    await session.flush()
    return activation_token