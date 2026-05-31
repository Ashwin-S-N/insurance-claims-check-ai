from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Plum Claims AI"
    database_url: str = "sqlite:///./claims.db"
    policy_terms_path: Path = Path(__file__).resolve().parents[2] / "policy_terms.json"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    enable_gemini: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_prefix="PLUM_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
