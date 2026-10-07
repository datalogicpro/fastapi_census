# Census Population API

A FastAPI app that returns population data for US states, cities, and towns from the US Census Bureau.

## Features

* Population for any US state.
* Population for cities and towns, including small ones.
* Returns every place in the state whose name matches, since many share names.
* Uses the latest Census American Community Survey 5-year data (2024).

## Requirements

* Python 3.13 or newer
* A free Census API key: https://api.census.gov/data/key_signup.html
* A Mapbox access token: https://account.mapbox.com/

## Installation

```bash
git clone https://github.com/datalogicpro/fastapi_census.git
cd fastapi_census
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project folder:

```text
CENSUS_API_KEY=your_census_api_key
MAPBOX_TOKEN=your_mapbox_token
```

Do not commit your `.env` file.

## Running the App

```bash
fastapi dev main.py
```

Interactive docs: http://127.0.0.1:8000/docs

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

Example: `/population/Hawaii/Honolulu`

```json
{
    "state": "Hawaii",
    "places": [
        {
            "place": "East Honolulu CDP, Hawaii",
            "population": 51360
        },
        {
            "place": "Urban Honolulu CDP, Hawaii",
            "population": 345482
        }
    ]
}
```

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

## Running Tests

```bash
python -m pytest
```

## Data Sources

* **US Census Bureau API**: American Community Survey 5-year estimates, table B01003 (total population).
* **Mapbox**: finds coordinates for names the Census doesn't list.
* **Census Geocoder**: finds which Census place contains those coordinates.