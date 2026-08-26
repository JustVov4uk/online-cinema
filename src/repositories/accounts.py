from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.accounts import (
    ActivationToken,
    PasswordResetToken,
    RefreshToken,
    User,
    UserGroup,
    UserGroupEnum,
    UserProfile,
)


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

async def create_refresh_token_record(
        session: AsyncSession,
        user_id: int,
        token: str,
        expires_at: datetime,
) -> RefreshToken:
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    session.add(refresh_token)
    await session.flush()

    return refresh_token

async def get_activation_token_by_token(
        session: AsyncSession,
        token: str,
) -> ActivationToken | None:
    statement = select(ActivationToken).where(ActivationToken.token == token)
    result = await session.execute(statement)
    return result.scalar_one_or_none()

async def activate_user(
        session: AsyncSession,
        user: User,
) -> User:
    user.is_active = True
    await session.flush()
    await session.refresh(user)
    return user

async def delete_activation_token(
        session: AsyncSession,
        activation_token: ActivationToken,
) -> None:
    await session.delete(activation_token)
    await session.flush()

async def get_refresh_token_by_token(
        session: AsyncSession,
        token: str,
) -> RefreshToken | None:
    statement = select(RefreshToken).where(RefreshToken.token == token)
    result = await session.execute(statement)
    return result.scalar_one_or_none()

async def delete_refresh_token(
        session: AsyncSession,
        refresh_token: RefreshToken,
) -> None:
    await session.delete(refresh_token)
    await session.flush()

async def create_password_reset_token(
        session: AsyncSession,
        user_id: int,
        token: str,
        expires_at: datetime,
) -> PasswordResetToken:

    password_reset_token = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )

    session.add(password_reset_token)
    await session.flush()

    return password_reset_token

async def get_password_reset_token_by_token(
        session: AsyncSession,
        token: str,
) -> PasswordResetToken | None:
    statement = select(PasswordResetToken).where(PasswordResetToken.token == token)
    result = await session.execute(statement)
    return result.scalar_one_or_none()

async def update_user_password(
        session: AsyncSession,
        user: User,
        hashed_password: str,
) -> User:
    user.hashed_password = hashed_password
    await session.flush()
    await session.refresh(user)
    return user

async def get_user_profile_by_user_id(
    session: AsyncSession,
    user_id: int,
) -> UserProfile | None:
    statement = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()

async def get_or_create_user_profile(
    session: AsyncSession,
    user_id: int,
) -> UserProfile:
    user_profile = await get_user_profile_by_user_id(
        session=session,
        user_id=user_id,
    )

    if user_profile is not None:
        return user_profile

    user_profile = UserProfile(user_id=user_id)
    session.add(user_profile)
    await session.flush()
    await session.refresh(user_profile)

    return user_profile

async def update_user_profile_avatar(
    session: AsyncSession,
    user_profile: UserProfile,
    avatar_url: str,
) -> UserProfile:
    user_profile.avatar = avatar_url
    await session.flush()
    await session.refresh(user_profile)
    return user_profile

async def delete_password_reset_token(
        session: AsyncSession,
        password_reset_token: PasswordResetToken,
) -> None:
    await session.delete(password_reset_token)
    await session.flush()

async def delete_activation_tokens_for_user(
    session: AsyncSession,
    user_id: int,
) -> None:
    statement = select(ActivationToken).where(ActivationToken.user_id == user_id)
    result = await session.execute(statement)
    activation_tokens = result.scalars().all()

    for activation_token in activation_tokens:
        await session.delete(activation_token)

    await session.flush()

async def delete_expired_auth_tokens(
    session: AsyncSession,
    now: datetime,
) -> tuple[int, int]:
    activation_statement = delete(ActivationToken).where(
        ActivationToken.expires_at < now
    )
    activation_result = await session.execute(activation_statement)

    password_reset_statement = delete(PasswordResetToken).where(
        PasswordResetToken.expires_at < now
    )
    password_reset_result = await session.execute(password_reset_statement)

    return activation_result.rowcount or 0, password_reset_result.rowcount or 0
