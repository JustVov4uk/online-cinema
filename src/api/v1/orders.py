from datetime import date, datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user, require_admin
from src.database.models.accounts import User, UserGroup, UserGroupEnum
from src.database.models.orders import OrderStatus
from src.database.session import get_database
from src.repositories.cart import clear_cart, get_or_create_cart
from src.repositories.orders import (
    cancel_order,
    create_order,
    get_order_by_id,
    get_orders,
    get_orders_for_user,
    get_pending_order_with_movie_ids,
)
from src.repositories.purchased import get_purchased_movie_ids_for_user
from src.schemas.orders import OrderCreateResponse, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])
admin_router = APIRouter(prefix="/admin/orders", tags=["admin orders"])


async def _is_admin(session: AsyncSession, user: User) -> bool:
    user_group = await session.get(UserGroup, user.group_id)
    return user_group is not None and user_group.name == UserGroupEnum.ADMIN


@router.post(
    "/",
    response_model=OrderCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order_from_cart(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
):
    cart = await get_or_create_cart(
        session=session,
        user_id=current_user.id,
    )

    if not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty.",
        )

    cart_movie_ids = [item.movie_id for item in cart.items]
    purchased_movie_ids = await get_purchased_movie_ids_for_user(
        session=session,
        user_id=current_user.id,
        movie_ids=cart_movie_ids,
    )
    excluded_movie_ids = [
        item.movie_id for item in cart.items if item.movie_id in purchased_movie_ids
    ]
    order_items = [
        item for item in cart.items if item.movie_id not in purchased_movie_ids
    ]

    if not order_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart does not contain movies available for order.",
        )

    movie_prices = {item.movie_id: item.movie.price for item in order_items}
    existing_order = await get_pending_order_with_movie_ids(
        session=session,
        user_id=current_user.id,
        movie_ids=set(movie_prices),
    )
    if existing_order is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pending order with the same movies already exists.",
        )

    order = await create_order(
        session=session,
        user_id=current_user.id,
        movie_prices=movie_prices,
    )
    order_id = order.id

    await clear_cart(
        session=session,
        cart=cart,
    )
    await session.commit()

    created_order = await get_order_by_id(
        session=session,
        order_id=order_id,
    )
    if created_order is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Created order could not be loaded.",
        )

    return OrderCreateResponse(
        order=created_order,
        excluded_movie_ids=excluded_movie_ids,
    )


@router.get("/", response_model=list[OrderRead])
async def list_my_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return await get_orders_for_user(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )


@router.get("/{order_id}", response_model=OrderRead)
async def retrieve_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
):
    order = await get_order_by_id(
        session=session,
        order_id=order_id,
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    if order.user_id != current_user.id and not await _is_admin(session, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view this order.",
        )

    return order


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_my_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_database)],
):
    order = await get_order_by_id(
        session=session,
        order_id=order_id,
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    if order.user_id != current_user.id and not await _is_admin(session, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot cancel this order.",
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be canceled.",
        )

    canceled_order = await cancel_order(
        session=session,
        order=order,
    )
    await session.commit()

    loaded_order = await get_order_by_id(
        session=session,
        order_id=canceled_order.id,
    )
    if loaded_order is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Canceled order could not be loaded.",
        )

    return loaded_order


@admin_router.get("/", response_model=list[OrderRead])
async def list_admin_orders(
    current_user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_database)],
    user_id: Annotated[int | None, Query(gt=0)] = None,
    order_status: Annotated[OrderStatus | None, Query(alias="status")] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    start_datetime = (
        datetime.combine(date_from, time.min) if date_from is not None else None
    )
    end_datetime = datetime.combine(date_to, time.max) if date_to is not None else None

    return await get_orders(
        session=session,
        user_id=user_id,
        status=order_status,
        date_from=start_datetime,
        date_to=end_datetime,
        skip=skip,
        limit=limit,
    )
