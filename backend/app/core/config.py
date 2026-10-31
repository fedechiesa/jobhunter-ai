from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    database_url: PostgresDsn
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    sources_file: Path = ROOT / "config" / "sources.json"
    sync_interval_seconds: int = Field(default=3600, ge=60, le=604800)
    provider_timeout_seconds: float = Field(default=10, ge=1, le=30)
    provider_max_attempts: int = Field(default=2, ge=1, le=3)
    provider_request_delay_seconds: float = Field(default=0.3, ge=0.25, le=10)
    source_min_interval_seconds: int = Field(default=60, ge=0, le=86400)
    source_error_backoff_seconds: int = Field(default=60, ge=0, le=86400)
    profile_draft_file: Path = ROOT / "private" / "profile.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
