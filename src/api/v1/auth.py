from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user
from src.core.config import get_settings
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_secure_token,
    hash_password,
    verify_password,
)
from src.database.models.accounts import User, UserGroupEnum
from src.database.session import get_database
from src.repositories.accounts import (
    activate_user,
    create_activation_token,
    create_password_reset_token,
    create_refresh_token_record,
    create_user,
    delete_activation_token,
    delete_activation_tokens_for_user,
    delete_password_reset_token,
    delete_refresh_token,
    get_activation_token_by_token,
    get_password_reset_token_by_token,
    get_refresh_token_by_token,
    get_user_by_email,
    get_user_group_by_name,
    update_user_password,
)
from src.schemas.accounts import (
    AccessTokenResponse,
    ActivationResendRequest,
    ActivationResendResponse,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetResponse,
    RefreshTokenRequest,
    TokenPair,
    UserActivation,
    UserCreate,
    UserLogin,
    UserRead,
)
from src.tasks.email import send_activation_email_task, send_password_reset_email_task

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

    send_activation_email_task.delay(user.email, activation_token)

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

@router.post("/login", response_model=TokenPair)
async def login_user(
        payload: UserLogin,
        session: Annotated[AsyncSession, Depends(get_database)],
):
    user = await get_user_by_email(session, payload.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active.",
        )

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    settings = get_settings()
    refresh_token_expires_at = datetime.now(UTC) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    await create_refresh_token_record(
        session=session,
        user_id=user.id,
        token=refresh_token,
        expires_at=refresh_token_expires_at,
    )

    await session.commit()

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_database)],
):
    refresh_token_record = await get_refresh_token_by_token(
        session=session,
        token=payload.refresh_token,
    )

    if refresh_token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    if refresh_token_record.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired.",
        )

    token_payload = decode_token(payload.refresh_token)

    if token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    user_id = token_payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    access_token = create_access_token(subject=user_id)

    return AccessTokenResponse(access_token=access_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user(
        payload: RefreshTokenRequest,
        session: Annotated[AsyncSession, Depends(get_database)],
) -> None:
    refresh_token_record = await get_refresh_token_by_token(
        session=session,
        token=payload.refresh_token,
    )

    if refresh_token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )
    await delete_refresh_token(session, refresh_token_record)
    await session.commit()

@router.post("/password-reset/request", response_model=PasswordResetResponse)
async def request_password_reset(
    payload: PasswordResetRequest,
    session: Annotated[AsyncSession, Depends(get_database)],
):
    user = await get_user_by_email(session, payload.email)

    response = PasswordResetResponse(
        message="If this email exists, password reset instructions were sent."
    )

    if user is None:
        return response

    reset_token = generate_secure_token()
    reset_token_expires_at = datetime.now(UTC) + timedelta(hours=1)

    await create_password_reset_token(
        session=session,
        user_id=user.id,
        token=reset_token,
        expires_at=reset_token_expires_at,
    )

    await session.commit()

    send_password_reset_email_task.delay(user.email, reset_token)

    return response

@router.post("/password-reset/confirm", response_model=PasswordResetResponse)
async def password_reset_confirm(
    payload: PasswordResetConfirm,
    session: Annotated[AsyncSession, Depends(get_database)],
):
    password_reset_token = await get_password_reset_token_by_token(
        session=session,
        token=payload.token,
    )

    if password_reset_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset token",
        )

    if password_reset_token.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired.",
        )
    user = await session.get(User, password_reset_token.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User for this password reset token does not exist.",
        )

    hashed_password = hash_password(payload.new_password)

    await update_user_password(
        session=session,
        user=user,
        hashed_password=hashed_password,
    )
    await delete_password_reset_token(session, password_reset_token)
    await session.commit()

    return PasswordResetResponse(message="Password has been reset successfully.")

@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user

@router.post("/password-change", response_model=PasswordResetResponse)
async def change_password(
    payload: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
):
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect.",
        )

    hashed_password = hash_password(payload.new_password)

    await update_user_password(
        session=session,
        user=current_user,
        hashed_password=hashed_password,
    )
    await session.commit()

    return PasswordResetResponse(message="Password has been changed successfully.")

@router.post("/activation/resend", response_model=ActivationResendResponse)
async def resend_activation_token(
    payload: ActivationResendRequest,
    session: Annotated[AsyncSession, Depends(get_database)],
):
    response = ActivationResendResponse(
        message="If this email exists and is not active,"
                " activation instructions were sent."
    )

    user = await get_user_by_email(session, payload.email)

    if user is None or user.is_active:
        return response

    await delete_activation_tokens_for_user(
        session=session,
        user_id=user.id,
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

    send_activation_email_task.delay(user.email, activation_token)

    return response
