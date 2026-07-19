from functools import cached_property

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DODOMONEY_",
        extra="ignore",
    )

    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("DODOMONEY_ENV", "DODOMONEY_ENVIRONMENT"),
    )
    database_url: str = "sqlite:///./dodomoney.db"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    redis_url: str = "redis://127.0.0.1:6379/0"
    verification_code_secret: str = "change-me-in-production"
    verification_code_ttl_seconds: int = 300
    verification_send_cooldown_seconds: int = 60
    verification_max_attempts: int = 5
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "no-reply@dodomoney.local"
    smtp_use_ssl: bool = False
    smtp_use_tls: bool = True
    expose_verification_code: bool = False
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    vision_model: str | None = None
    llm_timeout_seconds: float = 30.0
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias=AliasChoices("DODOMONEY_CORS_ORIGINS", "DODOMONEY_CORS_ORIGINS_RAW"),
    )
    cors_origin_regex: str | None = r"http://(localhost|127\.0\.0\.1):\d+"

    @cached_property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment == "production" and len(self.verification_code_secret) < 32:
            raise ValueError("生产环境的 DODOMONEY_VERIFICATION_CODE_SECRET 至少需要 32 个字符")
        if self.environment == "production" and self.expose_verification_code:
            raise ValueError("生产环境禁止回显邮箱验证码")
        if self.environment == "production" and not self.smtp_host:
            raise ValueError("生产环境必须配置 SMTP 邮件服务")
        return self


settings = Settings()
