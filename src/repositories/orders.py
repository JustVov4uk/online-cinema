from datetime import datetime
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.movies import Movie
from src.database.models.orders import Order, OrderItem, OrderStatus


def _order_load_options() -> tuple:
    return (
        selectinload(Order.items).selectinload(OrderItem.movie).selectinload(Movie.director),
        selectinload(Order.items)
        .selectinload(OrderItem.movie)
        .selectinload(Movie.certification),
        selectinload(Order.items).selectinload(OrderItem.movie).selectinload(Movie.genres),
        selectinload(Order.items).selectinload(OrderItem.movie).selectinload(Movie.stars),
    )


async def get_paid_movie_ids_for_user(
    session: AsyncSession,
    user_id: int,
) -> set[int]:
    statement = (
        select(OrderItem.movie_id)
        .join(Order)
        .where(
            Order.user_id == user_id,
            Order.status == OrderStatus.PAID,
        )
    )
    result = await session.execute(statement)
    return set(result.scalars().all())


async def get_pending_order_with_movie_ids(
    session: AsyncSession,
    user_id: int,
    movie_ids: set[int],
) -> Order | None:
    statement = (
        select(Order)
        .where(
            Order.user_id == user_id,
            Order.status == OrderStatus.PENDING,
        )
        .options(selectinload(Order.items))
    )
    result = await session.execute(statement)

    for order in result.scalars().all():
        order_movie_ids = {item.movie_id for item in order.items}
        if order_movie_ids == movie_ids:
            return order

    return None


async def create_order(
    session: AsyncSession,
    user_id: int,
    movie_prices: dict[int, Decimal],
) -> Order:
    order = Order(
        user_id=user_id,
        total_amount=sum(movie_prices.values(), Decimal("0.00")),
    )
    session.add(order)
    await session.flush()

    for movie_id, price in movie_prices.items():
        session.add(
            OrderItem(
                order_id=order.id,
                movie_id=movie_id,
                price_at_order=price,
            )
        )

    await session.flush()
    await session.refresh(order)

    return order


async def get_order_by_id(
    session: AsyncSession,
    order_id: int,
) -> Order | None:
    statement = (
        select(Order)
        .where(Order.id == order_id)
        .options(*_order_load_options())
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_orders_for_user(
    session: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[Order]:
    statement = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(*_order_load_options())
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_orders(
    session: AsyncSession,
    user_id: int | None = None,
    status: OrderStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Order]:
    statement: Select[tuple[Order]] = select(Order).options(*_order_load_options())

    if user_id is not None:
        statement = statement.where(Order.user_id == user_id)

    if status is not None:
        statement = statement.where(Order.status == status)

    if date_from is not None:
        statement = statement.where(Order.created_at >= date_from)

    if date_to is not None:
        statement = statement.where(Order.created_at <= date_to)

    statement = statement.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def cancel_order(
    session: AsyncSession,
    order: Order,
) -> Order:
    order.status = OrderStatus.CANCELED
    await session.flush()
    await session.refresh(order)

    return order
