from collections.abc import Callable, Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from config import settings
from main import app
from rate_limit import limiter
from services.http_client import get_http_client
from services.population import census_cache
from tests.helpers import FakeAPI


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    census_cache.clear()
    limiter.reset()

    # Retries happen right away in tests, with no waiting
    monkeypatch.setattr(settings, "retry_backoff", 0)

    yield

    app.dependency_overrides.clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def fake_api() -> Callable[..., FakeAPI]:
    """Makes the app's routes use a FakeAPI instead of the real internet."""

    def install(*responses: httpx.Response | Exception) -> FakeAPI:
        api = FakeAPI(*responses)
        app.dependency_overrides[get_http_client] = lambda: api.client
        return api

    return install
