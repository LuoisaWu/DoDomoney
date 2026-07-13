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
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: float = 30.0
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias=AliasChoices("DODOMONEY_CORS_ORIGINS", "DODOMONEY_CORS_ORIGINS_RAW"),
    )
    cors_origin_regex: str | None = r"http://(localhost|127\.0\.0\.1):\d+"

    @cached_property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


settings = Settings()
