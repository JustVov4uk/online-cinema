from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.movies import Movie
from src.database.models.orders import Order
from src.database.models.purchased import PurchasedMovie

if TYPE_CHECKING:
    from src.database.models.payments import Payment


def _purchased_movie_load_options() -> tuple:
    return (
        selectinload(PurchasedMovie.movie).selectinload(Movie.director),
        selectinload(PurchasedMovie.movie).selectinload(Movie.certification),
        selectinload(PurchasedMovie.movie).selectinload(Movie.genres),
        selectinload(PurchasedMovie.movie).selectinload(Movie.stars),
    )


async def create_purchased_movies_for_order(
    session: AsyncSession,
    order: Order,
) -> list[PurchasedMovie]:
    movie_ids = [order_item.movie_id for order_item in order.items]
    existing_movie_ids = await get_purchased_movie_ids_for_user(
        session=session,
        user_id=order.user_id,
        movie_ids=movie_ids,
    )
    purchased_movies = [
        PurchasedMovie(
            user_id=order.user_id,
            movie_id=order_item.movie_id,
            order_item_id=order_item.id,
        )
        for order_item in order.items
        if order_item.movie_id not in existing_movie_ids
    ]

    if not purchased_movies:
        return []

    session.add_all(purchased_movies)
    await session.flush()

    return purchased_movies


async def create_purchased_movies_for_payment(
    session: AsyncSession,
    payment: "Payment",
) -> list[PurchasedMovie]:
    movie_ids = [item.order_item.movie_id for item in payment.items]
    existing_movie_ids = await get_purchased_movie_ids_for_user(
        session=session,
        user_id=payment.user_id,
        movie_ids=movie_ids,
    )
    purchased_movies = [
        PurchasedMovie(
            user_id=payment.user_id,
            movie_id=item.order_item.movie_id,
            order_item_id=item.order_item_id,
        )
        for item in payment.items
        if item.order_item.movie_id not in existing_movie_ids
    ]

    if not purchased_movies:
        return []

    session.add_all(purchased_movies)
    await session.flush()

    return purchased_movies


async def get_purchased_movie_by_user_and_movie(
    session: AsyncSession,
    user_id: int,
    movie_id: int,
) -> PurchasedMovie | None:
    statement = select(PurchasedMovie).where(
        PurchasedMovie.user_id == user_id,
        PurchasedMovie.movie_id == movie_id,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_purchased_movie_ids_for_user(
    session: AsyncSession,
    user_id: int,
    movie_ids: list[int],
) -> set[int]:
    if not movie_ids:
        return set()

    statement = select(PurchasedMovie.movie_id).where(
        PurchasedMovie.user_id == user_id,
        PurchasedMovie.movie_id.in_(movie_ids),
    )
    result = await session.execute(statement)
    return set(result.scalars().all())


async def get_purchased_movies_for_user(
    session: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[PurchasedMovie]:
    statement = (
        select(PurchasedMovie)
        .where(PurchasedMovie.user_id == user_id)
        .options(*_purchased_movie_load_options())
        .order_by(PurchasedMovie.purchased_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())
