# Changelog

All notable changes to this project are listed here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- pre-commit runs Ruff from the project's `.venv`, so it uses the same version as `uv.lock`.
- Dependabot skips Python version updates for the Docker image. The project stays on Python 3.13 until a planned upgrade.
- Updated FastAPI to 0.143.0, Ruff to 0.17.0, and setup-uv to 10.3.0.
- The Docker image starts uvicorn directly, with its plain-text request log turned off, so each request is logged once as JSON.
- Requests to `/health` are no longer logged.
- GitHub Actions deploys to Render through a deploy hook after the test and Docker build checks pass on `main`. Render's own Auto-Deploy is off.

## [1.0.0] - 2026-10-12

### Added

- Retries with exponential backoff for temporary failures from the Census, Mapbox, and the Census Geocoder.
- JSON logs with a request ID on every line, and an `X-Request-ID` header on every response.
- A log line for every request, with method, path, status, and duration.
- Error logs for outside services include the service's host name and status code, never the full URL.
- Sentry error tracking in production, set up so API keys are never sent.
- Rate limit of 60 requests per minute per client. `/health` is not limited.
- `422` errors for blank or too-long state and city names.
- `502` errors when an outside service sends data in an unexpected shape.
- Endpoint summaries, field descriptions, examples, and error responses in `/docs`.
- MIT license.
- mypy type checking, pre-commit hooks, Dependabot, and a 90% test coverage minimum.
- pip-audit checks for packages with known security issues, run in GitHub Actions.
- pre-commit checks for trailing spaces, file endings, YAML and TOML syntax, merge conflicts, large files, and an out-of-date `uv.lock`.
- A Docker image build in GitHub Actions.
- Optional settings listed in `.env.example`.
- README sections for Try It, How It Works (with a request-flow diagram), Deployment, Future Improvements, and Author.

### Changed

- Population routes moved to `/v1/population/...`.
- Outside API calls are now async, with one shared HTTP client.
- Mapbox lookups make no extra Census call, because place data is cached per state.
- Tests split by feature, with type hints.
- Packages are managed with uv, with exact versions locked in `uv.lock`. GitHub Actions and the Docker image install from it.
- `ENVIRONMENT` and `LOG_LEVEL` accept only valid values, so a typo stops the app at startup.
- The version number is read from `pyproject.toml`, so it is set in one place.
- Any warning now fails the test run.
- GitHub Actions runs with read-only access.
- The Docker image leaves out git history, tests, and CI files.
- Tests use `httpx2` for FastAPI's test client, which removes a deprecation warning.
- The README Tech Stack is grouped by purpose, and each challenge lists its problem and its solution.

### Removed

- The old routes at `/population/...`.
- `requirements.txt` and `requirements-dev.txt`, replaced by `pyproject.toml` and `uv.lock`.
