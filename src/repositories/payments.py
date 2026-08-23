from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.movies import Movie
from src.database.models.orders import Order, OrderItem, OrderStatus
from src.database.models.payments import Payment, PaymentItem, PaymentStatus


def _payment_load_options() -> tuple:
    return (
        selectinload(Payment.order),
        selectinload(Payment.items)
        .selectinload(PaymentItem.order_item)
        .selectinload(OrderItem.movie)
        .selectinload(Movie.director),
        selectinload(Payment.items)
        .selectinload(PaymentItem.order_item)
        .selectinload(OrderItem.movie)
        .selectinload(Movie.certification),
        selectinload(Payment.items)
        .selectinload(PaymentItem.order_item)
        .selectinload(OrderItem.movie)
        .selectinload(Movie.genres),
        selectinload(Payment.items)
        .selectinload(PaymentItem.order_item)
        .selectinload(OrderItem.movie)
        .selectinload(Movie.stars),
    )


async def create_payment_for_order(
    session: AsyncSession,
    order: Order,
    status: PaymentStatus,
    external_payment_id: str | None = None,
) -> Payment:
    payment = Payment(
        user_id=order.user_id,
        order_id=order.id,
        status=status,
        amount=order.total_amount,
        external_payment_id=external_payment_id,
    )
    session.add(payment)
    await session.flush()

    for order_item in order.items:
        session.add(
            PaymentItem(
                payment_id=payment.id,
                order_item_id=order_item.id,
                price_at_payment=order_item.price_at_order,
            )
        )

    if status == PaymentStatus.SUCCESSFUL:
        order.status = OrderStatus.PAID

    await session.flush()
    await session.refresh(payment)

    return payment


async def get_payment_by_id(
    session: AsyncSession,
    payment_id: int,
) -> Payment | None:
    statement = (
        select(Payment)
        .where(Payment.id == payment_id)
        .options(*_payment_load_options())
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_payment_by_external_id(
    session: AsyncSession,
    external_payment_id: str,
) -> Payment | None:
    statement = (
        select(Payment)
        .where(Payment.external_payment_id == external_payment_id)
        .options(*_payment_load_options())
        .order_by(Payment.created_at.desc())
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def get_payment_by_order_id(
    session: AsyncSession,
    order_id: int,
) -> Payment | None:
    statement = (
        select(Payment)
        .where(Payment.order_id == order_id)
        .options(*_payment_load_options())
        .order_by(Payment.created_at.desc())
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def get_payments_for_user(
    session: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[Payment]:
    statement = (
        select(Payment)
        .where(Payment.user_id == user_id)
        .options(*_payment_load_options())
        .order_by(Payment.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_payments(
    session: AsyncSession,
    user_id: int | None = None,
    status: PaymentStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Payment]:
    statement: Select[tuple[Payment]] = select(Payment).options(
        *_payment_load_options()
    )

    if user_id is not None:
        statement = statement.where(Payment.user_id == user_id)

    if status is not None:
        statement = statement.where(Payment.status == status)

    if date_from is not None:
        statement = statement.where(Payment.created_at >= date_from)

    if date_to is not None:
        statement = statement.where(Payment.created_at <= date_to)

    statement = statement.order_by(Payment.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def update_payment_status(
    session: AsyncSession,
    payment: Payment,
    status: PaymentStatus,
) -> Payment:
    payment.status = status

    if status == PaymentStatus.SUCCESSFUL:
        payment.order.status = OrderStatus.PAID

    await session.flush()
    await session.refresh(payment)

    return payment
