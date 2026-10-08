import pytest

from services.population import get_census_rows


@pytest.fixture(autouse=True)
def clear_cache():
    get_census_rows.cache_clear()
