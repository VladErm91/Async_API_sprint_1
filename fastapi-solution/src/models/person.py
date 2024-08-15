from pydantic import BaseModel


class IdModel(BaseModel):
    uuid: str


class Film(IdModel):
    title: str


class FilmRating(Film):
    imdb_rating: float | None = 0.0


class PersonRoleInFilms(BaseModel):
    role: str
    films_details: list[FilmRating]


class PersonWithFilms(IdModel):
    full_name: str
    roles: list[PersonRoleInFilms]


class PortfolioFilm(BaseModel):
    uuid: str
    roles: list[str]


class Person(IdModel):
    full_name: str


class PersonFilm(Person):
    films: list[PortfolioFilm]
