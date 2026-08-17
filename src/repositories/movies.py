from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.movies import Certification, Director, Genre, Movie, Star
from src.schemas.movies import MovieCreate, MovieUpdate


async def get_director_by_id(
    session: AsyncSession,
    director_id: int,
) -> Director | None:
    statement = select(Director).where(Director.id == director_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_certification_by_id(
    session: AsyncSession,
    certification_id: int,
) -> Certification | None:
    statement = select(Certification).where(Certification.id == certification_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_genres_by_ids(
    session: AsyncSession,
    genre_ids: list[int],
) -> list[Genre]:
    statement = select(Genre).where(Genre.id.in_(genre_ids))
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_stars_by_ids(
    session: AsyncSession,
    star_ids: list[int],
) -> list[Star]:
    statement = select(Star).where(Star.id.in_(star_ids))
    result = await session.execute(statement)
    return list(result.scalars().all())


async def create_movie(
    session: AsyncSession,
    payload: MovieCreate,
    genres: list[Genre],
    stars: list[Star],
) -> Movie:
    movie = Movie(
        uuid=uuid4(),
        name=payload.name,
        year=payload.year,
        time=payload.time,
        imdb=payload.imdb,
        votes=payload.votes,
        metascore=payload.metascore,
        gross=payload.gross,
        description=payload.description,
        price=payload.price,
        director_id=payload.director_id,
        certification_id=payload.certification_id,
        genres=genres,
        stars=stars,
    )

    session.add(movie)
    await session.flush()
    await session.refresh(movie)

    return movie


async def get_movie_by_id(
    session: AsyncSession,
    movie_id: int,
) -> Movie | None:
    statement = (
        select(Movie)
        .where(Movie.id == movie_id)
        .options(
            selectinload(Movie.director),
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.stars),
        )
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_movies(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> list[Movie]:
    statement = (
        select(Movie)
        .options(
            selectinload(Movie.director),
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.stars),
        )
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def update_movie(
    session: AsyncSession,
    movie: Movie,
    payload: MovieUpdate,
    genres: list[Genre] | None = None,
    stars: list[Star] | None = None,
) -> Movie:
    update_data = payload.model_dump(
        exclude_unset=True,
        exclude={"genre_ids", "star_ids"},
    )

    for field, value in update_data.items():
        setattr(movie, field, value)

    if genres is not None:
        movie.genres = genres

    if stars is not None:
        movie.stars = stars

    await session.flush()
    await session.refresh(movie)

    return movie


async def delete_movie(
    session: AsyncSession,
    movie: Movie,
) -> None:
    await session.delete(movie)
    await session.flush()
