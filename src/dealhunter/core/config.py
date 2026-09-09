from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DEALHUNTER_",
        env_file=".env",
        extra="ignore",
    )

    env: str = "local"
    database_url: str = "sqlite:///./dealhunter.db"
    redis_url: str = "redis://localhost:6379/0"
    shopee_base_url: str = "https://shopee.vn"
    shopee_transport: str = "http"
    shopee_timeout_seconds: float = 30.0
    shopee_max_concurrency: int = 3
    raw_evidence_retention: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
