from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Request

from config import settings
from rate_limit import limiter
from schemas.population import CityPopulation, ErrorResponse, StatePopulation
from services.http_client import get_http_client
from services.population import (
    StateInfo,
    get_coordinates,
    get_place_by_code,
    get_place_code,
    get_places,
    get_state,
)

router = APIRouter(prefix="/v1/population", tags=["population"])

StateName = Annotated[
    str,
    Path(
        min_length=2,
        max_length=50,
        pattern=r"\S",
        description="US state name, not case-sensitive",
        examples=["Alaska"],
    ),
]
CityName = Annotated[
    str,
    Path(
        min_length=1,
        max_length=100,
        pattern=r"\S",
        description="City or town name, not case-sensitive",
        examples=["Kailua"],
    ),
]
HttpClient = Annotated[httpx.AsyncClient, Depends(get_http_client)]


def error(description: str) -> dict[str, Any]:
    return {"model": ErrorResponse, "description": description}


COMMON_ERRORS: dict[int | str, dict[str, Any]] = {
    429: error("Too many requests"),
    502: error("An external data service failed"),
}


async def find_state(client: httpx.AsyncClient, state: str) -> StateInfo:
    state_info = await get_state(client, state)

    if state_info is None:
        raise HTTPException(status_code=404, detail="State not found")

    return state_info


@router.get(
    "/{state}",
    summary="State population",
    responses={404: error("State not found"), **COMMON_ERRORS},
)
@limiter.limit(settings.rate_limit)
async def state_population(
    request: Request, state: StateName, client: HttpClient
) -> StatePopulation:
    """Total population of a US state, from the Census ACS 5-year estimates."""
    state_info = await find_state(client, state)

    return StatePopulation(state=state_info.name, population=state_info.population)


@router.get(
    "/{state}/{city}",
    summary="City or town population",
    responses={404: error("State or city not found"), **COMMON_ERRORS},
)
@limiter.limit(settings.rate_limit)
async def city_population(
    request: Request, state: StateName, city: CityName, client: HttpClient
) -> CityPopulation:
    """Every Census place in the state with this name.

    If no place has the name, the API finds where the name is with Mapbox and
    returns the Census place that contains it, with a note.
    """
    state_info = await find_state(client, state)

    places = await get_places(client, state_info.code, city)

    if places:
        return CityPopulation(state=state_info.name, places=places)

    coordinates = await get_coordinates(client, city, state_info.name)

    if coordinates is None:
        raise HTTPException(status_code=404, detail="City not found")

    longitude, latitude = coordinates

    place_code = await get_place_code(client, longitude, latitude, state_info.code)

    if place_code is None:
        raise HTTPException(status_code=404, detail="City not found")

    place = await get_place_by_code(client, state_info.code, place_code)

    if place is None:
        raise HTTPException(status_code=404, detail="City not found")

    return CityPopulation(
        state=state_info.name,
        places=[place],
        note=(
            f"The Census has no place named {city.strip()}. "
            f"It lies within {place.place}."
        ),
    )
