from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(examples=["State not found"])


class StatePopulation(BaseModel):
    state: str = Field(examples=["Alaska"])
    population: int = Field(
        description="Total population, ACS 5-year estimate", examples=[735706]
    )


class Place(BaseModel):
    place: str = Field(
        description="Census place name, including its type, such as city or CDP",
        examples=["Kailua CDP (Honolulu County), Hawaii"],
    )
    population: int = Field(
        description="Total population, ACS 5-year estimate", examples=[39640]
    )


class CityPopulation(BaseModel):
    state: str = Field(examples=["Hawaii"])
    places: list[Place] = Field(
        description="Every place in the state with a matching name"
    )
    note: str | None = Field(
        default=None,
        description="Set when the name was found inside a larger Census place",
        examples=[None],
    )
