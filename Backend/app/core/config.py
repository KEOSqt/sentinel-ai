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
    # Origins allowed to call the API. Set as JSON, e.g.
    # SENTINEL_CORS_ORIGINS='["http://localhost:3000"]'
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def cors_allow_credentials(self) -> bool:
        """Credentials cannot be combined with a wildcard origin.

        The CORS spec forbids ``Access-Control-Allow-Origin: *`` alongside
        ``Access-Control-Allow-Credentials: true``; browsers reject it.
        """
        return "*" not in self.cors_origins


settings = Settings()