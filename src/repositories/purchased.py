from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.movies import Movie
from src.database.models.orders import Order
from src.database.models.purchased import PurchasedMovie


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
    purchased_movies = [
        PurchasedMovie(
            user_id=order.user_id,
            movie_id=order_item.movie_id,
            order_item_id=order_item.id,
        )
        for order_item in order.items
    ]

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
