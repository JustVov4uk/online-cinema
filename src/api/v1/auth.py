from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import generate_secure_token, hash_password
from src.database.models.accounts import UserGroupEnum
from src.database.session import get_database
from src.repositories.accounts import (
    create_activation_token,
    create_user,
    get_user_by_email,
    get_user_group_by_name,
)
from src.schemas.accounts import UserCreate, UserRead

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
