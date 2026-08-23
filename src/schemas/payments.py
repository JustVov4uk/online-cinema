from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.database.models.payments import PaymentStatus
from src.schemas.orders import OrderItemRead


class PaymentCreate(BaseModel):
    order_id: int = Field(gt=0)
    payment_method: str = Field(default="mock_card", min_length=1, max_length=50)


class PaymentSessionRead(BaseModel):
    order_id: int
    amount: Decimal
    external_payment_id: str
    payment_url: str


class PaymentWebhookRequest(BaseModel):
    order_id: int = Field(gt=0)
    external_payment_id: str = Field(min_length=1, max_length=255)
    status: PaymentStatus


class PaymentItemRead(BaseModel):
    id: int
    order_item: OrderItemRead
    price_at_payment: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentRead(BaseModel):
    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatus
    amount: Decimal
    external_payment_id: str | None
    items: list[PaymentItemRead]

    model_config = ConfigDict(from_attributes=True)
