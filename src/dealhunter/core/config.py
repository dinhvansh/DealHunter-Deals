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

    chrome_profile_dir: str = "./data/chrome-profile"
    chrome_headless: bool = True
    chrome_executable_path: str | None = None
    browser_login_public_url: str | None = None

    secret_key: str | None = None
    secret_key_file: str = "./data/master.key"
    session_days: int = 30
    session_cookie_secure: bool = False

    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    affiliate_provider: str = "generic"
    affiliate_key: str = "aff_id"
    affiliate_value: str = "demo"

    account_verification_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
