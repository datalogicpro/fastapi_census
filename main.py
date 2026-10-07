import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from routes.population import router as population_router


app = FastAPI()


@app.exception_handler(requests.RequestException)
def handle_request_error(request: Request, exc: requests.RequestException):
    return JSONResponse(
        status_code=502,
        content={"detail": "External data service error"}
    )


app.include_router(population_router)