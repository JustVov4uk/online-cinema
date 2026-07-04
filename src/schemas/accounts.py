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
