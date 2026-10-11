from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    census_api_key: SecretStr
    mapbox_token: SecretStr
    request_timeout: float = 10
    user_agent: str = "fastapi-census (github.com/datalogicpro/fastapi_census)"
    rate_limit: str = "60/minute"


settings = Settings()
