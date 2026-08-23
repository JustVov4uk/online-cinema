from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base
from src.database.models.accounts import User
from src.database.models.movies import Movie
from src.database.models.orders import OrderItem


class PurchasedMovie(Base):
    __tablename__ = "purchased_movies"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "movie_id",
            name="uq_purchased_movies_user_id_movie_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id"),
        nullable=False,
    )
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    user: Mapped[User] = relationship("User")
    movie: Mapped[Movie] = relationship("Movie")
    order_item: Mapped[OrderItem] = relationship("OrderItem")
