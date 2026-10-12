"""Fake HTTP responses and sample data shared by the tests."""

from typing import Any

import httpx


class FakeAPI:
    """Answers HTTP requests with canned responses, in order, and records them."""

    def __init__(self, *responses: httpx.Response | Exception) -> None:
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []
        self.client = httpx.AsyncClient(transport=httpx.MockTransport(self.handle))

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response


def ok(data: Any) -> httpx.Response:
    return httpx.Response(200, json=data)


def status(code: int) -> httpx.Response:
    return httpx.Response(code)


STATES = [
    ["NAME", "B01003_001E", "state"],
    ["Alaska", "735706", "02"],
    ["Hawaii", "1440000", "15"],
]

HAWAII_PLACES = [
    ["NAME", "B01003_001E", "state", "place"],
    ["East Honolulu CDP, Hawaii", "51360", "15", "06290"],
    ["Kailua CDP (Hawaii County), Hawaii", "21818", "15", "23000"],
    ["Kailua CDP (Honolulu County), Hawaii", "39640", "15", "23150"],
    ["Urban Honolulu CDP, Hawaii", "345482", "15", "71550"],
]

ALASKA_PLACES = [
    ["NAME", "B01003_001E", "state", "place"],
    ["Anchorage municipality, Alaska", "291538", "02", "03000"],
    ["Fairbanks city, Alaska", "32515", "02", "24230"],
]

KAILUA_HAWAII_COUNTY = {
    "place": "Kailua CDP (Hawaii County), Hawaii",
    "population": 21818,
}

KAILUA_HONOLULU_COUNTY = {
    "place": "Kailua CDP (Honolulu County), Hawaii",
    "population": 39640,
}


def mapbox_response(region: str = "Hawaii") -> httpx.Response:
    return ok(
        {
            "features": [
                {
                    "geometry": {"coordinates": [-155.997, 19.6419]},
                    "properties": {"context": {"region": {"name": region}}},
                }
            ]
        }
    )


def geocoder_response(layers: dict[str, list[dict[str, str]]]) -> httpx.Response:
    return ok({"result": {"geographies": layers}})
