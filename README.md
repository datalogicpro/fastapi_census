# Census Population API

[![Tests](https://github.com/datalogicpro/fastapi_census/actions/workflows/tests.yml/badge.svg)](https://github.com/datalogicpro/fastapi_census/actions/workflows/tests.yml)

A FastAPI app that returns population data for US states, cities, and towns from the US Census Bureau.

**Live demo:** https://fastapi-census.onrender.com/docs

The app runs on Render's free plan, so the first request after a quiet period can take up to a minute while it wakes up.

## Features

* Population for any US state, plus the District of Columbia and Puerto Rico.
* Population for cities and towns, including small ones.
* Returns every place in the state with a matching name, since many share names.
* Finds names the Census doesn't use, such as neighborhoods and hyphenated town names, and returns the Census place that contains them.
* Uses the latest Census American Community Survey 5-year data (2024).
* Caches Census data in memory, so repeat lookups are fast.
* Async calls to outside APIs through one shared HTTP client.
* Rate limit of 60 requests per minute per client.
* Versioned routes under `/v1`.

## Tech Stack

* **Python 3.13** and **FastAPI**
* **Pydantic** for response models
* **pydantic-settings** for loading and checking API keys
* **httpx** for async calls to outside APIs
* **slowapi** for rate limiting
* **pytest** and **pytest-cov** for tests and coverage
* **Ruff** for linting and formatting
* **mypy** for type checking
* **pre-commit** to run Ruff and mypy before every commit
* **Docker** for running in a container
* **GitHub Actions** for automatic checks on every push
* **Dependabot** for weekly dependency updates

## Project Structure

```text
fastapi_census/
├── main.py                   # Creates the app, adds the routes, handles errors
├── config.py                 # Loads and checks settings and API keys
├── rate_limit.py             # Rate limiter shared by the routes
├── routes/
│   ├── health.py             # Health check endpoint
│   └── population.py         # Population endpoints
├── services/
│   ├── errors.py             # Error for bad data from outside services
│   ├── http_client.py        # Shared async HTTP client
│   └── population.py         # Calls to the Census, Mapbox, and Census Geocoder
├── schemas/
│   └── population.py         # Pydantic response models
├── tests/
│   ├── conftest.py           # Shared test setup
│   ├── helpers.py            # Fake API responses and sample data
│   ├── test_census.py        # Census data tests
│   ├── test_geocoding.py     # Mapbox and Census Geocoder tests
│   └── test_routes.py        # Endpoint, error, and rate limit tests
├── .github/
│   ├── workflows/tests.yml   # GitHub Actions checks
│   └── dependabot.yml        # Dependency updates
├── .pre-commit-config.yaml   # Checks run before every commit
├── Dockerfile
├── pyproject.toml            # Project, pytest, coverage, Ruff, and mypy settings
├── requirements.txt          # Packages needed to run
├── requirements-dev.txt      # Adds testing and code-check tools
├── .env.example              # Names of the keys to set
└── LICENSE
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
pre-commit install
```

`requirements.txt` holds what the app needs to run. `requirements-dev.txt` adds the testing and code-check tools.

## Environment Variables

Copy `.env.example` to a new file named `.env` in the project folder, then add your keys:

```text
CENSUS_API_KEY=your_census_api_key
MAPBOX_TOKEN=your_mapbox_token
```

Do not commit your `.env` file. If a key is missing, the app stops at startup with an error naming it.

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

The container runs as a non-root user and listens on the `PORT` environment variable (default `8000`).

## Endpoints

### `GET /v1/population/{state}`

Example: `/v1/population/Alaska`

```json
{
    "state": "Alaska",
    "population": 735706
}
```

### `GET /v1/population/{state}/{city}`

Example: `/v1/population/Hawaii/Kailua`

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

If no Census place has the name, the API looks up the name with Mapbox, finds which Census place contains it, and returns that place with a note.

Example: `/v1/population/Hawaii/Kailua-Kona`

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

### `GET /health`

Returns `{"status": "ok"}` when the app is running. Hosting services call it to check that the app is up. It makes no outside API calls and is not rate limited.

## Errors

* `404` with `State not found` or `City not found` when there is no match.
* `422` when a state or city name is blank or too long (state: 2 to 50 characters, city: 1 to 100 characters).
* `429` with `Too many requests, try again later` when a client sends more than 60 requests in a minute.
* `502` with `External data service error` if the Census, Mapbox, or the Census Geocoder fails, doesn't answer within 10 seconds, or sends data in an unexpected shape.

Each `502` is logged with the error type and the endpoint path. API keys are never written to the logs.

## Running Tests and Checks

```powershell
python -m pytest
ruff check .
ruff format --check .
mypy .
```

Tests use fake API responses, so they need no internet or real keys. The test run fails if coverage drops below 90%.

GitHub Actions runs all four on every push. pre-commit runs Ruff and mypy before every commit.

## Challenges

* **Census place names include a type.** The Census lists places such as `Anchorage municipality` or `Kailua CDP`. The API drops the type before matching, so users can search by the plain name.
* **Many places share a name.** Hawaii has two places named Kailua. The API returns every match instead of guessing.
* **Common names the Census doesn't use.** Names like `Kailua-Kona` are not Census places. The API finds the name's coordinates with Mapbox, then uses the Census Geocoder to find the Census place at those coordinates.
* **API keys in logs.** httpx logs every request URL, and the Census and Mapbox URLs contain API keys. The app turns off those log lines and logs only the error type and endpoint path.
* **Bad data from outside services.** A changed or broken response from an outside API returns a clean `502` instead of crashing the app.
* **Rate limiting behind a proxy.** Render sends requests through a proxy. The Docker image trusts the forwarded client address, so each client is counted separately.

## Limitations

* Population numbers are ACS 5-year estimates, not exact counts.
* When a name is found through Mapbox, the population is for the whole Census place that contains it, not just the named area.
* Areas outside any Census place (such as rural land) return `404`.
* The cache and the rate limit counts are kept in memory, so they reset when the app restarts.
* Moving to a newer survey year means changing the Census URL and redeploying.

## Data Sources

* **US Census Bureau API**: American Community Survey 5-year estimates, table B01003 (total population).
* **Mapbox**: finds coordinates for names the Census doesn't list.
* **Census Geocoder**: finds which Census place contains those coordinates.

## License

MIT. See [LICENSE](LICENSE).