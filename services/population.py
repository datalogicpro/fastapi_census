import os

import requests
from dotenv import load_dotenv


load_dotenv()

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

CENSUS_URL = "https://api.census.gov/data/2024/acs/acs5"
MAPBOX_URL = "https://api.mapbox.com/search/geocode/v6/forward"
GEOCODER_URL = (
    "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
)

TIMEOUT = 10


def get_census_rows(geography: str, state_code: str | None = None) -> list[list[str]]:
    params = {
        "get": "NAME,B01003_001E",
        "for": geography,
        "key": CENSUS_API_KEY
    }

    if state_code:
        params["in"] = f"state:{state_code}"

    response = requests.get(CENSUS_URL, params=params, timeout=TIMEOUT)
    response.raise_for_status()

    return response.json()[1:]


def get_state(state: str) -> dict[str, str | int] | None:
    for name, population, code in get_census_rows("state:*"):
        if name.lower() == state.lower():
            return {
                "code": code,
                "state": name,
                "population": int(population)
            }

    return None


def get_places(state_code: str, city: str) -> list[dict[str, str | int]]:
    places = []

    for name, population, _, _ in get_census_rows("place:*", state_code):
        place_name = name.split(",")[0].split(" (")[0]

        if city.lower() in place_name.lower():
            places.append({
                "place": name,
                "population": int(population)
            })

    return places


def get_coordinates(city: str, state: str) -> list[float] | None:
    params = {
        "q": f"{city}, {state}",
        "country": "us",
        "types": "place,locality,neighborhood",
        "access_token": MAPBOX_TOKEN
    }

    response = requests.get(MAPBOX_URL, params=params, timeout=TIMEOUT)
    response.raise_for_status()

    for feature in response.json().get("features", []):
        region = feature["properties"]["context"].get("region", {})

        if region.get("name") == state:
            return feature["geometry"]["coordinates"]

    return None


def get_place_code(longitude: float, latitude: float, state_code: str) -> str | None:
    params = {
        "x": longitude,
        "y": latitude,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "layers": "Incorporated Places,Census Designated Places",
        "format": "json"
    }

    response = requests.get(GEOCODER_URL, params=params, timeout=TIMEOUT)
    response.raise_for_status()

    geographies = response.json()["result"]["geographies"]

    for layer in ("Incorporated Places", "Census Designated Places"):
        for place in geographies.get(layer, []):
            if place["STATE"] == state_code:
                return place["PLACE"]

    return None


def get_place_by_code(state_code: str, place_code: str) -> dict[str, str | int]:
    rows = get_census_rows(f"place:{place_code}", state_code)
    name, population, _, _ = rows[0]

    return {
        "place": name,
        "population": int(population)
    }