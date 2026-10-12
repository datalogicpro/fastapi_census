import httpx
import pytest

from services.errors import ExternalDataError
from services.population import get_coordinates, get_place_code
from tests.helpers import FakeAPI, geocoder_response, mapbox_response, ok, status

pytestmark = pytest.mark.anyio


async def test_coordinates_in_state() -> None:
    api = FakeAPI(mapbox_response("Hawaii"))

    result = await get_coordinates(api.client, "Kailua-Kona", "Hawaii")

    assert result == (-155.997, 19.6419)


async def test_coordinates_search_us_with_state() -> None:
    api = FakeAPI(ok({"features": []}))

    await get_coordinates(api.client, " Kailua-Kona ", "Hawaii")

    params = api.requests[0].url.params
    assert params["q"] == "Kailua-Kona, Hawaii"
    assert params["country"] == "us"


async def test_coordinates_skip_other_states() -> None:
    api = FakeAPI(mapbox_response("California"))

    assert await get_coordinates(api.client, "Kona", "Hawaii") is None


async def test_coordinates_not_found() -> None:
    api = FakeAPI(ok({"features": []}))

    assert await get_coordinates(api.client, "Nowhere", "Hawaii") is None


async def test_coordinates_client_error() -> None:
    api = FakeAPI(status(401))

    with pytest.raises(httpx.HTTPStatusError):
        await get_coordinates(api.client, "Kailua-Kona", "Hawaii")


@pytest.mark.parametrize(
    "bad_response",
    [
        ok([]),
        ok({"features": [{"properties": {}}]}),
        ok(
            {
                "features": [
                    {
                        "geometry": {},
                        "properties": {"context": {"region": {"name": "Hawaii"}}},
                    }
                ]
            }
        ),
    ],
)
async def test_coordinates_bad_data(bad_response: httpx.Response) -> None:
    api = FakeAPI(bad_response)

    with pytest.raises(ExternalDataError):
        await get_coordinates(api.client, "Kailua-Kona", "Hawaii")


async def test_place_code_incorporated_place_first() -> None:
    api = FakeAPI(
        geocoder_response(
            {
                "Incorporated Places": [{"STATE": "02", "PLACE": "03000"}],
                "Census Designated Places": [{"STATE": "02", "PLACE": "11111"}],
            }
        )
    )

    assert await get_place_code(api.client, -149.9, 61.2, "02") == "03000"


async def test_place_code_census_designated_place() -> None:
    api = FakeAPI(
        geocoder_response(
            {"Census Designated Places": [{"STATE": "15", "PLACE": "23000"}]}
        )
    )

    assert await get_place_code(api.client, -155.997, 19.6419, "15") == "23000"


async def test_place_code_skips_other_states() -> None:
    api = FakeAPI(
        geocoder_response(
            {"Census Designated Places": [{"STATE": "06", "PLACE": "23000"}]}
        )
    )

    assert await get_place_code(api.client, -155.997, 19.6419, "15") is None


async def test_place_code_none_found() -> None:
    api = FakeAPI(geocoder_response({}))

    assert await get_place_code(api.client, -155.5, 19.5, "15") is None


@pytest.mark.parametrize(
    "bad_response",
    [
        ok({}),
        geocoder_response({"Census Designated Places": [{"STATE": "15"}]}),
        httpx.Response(200, text="not json"),
    ],
)
async def test_place_code_bad_data(bad_response: httpx.Response) -> None:
    api = FakeAPI(bad_response)

    with pytest.raises(ExternalDataError):
        await get_place_code(api.client, -155.997, 19.6419, "15")
