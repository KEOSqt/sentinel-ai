import json
from typing import Annotated, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    # NoDecode stops pydantic-settings from JSON-decoding this itself, so a
    # plain comma-separated value does not crash startup with a bare
    # SettingsError. Both forms are accepted; see _parse_cors_origins.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3111"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        raw = value.strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]

        # Documented form: a JSON array.
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"SENTINEL_CORS_ORIGINS looks like JSON but is not valid: {exc.msg}. "
                    "Use a JSON array such as [\"http://localhost:3000\"], "
                    "or a comma-separated list such as http://localhost:3000."
                ) from exc
            if not isinstance(parsed, list):
                raise ValueError(f"SENTINEL_CORS_ORIGINS must be a list of origins, got {type(parsed).__name__}.")
            return [str(item).strip() for item in parsed if str(item).strip()]

        # A JSON object is never a valid origin list; reject it rather than
        # silently treating the whole thing as one nonsense origin.
        if raw.startswith("{"):
            raise ValueError('SENTINEL_CORS_ORIGINS must be a list of origins, not an object. Use ["http://localhost:3000"].')

        # A single quoted origin, e.g. '"http://localhost:3000"'.
        if raw.startswith('"'):
            if not (raw.endswith('"') and len(raw) >= 2):
                raise ValueError(f"SENTINEL_CORS_ORIGINS has an unterminated quote: {raw!r}.")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"SENTINEL_CORS_ORIGINS is not a valid quoted origin: {exc.msg}.") from exc
            if isinstance(parsed, str):
                return [parsed.strip()] if parsed.strip() else []

        # Convenience form: comma-separated.
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        """Credentials cannot be combined with a wildcard origin.

        The CORS spec forbids ``Access-Control-Allow-Origin: *`` alongside
        ``Access-Control-Allow-Credentials: true``; browsers reject it.
        """
        return "*" not in self.cors_origins


settings = Settings()