from fastapi import FastAPI, HTTPException

from routes.population import (
    get_coordinates,
    get_place_by_code,
    get_place_code,
    get_places,
    get_state
)


app = FastAPI()


@app.get("/population/{state}")
def state_population(state: str):
    result = get_state(state)

    if result is None:
        raise HTTPException(status_code=404, detail="State not found")

    return {
        "state": result["state"],
        "population": result["population"]
    }


@app.get("/population/{state}/{city}")
def city_population(state: str, city: str):
    state_info = get_state(state)

    if state_info is None:
        raise HTTPException(status_code=404, detail="State not found")

    places = get_places(state_info["code"], city)

    if places:
        return {
            "state": state_info["state"],
            "places": places
        }

    coordinates = get_coordinates(city, state_info["state"])

    if coordinates is None:
        raise HTTPException(status_code=404, detail="City not found")

    longitude, latitude = coordinates

    place_code = get_place_code(longitude, latitude, state_info["code"])

    if place_code is None:
        raise HTTPException(status_code=404, detail="City not found")

    place = get_place_by_code(state_info["code"], place_code)

    return {
        "state": state_info["state"],
        "places": [place],
        "note": (
            f"The Census has no place named {city}. "
            f"It lies within {place['place']}."
        )
    }