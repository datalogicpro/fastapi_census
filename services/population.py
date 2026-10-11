from dataclasses import dataclass

import httpx

from config import settings
from schemas.population import Place
from services.errors import ExternalDataError

CENSUS_URL = "https://api.census.gov/data/2024/acs/acs5"
MAPBOX_URL = "https://api.mapbox.com/search/geocode/v6/forward"
GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"

# The 2024 survey data never changes, so Census rows are kept until the app restarts
census_cache: dict[tuple[str, str | None], list[list[str]]] = {}


@dataclass(frozen=True)
class StateInfo:
    code: str
    name: str
    population: int


async def get_census_rows(
    client: httpx.AsyncClient, geography: str, state_code: str | None = None
) -> list[list[str]]:
    key = (geography, state_code)

    if (cached := census_cache.get(key)) is not None:
        return cached

    params = {
        "get": "NAME,B01003_001E",
        "for": geography,
        "key": settings.census_api_key.get_secret_value(),
    }

    if state_code:
        params["in"] = f"state:{state_code}"

    response = await client.get(CENSUS_URL, params=params)
    response.raise_for_status()

    try:
        data = response.json()

        if not isinstance(data, list) or not data:
            raise ValueError("expected a list of rows")

        # The first row holds the column names
        width = len(data[0])
        rows: list[list[str]] = data[1:]

        if not all(isinstance(row, list) and len(row) == width for row in rows):
            raise ValueError("unexpected row shape")
    except (TypeError, ValueError) as exc:
        raise ExternalDataError("Census response") from exc

    census_cache[key] = rows

    return rows


async def get_state(client: httpx.AsyncClient, state: str) -> StateInfo | None:
    rows = await get_census_rows(client, "state:*")

    try:
        for name, population, code in rows:
            if name.lower() == state.strip().lower():
                return StateInfo(code=code, name=name, population=int(population))
    except (TypeError, ValueError) as exc:
        raise ExternalDataError("Census state rows") from exc

    return None


def short_place_name(census_name: str) -> str:
    """'Anchorage municipality, Alaska' -> 'Anchorage'."""
    place_name = census_name.split(",")[0].split(" (")[0]
    words = place_name.split()

    # Drop the place type the Census adds, such as "city", "town", or "CDP"
    while words and (words[-1].islower() or words[-1] == "CDP"):
        words.pop()

    return " ".join(words)


async def get_places(
    client: httpx.AsyncClient, state_code: str, city: str
) -> list[Place]:
    rows = await get_census_rows(client, "place:*", state_code)

    places = []

    try:
        for name, population, _, _ in rows:
            if short_place_name(name).lower() == city.strip().lower():
                places.append(Place(place=name, population=int(population)))
    except (TypeError, ValueError) as exc:
        raise ExternalDataError("Census place rows") from exc

    return places


async def get_place_by_code(
    client: httpx.AsyncClient, state_code: str, place_code: str
) -> Place | None:
    rows = await get_census_rows(client, "place:*", state_code)

    try:
        for name, population, _, code in rows:
            if code == place_code:
                return Place(place=name, population=int(population))
    except (TypeError, ValueError) as exc:
        raise ExternalDataError("Census place rows") from exc

    return None


async def get_coordinates(
    client: httpx.AsyncClient, city: str, state: str
) -> tuple[float, float] | None:
    params = {
        "q": f"{city.strip()}, {state}",
        "country": "us",
        "types": "place,locality,neighborhood",
        "access_token": settings.mapbox_token.get_secret_value(),
    }

    response = await client.get(MAPBOX_URL, params=params)
    response.raise_for_status()

    try:
        for feature in response.json().get("features") or []:
            region = feature["properties"]["context"].get("region") or {}

            if region.get("name") == state:
                longitude, latitude = feature["geometry"]["coordinates"]
                return float(longitude), float(latitude)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ExternalDataError("Mapbox response") from exc

    return None


async def get_place_code(
    client: httpx.AsyncClient, longitude: float, latitude: float, state_code: str
) -> str | None:
    params: dict[str, str | float] = {
        "x": longitude,
        "y": latitude,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "layers": "Incorporated Places,Census Designated Places",
        "format": "json",
    }

    response = await client.get(GEOCODER_URL, params=params)
    response.raise_for_status()

    try:
        geographies = response.json()["result"]["geographies"]

        for layer in ("Incorporated Places", "Census Designated Places"):
            for place in geographies.get(layer) or []:
                if place["STATE"] == state_code:
                    return str(place["PLACE"])
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ExternalDataError("Census Geocoder response") from exc

    return None
