from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    census_api_key: SecretStr
    mapbox_token: SecretStr


settings = Settings()
