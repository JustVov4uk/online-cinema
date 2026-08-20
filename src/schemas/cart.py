from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.movies import MovieRead


class CartItemCreate(BaseModel):
    movie_id: int = Field(gt=0)


class CartItemRead(BaseModel):
    id: int
    movie: MovieRead
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartRead(BaseModel):
    id: int
    items: list[CartItemRead]

    model_config = ConfigDict(from_attributes=True)
