from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import generate_secure_token, hash_password
from src.database.models.accounts import User, UserGroupEnum
from src.database.session import get_database
from src.repositories.accounts import (
    activate_user,
    create_activation_token,
    create_user,
    delete_activation_token,
    get_activation_token_by_token,
    get_user_by_email,
    get_user_group_by_name,
)
from src.schemas.accounts import UserActivation, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_database)],
):
    existing_user = await get_user_by_email(session, payload.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists.",
        )

    user_group = await get_user_group_by_name(session, UserGroupEnum.USER)
    if user_group is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user group is not configured.",
        )

    hashed_password = hash_password(payload.password)

    user = await create_user(
        session=session,
        email=payload.email,
        hashed_password=hashed_password,
        group_id=user_group.id,
    )

    activation_token = generate_secure_token()
    activation_token_expires_at = datetime.now(UTC) + timedelta(hours=24)

    await create_activation_token(
        session=session,
        user_id=user.id,
        token=activation_token,
        expires_at=activation_token_expires_at,
    )
    await session.commit()
    return user

@router.post("/activate", response_model=UserRead)
async def activate_account(
        payload: UserActivation,
        session: Annotated[AsyncSession, Depends(get_database)],
):
    activation_token = await get_activation_token_by_token(
        session=session,
        token=payload.token,
    )
    if activation_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activation token.",
        )

    if activation_token.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token has expired.",
        )
    user = await session.get(User, activation_token.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User for this activation token does not exist.",
        )

    if user.is_active:
        await delete_activation_token(session, activation_token)
        await session.commit()
        return user

    user = await activate_user(session, user)
    await delete_activation_token(session, activation_token)

    await session.commit()

    return user