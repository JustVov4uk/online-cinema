from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import require_moderator_or_admin
from src.database.models.accounts import User
from src.database.session import get_database
from src.repositories.movies import (
    create_movie,
    delete_movie,
    get_certification_by_id,
    get_director_by_id,
    get_genres_by_ids,
    get_movie_by_id,
    get_movies,
    get_stars_by_ids,
    update_movie,
)
from src.schemas.movies import MovieCreate, MovieRead, MovieUpdate

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=list[MovieRead])
async def list_movies(
    session: Annotated[AsyncSession, Depends(get_database)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return await get_movies(
        session=session,
        skip=skip,
        limit=limit,
    )


@router.get("/{movie_id}", response_model=MovieRead)
async def retrieve_movie(
    movie_id: int,
    session: Annotated[AsyncSession, Depends(get_database)],
):
    movie = await get_movie_by_id(
        session=session,
        movie_id=movie_id,
    )

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found.",
        )

    return movie


@router.post("/", response_model=MovieRead, status_code=status.HTTP_201_CREATED)
async def create_movie_endpoint(
    payload: MovieCreate,
    session: Annotated[AsyncSession, Depends(get_database)],
    current_user: Annotated[User, Depends(require_moderator_or_admin)],
):
    director = await get_director_by_id(
        session=session,
        director_id=payload.director_id,
    )
    if director is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Director does not exist.",
        )

    certification = await get_certification_by_id(
        session=session,
        certification_id=payload.certification_id,
    )
    if certification is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certification does not exist.",
        )

    genres = await get_genres_by_ids(
        session=session,
        genre_ids=payload.genre_ids,
    )
    if len(genres) != len(set(payload.genre_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more genres do not exist.",
        )

    stars = await get_stars_by_ids(
        session=session,
        star_ids=payload.star_ids,
    )
    if len(stars) != len(set(payload.star_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more stars do not exist.",
        )

    movie = await create_movie(
        session=session,
        payload=payload,
        genres=genres,
        stars=stars,
    )
    movie_id = movie.id

    await session.commit()

    created_movie = await get_movie_by_id(
        session=session,
        movie_id=movie_id,
    )
    if created_movie is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Created movie could not be loaded.",
        )

    return created_movie


@router.patch("/{movie_id}", response_model=MovieRead)
async def update_movie_endpoint(
    movie_id: int,
    payload: MovieUpdate,
    session: Annotated[AsyncSession, Depends(get_database)],
    current_user: Annotated[User, Depends(require_moderator_or_admin)],
):
    movie = await get_movie_by_id(
        session=session,
        movie_id=movie_id,
    )
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found.",
        )

    if payload.director_id is not None:
        director = await get_director_by_id(
            session=session,
            director_id=payload.director_id,
        )
        if director is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Director does not exist.",
            )

    if payload.certification_id is not None:
        certification = await get_certification_by_id(
            session=session,
            certification_id=payload.certification_id,
        )
        if certification is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Certification does not exist.",
            )

    genres = None
    if payload.genre_ids is not None:
        genres = await get_genres_by_ids(
            session=session,
            genre_ids=payload.genre_ids,
        )
        if len(genres) != len(set(payload.genre_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more genres do not exist.",
            )

    stars = None
    if payload.star_ids is not None:
        stars = await get_stars_by_ids(
            session=session,
            star_ids=payload.star_ids,
        )
        if len(stars) != len(set(payload.star_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more stars do not exist.",
            )

    movie = await update_movie(
        session=session,
        movie=movie,
        payload=payload,
        genres=genres,
        stars=stars,
    )
    movie_id = movie.id

    await session.commit()

    updated_movie = await get_movie_by_id(
        session=session,
        movie_id=movie_id,
    )
    if updated_movie is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Updated movie could not be loaded.",
        )

    return updated_movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie_endpoint(
    movie_id: int,
    session: Annotated[AsyncSession, Depends(get_database)],
    current_user: Annotated[User, Depends(require_moderator_or_admin)],
):
    movie = await get_movie_by_id(
        session=session,
        movie_id=movie_id,
    )
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found.",
        )

    await delete_movie(
        session=session,
        movie=movie,
    )
    await session.commit()
