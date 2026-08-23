from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user
from src.database.models.accounts import User
from src.database.session import get_database
from src.repositories.cart import (
    add_movie_to_cart,
    clear_cart,
    get_cart_by_user_id,
    get_cart_item_by_cart_and_movie,
    get_or_create_cart,
    remove_cart_item,
)
from src.repositories.movies import get_movie_by_id
from src.schemas.cart import CartItemCreate, CartRead

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartRead)
async def retrieve_cart(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
):
    cart = await get_or_create_cart(
        session=session,
        user_id=current_user.id,
    )
    await session.commit()

    cart = await get_cart_by_user_id(
        session=session,
        user_id=current_user.id,
    )
    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cart could not be loaded.",
        )

    return cart


@router.post("/items/", response_model=CartRead, status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    payload: CartItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
):
    movie = await get_movie_by_id(
        session=session,
        movie_id=payload.movie_id,
    )
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found.",
        )

    cart = await get_or_create_cart(
        session=session,
        user_id=current_user.id,
    )

    existing_item = await get_cart_item_by_cart_and_movie(
        session=session,
        cart_id=cart.id,
        movie_id=payload.movie_id,
    )
    if existing_item is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Movie is already in cart.",
        )

    await add_movie_to_cart(
        session=session,
        cart=cart,
        movie_id=payload.movie_id,
    )
    await session.commit()

    cart = await get_cart_by_user_id(
        session=session,
        user_id=current_user.id,
    )

    return cart


@router.delete("/items/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cart_item(
    movie_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
) -> None:
    cart = await get_or_create_cart(
        session=session,
        user_id=current_user.id,
    )

    cart_item = await get_cart_item_by_cart_and_movie(
        session=session,
        cart_id=cart.id,
        movie_id=movie_id,
    )
    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found.",
        )

    await remove_cart_item(
        session=session,
        cart_item=cart_item,
    )
    await session.commit()


@router.delete("/items", status_code=status.HTTP_204_NO_CONTENT)
async def clear_user_cart(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
) -> None:
    cart = await get_or_create_cart(
        session=session,
        user_id=current_user.id,
    )

    await clear_cart(
        session=session,
        cart=cart,
    )
    await session.commit()
