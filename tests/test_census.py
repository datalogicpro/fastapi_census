import httpx
import pytest

from schemas.population import Place
from services.errors import ExternalDataError
from services.population import (
    StateInfo,
    get_census_rows,
    get_place_by_code,
    get_places,
    get_state,
    short_place_name,
)
from tests.helpers import (
    ALASKA_PLACES,
    HAWAII_PLACES,
    KAILUA_HAWAII_COUNTY,
    KAILUA_HONOLULU_COUNTY,
    STATES,
    FakeAPI,
    ok,
    status,
)

pytestmark = pytest.mark.anyio


async def test_census_rows_skip_header() -> None:
    api = FakeAPI(ok(STATES))

    rows = await get_census_rows(api.client, "state:*")

    assert rows == STATES[1:]


async def test_census_request_params() -> None:
    api = FakeAPI(ok(HAWAII_PLACES))

    await get_census_rows(api.client, "place:*", "15")

    params = api.requests[0].url.params
    assert params["get"] == "NAME,B01003_001E"
    assert params["for"] == "place:*"
    assert params["in"] == "state:15"
    assert "key" in params


async def test_census_rows_are_cached() -> None:
    api = FakeAPI(ok(STATES))

    await get_state(api.client, "Alaska")
    await get_state(api.client, "Hawaii")

    assert len(api.requests) == 1


async def test_census_client_error() -> None:
    api = FakeAPI(status(400))

    with pytest.raises(httpx.HTTPStatusError):
        await get_state(api.client, "Alaska")


@pytest.mark.parametrize(
    "bad_response",
    [
        ok({}),
        ok([]),
        ok([["NAME", "B01003_001E", "state"], ["Alaska", "735706"]]),
        httpx.Response(200, text="not json"),
    ],
)
async def test_census_bad_data(bad_response: httpx.Response) -> None:
    api = FakeAPI(bad_response)

    with pytest.raises(ExternalDataError):
        await get_state(api.client, "Alaska")


async def test_get_state_found() -> None:
    api = FakeAPI(ok(STATES))

    result = await get_state(api.client, " alaska ")

    assert result == StateInfo(code="02", name="Alaska", population=735706)


async def test_get_state_not_found() -> None:
    api = FakeAPI(ok(STATES))

    assert await get_state(api.client, "Nowhere") is None


async def test_get_state_bad_population() -> None:
    api = FakeAPI(ok([["NAME", "B01003_001E", "state"], ["Alaska", None, "02"]]))

    with pytest.raises(ExternalDataError):
        await get_state(api.client, "Alaska")


@pytest.mark.parametrize(
    ("census_name", "short_name"),
    [
        ("Anchorage municipality, Alaska", "Anchorage"),
        ("Fairbanks city, Alaska", "Fairbanks"),
        ("Kailua CDP (Honolulu County), Hawaii", "Kailua"),
        ("Urban Honolulu CDP, Hawaii", "Urban Honolulu"),
    ],
)
def test_short_place_name(census_name: str, short_name: str) -> None:
    assert short_place_name(census_name) == short_name


async def test_get_places_returns_every_match() -> None:
    api = FakeAPI(ok(HAWAII_PLACES))

    result = await get_places(api.client, "15", "kailua")

    assert [place.model_dump() for place in result] == [
        KAILUA_HAWAII_COUNTY,
        KAILUA_HONOLULU_COUNTY,
    ]


async def test_get_places_drops_place_type() -> None:
    api = FakeAPI(ok(ALASKA_PLACES))

    result = await get_places(api.client, "02", "Anchorage")

    assert result == [Place(place="Anchorage municipality, Alaska", population=291538)]


async def test_get_places_skips_partial_match() -> None:
    api = FakeAPI(ok(HAWAII_PLACES))

    assert await get_places(api.client, "15", "Honolulu") == []


async def test_get_places_bad_population() -> None:
    rows = [HAWAII_PLACES[0], ["Kailua CDP, Hawaii", "lots", "15", "23150"]]
    api = FakeAPI(ok(rows))

    with pytest.raises(ExternalDataError):
        await get_places(api.client, "15", "Kailua")


async def test_get_place_by_code() -> None:
    api = FakeAPI(ok(HAWAII_PLACES))

    result = await get_place_by_code(api.client, "15", "23000")

    assert result is not None
    assert result.model_dump() == KAILUA_HAWAII_COUNTY


async def test_get_place_by_code_not_found() -> None:
    api = FakeAPI(ok(HAWAII_PLACES))

    assert await get_place_by_code(api.client, "15", "99999") is None


async def test_get_place_by_code_bad_population() -> None:
    rows = [HAWAII_PLACES[0], ["Kailua CDP, Hawaii", None, "15", "23000"]]
    api = FakeAPI(ok(rows))

    with pytest.raises(ExternalDataError):
        await get_place_by_code(api.client, "15", "23000")
