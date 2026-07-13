from functools import cached_property

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DODOMONEY_",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = "sqlite:///./dodomoney.db"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins_raw: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("DODOMONEY_CORS_ORIGINS", "DODOMONEY_CORS_ORIGINS_RAW"),
    )

    @cached_property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


settings = Settings()
