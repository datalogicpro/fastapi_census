# Changelog

All notable changes to this project are listed here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-11

### Added

- Retries with exponential backoff for temporary failures from the Census, Mapbox, and the Census Geocoder.
- JSON logs with a request ID on every line, and an `X-Request-ID` header on every response.
- A log line for every request, with method, path, status, and duration.
- Sentry error tracking in production, set up so API keys are never sent.
- Rate limit of 60 requests per minute per client. `/health` is not limited.
- `422` errors for blank or too-long state and city names.
- `502` errors when an outside service sends data in an unexpected shape.
- Endpoint summaries, field descriptions, examples, and error responses in `/docs`.
- MIT license.
- mypy type checking, pre-commit hooks, Dependabot, and a 90% test coverage minimum.

### Changed

- Population routes moved to `/v1/population/...`.
- Outside API calls are now async, with one shared HTTP client.
- Mapbox lookups make no extra Census call, because place data is cached per state.
- Tests split by feature, with type hints.

### Removed

- The old routes at `/population/...`.