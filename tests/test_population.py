import pytest
import requests
from fastapi.testclient import TestClient

from main import app
from services.population import get_places, get_state

client = TestClient(app)

STATES = [
    ["NAME", "B01003_001E", "state"],
    ["Alaska", "735706", "02"],
    ["Hawaii", "1440000", "15"],
]

HAWAII_PLACES = [
    ["NAME", "B01003_001E", "state", "place"],
    ["East Honolulu CDP, Hawaii", "51360", "15", "06290"],
    ["Kailua CDP (Honolulu County), Hawaii", "39640", "15", "23150"],
    ["Urban Honolulu CDP, Hawaii", "345482", "15", "71550"],
]


class FakeResponse:
    def __init__(self, data=None, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_get_state_found(monkeypatch):
    monkeypatch.setattr("requests.get", lambda url, **kwargs: FakeResponse(STATES))

    result = get_state("alaska")

    assert result == {"code": "02", "state": "Alaska", "population": 735706}


def test_get_state_not_found(monkeypatch):
    monkeypatch.setattr("requests.get", lambda url, **kwargs: FakeResponse(STATES))

    assert get_state("Nowhere") is None


def test_get_places_exact_match(monkeypatch):
    monkeypatch.setattr(
        "requests.get", lambda url, **kwargs: FakeResponse(HAWAII_PLACES)
    )

    result = get_places("15", "Kailua")

    assert result == [
        {"place": "Kailua CDP (Honolulu County), Hawaii", "population": 39640}
    ]


def test_get_places_skips_partial_match(monkeypatch):
    monkeypatch.setattr(
        "requests.get", lambda url, **kwargs: FakeResponse(HAWAII_PLACES)
    )

    assert get_places("15", "Honolulu") == []


def test_census_http_error(monkeypatch):
    monkeypatch.setattr(
        "requests.get", lambda url, **kwargs: FakeResponse(status_code=500)
    )

    with pytest.raises(requests.HTTPError):
        get_state("Alaska")


def test_main_state_population(monkeypatch):
    monkeypatch.setattr("requests.get", lambda url, **kwargs: FakeResponse(STATES))

    response = client.get("/population/Alaska")

    assert response.status_code == 200
    assert response.json() == {"state": "Alaska", "population": 735706}


def test_main_city_population(monkeypatch):
    responses = [FakeResponse(STATES), FakeResponse(HAWAII_PLACES)]

    monkeypatch.setattr("requests.get", lambda url, **kwargs: responses.pop(0))

    response = client.get("/population/Hawaii/Kailua")

    assert response.status_code == 200
    assert response.json()["state"] == "Hawaii"
    assert len(response.json()["places"]) == 1


def test_main_state_not_found(monkeypatch):
    monkeypatch.setattr("requests.get", lambda url, **kwargs: FakeResponse(STATES))

    response = client.get("/population/Nowhere")

    assert response.status_code == 404
    assert response.json() == {"detail": "State not found"}


def test_main_city_not_found(monkeypatch):
    responses = [
        FakeResponse(STATES),
        FakeResponse(HAWAII_PLACES),
        FakeResponse({"features": []}),
    ]

    monkeypatch.setattr("requests.get", lambda url, **kwargs: responses.pop(0))

    response = client.get("/population/Hawaii/Nowhere")

    assert response.status_code == 404
    assert response.json() == {"detail": "City not found"}


def test_main_city_found_through_mapbox(monkeypatch):
    responses = [
        FakeResponse(STATES),
        FakeResponse(HAWAII_PLACES),
        FakeResponse(
            {
                "features": [
                    {
                        "geometry": {"coordinates": [-155.997, 19.6419]},
                        "properties": {"context": {"region": {"name": "Hawaii"}}},
                    }
                ]
            }
        ),
        FakeResponse(
            {
                "result": {
                    "geographies": {
                        "Census Designated Places": [{"STATE": "15", "PLACE": "23000"}]
                    }
                }
            }
        ),
        FakeResponse(
            [
                ["NAME", "B01003_001E", "state", "place"],
                ["Kailua CDP (Hawaii County), Hawaii", "21818", "15", "23000"],
            ]
        ),
    ]

    monkeypatch.setattr("requests.get", lambda url, **kwargs: responses.pop(0))

    response = client.get("/population/Hawaii/Kailua-Kona")

    assert response.status_code == 200
    assert response.json() == {
        "state": "Hawaii",
        "places": [
            {"place": "Kailua CDP (Hawaii County), Hawaii", "population": 21818}
        ],
        "note": (
            "The Census has no place named Kailua-Kona. "
            "It lies within Kailua CDP (Hawaii County), Hawaii."
        ),
    }


def test_main_mapbox_wrong_state_skipped(monkeypatch):
    responses = [
        FakeResponse(STATES),
        FakeResponse(HAWAII_PLACES),
        FakeResponse(
            {
                "features": [
                    {
                        "geometry": {"coordinates": [-118.0756, 33.8315]},
                        "properties": {"context": {"region": {"name": "California"}}},
                    }
                ]
            }
        ),
    ]

    monkeypatch.setattr("requests.get", lambda url, **kwargs: responses.pop(0))

    response = client.get("/population/Hawaii/Kona")

    assert response.status_code == 404


def test_main_geocoder_finds_no_place(monkeypatch):
    responses = [
        FakeResponse(STATES),
        FakeResponse(HAWAII_PLACES),
        FakeResponse(
            {
                "features": [
                    {
                        "geometry": {"coordinates": [-155.5, 19.5]},
                        "properties": {"context": {"region": {"name": "Hawaii"}}},
                    }
                ]
            }
        ),
        FakeResponse({"result": {"geographies": {}}}),
    ]

    monkeypatch.setattr("requests.get", lambda url, **kwargs: responses.pop(0))

    response = client.get("/population/Hawaii/Volcano National Park")

    assert response.status_code == 404
    assert response.json() == {"detail": "City not found"}


def test_main_census_error_returns_502(monkeypatch):
    monkeypatch.setattr(
        "requests.get", lambda url, **kwargs: FakeResponse(status_code=500)
    )

    response = client.get("/population/Alaska")

    assert response.status_code == 502
    assert response.json() == {"detail": "External data service error"}


def test_main_timeout_returns_502(monkeypatch):
    def fake_get(url, **kwargs):
        raise requests.Timeout()

    monkeypatch.setattr("requests.get", fake_get)

    response = client.get("/population/Alaska")

    assert response.status_code == 502
    assert response.json() == {"detail": "External data service error"}


def test_requests_use_timeout(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(kwargs)
        return FakeResponse(STATES)

    monkeypatch.setattr("requests.get", fake_get)

    get_state("Alaska")

    assert calls[0]["timeout"] == 10


def test_census_rows_are_cached(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(kwargs)
        return FakeResponse(STATES)

    monkeypatch.setattr("requests.get", fake_get)

    get_state("Alaska")
    get_state("Hawaii")

    assert len(calls) == 1
