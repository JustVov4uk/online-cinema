from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user, require_admin
from src.database.models.accounts import User, UserGroup, UserGroupEnum
from src.database.models.orders import Order, OrderStatus
from src.database.models.payments import PaymentStatus
from src.database.session import get_database
from src.repositories.orders import get_order_by_id
from src.repositories.payments import (
    create_payment_for_order,
    get_payment_by_external_id,
    get_payment_by_id,
    get_payments,
    get_payments_for_user,
    update_payment_status,
)
from src.schemas.payments import (
    PaymentCreate,
    PaymentRead,
    PaymentSessionRead,
    PaymentWebhookRequest,
)

router = APIRouter(prefix="/payments", tags=["payments"])
admin_router = APIRouter(prefix="/admin/payments", tags=["admin payments"])

SUPPORTED_PAYMENT_METHODS = {"mock_card"}


async def _is_admin(session: AsyncSession, user: User) -> bool:
    user_group = await session.get(UserGroup, user.group_id)
    return user_group is not None and user_group.name == UserGroupEnum.ADMIN


def _calculate_order_items_total(order: Order) -> Decimal:
    return sum((item.price_at_order for item in order.items), Decimal("0.00"))


def _validate_order_total(order: Order) -> None:
    if _calculate_order_items_total(order) != order.total_amount:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order total does not match order items total.",
        )


@router.post(
    "/",
    response_model=PaymentSessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment_session(
    payload: PaymentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
):
    if payload.payment_method not in SUPPORTED_PAYMENT_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment method is not available. Use mock_card in test mode.",
        )

    order = await get_order_by_id(
        session=session,
        order_id=payload.order_id,
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot pay for this order.",
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be paid.",
        )

    if not order.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not contain items.",
        )

    _validate_order_total(order)

    external_payment_id = f"mock_{uuid4().hex}"

    return PaymentSessionRead(
        order_id=order.id,
        amount=order.total_amount,
        external_payment_id=external_payment_id,
        payment_url=f"http://localhost:8000/mock-payments/{external_payment_id}",
    )


@router.get("/", response_model=list[PaymentRead])
async def list_my_payments(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return await get_payments_for_user(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )


@router.post("/webhook", response_model=PaymentRead)
async def process_payment_webhook(
    payload: PaymentWebhookRequest,
    session: Annotated[AsyncSession, Depends(get_database)],
):
    payment = await get_payment_by_external_id(
        session=session,
        external_payment_id=payload.external_payment_id,
    )

    if payment is not None:
        payment = await update_payment_status(
            session=session,
            payment=payment,
            status=payload.status,
        )
        payment_id = payment.id
        await session.commit()

        updated_payment = await get_payment_by_id(
            session=session,
            payment_id=payment_id,
        )
        if updated_payment is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Updated payment could not be loaded.",
            )

        return updated_payment

    order = await get_order_by_id(
        session=session,
        order_id=payload.order_id,
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    if not order.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not contain items.",
        )

    _validate_order_total(order)

    payment = await create_payment_for_order(
        session=session,
        order=order,
        status=payload.status,
        external_payment_id=payload.external_payment_id,
    )
    payment_id = payment.id
    await session.commit()

    created_payment = await get_payment_by_id(
        session=session,
        payment_id=payment_id,
    )
    if created_payment is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Created payment could not be loaded.",
        )

    return created_payment


@router.get("/{payment_id}", response_model=PaymentRead)
async def retrieve_payment(
    payment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
):
    payment = await get_payment_by_id(
        session=session,
        payment_id=payment_id,
    )
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    if payment.user_id != current_user.id and not await _is_admin(
        session,
        current_user,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view this payment.",
        )

    return payment


@admin_router.get("/", response_model=list[PaymentRead])
async def list_admin_payments(
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_database)],
    user_id: Annotated[int | None, Query(gt=0)] = None,
    payment_status: Annotated[PaymentStatus | None, Query(alias="status")] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    start_datetime = (
        datetime.combine(date_from, time.min) if date_from is not None else None
    )
    end_datetime = datetime.combine(date_to, time.max) if date_to is not None else None

    return await get_payments(
        session=session,
        user_id=user_id,
        status=payment_status,
        date_from=start_datetime,
        date_to=end_datetime,
        skip=skip,
        limit=limit,
    )
