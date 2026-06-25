import json
from typing import Any
from pydantic import AnyHttpUrl, BeforeValidator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

def _coerce_cors_origins(v: Any) -> list[str]:
    if isinstance(v, str):
        if not v.strip():
            return []
        try:
            origins = json.loads(v)
            if isinstance(origins, list):
                return [str(origin) for origin in origins]
        except (json.JSONDecodeError, TypeError):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
    elif isinstance(v, list):
        return [str(origin) for origin in v]
    return []

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Core Settings
    PROJECT_NAME: str = "HumanityOS"
    ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8080
    SECRET_KEY: str = "placeholder_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS Settings
    BACKEND_CORS_ORIGINS: Annotated[
        list[str], 
        BeforeValidator(_coerce_cors_origins)
    ] = []

    # Postgres Settings
    DATABASE_URL: str = "postgresql+asyncpg://humanity:humanity_password@localhost:5432/humanityos"

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # ChromaDB Settings
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8001

    # Google Gemini Settings
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # MCP Settings
    MCP_SERVER_URLS: Annotated[
        list[str],
        BeforeValidator(_coerce_cors_origins)
    ] = []

    # Logging
    LOG_LEVEL: str = "INFO"
    STRUCTURED_LOGGING: bool = False

    # Security
    FIREBASE_PROJECT_ID: str = "humanityos-prod"
    RATE_LIMIT_PER_MINUTE: int = 60

settings = Settings()
