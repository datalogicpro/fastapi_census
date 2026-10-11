import logging
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from config import settings
from services.http_client import create_http_client
from tests.helpers import (
    HAWAII_PLACES,
    KAILUA_HAWAII_COUNTY,
    KAILUA_HONOLULU_COUNTY,
    STATES,
    FakeAPI,
    geocoder_response,
    mapbox_response,
    ok,
    status,
)

FakeAPIFactory = Callable[..., FakeAPI]


def test_state_population(client: TestClient, fake_api: FakeAPIFactory) -> None:
    fake_api(ok(STATES))

    response = client.get("/v1/population/alaska")

    assert response.status_code == 200
    assert response.json() == {"state": "Alaska", "population": 735706}


def test_city_population(client: TestClient, fake_api: FakeAPIFactory) -> None:
    fake_api(ok(STATES), ok(HAWAII_PLACES))

    response = client.get("/v1/population/Hawaii/Kailua")

    assert response.status_code == 200
    assert response.json() == {
        "state": "Hawaii",
        "places": [KAILUA_HAWAII_COUNTY, KAILUA_HONOLULU_COUNTY],
        "note": None,
    }


def test_city_found_through_mapbox(
    client: TestClient, fake_api: FakeAPIFactory
) -> None:
    fake_api(
        ok(STATES),
        ok(HAWAII_PLACES),
        mapbox_response("Hawaii"),
        geocoder_response(
            {"Census Designated Places": [{"STATE": "15", "PLACE": "23000"}]}
        ),
    )

    response = client.get("/v1/population/Hawaii/Kailua-Kona")

    assert response.status_code == 200
    assert response.json() == {
        "state": "Hawaii",
        "places": [KAILUA_HAWAII_COUNTY],
        "note": (
            "The Census has no place named Kailua-Kona. "
            "It lies within Kailua CDP (Hawaii County), Hawaii."
        ),
    }


def test_repeat_requests_use_cache(
    client: TestClient, fake_api: FakeAPIFactory
) -> None:
    api = fake_api(ok(STATES), ok(HAWAII_PLACES))

    client.get("/v1/population/Hawaii/Kailua")
    client.get("/v1/population/Hawaii/Kailua")

    assert len(api.requests) == 2


def test_state_not_found(client: TestClient, fake_api: FakeAPIFactory) -> None:
    fake_api(ok(STATES))

    response = client.get("/v1/population/Nowhere")

    assert response.status_code == 404
    assert response.json() == {"detail": "State not found"}


def test_city_not_found(client: TestClient, fake_api: FakeAPIFactory) -> None:
    fake_api(ok(STATES), ok(HAWAII_PLACES), ok({"features": []}))

    response = client.get("/v1/population/Hawaii/Nowhere")

    assert response.status_code == 404
    assert response.json() == {"detail": "City not found"}


def test_geocoder_finds_no_place(client: TestClient, fake_api: FakeAPIFactory) -> None:
    fake_api(
        ok(STATES), ok(HAWAII_PLACES), mapbox_response("Hawaii"), geocoder_response({})
    )

    response = client.get("/v1/population/Hawaii/Volcano National Park")

    assert response.status_code == 404
    assert response.json() == {"detail": "City not found"}


def test_place_missing_from_census(
    client: TestClient, fake_api: FakeAPIFactory
) -> None:
    fake_api(
        ok(STATES),
        ok(HAWAII_PLACES),
        mapbox_response("Hawaii"),
        geocoder_response(
            {"Census Designated Places": [{"STATE": "15", "PLACE": "99999"}]}
        ),
    )

    response = client.get("/v1/population/Hawaii/Kailua-Kona")

    assert response.status_code == 404
    assert response.json() == {"detail": "City not found"}


@pytest.mark.parametrize(
    "path",
    [
        "/v1/population/%20%20",
        "/v1/population/" + "x" * 51,
        "/v1/population/Hawaii/%20",
        "/v1/population/Hawaii/" + "x" * 101,
    ],
)
def test_invalid_names(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 422


def test_old_unversioned_path_is_gone(client: TestClient) -> None:
    response = client.get("/population/Alaska")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "failure",
    [status(500), httpx.ConnectError("no network"), httpx.ReadTimeout("slow")],
)
def test_external_failure_returns_502(
    client: TestClient, fake_api: FakeAPIFactory, failure: Any
) -> None:
    fake_api(failure)

    response = client.get("/v1/population/Alaska")

    assert response.status_code == 502
    assert response.json() == {"detail": "External data service error"}


def test_bad_upstream_data_returns_502(
    client: TestClient, fake_api: FakeAPIFactory
) -> None:
    fake_api(ok({}))

    response = client.get("/v1/population/Alaska")

    assert response.status_code == 502


def test_external_error_is_logged_without_keys(
    client: TestClient,
    fake_api: FakeAPIFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake_api(status(500))

    client.get("/v1/population/Alaska")

    assert "HTTPStatusError on /v1/population/Alaska" in caplog.text
    assert settings.census_api_key.get_secret_value() not in caplog.text
    assert settings.mapbox_token.get_secret_value() not in caplog.text


def test_httpx_request_urls_are_not_logged() -> None:
    assert logging.getLogger("httpx").level == logging.WARNING


def test_rate_limit(client: TestClient, fake_api: FakeAPIFactory) -> None:
    # Only the first request reaches the fake API; the rest come from the cache
    fake_api(ok(STATES))
    limit = int(settings.rate_limit.split("/")[0])

    codes = [client.get("/v1/population/Alaska").status_code for _ in range(limit + 1)]

    assert codes[:limit] == [200] * limit
    assert codes[-1] == 429


def test_health_is_not_rate_limited(client: TestClient) -> None:
    limit = int(settings.rate_limit.split("/")[0])

    codes = {client.get("/health").status_code for _ in range(limit + 1)}

    assert codes == {200}


def test_http_client_settings() -> None:
    http_client = create_http_client()

    assert http_client.timeout.read == settings.request_timeout
    assert http_client.headers["User-Agent"] == settings.user_agent
    assert http_client.follow_redirects is True
