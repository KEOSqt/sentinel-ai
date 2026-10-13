from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SENTINEL_", extra="ignore")

    app_name: str = "SentinelAI"
    version: str = "0.1.0"
    database_url: str = "sqlite:///./sentinel.db"
    max_upload_bytes: int = 10 * 1024 * 1024
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    nvd_api_key: str | None = None
    nvd_enabled: bool = True
    data_dir: Path = Path("./data")


settings = Settings()
