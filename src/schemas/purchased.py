from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.schemas.movies import MovieRead


class PurchasedMovieRead(BaseModel):
    id: int
    movie: MovieRead
    purchased_at: datetime
    order_item_id: int

    model_config = ConfigDict(from_attributes=True)
