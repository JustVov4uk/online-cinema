from datetime import date, datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserProfileBase(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    avatar: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    info: str | None = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileRead(UserProfileBase):
    id: int
    user_id: int


class UserActivation(BaseModel):
    token: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetResponse(BaseModel):
    message: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class ActivationResendRequest(BaseModel):
    email: EmailStr


class ActivationResendResponse(BaseModel):
    message: str
