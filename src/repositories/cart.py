from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.cart import Cart, CartItem
from src.database.models.movies import Movie


async def get_cart_by_user_id(
    session: AsyncSession,
    user_id: int,
) -> Cart | None:
    statement = (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.director),
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.certification),
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.genres),
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.stars),
        )
        .execution_options(populate_existing=True)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_or_create_cart(
    session: AsyncSession,
    user_id: int,
) -> Cart:
    cart = await get_cart_by_user_id(
        session=session,
        user_id=user_id,
    )

    if cart is not None:
        return cart

    cart = Cart(user_id=user_id, items=[])
    session.add(cart)
    await session.flush()

    return cart


async def get_cart_item_by_cart_and_movie(
    session: AsyncSession,
    cart_id: int,
    movie_id: int,
) -> CartItem | None:
    statement = select(CartItem).where(
        CartItem.cart_id == cart_id,
        CartItem.movie_id == movie_id,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def add_movie_to_cart(
    session: AsyncSession,
    cart: Cart,
    movie_id: int,
) -> CartItem:
    cart_item = CartItem(
        cart_id=cart.id,
        movie_id=movie_id,
    )

    session.add(cart_item)
    await session.flush()
    await session.refresh(cart_item)

    return cart_item


async def get_cart_item_by_id(
    session: AsyncSession,
    cart_id: int,
    cart_item_id: int,
) -> CartItem | None:
    statement = select(CartItem).where(
        CartItem.id == cart_item_id,
        CartItem.cart_id == cart_id,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def remove_cart_item(
    session: AsyncSession,
    cart_item: CartItem,
) -> None:
    await session.delete(cart_item)
    await session.flush()


async def clear_cart(
    session: AsyncSession,
    cart: Cart,
) -> None:
    for item in cart.items:
        await session.delete(item)

    await session.flush()
