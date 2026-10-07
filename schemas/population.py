from pydantic import BaseModel


class StatePopulation(BaseModel):
    state: str
    population: int


class Place(BaseModel):
    place: str
    population: int


class CityPopulation(BaseModel):
    state: str
    places: list[Place]
    note: str | None = None
