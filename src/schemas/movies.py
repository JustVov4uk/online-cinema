from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GenreBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class GenreCreate(GenreBase):
    pass


class GenreRead(GenreBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class StarBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class StarCreate(StarBase):
    pass


class StarRead(StarBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DirectorBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class DirectorCreate(DirectorBase):
    pass


class DirectorRead(DirectorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CertificationBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class CertificationCreate(CertificationBase):
    pass


class CertificationRead(CertificationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MovieBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    year: int = Field(ge=1888)
    time: int = Field(gt=0)
    imdb: float = Field(ge=0, le=10)
    votes: int = Field(ge=0)
    metascore: int | None = Field(default=None, ge=0, le=100)
    gross: Decimal | None = Field(default=None, ge=0)
    description: str = Field(min_length=1)
    price: Decimal = Field(ge=0)


class MovieCreate(MovieBase):
    director_id: int
    certification_id: int
    genre_ids: list[int] = Field(default_factory=list)
    star_ids: list[int] = Field(default_factory=list)


class MovieUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    year: int | None = Field(default=None, ge=1888)
    time: int | None = Field(default=None, gt=0)
    imdb: float | None = Field(default=None, ge=0, le=10)
    votes: int | None = Field(default=None, ge=0)
    metascore: int | None = Field(default=None, ge=0, le=100)
    gross: Decimal | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, min_length=1)
    price: Decimal | None = Field(default=None, ge=0)
    director_id: int | None = None
    certification_id: int | None = None
    genre_ids: list[int] | None = None
    star_ids: list[int] | None = None


class MovieRead(MovieBase):
    id: int
    uuid: UUID
    director: DirectorRead
    certification: CertificationRead
    genres: list[GenreRead]
    stars: list[StarRead]

    model_config = ConfigDict(from_attributes=True)
