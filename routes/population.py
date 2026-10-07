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


def get_census_rows(geography, state_code=None):
    params = {
        "get": "NAME,B01003_001E",
        "for": geography,
        "key": CENSUS_API_KEY
    }

    if state_code:
        params["in"] = f"state:{state_code}"

    response = requests.get(CENSUS_URL, params=params)
    response.raise_for_status()

    return response.json()[1:]


def get_state(state):
    for name, population, code in get_census_rows("state:*"):
        if name.lower() == state.lower():
            return {
                "code": code,
                "state": name,
                "population": int(population)
            }

    return None


def get_places(state_code, city):
    places = []

    for name, population, _, _ in get_census_rows("place:*", state_code):
        place_name = name.split(",")[0].split(" (")[0]

        if city.lower() in place_name.lower():
            places.append({
                "place": name,
                "population": int(population)
            })

    return places


def get_coordinates(city, state):
    params = {
        "q": f"{city}, {state}",
        "country": "us",
        "types": "place,locality,neighborhood",
        "access_token": MAPBOX_TOKEN
    }

    response = requests.get(MAPBOX_URL, params=params)
    response.raise_for_status()

    for feature in response.json().get("features", []):
        region = feature["properties"]["context"].get("region", {})

        if region.get("name") == state:
            return feature["geometry"]["coordinates"]

    return None


def get_place_code(longitude, latitude, state_code):
    params = {
        "x": longitude,
        "y": latitude,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "layers": "Incorporated Places,Census Designated Places",
        "format": "json"
    }

    response = requests.get(GEOCODER_URL, params=params)
    response.raise_for_status()

    geographies = response.json()["result"]["geographies"]

    for layer in ("Incorporated Places", "Census Designated Places"):
        for place in geographies.get(layer, []):
            if place["STATE"] == state_code:
                return place["PLACE"]

    return None


def get_place_by_code(state_code, place_code):
    rows = get_census_rows(f"place:{place_code}", state_code)
    name, population, _, _ = rows[0]

    return {
        "place": name,
        "population": int(population)
    }