import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from rate_limit import limiter
from routes.health import router as health_router
from routes.population import router as population_router
from services.errors import ExternalDataError
from services.http_client import create_http_client

logger = logging.getLogger(__name__)

# httpx logs every request URL at INFO level, and those URLs contain API keys
logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # One shared HTTP client for the whole app, closed on shutdown
    async with create_http_client() as client:
        app.state.http_client = client
        yield


app = FastAPI(
    title="Census Population API",
    description="US Census population data for states, cities, and towns.",
    version="1.0.0",
    contact={"name": "datalogicpro", "url": "https://github.com/datalogicpro"},
    license_info={"name": "MIT", "identifier": "MIT"},
    lifespan=lifespan,
)

app.state.limiter = limiter


@app.exception_handler(httpx.HTTPError)
@app.exception_handler(ExternalDataError)
def handle_external_error(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "External service failed: %s on %s", type(exc).__name__, request.url.path
    )
    return JSONResponse(
        status_code=502, content={"detail": "External data service error"}
    )


@app.exception_handler(RateLimitExceeded)
def handle_rate_limit(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=429, content={"detail": "Too many requests, try again later"}
    )


app.include_router(health_router)
app.include_router(population_router)
