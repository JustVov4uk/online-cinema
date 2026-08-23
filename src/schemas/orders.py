from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from src.database.models.orders import OrderStatus
from src.schemas.movies import MovieRead


class OrderItemRead(BaseModel):
    id: int
    movie: MovieRead
    price_at_order: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatus
    total_amount: Decimal
    items: list[OrderItemRead]

    model_config = ConfigDict(from_attributes=True)


class OrderCreateResponse(BaseModel):
    order: OrderRead
    excluded_movie_ids: list[int] = []

    model_config = ConfigDict(from_attributes=True)
