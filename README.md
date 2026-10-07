# Census Population API

A FastAPI app that returns population data for US states, cities, and towns from the US Census Bureau.

## Features

* Population for any US state.
* Population for cities and towns, including small ones.
* Returns every place in the state with a matching name, since many share names.
* Uses the latest Census American Community Survey 5-year data (2024).
* Caches Census data in memory, so repeat lookups are fast.

## Tech Stack

* **Python 3.13** and **FastAPI**
* **Pydantic** for response models
* **requests** for calls to outside APIs
* **pytest** for tests
* **Ruff** for linting and formatting
* **Docker** for running in a container
* **GitHub Actions** for automatic checks on every push

## Project Structure

```text
fastapi_census/
├── main.py                 # Creates the app and adds the routes
├── routes/
│   └── population.py       # API endpoints
├── services/
│   └── population.py       # Calls to the Census, Mapbox, and Census Geocoder
├── schemas/
│   └── population.py       # Pydantic response models
├── test_population.py      # Tests
├── Dockerfile
├── requirements.txt        # Packages needed to run
├── requirements-dev.txt    # Adds testing and code-check tools
└── .env.example            # Names of the keys to set
```

## Requirements

* Python 3.13 or newer
* A free Census API key: https://api.census.gov/data/key_signup.html
* A Mapbox access token: https://account.mapbox.com/

## Installation

```powershell
git clone https://github.com/datalogicpro/fastapi_census.git
cd fastapi_census
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

`requirements.txt` holds what the app needs to run. `requirements-dev.txt` adds the testing and code-check tools.

## Environment Variables

Copy `.env.example` to a new file named `.env` in the project folder, then add your keys:

```text
CENSUS_API_KEY=your_census_api_key
MAPBOX_TOKEN=your_mapbox_token
```

Do not commit your `.env` file.

## Running the App

```powershell
fastapi dev main.py
```

Interactive docs: http://127.0.0.1:8000/docs

## Running with Docker

```powershell
docker build -t fastapi-census .
docker run --rm -p 8000:8000 --env-file .env fastapi-census
```

Interactive docs: http://localhost:8000/docs

## Endpoints

### `GET /population/{state}`

Example: `/population/Alaska`

```json
{
    "state": "Alaska",
    "population": 735706
}
```

### `GET /population/{state}/{city}`

Example: `/population/Hawaii/Kailua`

```json
{
    "state": "Hawaii",
    "places": [
        {
            "place": "Kailua CDP (Hawaii County), Hawaii",
            "population": 21818
        },
        {
            "place": "Kailua CDP (Honolulu County), Hawaii",
            "population": 39640
        }
    ],
    "note": null
}
```

The city name must match a Census place name exactly (not case-sensitive). Hawaii has two places named Kailua, so both are returned.

Place names follow the Census, which adds a type such as `city` or `CDP` (census-designated place).

If no Census place has the name, the API looks up the name with Mapbox, finds which Census place contains it, and returns that place with a note. This covers common names the Census doesn't use, like neighborhoods or hyphenated town names.

Example: `/population/Hawaii/Kailua-Kona`

```json
{
    "state": "Hawaii",
    "places": [
        {
            "place": "Kailua CDP (Hawaii County), Hawaii",
            "population": 21818
        }
    ],
    "note": "The Census has no place named Kailua-Kona. It lies within Kailua CDP (Hawaii County), Hawaii."
}
```

Returns `404` with `State not found` or `City not found` when there is no match.

Returns `502` with `External data service error` if the Census, Mapbox, or the Census Geocoder fails or doesn't answer within 10 seconds.

## Running Tests and Checks

```powershell
python -m pytest
ruff check .
ruff format --check .
```

GitHub Actions runs all three on every push.

## Data Sources

* **US Census Bureau API**: American Community Survey 5-year estimates, table B01003 (total population).
* **Mapbox**: finds coordinates for names the Census doesn't list.
* **Census Geocoder**: finds which Census place contains those coordinates.