from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from src.api.dependencies.auth import get_current_user
from src.core.config import get_settings
from src.database.models.accounts import User
from src.database.session import get_database
from src.repositories.accounts import (
    get_or_create_user_profile,
    update_user_profile_avatar,
)
from src.schemas.accounts import UserProfileRead
from src.services.storage import upload_avatar_to_storage

router = APIRouter(prefix="/profile", tags=["profile"])

ALLOWED_AVATAR_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@router.post("/avatar", response_model=UserProfileRead)
async def upload_avatar(
    file: Annotated[UploadFile, File(description="JPEG, PNG, or WebP avatar image.")],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
) -> UserProfileRead:
    settings = get_settings()

    if file.content_type not in ALLOWED_AVATAR_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar must be a JPEG, PNG, or WebP image.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar file cannot be empty.",
        )

    if len(content) > settings.AVATAR_MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Avatar file is too large.",
        )

    try:
        avatar_url = await run_in_threadpool(
            upload_avatar_to_storage,
            user_id=current_user.id,
            filename=file.filename or "avatar.jpg",
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Avatar storage is unavailable.",
        ) from error

    user_profile = await get_or_create_user_profile(
        session=session,
        user_id=current_user.id,
    )
    user_profile = await update_user_profile_avatar(
        session=session,
        user_profile=user_profile,
        avatar_url=avatar_url,
    )
    await session.commit()

    return user_profile
